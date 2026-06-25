"""
Falcon — Driver Companion Dashboard
Streamlit app with two tabs:
  1. Live Monitor  — streams webcam frames to the FastAPI backend and shows real-time state
  2. Session Logs  — visualises saved session CSV logs (original dashboard)

Run:
  streamlit run dashboard/app.py
Backend must be running:
  cd backend && uvicorn main:app --reload
"""

import base64
import io
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

st.set_page_config(page_title="Falcon Dashboard", page_icon="\U0001f985", layout="wide")
st.title("\U0001f985 Falcon — Driver Companion")

tab_live, tab_logs = st.tabs(["\U0001f4f9 Live Monitor", "\U0001f4ca Session Logs"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE MONITOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_live:
    # ── Backend health check ──────────────────────────────────────────────────
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=2).json()
        backend_ok = health.get("status") == "ok"
    except Exception:
        backend_ok = False

    if not backend_ok:
        st.error(
            "\u26a0\ufe0f Cannot reach backend at `http://127.0.0.1:8000`. "
            "Run `cd backend && uvicorn main:app --reload` first."
        )
    else:
        drowsiness_ok = health.get("drowsiness_loaded", False)
        distraction_ok = health.get("distraction_loaded", False)
        c1, c2, c3 = st.columns(3)
        c1.metric("Backend", "\u2705 Online")
        c2.metric("Drowsiness Model", "\u2705 Loaded" if drowsiness_ok else "\u274c Not loaded")
        c3.metric("Distraction Model", "\u2705 Loaded" if distraction_ok else "\u274c Not loaded")

        st.divider()

        # ── Controls ──────────────────────────────────────────────────────────
        col_ctrl, col_feed = st.columns([1, 2])
        with col_ctrl:
            st.subheader("Controls")
            run_live = st.toggle("Start Live Inference", value=False)
            fps_target = st.slider("Target FPS", min_value=1, max_value=15, value=5)
            st.caption("Webcam feed is processed locally; only JPEG frames are sent to the backend.")

        with col_feed:
            st.subheader("Camera Feed")
            frame_placeholder = st.empty()

        st.divider()

        # ── State display ─────────────────────────────────────────────────────
        st.subheader("Driver State")
        state_cols = st.columns(5)
        state_placeholder       = state_cols[0].empty()
        alert_placeholder       = state_cols[1].empty()
        drowsy_placeholder      = state_cols[2].empty()
        distraction_placeholder = state_cols[3].empty()
        latency_placeholder     = state_cols[4].empty()

        ALERT_COLOURS = {0: "\U0001f7e2", 1: "\U0001f7e1", 2: "\U0001f534"}
        STATE_LABELS  = {
            "safe":       "\U0001f7e2 Safe",
            "drowsy":     "\U0001f7e1 Drowsy",
            "distracted": "\U0001f7e0 Distracted",
            "critical":   "\U0001f534 Critical",
            "unknown":    "\u26aa Unknown",
        }

        if run_live:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("Could not open webcam (index 0). Check camera permissions.")
            else:
                frame_interval = 1.0 / fps_target
                try:
                    while run_live:
                        t0 = time.time()
                        ret, frame_bgr = cap.read()
                        if not ret:
                            st.warning("Dropped frame — retrying...")
                            time.sleep(0.05)
                            continue

                        # Show frame in UI
                        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                        frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                        # Encode as JPEG → base64
                        _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        b64 = base64.b64encode(buf.tobytes()).decode()

                        # Hit inference endpoint
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
                                    STATE_LABELS.get(driver_state, driver_state)
                                )
                                alert_placeholder.metric(
                                    "Alert Level",
                                    f"{ALERT_COLOURS.get(alert_level, '')} {alert_level}/2"
                                )
                                drowsy_placeholder.metric(
                                    "Drowsiness",
                                    drowsiness,
                                    f"{d_conf:.0%} conf"
                                )
                                distraction_placeholder.metric(
                                    "Distraction",
                                    distraction,
                                    f"{dist_conf:.0%} conf"
                                )
                                latency_placeholder.metric(
                                    "Latency",
                                    f"{latency_ms:.0f} ms"
                                )
                            else:
                                st.warning(f"Backend error {resp.status_code}: {resp.text[:120]}")
                        except requests.exceptions.Timeout:
                            st.warning("Inference request timed out — backend may be overloaded.")
                        except Exception as e:
                            st.error(f"Request failed: {e}")

                        # Throttle to target FPS
                        elapsed = time.time() - t0
                        sleep_time = frame_interval - elapsed
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                finally:
                    cap.release()
        else:
            frame_placeholder.info("Toggle \"Start Live Inference\" above to begin.")
            state_placeholder.metric("Driver State", "—")
            alert_placeholder.metric("Alert Level", "—")
            drowsy_placeholder.metric("Drowsiness", "—")
            distraction_placeholder.metric("Distraction", "—")
            latency_placeholder.metric("Latency", "—")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SESSION LOGS  (original dashboard, unchanged)
# ══════════════════════════════════════════════════════════════════════════════
with tab_logs:
    logs_dir = Path("logs")
    csvs = sorted(logs_dir.glob("session_*.csv"), reverse=True) if logs_dir.exists() else []

    if not csvs:
        st.warning("No session logs found. Run a live session first to generate logs.")
        st.stop()

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
    st.plotly_chart(fig_timeline, use_container_width=True)

    pose_df = df.dropna(subset=["yaw", "pitch", "roll"]) if all(c in df.columns for c in ["yaw","pitch","roll"]) else pd.DataFrame()
    if not pose_df.empty:
        st.subheader("Head Angles")
        fig_ang = go.Figure()
        for col, c in [("yaw", "#4fc3f7"), ("pitch", "#81c784"), ("roll", "#ffb74d")]:
            fig_ang.add_trace(go.Scatter(
                x=pose_df["elapsed_s"], y=pose_df[col],
                mode="lines", name=col.capitalize(),
                line=dict(color=c, width=1.5),
            ))
        fig_ang.update_layout(
            height=260, margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111", paper_bgcolor="#111",
            font_color="#ccc",
            yaxis=dict(zeroline=True, zerolinecolor="#444"),
        )
        st.plotly_chart(fig_ang, use_container_width=True)

    if "ear" in df.columns and df["ear"].notna().any():
        st.subheader("Eye Aspect Ratio (Drowsiness)")
        fig_ear = go.Figure()
        fig_ear.add_trace(go.Scatter(
            x=df["elapsed_s"], y=df["ear"],
            mode="lines", name="EAR",
            line=dict(color="#ce93d8", width=1.5),
        ))
        fig_ear.add_hline(y=0.22, line_dash="dash", line_color="#e57373",
                          annotation_text="Drowsy threshold")
        fig_ear.update_layout(
            height=220, margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111", paper_bgcolor="#111",
            font_color="#ccc",
        )
        st.plotly_chart(fig_ear, use_container_width=True)

    st.subheader("State Distribution")
    label_counts = df["label"].value_counts().reset_index()
    label_counts.columns = ["label", "count"]
    fig_pie = px.pie(
        label_counts, names="label", values="count",
        color="label", color_discrete_map=colour_map, height=320,
    )
    fig_pie.update_layout(margin=dict(l=0, r=0, t=8, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("Raw frame data"):
        st.dataframe(df, use_container_width=True)
