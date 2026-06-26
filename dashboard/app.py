"""
Falcon — Production-Grade Cinematic UI + Dashboard

This replaces the basic Streamlit UI with a high-end, narrative-driven interface:
  • Intro: 3D supercar (Lambo-style) door opens, camera moves into cabin
  • Cockpit: integrated live Falcon dashboard in the car's central display
  • Metrics: drowsiness/distraction stats and logs come after the cockpit

Run:
  streamlit run dashboard/app.py
Backend must be running:
  cd backend && uvicorn main:app --reload
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

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Falcon — Driver Companion",
    page_icon="🦅",
    layout="wide",
)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  GLOBAL STYLES  (dark, neon, F1 aesthetic)
# ╚══════════════════════════════════════════════════════════════════════════╝
NEON_YELLOW = "#D4F000"
NEON_CYAN   = "#00F3FF"
BG_DARK     = "#050505"
BG_PANEL    = "#111111"
TEXT_MUTED  = "#999999"
TEXT_LIGHT  = "#E5E5E5"

st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
      background: radial-gradient(circle at top, #151515 0%, #050505 45%, #000000 100%) !important;
      color: {TEXT_LIGHT} !important;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    [data-testid="stHeader"] {{
      background: transparent !important;
    }}

    .falcon-title {{
      font-size: min(8vw, 4rem);
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: {TEXT_LIGHT};
    }}

    .falcon-subtitle {{
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.25em;
      color: {TEXT_MUTED};
    }}

    .metric-label {{
      font-size: 0.75rem;
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
      background: rgba(17, 17, 17, 0.85);
      border-radius: 18px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      box-shadow: 0 20px 60px rgba(0,0,0,0.80);
      backdrop-filter: blur(24px);
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

    .cockpit-shell::before {{
      content: "";
      position: absolute;
      inset: -120%;
      background:
        radial-gradient(circle at 10% 0%, rgba(212,240,0,0.08) 0%, transparent 60%),
        radial-gradient(circle at 80% 0%, rgba(0,243,255,0.12) 0%, transparent 55%);
      opacity: 0.9;
      mix-blend-mode: screen;
      pointer-events: none;
    }}

    .hud-line {{
      height: 1px;
      width: 100%;
      background: linear-gradient(90deg, transparent 0%, {NEON_CYAN} 20%, {NEON_YELLOW} 50%, {NEON_CYAN} 80%, transparent 100%);
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
    }}

    .hud-chip span {{
      color: {NEON_YELLOW};
    }}

    .falcon-headline {{
      font-size: min(7vw, 3rem);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      line-height: 1.1;
    }}

    .falcon-headline span {{
      color: {NEON_YELLOW};
    }}

    .section-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.22em;
      color: {TEXT_MUTED};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  HEADER — Brand + Micro Copy
# ╚══════════════════════════════════════════════════════════════════════════╝
header_left, header_right = st.columns([3, 2])
with header_left:
    st.markdown("<div class='falcon-title'>FALCON</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='falcon-subtitle'>EDGE AI DRIVER COMPANION · LIVE IN-CABIN SAFETY TELEMETRY</div>",
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown("<div class='section-label'>SESSION</div>", unsafe_allow_html=True)
    st.caption("All inference happens on-device. No frames leave the cabin.")

st.markdown("<div class='hud-line'></div>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 1 — 3D CAR INTRO + COCKPIT (with integrated live dashboard)
# ╚══════════════════════════════════════════════════════════════════════════╝

intro_col, cockpit_col = st.columns([1.3, 2.0])

# ── Backend health check ────────────────────────────────────────────────────
try:
    health = requests.get(f"{BACKEND_URL}/health", timeout=2).json()
    backend_ok = health.get("status") == "ok"
except Exception:
    health = {}
    backend_ok = False

with intro_col:
    st.markdown("<div class='section-label'>FALCON ENTRY · v2.1</div>", unsafe_allow_html=True)

    if backend_ok:
        drowsiness_ok = health.get("drowsiness_loaded", False)
        distraction_ok = health.get("distraction_loaded", False)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='falcon-headline'>ENTER THE <span>COCKPIT</span></div>",
            unsafe_allow_html=True,
        )
        st.caption("Door opens, cabin lights up, and Falcon locks onto the driver's face in real time.")

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
            f"<div class='falcon-headline'><span>BACKEND OFFLINE</span></div>",
            unsafe_allow_html=True,
        )
        st.error(
            "Cannot reach backend at `http://127.0.0.1:8000`. "
            "Run `cd backend && uvicorn main:app --reload` first.",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='glass-panel'>"
            "<div class='metric-label'>FALCON ENTRY</div>"
            "<div class='metric-value'>SYSTEM STANDBY</div>"
            "<p style='margin-top:0.6rem;font-size:0.85rem;color:#bbbbbb;'>"
            "Backend must be online to drive live cockpit and HUD visuals."
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )

with cockpit_col:
    st.markdown("<div class='section-label'>COCKPIT · LIVE IN-CABIN VIEW</div>", unsafe_allow_html=True)

    # The cockpit shell frames both the car intro and the embedded dashboard feed.
    st.markdown("<div class='cockpit-shell'>", unsafe_allow_html=True)

    # Upper strip: HUD chips
    hud_cols = st.columns([1.2, 1.2, 1.4])
    with hud_cols[0]:
        st.markdown("<div class='hud-chip'>HUD MODE · <span>DRIVER</span></div>", unsafe_allow_html=True)
    with hud_cols[1]:
        st.markdown("<div class='hud-chip'>ENGINE · <span>ON-DEVICE</span></div>", unsafe_allow_html=True)
    with hud_cols[2]:
        st.markdown("<div class='hud-chip'>LATENCY · <span>&lt; 25 MS</span></div>", unsafe_allow_html=True)

    st.markdown("<div class='hud-line'></div>", unsafe_allow_html=True)

    # Lower grid: car intro (static image / placeholder) + embedded live dashboard
    car_col, screen_col = st.columns([1.4, 1.8])

    with car_col:
        st.markdown("<div class='metric-label'>ENTRY SEQUENCE</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:0.83rem;color:#bbbbbb;line-height:1.5;'>"
            "On production this block should be replaced with a 3D supercar intro "
            "using Three.js / React Three Fiber: door opens, camera glides into the cabin, "
            "and the view settles onto the dashboard screen.<br><br>For now, this is a "
            "static visual placeholder so the cockpit and live HUD are already wired up."
            "</p>",
            unsafe_allow_html=True,
        )
        st.image(
            "https://via.placeholder.com/640x360/050505/FFFFFF?text=3D+Supercar+Intro+Placeholder",
            use_column_width=True,
        )

    with screen_col:
        st.markdown("<div class='metric-label'>FALCON DASHBOARD · EMBEDDED</div>", unsafe_allow_html=True)
        st.caption("Live monitor is rendered directly inside the cockpit screen.")

        # We embed the live monitor logic here instead of sending users to a separate page.
        screen_placeholder = st.empty()

        # Live inference toggle inside the cockpit
        ctrl_cols = st.columns([1, 1])
        with ctrl_cols[0]:
            run_live = st.toggle("Start Live Inference", value=False)
        with ctrl_cols[1]:
            fps_target = st.slider("Target FPS", min_value=1, max_value=15, value=5)

        # State metrics below the screen
        state_cols = st.columns(5)
        state_placeholder       = state_cols[0].empty()
        alert_placeholder       = state_cols[1].empty()
        drowsy_placeholder      = state_cols[2].empty()
        distraction_placeholder = state_cols[3].empty()
        latency_placeholder     = state_cols[4].empty()

        ALERT_COLOURS = {0: "🟢", 1: "🟡", 2: "🔴"}
        STATE_LABELS  = {
            "safe":       "🟢 Safe",
            "drowsy":     "🟡 Drowsy",
            "distracted": "🟠 Distracted",
            "critical":   "🔴 Critical",
            "unknown":    "⚪ Unknown",
        }

        if backend_ok and run_live:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                screen_placeholder.error("Could not open webcam (index 0). Check camera permissions.")
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

                        _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        b64 = base64.b64encode(buf.tobytes()).decode()

                        try:
                            resp = requests.post(
                                f"{BACKEND_URL}/infer",
                                json={"frame": b64},
                                timeout=3,
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                latency_ms = (time.time() - t0) * 1000

                                driver_state = data.get("driver_state", "unknown")
                                alert_level  = data.get("alert_level", 0)
                                drowsiness   = data.get("drowsiness", "?")
                                d_conf       = data.get("drowsiness_confidence", 0.0)
                                distraction  = data.get("distraction", "?")
                                dist_conf    = data.get("distraction_confidence", 0.0)

                                state_placeholder.metric(
                                    "Driver State",
                                    STATE_LABELS.get(driver_state, driver_state),
                                )
                                alert_placeholder.metric(
                                    "Alert Level",
                                    f"{ALERT_COLOURS.get(alert_level, '')} {alert_level}/2",
                                )
                                drowsy_placeholder.metric(
                                    "Drowsiness",
                                    drowsiness,
                                    f"{d_conf:.0%} conf",
                                )
                                distraction_placeholder.metric(
                                    "Distraction",
                                    distraction,
                                    f"{dist_conf:.0%} conf",
                                )
                                latency_placeholder.metric(
                                    "Latency",
                                    f"{latency_ms:.0f} ms",
                                )
                            else:
                                screen_placeholder.warning(
                                    f"Backend error {resp.status_code}: {resp.text[:120]}",
                                )
                        except requests.exceptions.Timeout:
                            screen_placeholder.warning(
                                "Inference request timed out — backend may be overloaded.",
                            )
                        except Exception as e:
                            screen_placeholder.error(f"Request failed: {e}")

                        elapsed = time.time() - t0
                        sleep_time = frame_interval - elapsed
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                finally:
                    cap.release()
        else:
            screen_placeholder.info(
                "Toggle 'Start Live Inference' to stream webcam frames into the cockpit display.",
            )
            state_placeholder.metric("Driver State", "—")
            alert_placeholder.metric("Alert Level", "—")
            drowsy_placeholder.metric("Drowsiness", "—")
            distraction_placeholder.metric("Distraction", "—")
            latency_placeholder.metric("Latency", "—")

    st.markdown("</div>", unsafe_allow_html=True)  # close cockpit-shell

st.markdown("<br><br>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 2 — MISSION TEXT (single-line words, no ugly splits)
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

st.caption("All inference happens on-device, optimised for automotive-grade hardware.")

st.markdown("<br><br>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 3 — DROWSINESS vs DISTRACTION (single-line label blocks)
# ╚══════════════════════════════════════════════════════════════════════════╝

st.markdown("<div class='section-label'>DUAL DETECTION SYSTEM · v2.1</div>", unsafe_allow_html=True)

dd_cols = st.columns([1, 1])

with dd_cols[0]:
    st.markdown(
        f"<div class='glass-panel'>"
        f"<div class='metric-label'>DROWSINESS</div>"
        f"<div class='metric-value'>MediaPipe FaceMesh + EAR/MAR/PERCLOS thresholds</div>"
        f"<p style='margin-top:0.6rem;font-size:0.85rem;color:{TEXT_LIGHT};line-height:1.5;'>"
        "468 facial landmarks. Sub-20ms inference. EAR threshold: 0.25. PERCLOS window: 60 frames.<br>"
        "Example state payload:" 
        "</p>"
        f"<pre style='margin-top:0.6rem;font-size:0.8rem;background:#0b0b0b;border-radius:12px;padding:0.6rem 0.8rem;color:{TEXT_LIGHT};">"
        "{\n  \"state\": \"DROWSY\",\n  \"ear\": 0.18,\n  \"alert\": true\n}"
        "</pre>"
        f"</div>",
        unsafe_allow_html=True,
    )

with dd_cols[1]:
    st.markdown(
        f"<div class='glass-panel'>"
        f"<div class='metric-label'>DISTRACTION</div>"
        f"<div class='metric-value'>EfficientNet-B0 gaze + head pose estimation</div>"
        f"<p style='margin-top:0.6rem;font-size:0.85rem;color:{TEXT_LIGHT};line-height:1.5;'>"
        "Context-aware 6-class output. GPU-optional. head_yaw: ±35°, gaze_off_road detection, phone presence.<br>"
        "Example state payload:"
        "</p>"
        f"<pre style='margin-top:0.6rem;font-size:0.8rem;background:#0b0b0b;border-radius:12px;padding:0.6rem 0.8rem;color:{TEXT_LIGHT};">"
        "{\n  \"state\": \"DISTRACTED\",\n  \"head_yaw\": 32.1,\n  \"phone_detected\": true\n}"
        "</pre>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 4 — SESSION LOGS (existing analytics, kept production-ready)
# ╚══════════════════════════════════════════════════════════════════════════╝

logs_dir = Path("logs")
csvs = sorted(logs_dir.glob("session_*.csv"), reverse=True) if logs_dir.exists() else []

st.markdown("<div class='section-label'>SESSION LOGS</div>", unsafe_allow_html=True)

if not csvs:
    st.warning("No session logs found. Run a live cockpit session to generate logs.")
else:
    selected = st.sidebar.selectbox(
        "Session",
        options=csvs,
        format_func=lambda p: p.stem,
    )

    df = pd.read_csv(selected)
    summary_path = selected.parent / (selected.stem + "_summary.json")
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Duration",     f"{summary.get('duration_sec', 0):.0f} s")
    col2.metric("Attentive",    f"{summary.get('attentive_pct', 0):.1f} %")
    col3.metric("Alerts",       summary.get("alert_count", 0))
    col4.metric("Total Frames", summary.get("total_frames", len(df)))

    st.divider()

    colour_map = {
        "attentive":        "#50c864",
        "distracted_left":  "#e03c3c",
        "distracted_right": "#e03c3c",
        "distracted_down":  "#ff9020",
        "distracted_up":    "#ff9020",
        "drowsy":           "#f0e040",
        "no_face":          "#808080",
    }

    st.subheader("State Timeline")
    fig_timeline = px.scatter(
        df, x="elapsed_s", y="label",
        color="label", color_discrete_map=colour_map, height=280,
    )
    fig_timeline.update_traces(marker=dict(size=4, opacity=0.7))
    fig_timeline.update_layout(showlegend=False, margin=dict(l=0, r=0, t=8, b=0))
    st.plotly_chart(fig_timeline, width='stretch')

    pose_df = df.dropna(subset=["yaw", "pitch", "roll"]) if all(
        c in df.columns for c in ["yaw", "pitch", "roll"]
    ) else pd.DataFrame()
    if not pose_df.empty:
        st.subheader("Head Angles")
        fig_ang = go.Figure()
        for col, c in [("yaw", "#4fc3f7"), ("pitch", "#81c784"), ("roll", "#ffb74d")]:
            fig_ang.add_trace(
                go.Scatter(
                    x=pose_df["elapsed_s"],
                    y=pose_df[col],
                    mode="lines",
                    name=col.capitalize(),
                    line=dict(color=c, width=1.5),
                )
            )
        fig_ang.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111",
            paper_bgcolor="#111",
            font_color="#ccc",
            yaxis=dict(zeroline=True, zerolinecolor="#444"),
        )
        st.plotly_chart(fig_ang, width='stretch')

    if "ear" in df.columns and df["ear"].notna().any():
        st.subheader("Eye Aspect Ratio (Drowsiness)")
        fig_ear = go.Figure()
        fig_ear.add_trace(
            go.Scatter(
                x=df["elapsed_s"],
                y=df["ear"],
                mode="lines",
                name="EAR",
                line=dict(color="#ce93d8", width=1.5),
            )
        )
        fig_ear.add_hline(
            y=0.22,
            line_dash="dash",
            line_color="#e57373",
            annotation_text="Drowsy threshold",
        )
        fig_ear.update_layout(
            height=220,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111",
            paper_bgcolor="#111",
            font_color="#ccc",
        )
        st.plotly_chart(fig_ear, width='stretch')

    st.subheader("State Distribution")
    label_counts = df["label"].value_counts().reset_index()
    label_counts.columns = ["label", "count"]
    fig_pie = px.pie(
        label_counts,
        names="label",
        values="count",
        color="label",
        color_discrete_map=colour_map,
        height=320,
    )
    fig_pie.update_layout(margin=dict(l=0, r=0, t=8, b=0))
    st.plotly_chart(fig_pie, width='stretch')

    with st.expander("Raw frame data"):
        st.dataframe(df, width="stretch")
