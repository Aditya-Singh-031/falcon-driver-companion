import streamlit as st

def apply_custom_styles():
    TEXT_MUTED = "#999999"
    TEXT_LIGHT = "#E5E5E5"
    NEON_YELLOW = "#D4F000"
    NEON_CYAN = "#00F3FF"

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
          font-size: min(8vw, 4rem); font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; color: {TEXT_LIGHT}; line-height: 1;
        }}
        .falcon-subtitle {{ font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.25em; color: {TEXT_MUTED}; }}
        .metric-label {{ font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; color: {TEXT_MUTED}; }}
        .metric-value {{ font-size: 1.1rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }}
        
        .glass-panel {{
          background: rgba(17,17,17,0.85); border-radius: 18px; border: 1px solid rgba(255,255,255,0.06);
          box-shadow: 0 20px 60px rgba(0,0,0,0.80); backdrop-filter: blur(24px); padding: 1.1rem 1.4rem;
        }}
        .cockpit-shell {{
          border-radius: 28px; background: radial-gradient(circle at top, #1a1a1a 0%, #050505 55%, #000000 100%);
          border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 40px 120px rgba(0,0,0,0.95); padding: 1.5rem 1.8rem;
        }}
        .hud-line {{
          height: 1px; width: 100%; opacity: 0.65; margin: 0.5rem 0 0.6rem 0;
          background: linear-gradient(90deg, transparent 0%, {NEON_CYAN} 20%, {NEON_YELLOW} 50%, {NEON_CYAN} 80%, transparent 100%);
        }}
        .hud-chip {{
          font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; border-radius: 999px;
          padding: 0.25rem 0.9rem; border: 1px solid rgba(255,255,255,0.18);
          background: radial-gradient(circle at top left, rgba(212,240,0,0.16) 0%, rgba(5,5,5,1) 55%); color: {TEXT_LIGHT}; display: inline-block;
        }}
        .hud-chip span {{ color: {NEON_YELLOW}; }}
        .falcon-headline {{ font-size: min(7vw, 3rem); font-weight: 800; text-transform: uppercase; letter-spacing: 0.12em; line-height: 1.15; }}
        .falcon-headline span {{ color: {NEON_YELLOW}; }}
        .section-label {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.22em; color: {TEXT_MUTED}; margin-bottom: 0.4rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )