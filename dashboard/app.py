"""
Falcon — Production-Grade Cinematic Dashboard

Run:
  pip install -r dashboard/requirements.txt
  streamlit run dashboard/app.py

Backend must be running:
  cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import base64
import json
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND_URL      = "http://127.0.0.1:8000"
HEALTH_TTL_SEC  = 10        # re-check backend every 10 s, not every render
NEON_YELLOW      = "#D4F000"
NEON_CYAN        = "#00F3FF"
BG_DARK          = "#050505"
BG_PANEL         = "#111111"
TEXT_MUTED       = "#999999"
TEXT_LIGHT       = "#E5E5E5"

st.set_page_config(
    page_title="Falcon — Driver Companion",
    page_icon="🦅",
    layout="wide",
)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  STYLES
# ╚══════════════════════════════════════════════════════════════════════════╝
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
      background: radial-gradient(circle at top, #151515 0%, #050505 45%, #000000 100%) !important;
      color: {TEXT_LIGHT} !important;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}

    .falcon-title {{
      font-size: min(8vw, 4rem);
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: {TEXT_LIGHT};
      line-height: 1;
    }}
    .falcon-subtitle {{
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.25em;
      color: {TEXT_MUTED};
    }}
    .metric-label {{
      font-size: 0.72rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: {TEXT_MUTED};
    }}
    .metric-value {{
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .glass-panel {{
      background: rgba(17,17,17,0.85);
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.06);
      box-shadow: 0 20px 60px rgba(0,0,0,0.80);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      padding: 1.1rem 1.4rem 1.3rem 1.4rem;
    }}
    .cockpit-shell {{
      border-radius: 28px;
      background: radial-gradient(circle at top, #1a1a1a 0%, #050505 55%, #000000 100%);
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 40px 120px rgba(0,0,0,0.95);
      padding: 1.5rem 1.8rem;
      position: relative;
      overflow: hidden;
    }}
    .hud-line {{
      height: 1px;
      width: 100%;
      background: linear-gradient(
        90deg,
        transparent 0%,
        {NEON_CYAN} 20%,
        {NEON_YELLOW} 50%,
        {NEON_CYAN} 80%,
        transparent 100%
      );
      opacity: 0.65;
      margin: 0.5rem 0 0.6rem 0;
    }}
    .hud-chip {{
      font-size: 0.72rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      border-radius: 999px;
      padding: 0.25rem 0.9rem;
      border: 1px solid rgba(255,255,255,0.18);
      background: radial-gradient(circle at top left, rgba(212,240,0,0.16) 0%, rgba(5,5,5,1) 55%);
      color: {TEXT_LIGHT};
      display: inline-block;
    }}
    .hud-chip span {{ color: {NEON_YELLOW}; }}
    .falcon-headline {{
      font-size: min(7vw, 3rem);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      line-height: 1.15;
    }}
    .falcon-headline span {{ color: {NEON_YELLOW}; }}
    .section-label {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.22em;
      color: {TEXT_MUTED};
      margin-bottom: 0.4rem;
    }}
    pre {{
      white-space: pre-wrap !important;
      word-break: break-word !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  CACHED HEALTH CHECK  — polls backend at most once every HEALTH_TTL_SEC
# ╚══════════════════════════════════════════════════════════════════════════╝
@st.cache_data(ttl=HEALTH_TTL_SEC, show_spinner=False)
def _fetch_health() -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}


def get_health():
    health = _fetch_health()
    backend_ok = health.get("status") == "ok"
    return health, backend_ok


# ╔══════════════════════════════════════════════════════════════════════════╗
#  HEADER
# ╚══════════════════════════════════════════════════════════════════════════╝
header_left, header_right = st.columns([3, 2])
with header_left:
    st.markdown("<div class='falcon-title'>FALCON</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='falcon-subtitle'>"
        "EDGE AI DRIVER COMPANION &nbsp;·&nbsp; LIVE IN-CABIN SAFETY TELEMETRY"
        "</div>",
        unsafe_allow_html=True,
    )
with header_right:
    st.markdown("<div class='section-label'>SESSION</div>", unsafe_allow_html=True)
    st.caption("All inference happens on-device. No frames leave the cabin.")

st.markdown("<div class='hud-line'></div>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  COCKPIT SECTION
# ╚══════════════════════════════════════════════════════════════════════════╝
health, backend_ok = get_health()
intro_col, cockpit_col = st.columns([1.3, 2.0])

with intro_col:
    st.markdown("<div class='section-label'>FALCON ENTRY · v2.1</div>", unsafe_allow_html=True)

    if backend_ok:
        drowsiness_ok  = health.get("drowsiness_loaded", False)
        distraction_ok = health.get("distraction_loaded", False)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='falcon-headline'>ENTER THE <span>COCKPIT</span></div>",
            unsafe_allow_html=True,
        )
        st.caption("Falcon locks onto the driver's face in real time — zero cloud latency.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='glass-panel'>"
            f"<div class='metric-label'>SYSTEM STATUS</div>"
            f"<div class='metric-value'>🟢 BACKEND ONLINE</div>"
            f"<div style='margin-top:0.4rem'></div>"
            f"<div class='metric-label'>DROWSINESS MODEL</div>"
            f"<div class='metric-value'>{'🟢 LOADED' if drowsiness_ok else '🔴 NOT LOADED'}</div>"
            f"<div style='margin-top:0.4rem'></div>"
            f"<div class='metric-label'>DISTRACTION MODEL</div>"
            f"<div class='metric-value'>{'🟢 LOADED' if distraction_ok else '🔴 NOT LOADED'}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='falcon-headline'><span>BACKEND OFFLINE</span></div>",
            unsafe_allow_html=True,
        )
        st.error(
            "Cannot reach backend at `http://0.0.0.1:8000`.  \n"
            "Run: `cd backend && uvicorn main:app --reload`"
        )
        st.markdown(
            "<div class='glass-panel'>"
            "<div class='metric-label'>FALCON ENTRY</div>"
            "<div class='metric-value'>SYSTEM STANDBY</div>"
            "<p style='margin-top:0.6rem;font-size:0.85rem;color:#bbbbbb;'>"
            "Backend must be online for live cockpit and HUD visuals."
            "</p></div>",
            unsafe_allow_html=True,
        )

with cockpit_col:
    st.markdown("<div class='section-label'>COCKPIT · LIVE IN-CABIN VIEW</div>", unsafe_allow_html=True)
    st.markdown("<div class='cockpit-shell'>", unsafe_allow_html=True)

    # HUD chips
    hc1, hc2, hc3 = st.columns([1.2, 1.2, 1.4])
    with hc1:
        st.markdown("<div class='hud-chip'>HUD MODE · <span>DRIVER</span></div>", unsafe_allow_html=True)
    with hc2:
        st.markdown("<div class='hud-chip'>ENGINE · <span>ON-DEVICE</span></div>", unsafe_allow_html=True)
    with hc3:
        st.markdown("<div class='hud-chip'>LATENCY · <span>&lt; 25 MS</span></div>", unsafe_allow_html=True)

    st.markdown("<div class='hud-line'></div>", unsafe_allow_html=True)

    car_col, screen_col = st.columns([1.4, 1.8])

    with car_col:
        st.markdown("<div class='metric-label'>ENTRY SEQUENCE</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:0.83rem;color:#bbbbbb;line-height:1.5;'>"
            "This block is the mount point for a Three.js / React Three Fiber supercar intro: "
            "door opens → camera glides into cabin → view settles on the dashboard screen.<br><br>"
            "Replace this placeholder with an <code>&lt;iframe&gt;</code> pointing to the "
            "Next.js frontend once it is deployed."
            "</p>",
            unsafe_allow_html=True,
        )
        st.image(
            "https://picsum.photos/seed/falcon-cockpit/640/360",
            width=True,
        )

    with screen_col:
        st.markdown("<div class='metric-label'>FALCON DASHBOARD · EMBEDDED</div>", unsafe_allow_html=True)
        st.caption("Live frames are analysed on-device. Toggle inference to begin.")

        screen_placeholder = st.empty()

        ctrl_a, ctrl_b = st.columns([1, 1])
        with ctrl_a:
            run_live = st.toggle("Start Live Inference", value=False)
        with ctrl_b:
            fps_target = st.slider("Target FPS", min_value=1, max_value=15, value=5)

        sm_cols = st.columns(5)
        state_ph   = sm_cols[0].empty()
        alert_ph   = sm_cols[1].empty()
        drowsy_ph  = sm_cols[2].empty()
        dist_ph    = sm_cols[3].empty()
        lat_ph     = sm_cols[4].empty()

        ALERT_ICONS = {0: "🟢", 1: "🟡", 2: "🔴"}
        STATE_LABELS = {
            "safe":       "🟢 Safe",
            "drowsy":     "🟡 Drowsy",
            "distracted": "🟠 Distracted",
            "critical":   "🔴 Critical",
            "unknown":    "⚪ Unknown",
        }

        if backend_ok and run_live:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                screen_placeholder.error(
                    "Could not open webcam (index 0). "
                    "Check System Preferences → Privacy → Camera."
                )
            else:
                frame_interval = 1.0 / fps_target
                try:
                    while run_live:
                        t0 = time.time()
                        ret, frame_bgr = cap.read()
                        if not ret:
                            screen_placeholder.warning("Dropped frame — retrying...")
                            time.sleep(0.05)
                            continue

                        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                        screen_placeholder.image(frame_rgb, channels="RGB")

                        _, buf = cv2.imencode(
                            ".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80]
                        )
                        b64 = base64.b64encode(buf.tobytes()).decode()

                        try:
                            resp = requests.post(
                                f"{BACKEND_URL}/infer",
                                json={"frame": b64},
                                timeout=3,
                            )
                            if resp.status_code == 200:
                                data       = resp.json()
                                latency_ms = (time.time() - t0) * 1000

                                d_state  = data.get("driver_state", "unknown")
                                a_level  = data.get("alert_level", 0)
                                drowsy   = data.get("drowsiness", "?")
                                d_conf   = data.get("drowsiness_confidence", 0.0)
                                distr    = data.get("distraction", "?")
                                di_conf  = data.get("distraction_confidence", 0.0)

                                state_ph.metric(
                                    "Driver State",
                                    STATE_LABELS.get(d_state, d_state),
                                )
                                alert_ph.metric(
                                    "Alert Level",
                                    f"{ALERT_ICONS.get(a_level, '')} {a_level}/2",
                                )
                                drowsy_ph.metric("Drowsiness", drowsy, f"{d_conf:.0%}")
                                dist_ph.metric("Distraction", distr, f"{di_conf:.0%}")
                                lat_ph.metric("Latency", f"{latency_ms:.0f} ms")
                            else:
                                screen_placeholder.warning(
                                    f"Backend error {resp.status_code}: {resp.text[:120]}"
                                )
                        except requests.exceptions.Timeout:
                            screen_placeholder.warning(
                                "Inference timed out — backend may be overloaded."
                            )
                        except Exception as exc:
                            screen_placeholder.error(f"Request failed: {exc}")

                        sleep_time = frame_interval - (time.time() - t0)
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                finally:
                    cap.release()
        else:
            screen_placeholder.info(
                "Toggle **Start Live Inference** above to begin streaming webcam frames "
                "through the Falcon detection pipeline."
            )
            for ph, label in [
                (state_ph,  "Driver State"),
                (alert_ph,  "Alert Level"),
                (drowsy_ph, "Drowsiness"),
                (dist_ph,   "Distraction"),
                (lat_ph,    "Latency"),
            ]:
                ph.metric(label, "—")

    st.markdown("</div>", unsafe_allow_html=True)  # /cockpit-shell

st.markdown("<br><br>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  MISSION STATEMENT
# ╚══════════════════════════════════════════════════════════════════════════╝
st.markdown("<div class='section-label'>MISSION</div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="falcon-headline">
      REDEFINING IN-CABIN SAFETY.<br>
      REAL-TIME EDGE AI. ZERO CLOUD LATENCY.
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("All inference is on-device, optimised for automotive-grade hardware.")
st.markdown("<br><br>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  DUAL DETECTION PANELS
# ╚══════════════════════════════════════════════════════════════════════════╝
st.markdown("<div class='section-label'>DUAL DETECTION SYSTEM · v2.1</div>", unsafe_allow_html=True)

dd_l, dd_r = st.columns(2)

with dd_l:
    st.markdown(
        f"<div class='glass-panel'>"
        f"<div class='metric-label'>DROWSINESS</div>"
        f"<div class='metric-value'>MediaPipe FaceMesh + EAR / MAR / PERCLOS</div>"
        f"<p style='margin-top:0.6rem;font-size:0.85rem;color:{TEXT_LIGHT};line-height:1.5;'>"
        "468 facial landmarks. Sub-20 ms inference. EAR threshold 0.25. "
        "PERCLOS window 60 frames."
        "</p>"
        "<pre style='margin-top:0.6rem;font-size:0.78rem;background:#0b0b0b;"
        f"border-radius:10px;padding:0.6rem 0.9rem;color:{TEXT_LIGHT};'>"
        '{\n  &quot;state&quot;: &quot;DROWSY&quot;,\n  &quot;ear&quot;: 0.18,\n  &quot;alert&quot;: true\n}'
        "</pre>"
        "</div>",
        unsafe_allow_html=True,
    )

with dd_r:
    st.markdown(
        f"<div class='glass-panel'>"
        f"<div class='metric-label'>DISTRACTION</div>"
        f"<div class='metric-value'>EfficientNet-B0 · Gaze + Head Pose</div>"
        f"<p style='margin-top:0.6rem;font-size:0.85rem;color:{TEXT_LIGHT};line-height:1.5;'>"
        "Context-aware 6-class output. GPU-optional. "
        "head_yaw ±35°, gaze off-road detection, phone presence."
        "</p>"
        "<pre style='margin-top:0.6rem;font-size:0.78rem;background:#0b0b0b;"
        f"border-radius:10px;padding:0.6rem 0.9rem;color:{TEXT_LIGHT};'>"
        '{\n  &quot;state&quot;: &quot;DISTRACTED&quot;,\n  &quot;head_yaw&quot;: 32.1,\n  &quot;phone&quot;: true\n}'
        "</pre>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SESSION LOGS + ANALYTICS
# ╚══════════════════════════════════════════════════════════════════════════╝
logs_dir = Path("logs")
csvs     = sorted(logs_dir.glob("session_*.csv"), reverse=True) if logs_dir.exists() else []

st.markdown("<div class='section-label'>SESSION LOGS</div>", unsafe_allow_html=True)

if not csvs:
    st.info(
        "No session logs found yet. "
        "Run a live inference session in the cockpit above to generate logs."
    )
else:
    selected = st.sidebar.selectbox(
        "Session",
        options=csvs,
        format_func=lambda p: p.stem,
    )

    df           = pd.read_csv(selected)
    summary_path = selected.parent / (selected.stem + "_summary.json")
    summary      = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Duration",     f"{summary.get('duration_sec', 0):.0f} s")
    kc2.metric("Attentive",    f"{summary.get('attentive_pct', 0):.1f} %")
    kc3.metric("Alerts",       summary.get("alert_count", 0))
    kc4.metric("Total Frames", summary.get("total_frames", len(df)))

    st.divider()

    COLOUR_MAP = {
        "attentive":        "#50c864",
        "distracted_left":  "#e03c3c",
        "distracted_right": "#e03c3c",
        "distracted_down":  "#ff9020",
        "distracted_up":    "#ff9020",
        "drowsy":           "#f0e040",
        "no_face":          "#808080",
    }

    # State timeline
    st.subheader("State Timeline")
    fig_tl = px.scatter(
        df, x="elapsed_s", y="label",
        color="label",
        color_discrete_map=COLOUR_MAP,
        height=280,
    )
    fig_tl.update_traces(marker=dict(size=4, opacity=0.7))
    fig_tl.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="#111",
        paper_bgcolor="#111",
        font_color="#ccc",
    )
    st.plotly_chart(fig_tl, use_container_width=True)

    # Head angles
    if all(c in df.columns for c in ["yaw", "pitch", "roll"]):
        pose_df = df.dropna(subset=["yaw", "pitch", "roll"])
        if not pose_df.empty:
            st.subheader("Head Angles")
            fig_ang = go.Figure()
            for col_name, colour in [
                ("yaw",   "#4fc3f7"),
                ("pitch", "#81c784"),
                ("roll",  "#ffb74d"),
            ]:
                fig_ang.add_trace(go.Scatter(
                    x=pose_df["elapsed_s"],
                    y=pose_df[col_name],
                    mode="lines",
                    name=col_name.capitalize(),
                    line=dict(color=colour, width=1.5),
                ))
            fig_ang.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=8, b=0),
                plot_bgcolor="#111",
                paper_bgcolor="#111",
                font_color="#ccc",
                yaxis=dict(zeroline=True, zerolinecolor="#444"),
            )
            st.plotly_chart(fig_ang, use_container_width=True)

    # EAR curve
    if "ear" in df.columns and df["ear"].notna().any():
        st.subheader("Eye Aspect Ratio (Drowsiness)")
        fig_ear = go.Figure()
        fig_ear.add_trace(go.Scatter(
            x=df["elapsed_s"], y=df["ear"],
            mode="lines", name="EAR",
            line=dict(color="#ce93d8", width=1.5),
        ))
        fig_ear.add_hline(
            y=0.22, line_dash="dash", line_color="#e57373",
            annotation_text="Drowsy threshold",
        )
        fig_ear.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111",
            paper_bgcolor="#111",
            font_color="#ccc",
        )
        st.plotly_chart(fig_ear, use_container_width=True)

    # Distribution pie
    st.subheader("State Distribution")
    label_counts          = df["label"].value_counts().reset_index()
    label_counts.columns  = ["label", "count"]
    fig_pie = px.pie(
        label_counts, names="label", values="count",
        color="label", color_discrete_map=COLOUR_MAP, height=320,
    )
    fig_pie.update_layout(margin=dict(l=0, r=0, t=8, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("Raw frame data"):
        st.dataframe(df, use_container_width=True)
