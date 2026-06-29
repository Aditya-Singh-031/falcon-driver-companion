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
        
        # 3D Car with disable-pan and requestAnimationFrame door toggle
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
                
                model.addEventListener('load', () => {
                    model.pause();
                    model.currentTime = 0;
                });
                
                function animateDoors() {
                    if (!model.duration) return;
                    
                    // Smoothly interpolate current time toward target time
                    model.currentTime += (targetTime - model.currentTime) * 0.1;
                    
                    // Stop animating when we get close enough to the target
                    if (Math.abs(targetTime - model.currentTime) > 0.01) {
                        animFrame = requestAnimationFrame(animateDoors);
                    } else {
                        model.currentTime = targetTime;
                    }
                }
                
                model.addEventListener('click', () => {
                    if (!model.duration) return;
                    doorsOpen = !doorsOpen;
                    
                    // Set target: end of animation if opening, start if closing
                    targetTime = doorsOpen ? model.duration : 0;
                    
                    if (animFrame) cancelAnimationFrame(animFrame);
                    animateDoors();
                });
            </script>
            """,
            height=320
        )
        st.markdown(
            """
            <div style="margin-top: 0.5rem; text-align: center;">
                <div style="font-family: monospace; font-size: 0.7rem; color: #00F3FF; letter-spacing: 0.1em;">NODE ACTIVE</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with screen_col:
        st.markdown("<div class='metric-label'>FALCON DASHBOARD · EMBEDDED</div>", unsafe_allow_html=True)
        screen_placeholder = st.empty()

        ctrl_a, ctrl_b = st.columns([1, 1])
        with ctrl_a: run_live = st.toggle("Start Live Inference", value=False)
        with ctrl_b: fps_target = st.slider("Target FPS", 1, 15, 5)

    st.markdown("</div>", unsafe_allow_html=True) 
    
    return screen_placeholder, run_live, fps_target


def run_inference_loop(backend_ok, backend_url, screen_placeholder, run_live, fps_target, ph_list):
    state_ph, alert_ph, drowsy_ph, dist_ph, lat_ph = ph_list
    STATE_LABELS = {"safe": "🟢 Safe", "drowsy": "🟡 Drowsy", "distracted": "🟠 Distracted", "critical": "🔴 Critical", "unknown": "⚪ Unknown"}
    ALERT_ICONS = {0: "🟢", 1: "🟡", 2: "🔴"}

    if backend_ok and run_live:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            screen_placeholder.error("Could not open webcam. Check System Preferences → Privacy → Camera.")
        else:
            frame_interval = 1.0 / fps_target
            session_data = []  # Initialize list to hold telemetry
            session_start_time = time.time()
            
            try:
                while run_live:
                    t0 = time.time()
                    ret, frame_bgr = cap.read()
                    if not ret: continue

                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    screen_placeholder.image(frame_rgb, channels="RGB")

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
                            
                            # Append data for logging
                            session_data.append({
                                "elapsed_s": t0 - session_start_time,
                                "label": d_state,
                                "ear": data.get("drowsiness_confidence", 0) if data.get("drowsiness") == "drowsy" else 1 - data.get("drowsiness_confidence", 0)
                            })
                            
                    except Exception:
                        pass 

                    time.sleep(max(0, frame_interval - (time.time() - t0)))
            finally:
                cap.release()
                
                # Save the log file when the loop ends
                if session_data:
                    logs_dir = Path("logs")
                    logs_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    df = pd.DataFrame(session_data)
                    csv_path = logs_dir / f"session_{timestamp}.csv"
                    df.to_csv(csv_path, index=False)
                    
                    # Generate a basic summary JSON required by analytics_ui.py
                    summary_path = logs_dir / f"session_{timestamp}_summary.json"
                    summary = {
                        "duration_sec": df["elapsed_s"].iloc[-1] if not df.empty else 0,
                        "attentive_pct": (df["label"] == "safe").mean() * 100 if not df.empty else 0,
                        "alert_count": len(df[df["label"] != "safe"]),
                        "total_frames": len(df)
                    }
                    with open(summary_path, 'w') as f:
                        json.dump(summary, f)
                        
                    st.rerun() # Force Streamlit to refresh so the new log appears in the dropdown immediately
    else:
        if not run_live:
            screen_placeholder.info("Toggle **Start Live Inference** above to begin streaming.")
        state_ph.metric("Driver State", "—")
        alert_ph.metric("Alert Level", "—")
        drowsy_ph.metric("Drowsiness", "—")
        dist_ph.metric("Distraction", "—")
        lat_ph.metric("Latency", "—")