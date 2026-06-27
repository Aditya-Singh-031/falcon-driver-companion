import base64
import time
import cv2
import requests
import streamlit as st
import streamlit.components.v1 as components

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
        
        # 3D Car with Click-to-Toggle-Doors and Anti-Looping logic
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
                auto-rotate
                rotation-per-second="20deg"
                shadow-intensity="1"
                exposure="0.8"
                interaction-prompt="none">
            </model-viewer>
            <script>
                const model = document.querySelector('#supercar');
                let doorsOpen = false;
                
                // The GLB file has the animation set to repeat. 
                // This event listener catches the exact moment the animation finishes one cycle and hits the brakes.
                model.addEventListener('loop', () => {
                    model.pause();
                });
                
                model.addEventListener('click', () => {
                    doorsOpen = !doorsOpen;
                    // Play forwards to open (1), play in reverse to close (-1)
                    model.timeScale = doorsOpen ? 1 : -1; 
                    model.play();
                });
            </script>
            """,
            height=320
        )
        # Cleaned up text below the car
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

    st.markdown("</div>", unsafe_allow_html=True) # Close cockpit shell
    
    return screen_placeholder, run_live, fps_target


def run_inference_loop(backend_ok, backend_url, screen_placeholder, run_live, fps_target, ph_list):
    state_ph, alert_ph, drowsy_ph, dist_ph, lat_ph = ph_list
    STATE_LABELS = {"safe": "🟢 Safe", "drowsy": "🟡 Drowsy", "distracted": "🟠 Distracted", "critical": "🔴 Critical", "unknown": "⚪ Unknown"}
    ALERT_ICONS = {0: "🟢", 1: "🟡", 2: "🔴"}

    if backend_ok and run_live:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            screen_placeholder.error("Could not open webcam.")
        else:
            frame_interval = 1.0 / fps_target
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
                    except Exception:
                        pass # Silently drop timeouts to keep the video feed perfectly smooth

                    time.sleep(max(0, frame_interval - (time.time() - t0)))
            finally:
                cap.release()
    else:
        if not run_live:
            screen_placeholder.info("Toggle **Start Live Inference** above to begin streaming.")
        state_ph.metric("Driver State", "—")
        alert_ph.metric("Alert Level", "—")
        drowsy_ph.metric("Drowsiness", "—")
        dist_ph.metric("Distraction", "—")
        lat_ph.metric("Latency", "—")