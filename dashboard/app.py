"""
Falcon — Production Cinematic Cockpit Dashboard
================================================
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

# ── Constants ─────────────────────────────────────────────────────────────────
BACKEND_URL     = "http://127.0.0.1:8000"
HEALTH_TTL_SEC  = 10
NEON_YELLOW     = "#D4F000"
NEON_CYAN       = "#00F3FF"
BG_DARK         = "#050505"
BG_PANEL        = "#0d0d0d"
TEXT_MUTED      = "#666666"
TEXT_DIM        = "#999999"
TEXT_LIGHT      = "#E5E5E5"

st.set_page_config(
    page_title="FALCON — Driver Companion",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  GLOBAL CSS — Cinematic Brutalist Dark Theme
# ╚══════════════════════════════════════════════════════════════════════════╝
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;900&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, section.main > div {{
    background: {BG_DARK} !important;
    color: {TEXT_LIGHT} !important;
}}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{
    background: transparent !important;
    display: none !important;
}}
[data-testid="stSidebar"] {{
    background: #080808 !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}}
*, *::before, *::after {{ box-sizing: border-box; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: #0a0a0a; }}
::-webkit-scrollbar-thumb {{ background: #2a2a2a; border-radius: 2px; }}

/* ── Typography ── */
body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}

.f-display {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 900;
    font-size: clamp(3.5rem, 10vw, 7rem);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {TEXT_LIGHT};
    line-height: 0.9;
    margin: 0;
}}
.f-display .accent {{ color: {NEON_YELLOW}; }}

.f-headline {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: clamp(1.8rem, 4vw, 3.2rem);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {TEXT_LIGHT};
    line-height: 1.1;
    margin: 0;
}}
.f-headline .accent {{ color: {NEON_YELLOW}; }}
.f-headline .cyan   {{ color: {NEON_CYAN};   }}

.f-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
}}

.f-mono {{
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.82rem;
    color: {NEON_CYAN};
}}

.f-body {{
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    color: {TEXT_DIM};
    line-height: 1.6;
}}

/* ── HUD Line ── */
.hud-line {{
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        rgba(0,243,255,0.6) 15%,
        rgba(212,240,0,0.8) 50%,
        rgba(0,243,255,0.6) 85%,
        transparent 100%
    );
    margin: 0.8rem 0;
    position: relative;
}}
.hud-line::before, .hud-line::after {{
    content: '';
    position: absolute;
    top: -2px;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: {NEON_CYAN};
    box-shadow: 0 0 8px {NEON_CYAN};
}}
.hud-line::before {{ left: 15%; }}
.hud-line::after  {{ right: 15%; }}

.hud-line-sm {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 0.5rem 0;
}}

/* ── Chip / Badge ── */
.hud-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.3rem 0.8rem;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 2px;
    background: rgba(255,255,255,0.03);
    color: {TEXT_DIM};
}}
.hud-chip .dot {{
    width: 5px; height: 5px;
    border-radius: 50%;
    background: {NEON_YELLOW};
    box-shadow: 0 0 6px {NEON_YELLOW};
    animation: pulse-dot 2s ease-in-out infinite;
}}
.hud-chip .dot-cyan {{
    background: {NEON_CYAN};
    box-shadow: 0 0 6px {NEON_CYAN};
}}
.hud-chip .dot-red {{
    background: #ff4444;
    box-shadow: 0 0 6px #ff4444;
    animation: none;
}}
@keyframes pulse-dot {{
    0%,100% {{ opacity:1; transform:scale(1); }}
    50%      {{ opacity:0.4; transform:scale(0.7); }}
}}

/* ── Status Pill ── */
.status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 2px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 500;
}}
.status-pill.online {{
    background: rgba(212,240,0,0.08);
    border: 1px solid rgba(212,240,0,0.3);
    color: {NEON_YELLOW};
}}
.status-pill.offline {{
    background: rgba(255,68,68,0.08);
    border: 1px solid rgba(255,68,68,0.3);
    color: #ff6666;
}}
.status-pill.standby {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    color: {TEXT_DIM};
}}

/* ── Glass Panel ── */
.glass {{
    background: rgba(13,13,13,0.9);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 4px;
    box-shadow:
        0 1px 0 rgba(255,255,255,0.05) inset,
        0 24px 64px rgba(0,0,0,0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
}}
.glass::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 60%);
    pointer-events: none;
}}

/* ── Cockpit Shell ── */
.cockpit-shell {{
    background:
        radial-gradient(ellipse at 50% -10%, rgba(0,243,255,0.04) 0%, transparent 60%),
        radial-gradient(ellipse at 20% 100%, rgba(212,240,0,0.03) 0%, transparent 50%),
        #080808;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px;
    padding: 1.4rem 1.6rem 1.6rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 40px 120px rgba(0,0,0,0.9), inset 0 1px 0 rgba(255,255,255,0.05);
}}
.cockpit-shell::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, {NEON_CYAN}, {NEON_YELLOW}, {NEON_CYAN}, transparent);
    opacity: 0.5;
}}

/* ── Screen Bezel ── */
.screen-bezel {{
    background: #000;
    border: 1px solid rgba(0,243,255,0.2);
    border-radius: 4px;
    padding: 0.2rem;
    box-shadow:
        0 0 0 1px rgba(0,0,0,1),
        0 0 20px rgba(0,243,255,0.08),
        inset 0 0 30px rgba(0,0,0,0.8);
    position: relative;
}}
.screen-bezel::before {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 4px;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
    pointer-events: none;
    z-index: 1;
}}

/* ── Metric Cards ── */
.metric-card {{
    background: rgba(10,10,10,0.8);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 3px;
    padding: 0.7rem 0.9rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(212,240,0,0.3), transparent);
}}
.mc-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.58rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin-bottom: 0.3rem;
}}
.mc-value {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {TEXT_LIGHT};
    line-height: 1;
}}
.mc-value.safe       {{ color: #5edd7a; }}
.mc-value.drowsy     {{ color: {NEON_YELLOW}; }}
.mc-value.distracted {{ color: #ff9020; }}
.mc-value.critical   {{ color: #ff4444; }}
.mc-value.unknown    {{ color: {TEXT_MUTED}; }}
.mc-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: {TEXT_MUTED};
    margin-top: 0.15rem;
}}

/* ── Detection Panels ── */
.detect-panel {{
    background: rgba(10,10,10,0.95);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px;
    padding: 1.4rem;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s ease;
}}
.detect-panel:hover {{
    border-color: rgba(212,240,0,0.2);
}}
.detect-panel::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}}
.dp-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 900;
    font-size: clamp(2.5rem, 5vw, 4rem);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {TEXT_LIGHT};
    line-height: 0.9;
    margin: 0.6rem 0 0.8rem;
}}
.dp-title.drowsiness  {{ color: {NEON_YELLOW}; text-shadow: 0 0 40px rgba(212,240,0,0.15); }}
.dp-title.distraction {{ color: {NEON_CYAN};   text-shadow: 0 0 40px rgba(0,243,255,0.15); }}

.code-block {{
    background: #050505;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 3px;
    padding: 0.8rem 1rem;
    margin-top: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.6;
    color: #ccc;
    overflow-x: auto;
    white-space: pre;
}}
.code-block .key   {{ color: {NEON_CYAN};   }}
.code-block .val   {{ color: {NEON_YELLOW}; }}
.code-block .bool  {{ color: #ff9020; }}

/* ── Tech Cards ── */
.tech-card {{
    background: rgba(10,10,10,0.95);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 4px;
    padding: 1.1rem 1.2rem;
    position: relative;
    overflow: hidden;
}}
.tech-card::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,243,255,0.3), transparent);
}}
.tc-name {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {TEXT_LIGHT};
}}
.tc-version {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: {NEON_CYAN};
    letter-spacing: 0.08em;
    margin-top: 0.1rem;
}}
.tc-stat {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.6rem;
    font-weight: 900;
    color: {NEON_YELLOW};
    line-height: 1;
    margin-top: 0.5rem;
}}
.tc-stat-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: {TEXT_MUTED};
}}

/* ── Section Divider ── */
.section-divider {{
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0 1.2rem;
}}
.section-divider .sd-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: {TEXT_MUTED};
    flex-shrink: 0;
    letter-spacing: 0.1em;
}}
.section-divider .sd-title {{
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {TEXT_DIM};
    flex-shrink: 0;
}}
.section-divider .sd-line {{
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.06);
}}

/* ── Mission Statement ── */
.mission-block {{
    padding: 3rem 0;
    position: relative;
}}
.mission-line {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 900;
    font-size: clamp(2.2rem, 5.5vw, 5rem);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    line-height: 1.05;
    color: rgba(229,229,229,0.15);
}}
.mission-line.lit {{
    color: {TEXT_LIGHT};
}}
.mission-line.accent {{
    color: {NEON_YELLOW};
}}

/* ── Footer ── */
.footer {{
    border-top: 1px solid rgba(255,255,255,0.05);
    padding: 1.5rem 0 2rem;
    margin-top: 3rem;
}}

/* ── Offline Banner ── */
.offline-banner {{
    background: rgba(255,68,68,0.06);
    border: 1px solid rgba(255,68,68,0.2);
    border-radius: 4px;
    padding: 1.2rem 1.4rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}}
.ob-icon {{
    font-size: 1.4rem;
    flex-shrink: 0;
    line-height: 1;
    margin-top: 0.1rem;
}}
.ob-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #ff6666;
}}
.ob-body {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: {TEXT_DIM};
    margin-top: 0.3rem;
    line-height: 1.5;
}}

/* ── Streamlit overrides ── */
div[data-testid="stMetric"] {{
    background: rgba(10,10,10,0.8) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 3px !important;
    padding: 0.7rem 0.9rem !important;
}}
div[data-testid="stMetric"] label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: {TEXT_MUTED} !important;
    font-weight: 500 !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    color: {TEXT_LIGHT} !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
}}
div[data-testid="stPlotlyChart"] {{
    background: transparent !important;
}}
.stToggle > label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.08em !important;
    color: {TEXT_DIM} !important;
}}
div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: 1px solid rgba(212,240,0,0.4) !important;
    border-radius: 2px !important;
    color: {NEON_YELLOW} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stButton"] > button:hover {{
    background: rgba(212,240,0,0.1) !important;
    border-color: {NEON_YELLOW} !important;
    box-shadow: 0 0 12px rgba(212,240,0,0.2) !important;
}}
div[data-testid="stSlider"] {{
    padding: 0 !important;
}}
div[data-testid="stSlider"] > div {{
    color: {TEXT_DIM} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
}}
div[data-testid="stExpander"] {{
    background: rgba(10,10,10,0.8) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 3px !important;
}}
.stSelectbox > label, .stMultiSelect > label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: {TEXT_MUTED} !important;
}}
div[data-baseweb="select"] {{
    background: rgba(10,10,10,0.9) !important;
}}
div[data-baseweb="select"] > div {{
    background: rgba(10,10,10,0.9) !important;
    border-color: rgba(255,255,255,0.08) !important;
    color: {TEXT_LIGHT} !important;
    border-radius: 3px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
}}
.stDataFrame, .stDataFrameContainer {{
    background: rgba(10,10,10,0.8) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 3px !important;
}}
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Barlow Condensed', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: {TEXT_LIGHT} !important;
}}
</style>
""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  HELPERS
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
    return health, health.get("status") == "ok"


def section_divider(num: str, title: str):
    st.markdown(
        f"""<div class="section-divider">
              <span class="sd-num">{num}</span>
              <span class="sd-title">{title}</span>
              <div class="sd-line"></div>
            </div>""",
        unsafe_allow_html=True,
    )


def hud_line():
    st.markdown('<div class="hud-line"></div>', unsafe_allow_html=True)


def hud_line_sm():
    st.markdown('<div class="hud-line-sm"></div>', unsafe_allow_html=True)


ALERT_ICONS = {0: "●", 1: "▲", 2: "✕"}
ALERT_COLORS = {0: "#5edd7a", 1: NEON_YELLOW, 2: "#ff4444"}
STATE_CSS_CLASS = {
    "safe":       "safe",
    "drowsy":     "drowsy",
    "distracted": "distracted",
    "critical":   "critical",
    "unknown":    "unknown",
}
STATE_LABEL = {
    "safe":       "SAFE",
    "drowsy":     "DROWSY",
    "distracted": "DISTRACTED",
    "critical":   "CRITICAL",
    "unknown":    "STANDBY",
}

# ╔══════════════════════════════════════════════════════════════════════════╗
#  HEADER
# ╚══════════════════════════════════════════════════════════════════════════╝
health, backend_ok = get_health()

top_l, top_mid, top_r = st.columns([2.5, 3, 2])

with top_l:
    drowsy_ok  = health.get("drowsiness_loaded",  False)
    distract_ok = health.get("distraction_loaded", False)
    status_cls = "online" if backend_ok else "offline"
    status_txt = "ONLINE" if backend_ok else "OFFLINE"
    st.markdown(
        f"""
        <div style="display:flex; align-items:flex-end; gap:1.2rem; padding-top:0.4rem;">
          <div>
            <div class="f-label" style="margin-bottom:0.2rem;">SYSTEM</div>
            <div class="status-pill {status_cls}">
              <span class="dot{'  dot-red' if not backend_ok else ''}">&#9679;</span>
              BACKEND {status_txt}
            </div>
          </div>
          <div>
            <div class="f-label" style="margin-bottom:0.2rem;">DROWSINESS</div>
            <div class="status-pill {'online' if drowsy_ok else 'standby'}">
              {'LOADED' if drowsy_ok else 'NOT LOADED'}
            </div>
          </div>
          <div>
            <div class="f-label" style="margin-bottom:0.2rem;">DISTRACTION</div>
            <div class="status-pill {'online' if distract_ok else 'standby'}">
              {'LOADED' if distract_ok else 'NOT LOADED'}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_mid:
    st.markdown(
        '<div class="f-display" style="text-align:center;">FAL<span class="accent">CON</span></div>',
        unsafe_allow_html=True,
    )

with top_r:
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S · %d %b %Y")
    st.markdown(
        f"""<div style="text-align:right; padding-top:1.2rem;">
              <div class="f-mono">{ts}</div>
              <div class="f-label" style="margin-top:0.4rem;">
                EDGE AI · ON-DEVICE · ZERO CLOUD
              </div>
            </div>""",
        unsafe_allow_html=True,
    )

hud_line()
st.markdown(
    '<div class="f-label" style="text-align:center; letter-spacing:0.3em; padding:0.1rem 0 0.6rem;">'
    'EDGE AI DRIVER COMPANION &nbsp;·&nbsp; REAL-TIME IN-CABIN SAFETY TELEMETRY &nbsp;·&nbsp; v2.1'
    '</div>',
    unsafe_allow_html=True,
)
hud_line()

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 01 · COCKPIT
# ╚══════════════════════════════════════════════════════════════════════════╝
section_divider("01", "COCKPIT · LIVE IN-CABIN VIEW")

st.markdown('<div class="cockpit-shell">', unsafe_allow_html=True)

# HUD chips row
chip_a, chip_b, chip_c, chip_d, chip_s = st.columns([1.2, 1.2, 1.2, 1.2, 4])
with chip_a:
    st.markdown(
        '<div class="hud-chip"><span class="dot"></span>HUD MODE · DRIVER</div>',
        unsafe_allow_html=True,
    )
with chip_b:
    st.markdown(
        '<div class="hud-chip"><span class="dot dot-cyan"></span>ENGINE · ON-DEVICE</div>',
        unsafe_allow_html=True,
    )
with chip_c:
    st.markdown(
        f'<div class="hud-chip"><span class="dot"></span>LATENCY · &lt; 25 MS</div>',
        unsafe_allow_html=True,
    )
with chip_d:
    chipcolor = "dot" if backend_ok else "dot dot-red"
    st.markdown(
        f'<div class="hud-chip"><span class="{chipcolor}"></span>'
        f'{"CONNECTED" if backend_ok else "DISCONNECTED"}'
        f'</div>',
        unsafe_allow_html=True,
    )

hud_line_sm()

# Cockpit columns: info | live feed | metrics
info_col, feed_col, meta_col = st.columns([1.2, 2.4, 1.4])

with info_col:
    st.markdown('<div class="f-label">FALCON ENTRY · SEQUENCE INIT</div>', unsafe_allow_html=True)
    st.markdown(
        f"""<div style="margin-top:0.8rem;">
              <div class="f-headline">ENTER<br>THE <span class="accent">COCKPIT</span></div>
            </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="f-body" style="margin-top:0.8rem; max-width:26ch;">'
        f'Falcon locks onto the driver\'s face in real time — all inference runs on-device with '
        f'zero cloud latency.'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    if backend_ok:
        st.markdown(
            f"""<div class="glass" style="padding:0.9rem 1rem;">
                  <div class="f-label" style="margin-bottom:0.5rem;">SYSTEM STATUS</div>
                  <div style="display:flex; flex-direction:column; gap:0.4rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                      <span class="f-mono" style="font-size:0.65rem; color:#666;">BACKEND</span>
                      <span class="f-mono" style="font-size:0.7rem; color:{NEON_YELLOW};">ONLINE ●</span>
                    </div>
                    <div class="hud-line-sm"></div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                      <span class="f-mono" style="font-size:0.65rem; color:#666;">DROWSINESS</span>
                      <span class="f-mono" style="font-size:0.7rem; color:{'#5edd7a' if drowsy_ok else '#ff4444'};">{'LOADED' if drowsy_ok else 'FAILED'}</span>
                    </div>
                    <div class="hud-line-sm"></div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                      <span class="f-mono" style="font-size:0.65rem; color:#666;">DISTRACTION</span>
                      <span class="f-mono" style="font-size:0.7rem; color:{'#5edd7a' if distract_ok else '#ff4444'};">{'LOADED' if distract_ok else 'FAILED'}</span>
                    </div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="offline-banner">
                  <div class="ob-icon">⚡</div>
                  <div>
                    <div class="ob-title">BACKEND OFFLINE</div>
                    <div class="ob-body">cd backend<br>uvicorn main:app --reload --host 0.0.0.0 --port 8000</div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

with feed_col:
    st.markdown('<div class="f-label" style="margin-bottom:0.4rem;">LIVE FEED · WEBCAM INPUT</div>', unsafe_allow_html=True)

    ctrl_l, ctrl_r = st.columns([2, 2])
    with ctrl_l:
        run_live = st.toggle("▶  Start Live Inference", value=False)
    with ctrl_r:
        fps_target = st.slider("Target FPS", 1, 15, 5, label_visibility="collapsed")
        st.markdown(
            f'<div class="f-label" style="margin-top:-0.3rem;">FPS TARGET: {fps_target}</div>',
            unsafe_allow_html=True,
        )

    screen_ph = st.empty()

    if not run_live:
        screen_ph.markdown(
            f"""<div class="screen-bezel" style="aspect-ratio:16/9; display:flex; align-items:center; justify-content:center; min-height:240px;">
                  <div style="text-align:center;">
                    <div style="font-size:3rem; opacity:0.15;">◉</div>
                    <div class="f-label" style="margin-top:0.6rem; letter-spacing:0.2em;">INFERENCE PAUSED</div>
                    <div class="f-mono" style="font-size:0.65rem; color:{TEXT_MUTED}; margin-top:0.2rem;">TOGGLE ABOVE TO BEGIN</div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4, m5 = st.columns(5)
    state_ph  = m1.empty()
    alert_ph  = m2.empty()
    drowsy_ph = m3.empty()
    dist_ph   = m4.empty()
    lat_ph    = m5.empty()

    def render_metrics(d_state="—", a_level=0, drowsy="—", d_conf=0.0,
                       distr="—", di_conf=0.0, latency=0.0):
        css_cls  = STATE_CSS_CLASS.get(d_state, "unknown")
        lbl      = STATE_LABEL.get(d_state, "STANDBY")
        al_icon  = ALERT_ICONS.get(a_level, "●")
        al_color = ALERT_COLORS.get(a_level, TEXT_MUTED)
        state_ph.markdown(
            f'<div class="metric-card"><div class="mc-label">DRIVER STATE</div>'
            f'<div class="mc-value {css_cls}">{lbl}</div></div>',
            unsafe_allow_html=True,
        )
        alert_ph.markdown(
            f'<div class="metric-card"><div class="mc-label">ALERT LEVEL</div>'
            f'<div class="mc-value" style="color:{al_color};">'
            f'{al_icon} {a_level}/2</div></div>',
            unsafe_allow_html=True,
        )
        drowsy_ph.markdown(
            f'<div class="metric-card"><div class="mc-label">DROWSINESS</div>'
            f'<div class="mc-value">{str(drowsy).upper()}</div>'
            f'<div class="mc-sub">{d_conf:.0%}</div></div>',
            unsafe_allow_html=True,
        )
        dist_ph.markdown(
            f'<div class="metric-card"><div class="mc-label">DISTRACTION</div>'
            f'<div class="mc-value">{str(distr).upper()}</div>'
            f'<div class="mc-sub">{di_conf:.0%}</div></div>',
            unsafe_allow_html=True,
        )
        lat_ph.markdown(
            f'<div class="metric-card"><div class="mc-label">LATENCY</div>'
            f'<div class="mc-value">{latency:.0f}<span style="font-size:0.8rem;font-weight:400;color:{TEXT_MUTED}"> MS</span></div></div>',
            unsafe_allow_html=True,
        )

    render_metrics()

with meta_col:
    st.markdown('<div class="f-label">PIPELINE TELEMETRY</div>', unsafe_allow_html=True)
    st.markdown(
        f"""<div class="glass" style="padding:1rem; margin-top:0.4rem;">
              <div class="f-label" style="margin-bottom:0.5rem;">MODEL STACK</div>
              <div style="display:flex; flex-direction:column; gap:0.5rem;">
                <div>
                  <div class="f-mono" style="font-size:0.65rem;">FACE MESH</div>
                  <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:{TEXT_DIM};">MediaPipe 0.10 · 468 pts</div>
                </div>
                <div class="hud-line-sm"></div>
                <div>
                  <div class="f-mono" style="font-size:0.65rem;">DISTRACTION</div>
                  <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:{TEXT_DIM};">EfficientNet-B0 · 6-cls</div>
                </div>
                <div class="hud-line-sm"></div>
                <div>
                  <div class="f-mono" style="font-size:0.65rem;">DROWSINESS</div>
                  <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:{TEXT_DIM};">EAR · PERCLOS · MAR</div>
                </div>
                <div class="hud-line-sm"></div>
                <div>
                  <div class="f-mono" style="font-size:0.65rem;">CONTEXT ENGINE</div>
                  <div style="font-family:'Inter',sans-serif; font-size:0.75rem; color:{TEXT_DIM};">Rule-based alert fusion</div>
                </div>
              </div>

              <div class="hud-line-sm" style="margin:0.8rem 0;"></div>

              <div class="f-label" style="margin-bottom:0.5rem;">THRESHOLDS</div>
              <div style="display:flex; flex-direction:column; gap:0.3rem;">
                <div style="display:flex; justify-content:space-between;">
                  <span style="font-family:'Inter',sans-serif; font-size:0.73rem; color:{TEXT_DIM};">EAR</span>
                  <span class="f-mono" style="font-size:0.7rem; color:{NEON_YELLOW};">0.25</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                  <span style="font-family:'Inter',sans-serif; font-size:0.73rem; color:{TEXT_DIM};">PERCLOS</span>
                  <span class="f-mono" style="font-size:0.7rem; color:{NEON_YELLOW};">60 FRM</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                  <span style="font-family:'Inter',sans-serif; font-size:0.73rem; color:{TEXT_DIM};">HEAD YAW</span>
                  <span class="f-mono" style="font-size:0.7rem; color:{NEON_YELLOW};">±35°</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                  <span style="font-family:'Inter',sans-serif; font-size:0.73rem; color:{TEXT_DIM};">CONF. MIN</span>
                  <span class="f-mono" style="font-size:0.7rem; color:{NEON_YELLOW};">0.65</span>
                </div>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)  # /cockpit-shell

# ── Live inference loop ────────────────────────────────────────────────────
if backend_ok and run_live:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        screen_ph.markdown(
            f"""<div class="screen-bezel" style="padding:2rem; text-align:center;">
                  <div class="ob-title">CAMERA ACCESS DENIED</div>
                  <div class="ob-body">Could not open webcam (index 0).<br>
                  Check System Preferences → Privacy → Camera.</div>
                </div>""",
            unsafe_allow_html=True,
        )
    else:
        frame_interval = 1.0 / fps_target
        try:
            while run_live:
                t0 = time.time()
                ret, frame_bgr = cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue

                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                screen_ph.image(frame_rgb, channels="RGB", use_container_width=True)

                _, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                b64 = base64.b64encode(buf.tobytes()).decode()

                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/infer",
                        json={"frame": b64},
                        timeout=3,
                    )
                    if resp.status_code == 200:
                        data      = resp.json()
                        latency   = (time.time() - t0) * 1000
                        render_metrics(
                            d_state  = data.get("driver_state", "unknown"),
                            a_level  = data.get("alert_level", 0),
                            drowsy   = data.get("drowsiness", "—"),
                            d_conf   = data.get("drowsiness_confidence", 0.0),
                            distr    = data.get("distraction", "—"),
                            di_conf  = data.get("distraction_confidence", 0.0),
                            latency  = latency,
                        )
                except Exception:
                    pass

                elapsed = time.time() - t0
                if frame_interval - elapsed > 0:
                    time.sleep(frame_interval - elapsed)
        finally:
            cap.release()

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 02 · MISSION
# ╚══════════════════════════════════════════════════════════════════════════╝
section_divider("02", "MISSION STATEMENT")

st.markdown(
    f"""<div class="mission-block">
          <div class="mission-line lit">REDEFINING IN-CABIN SAFETY.</div>
          <div class="mission-line lit">REAL-TIME EDGE AI.</div>
          <div class="mission-line accent">ZERO CLOUD LATENCY.</div>
          <div class="f-body" style="margin-top:1.2rem; max-width:55ch;">
            Every frame is processed on-device. No biometric data leaves the vehicle.
            Falcon delivers sub-25 ms alert latency on consumer-grade automotive hardware —
            no connectivity required, no privacy compromise.
          </div>
        </div>""",
    unsafe_allow_html=True,
)

hud_line()

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 03 · DUAL DETECTION
# ╚══════════════════════════════════════════════════════════════════════════╝
section_divider("03", "DUAL DETECTION SYSTEM")

dd_l, dd_sep, dd_r = st.columns([1, 0.04, 1])

with dd_l:
    st.markdown(
        f"""<div class="detect-panel">
              <div class="f-label">SYSTEM · 01</div>
              <div class="dp-title drowsiness">DROWSINESS</div>
              <div class="f-body">
                MediaPipe FaceMesh extracts 468 facial landmarks per frame.
                Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR), and PERCLOS
                are computed geometrically — no secondary model required.
              </div>
              <div class="hud-line-sm" style="margin:0.9rem 0;"></div>
              <div style="display:flex; gap:0.6rem; flex-wrap:wrap; margin-bottom:0.8rem;">
                <div class="hud-chip">EAR THRESHOLD · 0.25</div>
                <div class="hud-chip">PERCLOS WINDOW · 60 FRM</div>
                <div class="hud-chip">INFERENCE · &lt;8 MS</div>
              </div>
              <div class="code-block"><span class="key">"state"</span>: <span class="val">"DROWSY"</span>,
<span class="key">"ear"</span>: <span class="val">0.18</span>,
<span class="key">"perclos"</span>: <span class="val">0.42</span>,
<span class="key">"alert"</span>: <span class="bool">true</span></div>
            </div>""",
        unsafe_allow_html=True,
    )

with dd_sep:
    st.markdown(
        '<div style="height:100%; width:1px; background:rgba(255,255,255,0.06); margin:0 auto;"></div>',
        unsafe_allow_html=True,
    )

with dd_r:
    st.markdown(
        f"""<div class="detect-panel">
              <div class="f-label">SYSTEM · 02</div>
              <div class="dp-title distraction">DISTRACTION</div>
              <div class="f-body">
                EfficientNet-B0 classifies driver attention across 6 categories
                using head pose and gaze direction. GPU-optional — runs at
                real-time on CPU via ONNX optimisation.
              </div>
              <div class="hud-line-sm" style="margin:0.9rem 0;"></div>
              <div style="display:flex; gap:0.6rem; flex-wrap:wrap; margin-bottom:0.8rem;">
                <div class="hud-chip">6-CLASS OUTPUT</div>
                <div class="hud-chip">HEAD YAW ±35°</div>
                <div class="hud-chip">EFFICIENTNET-B0</div>
              </div>
              <div class="code-block"><span class="key">"state"</span>: <span class="val">"DISTRACTED"</span>,
<span class="key">"head_yaw"</span>: <span class="val">32.1</span>,
<span class="key">"phone_detected"</span>: <span class="bool">true</span>,
<span class="key">"confidence"</span>: <span class="val">0.91</span></div>
            </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 04 · TECH STACK
# ╚══════════════════════════════════════════════════════════════════════════╝
section_divider("04", "TECH STACK · MODEL SPECIFICATIONS")

tc1, tc2, tc3, tc4, tc5 = st.columns(5)

tech_cards = [
    ("FACE MESH",        "MediaPipe 0.10",  "468", "LANDMARKS",   "< 8 MS"),
    ("EFFICIENTNET",     "B0 · ONNX",       "6",   "CLASSES",     "< 12 MS"),
    ("CONTEXT ENGINE",   "Rule Fusion",     "3",   "ALERT LEVELS","< 1 MS"),
    ("FASTAPI",          "v0.104 Backend",  "100", "FPS MAX",     "< 25 MS"),
    ("STREAMLIT",        "v1.28 Frontend",  "60",  "FPS TARGET",  "< 17 MS"),
]

for col, (name, version, stat_val, stat_lbl, latency) in zip(
    [tc1, tc2, tc3, tc4, tc5], tech_cards
):
    with col:
        st.markdown(
            f"""<div class="tech-card">
                  <div class="tc-name">{name}</div>
                  <div class="tc-version">{version}</div>
                  <div class="tc-stat">{stat_val}</div>
                  <div class="tc-stat-label">{stat_lbl}</div>
                  <div class="hud-line-sm" style="margin:0.6rem 0;"></div>
                  <div class="f-mono" style="font-size:0.65rem; color:{TEXT_MUTED};">{latency}</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
hud_line()

# ╔══════════════════════════════════════════════════════════════════════════╗
#  SECTION 05 · SESSION ANALYTICS
# ╚══════════════════════════════════════════════════════════════════════════╝
section_divider("05", "SESSION ANALYTICS · LOG VIEWER")

logs_dir = Path("logs")
csvs     = sorted(logs_dir.glob("session_*.csv"), reverse=True) if logs_dir.exists() else []

COLOUR_MAP = {
    "attentive":        "#5edd7a",
    "distracted_left":  "#ff4444",
    "distracted_right": "#ff4444",
    "distracted_down":  "#ff9020",
    "distracted_up":    "#ff9020",
    "drowsy":           NEON_YELLOW,
    "no_face":          "#555555",
}

PLOTLY_BASE = dict(
    plot_bgcolor  = "#080808",
    paper_bgcolor = "#080808",
    font          = dict(color="#888", family="Inter", size=11),
    margin        = dict(l=4, r=4, t=12, b=4),
    xaxis         = dict(gridcolor="#1a1a1a", zeroline=False),
    yaxis         = dict(gridcolor="#1a1a1a", zeroline=False),
)

if not csvs:
    st.markdown(
        f"""<div class="glass" style="padding:2.5rem; text-align:center;">
              <div style="font-size:2.5rem; opacity:0.1; margin-bottom:0.8rem;">◎</div>
              <div class="f-label" style="letter-spacing:0.22em;">NO SESSION LOGS</div>
              <div class="f-body" style="margin:0.5rem auto 0; max-width:40ch; text-align:center;">
                Run a live inference session in the cockpit above.
                Logs will appear here automatically.
              </div>
            </div>""",
        unsafe_allow_html=True,
    )
else:
    log_col, picker_spacer = st.columns([3, 1])
    with log_col:
        selected = st.selectbox(
            "SESSION",
            options=csvs,
            format_func=lambda p: p.stem,
        )

    df           = pd.read_csv(selected)
    summary_path = selected.parent / (selected.stem + "_summary.json")
    summary      = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("DURATION",     f"{summary.get('duration_sec', 0):.0f} s")
    k2.metric("ATTENTIVE",    f"{summary.get('attentive_pct', 0):.1f}%")
    k3.metric("ALERTS FIRED", summary.get("alert_count", 0))
    k4.metric("TOTAL FRAMES", summary.get("total_frames", len(df)))
    k5.metric("AVG LATENCY",  f"{summary.get('avg_latency_ms', 0):.1f} ms")

    hud_line_sm()

    charts_l, charts_r = st.columns([2, 1])

    with charts_l:
        st.markdown('<div class="f-label" style="margin-bottom:0.4rem;">STATE TIMELINE</div>', unsafe_allow_html=True)
        fig_tl = px.scatter(
            df, x="elapsed_s", y="label",
            color="label", color_discrete_map=COLOUR_MAP,
            height=220,
        )
        fig_tl.update_traces(marker=dict(size=3, opacity=0.7))
        fig_tl.update_layout(showlegend=False, **PLOTLY_BASE)
        st.plotly_chart(fig_tl, use_container_width=True)

        if all(c in df.columns for c in ["yaw", "pitch", "roll"]):
            pose_df = df.dropna(subset=["yaw", "pitch", "roll"])
            if not pose_df.empty:
                st.markdown('<div class="f-label" style="margin-bottom:0.4rem;">HEAD ANGLES</div>', unsafe_allow_html=True)
                fig_ang = go.Figure()
                for col_name, colour, lbl in [
                    ("yaw",   NEON_CYAN,    "Yaw"),
                    ("pitch", "#81c784",    "Pitch"),
                    ("roll",  NEON_YELLOW,  "Roll"),
                ]:
                    fig_ang.add_trace(go.Scatter(
                        x=pose_df["elapsed_s"], y=pose_df[col_name],
                        mode="lines", name=lbl,
                        line=dict(color=colour, width=1.5),
                    ))
                fig_ang.update_layout(height=220, **PLOTLY_BASE,
                    legend=dict(orientation="h", y=1.1, font=dict(size=10)))
                st.plotly_chart(fig_ang, use_container_width=True)

        if "ear" in df.columns and df["ear"].notna().any():
            st.markdown('<div class="f-label" style="margin-bottom:0.4rem;">EYE ASPECT RATIO</div>', unsafe_allow_html=True)
            fig_ear = go.Figure()
            fig_ear.add_trace(go.Scatter(
                x=df["elapsed_s"], y=df["ear"],
                mode="lines", name="EAR",
                line=dict(color="#ce93d8", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(206,147,216,0.05)",
            ))
            fig_ear.add_hline(
                y=0.22, line_dash="dash", line_color="#e57373",
                annotation_text="Threshold 0.22",
                annotation_font=dict(size=10, color="#e57373"),
            )
            fig_ear.update_layout(height=200, showlegend=False, **PLOTLY_BASE)
            st.plotly_chart(fig_ear, use_container_width=True)

    with charts_r:
        st.markdown('<div class="f-label" style="margin-bottom:0.4rem;">STATE DISTRIBUTION</div>', unsafe_allow_html=True)
        label_counts         = df["label"].value_counts().reset_index()
        label_counts.columns = ["label", "count"]
        fig_pie = go.Figure(go.Pie(
            labels=label_counts["label"],
            values=label_counts["count"],
            hole=0.6,
            marker=dict(
                colors=[COLOUR_MAP.get(l, "#555") for l in label_counts["label"]],
                line=dict(color="#080808", width=2),
            ),
            textinfo="percent",
            textfont=dict(size=10, color="#ccc"),
        ))
        fig_pie.update_layout(
            height=280,
            showlegend=True,
            legend=dict(font=dict(size=9, color="#888"), x=0, y=-0.1, orientation="h"),
            margin=dict(l=4, r=4, t=12, b=4),
            paper_bgcolor="#080808",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("↓  RAW FRAME DATA"):
        st.dataframe(df, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
#  FOOTER
# ╚══════════════════════════════════════════════════════════════════════════╝
hud_line()
st.markdown(
    f"""<div class="footer">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
            <div>
              <div class="f-display" style="font-size:1.6rem; letter-spacing:0.2em;">
                FAL<span class="accent">CON</span>
              </div>
              <div class="f-label" style="margin-top:0.2rem;">EDGE AI DRIVER COMPANION · v2.1</div>
            </div>
            <div style="text-align:right;">
              <div class="f-mono" style="font-size:0.68rem; color:{TEXT_MUTED};">
                ALL INFERENCE ON-DEVICE · NO DATA LEAVES THE VEHICLE
              </div>
              <div class="f-mono" style="font-size:0.65rem; color:{TEXT_MUTED}; margin-top:0.2rem;">
                MediaPipe · EfficientNet-B0 · FastAPI · Streamlit
              </div>
            </div>
          </div>
        </div>""",
    unsafe_allow_html=True,
)
