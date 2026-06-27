import requests
import streamlit as st

# Import our newly split modules
from modules.styles import apply_custom_styles
from modules.cockpit_ui import render_cockpit
from modules.analytics_ui import render_analytics

# ── Config ────────────────────────────────────────────────────────────────────
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Falcon — Driver Companion", page_icon="🦅", layout="wide")
apply_custom_styles()

@st.cache_data(ttl=10, show_spinner=False)
def _fetch_health() -> dict:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if r.ok: return r.json()
    except: pass
    return {}

health = _fetch_health()
backend_ok = health.get("status") in ["ok", "degraded"]

# ── Header ────────────────────────────────────────────────────────────────────
header_left, header_right = st.columns([3, 2])
with header_left:
    st.markdown("<div class='falcon-title'>FALCON</div>", unsafe_allow_html=True)
    st.markdown("<div class='falcon-subtitle'>EDGE AI DRIVER COMPANION &nbsp;·&nbsp; LIVE IN-CABIN SAFETY TELEMETRY</div>", unsafe_allow_html=True)
with header_right:
    st.markdown("<div class='section-label'>SESSION</div>", unsafe_allow_html=True)
    st.caption("All inference happens on-device. No frames leave the cabin.")

st.markdown("<div class='hud-line'></div>", unsafe_allow_html=True)

# ── Setup Area ────────────────────────────────────────────────────────────────
intro_col, cockpit_col = st.columns([1.3, 2.0])
with intro_col:
    st.markdown("<div class='section-label'>FALCON ENTRY · v2.1</div>", unsafe_allow_html=True)
    if backend_ok:
        st.markdown("<br><div class='falcon-headline'>ENTER THE <span>COCKPIT</span></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='glass-panel'>"
            f"<div class='metric-label'>SYSTEM STATUS</div><div class='metric-value'>🟢 BACKEND ONLINE</div><div style='margin-top:0.4rem'></div>"
            f"<div class='metric-label'>DROWSINESS MODEL</div><div class='metric-value'>{'🟢 LOADED' if health.get('drowsiness_loaded') else '🔴 NOT LOADED'}</div><div style='margin-top:0.4rem'></div>"
            f"<div class='metric-label'>DISTRACTION MODEL</div><div class='metric-value'>{'🟢 LOADED' if health.get('distraction_loaded') else '🔴 NOT LOADED'}</div>"
            f"</div>", unsafe_allow_html=True
        )
    else:
        st.markdown("<br><div class='falcon-headline'><span>BACKEND OFFLINE</span></div>", unsafe_allow_html=True)
        st.error("Cannot reach backend. Run: `cd backend && uvicorn main:app --reload`")

with cockpit_col:
    render_cockpit(backend_ok, BACKEND_URL)

st.markdown("<br><br>", unsafe_allow_html=True)

# ── Mission & Analytics ───────────────────────────────────────────────────────
st.markdown("<div class='section-label'>MISSION</div>", unsafe_allow_html=True)
st.markdown("<div class='falcon-headline'>REDEFINING IN-CABIN SAFETY.<br>REAL-TIME EDGE AI. ZERO CLOUD LATENCY.</div>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

render_analytics()