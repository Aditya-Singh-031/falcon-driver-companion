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


def render_cockpit_top(backend_ok: bool):
    # ── Init session state ────────────────────────────────────────────────────
    if "run_live" not in st.session_state:
        st.session_state.run_live = False
    if "fps_target" not in st.session_state:
        st.session_state.fps_target = 5

    st.markdown("<div class='section-label'>COCKPIT · LIVE IN-CABIN VIEW</div>", unsafe_allow_html=True)
    st.markdown("<div class='cockpit-shell'>", unsafe_allow_html=True)

    hc1, hc2, hc3 = st.columns([1.2, 1.2, 1.4])
    with hc1: st.markdown("<div class='hud-chip'>HUD MODE · <span>DRIVER</span></div>", unsafe_allow_html=True)
    with hc2: st.markdown("<div class='hud-chip'>ENGINE · <span>ON-DEVICE</span></div>", unsafe_allow_html=True)
    with hc3: st.markdown("<div class='hud-chip'>LATENCY · <span>&lt; 25 MS</span></div>", unsafe_allow_html=True)

    st.markdown("<div class='hud-line'></div>", unsafe_allow_html=True)

    car_col, screen_col = st.columns([1.4, 1.8])

    with car_col:
        st.markdown("<div class='metric-label'>3D CABIN TELEMETRY</div>", unsafe_allow_html=True)
        components.html(
            """
            <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
            <style>
                model-viewer { width: 100%; height: 320px; background-color: transparent; outline: none; cursor: grab; }
                model-viewer:active { cursor: grabbing; }
            </style>
            <model-viewer
                id="supercar"
                src="http://localhost:3000/models/lamborghini_centenario_roadster_sdc.glb"
                camera-controls
                disable-pan
                disable-zoom
                auto-rotate
                rotation-per-second="20deg"
                shadow-intensity="1"
                exposure="0.8"
                interaction-prompt="none">
            </model-viewer>
            <script>
                const model = document.querySelector('#supercar');
                let doorsOpen = false;
                let animFrame = null;
                let targetTime = 0;
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
            # Use on_change callback so the toggle flip is committed to session_state
            # BEFORE the next script rerun reads it.
            def _toggle_inference():
                st.session_state.run_live = not st.session_state.run_live

            st.toggle(
                "Start Live Inference",
                value=st.session_state.run_live,
                on_change=_toggle_inference,
                key="_run_live_widget",
            )
        with ctrl_b:
            st.session_state.fps_target = st.slider(
                "Target FPS", 1, 15, st.session_state.fps_target, key="_fps_slider"
            )

    st.markdown("</div>", unsafe_allow_html=True)

    return screen_placeholder, st.session_state.run_live, st.session_state.fps_target


def run_inference_loop(backend_ok, backend_url, screen_placeholder, run_live, fps_target, ph_list):
    state_ph, alert_ph, drowsy_ph, dist_ph, lat_ph = ph_list

    STATE_LABELS = {
        "safe": "🟢 Safe",
        "drowsy": "🟡 Drowsy",
        "distracted": "🟠 Distracted",
        "critical": "🔴 Critical",
        "unknown": "⚪ Unknown",
    }
    ALERT_ICONS = {0: "🟢", 1: "🟡", 2: "🔴"}

    # ── Idle state ────────────────────────────────────────────────────────────
    if not run_live:
        screen_placeholder.info("Toggle **Start Live Inference** above to begin streaming.")
        for ph in ph_list:
            ph.metric("—", "—")
        return

    if not backend_ok:
        screen_placeholder.error("Backend offline — start it with `cd backend && uvicorn main:app --reload`")
        return

    # ── Live inference loop ────────────────────────────────────────────────────
    # Open capture once; Streamlit re-executes this function every ~rerun cycle
    # so we cache the VideoCapture object in session_state to avoid re-opening.
    if "cap" not in st.session_state or st.session_state.cap is None:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            screen_placeholder.error(
                "❌ Could not open webcam.\n\n"
                "**macOS:** System Settings → Privacy & Security → Camera → allow Terminal / your browser.\n\n"
                "**Linux/Windows:** Make sure no other app is holding the camera."
            )
            st.session_state.run_live = False
            return
        st.session_state.cap = cap
    else:
        cap = st.session_state.cap

    session_data = st.session_state.get("session_data", [])
    session_start = st.session_state.get("session_start", time.time())
    st.session_state.session_start = session_start

    frame_interval = 1.0 / fps_target
    stop_requested = False

    # Run a fixed burst of frames per Streamlit rerun so we don't block the
    # event loop indefinitely (Streamlit will auto-rerun via st.rerun() below).
    FRAMES_PER_BURST = max(1, fps_target * 2)

    for _ in range(FRAMES_PER_BURST):
        # Check if user toggled off mid-burst
        if not st.session_state.run_live:
            stop_requested = True
            break

        t0 = time.time()
        ret, frame_bgr = cap.read()
        if not ret:
            continue

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        screen_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

        _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64 = base64.b64encode(buf.tobytes()).decode()

        try:
            resp = requests.post(f"{backend_url}/infer", json={"frame": b64}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                d_state = data.get("driver_state", "unknown")
                a_level = data.get("alert_level", 0)

                state_ph.metric("Driver State", STATE_LABELS.get(d_state, d_state))
                alert_ph.metric("Alert Level", f"{ALERT_ICONS.get(a_level, '')} {a_level}/2")
                drowsy_ph.metric("Drowsiness", data.get("drowsiness", "?"), f"{data.get('drowsiness_confidence', 0):.0%}")
                dist_ph.metric("Distraction", data.get("distraction", "?"), f"{data.get('distraction_confidence', 0):.0%}")
                lat_ph.metric("Latency", f"{(time.time() - t0) * 1000:.0f} ms")

                session_data.append({
                    "elapsed_s": t0 - session_start,
                    "label": d_state,
                    "ear": (
                        data.get("drowsiness_confidence", 0)
                        if data.get("drowsiness") == "drowsy"
                        else 1 - data.get("drowsiness_confidence", 0)
                    ),
                })
        except Exception:
            pass

        elapsed = time.time() - t0
        time.sleep(max(0, frame_interval - elapsed))

    st.session_state.session_data = session_data

    # ── Session ended — save logs ─────────────────────────────────────────────
    if stop_requested or not st.session_state.run_live:
        cap.release()
        st.session_state.cap = None

        if session_data:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            df = pd.DataFrame(session_data)
            df.to_csv(logs_dir / f"session_{timestamp}.csv", index=False)

            summary = {
                "duration_sec": float(df["elapsed_s"].iloc[-1]) if not df.empty else 0,
                "attentive_pct": float((df["label"] == "safe").mean() * 100) if not df.empty else 0,
                "alert_count": int(len(df[df["label"] != "safe"])),
                "total_frames": len(df),
            }
            with open(logs_dir / f"session_{timestamp}_summary.json", "w") as f:
                json.dump(summary, f)

        st.session_state.session_data = []
        st.rerun()
        return

    # ── Keep looping — trigger next burst ─────────────────────────────────────
    st.rerun()
