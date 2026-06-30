import base64
import time
import cv2
import requests
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path
from typing import Optional

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def _ensure_logs_dir():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def render_cockpit_top(backend_ok: bool):
    for key, default in [
        ("run_live", False),
        ("fps_target", 5),
        ("session_data", []),
        ("session_start", None),
        ("cap", None),
        ("current_session_file", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    st.markdown("<div class='section-label'>COCKPIT · LIVE IN-CABIN VIEW</div>", unsafe_allow_html=True)
    st.markdown("<div class='cockpit-shell'>", unsafe_allow_html=True)

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
        st.markdown("<div class='metric-label'>3D CABIN TELEMETRY</div>", unsafe_allow_html=True)
        components.html(
            """
            <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
            <style>
                model-viewer {
                    width: 100%; height: 320px;
                    background-color: transparent;
                    outline: none; cursor: grab;
                }
                model-viewer:active { cursor: grabbing; }
            </style>
            <model-viewer
                id="supercar"
                src="http://localhost:3000/models/lamborghini_centenario_roadster_sdc.glb"
                camera-controls disable-pan disable-zoom auto-rotate
                rotation-per-second="20deg"
                shadow-intensity="1" exposure="0.8"
                interaction-prompt="none">
            </model-viewer>
            <script>
                const model = document.querySelector('#supercar');
                let doorsOpen = false, animFrame = null, targetTime = 0;
                model.addEventListener('load', () => { model.pause(); model.currentTime = 0; });
                function animateDoors() {
                    if (!model.duration) return;
                    model.currentTime += (targetTime - model.currentTime) * 0.1;
                    if (Math.abs(targetTime - model.currentTime) > 0.01) {
                        animFrame = requestAnimationFrame(animateDoors);
                    } else { model.currentTime = targetTime; }
                }
                model.addEventListener('click', () => {
                    if (!model.duration) return;
                    doorsOpen = !doorsOpen;
                    targetTime = doorsOpen ? model.duration : 0;
                    if (animFrame) cancelAnimationFrame(animFrame);
                    animateDoors();
                });
            </script>
            """,
            height=320,
        )
        st.markdown(
            "<div style='margin-top:0.5rem;text-align:center;'>"
            "<div style='font-family:monospace;font-size:0.7rem;color:#00F3FF;letter-spacing:0.1em;'>NODE ACTIVE</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    with screen_col:
        st.markdown("<div class='metric-label'>FALCON DASHBOARD · EMBEDDED</div>", unsafe_allow_html=True)
        screen_placeholder = st.empty()

        ctrl_a, ctrl_b = st.columns([1, 1])
        with ctrl_a:
            def _toggle_inference():
                st.session_state.run_live = not st.session_state.run_live
                if st.session_state.run_live:
                    _ensure_logs_dir()
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.current_session_file = LOGS_DIR / f"session_{ts}.csv"
                    st.session_state.session_start = time.time()
                    st.session_state.session_data = []
                else:
                    cap = st.session_state.get("cap")
                    if cap is not None:
                        try:
                            cap.release()
                        except Exception:
                            pass
                        st.session_state.cap = None

            st.toggle(
                "Start Live Inference",
                value=st.session_state.run_live,
                on_change=_toggle_inference,
                key="_run_live_widget",
            )
        with ctrl_b:
            current_fps = st.session_state.get("fps_target", 5)
            if not isinstance(current_fps, int) or not (1 <= current_fps <= 30):
                current_fps = 5
                st.session_state.fps_target = 5
            st.session_state.fps_target = st.slider(
                "Target FPS", 1, 30, current_fps, key="_fps_slider"
            )

    st.markdown("</div>", unsafe_allow_html=True)

    return screen_placeholder, st.session_state.run_live, st.session_state.fps_target


def _open_camera() -> Optional[cv2.VideoCapture]:
    """Try camera index 0, then 1, return opened cap or None."""
    for idx in (0, 1):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            cap.read()
            return cap
        cap.release()
    return None


def run_inference_loop(
    backend_ok: bool,
    backend_url: str,
    screen_placeholder,
    run_live: bool,
    fps_target: int,
    ph_list: list,
):
    state_ph, alert_ph, drowsy_ph, dist_ph, lat_ph = ph_list

    STATE_LABELS = {
        "safe": "🟢 Safe",
        "drowsy": "🟡 Drowsy",
        "distracted": "🟠 Distracted",
        "critical": "🔴 Critical",
        "unknown": "⚪ Unknown",
    }
    ALERT_ICONS = {0: "🟢", 1: "🟡", 2: "🔴"}

    if not run_live:
        screen_placeholder.info("Toggle **Start Live Inference** above to begin streaming.")
        for ph in ph_list:
            ph.metric("—", "—")
        return

    if not backend_ok:
        screen_placeholder.error(
            "Backend offline — start it with `cd backend && uvicorn main:app --reload`"
        )
        return

    cap = st.session_state.get("cap")
    if cap is None or not cap.isOpened():
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        cap = _open_camera()
        if cap is None:
            screen_placeholder.error(
                "❌ Could not open webcam (tried indices 0 and 1).\n\n"
                "**macOS:** System Settings → Privacy & Security → Camera → allow Terminal / iTerm.\n\n"
                "**Linux:** Make sure no other app holds `/dev/video0`. Try `v4l2-ctl --list-devices`.\n\n"
                "**Windows:** Check Device Manager; close any app using the camera."
            )
            st.session_state.run_live = False
            st.session_state.cap = None
            return
        st.session_state.cap = cap

    session_data: list = st.session_state.session_data
    session_start: float = st.session_state.session_start or time.time()
    session_file: Optional[Path] = st.session_state.current_session_file

    frame_interval = 1.0 / max(fps_target, 1)
    stop_requested = False
    FRAMES_PER_BURST = max(1, min(fps_target * 2, 20))

    for _ in range(FRAMES_PER_BURST):
        if not st.session_state.run_live:
            stop_requested = True
            break

        t0 = time.time()
        ret, frame_bgr = cap.read()
        if not ret:
            cap.release()
            st.session_state.cap = None
            screen_placeholder.warning("⚠ Camera read failed — retrying next cycle.")
            break

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        screen_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

        _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64 = base64.b64encode(buf.tobytes()).decode()

        row = None
        try:
            resp = requests.post(f"{backend_url}/infer", json={"frame": b64}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                d_state = data.get("driver_state", "unknown")
                a_level = data.get("alert_level", 0)
                latency_ms = (time.time() - t0) * 1000

                state_ph.metric("Driver State", STATE_LABELS.get(d_state, d_state))
                alert_ph.metric("Alert Level", f"{ALERT_ICONS.get(a_level, '')} {a_level}/2")
                drowsy_ph.metric(
                    "Drowsiness",
                    data.get("drowsiness", "?"),
                    f"{data.get('drowsiness_confidence', 0):.0%}",
                )
                dist_ph.metric(
                    "Distraction",
                    data.get("distraction", "?"),
                    f"{data.get('distraction_confidence', 0):.0%}",
                )
                lat_ph.metric("Latency", f"{latency_ms:.0f} ms")

                row = {
                    "timestamp": datetime.now().isoformat(timespec="milliseconds"),
                    "elapsed_s": round(t0 - session_start, 3),
                    "driver_state": d_state,
                    "alert_level": a_level,
                    "drowsiness": data.get("drowsiness", ""),
                    "drowsiness_confidence": round(data.get("drowsiness_confidence", 0), 4),
                    "distraction": data.get("distraction", ""),
                    "distraction_confidence": round(data.get("distraction_confidence", 0), 4),
                    "latency_ms": round(latency_ms, 1),
                    "yaw": data.get("yaw", None),
                    "pitch": data.get("pitch", None),
                    "roll": data.get("roll", None),
                }
                session_data.append(row)

                if session_file is not None:
                    _ensure_logs_dir()
                    write_header = not session_file.exists()
                    pd.DataFrame([row]).to_csv(
                        session_file,
                        mode="a",
                        header=write_header,
                        index=False,
                    )
        except Exception:
            pass

        elapsed = time.time() - t0
        time.sleep(max(0.0, frame_interval - elapsed))

    st.session_state.session_data = session_data

    if stop_requested or not st.session_state.run_live:
        cap = st.session_state.get("cap")
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
            st.session_state.cap = None

        if session_data and session_file is not None:
            df = pd.DataFrame(session_data)
            df.to_csv(session_file, index=False)

            summary = {
                "session_file": session_file.name,
                "started_at": datetime.fromtimestamp(session_start).isoformat(),
                "ended_at": datetime.now().isoformat(),
                "duration_sec": round(float(df["elapsed_s"].iloc[-1]), 2) if not df.empty else 0,
                "attentive_pct": round(
                    float((df["driver_state"] == "safe").mean() * 100), 2
                ) if not df.empty else 0,
                "alert_count": int(len(df[df["driver_state"] != "safe"])),
                "total_frames": len(df),
                "mean_latency_ms": round(float(df["latency_ms"].mean()), 1) if not df.empty else 0,
            }
            summary_path = session_file.parent / (session_file.stem + "_summary.json")
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)

        st.session_state.session_data = []
        st.session_state.current_session_file = None
        st.rerun()
        return

    st.rerun()
