import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

def render_analytics():
    logs_dir = Path("logs")
    csvs = sorted(logs_dir.glob("session_*.csv"), reverse=True) if logs_dir.exists() else []

    st.markdown("<div class='section-label'>SESSION LOGS</div>", unsafe_allow_html=True)

    if not csvs:
        st.info("No session logs found yet. Run a live inference session to generate logs.")
        return

    selected = st.sidebar.selectbox("Session", options=csvs, format_func=lambda p: p.stem)
    df = pd.read_csv(selected)
    
    summary_path = selected.parent / (selected.stem + "_summary.json")
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Duration", f"{summary.get('duration_sec', 0):.0f} s")
    kc2.metric("Attentive", f"{summary.get('attentive_pct', 0):.1f} %")
    kc3.metric("Alerts", summary.get("alert_count", 0))
    kc4.metric("Total Frames", summary.get("total_frames", len(df)))

    st.divider()

    COLOUR_MAP = {
        "attentive": "#50c864", "distracted_left": "#e03c3c", "distracted_right": "#e03c3c",
        "distracted_down": "#ff9020", "distracted_up": "#ff9020", "drowsy": "#f0e040", "no_face": "#808080"
    }

    st.subheader("State Timeline")
    fig_tl = px.scatter(df, x="elapsed_s", y="label", color="label", color_discrete_map=COLOUR_MAP, height=280)
    fig_tl.update_traces(marker=dict(size=4, opacity=0.7))
    fig_tl.update_layout(showlegend=False, margin=dict(l=0, r=0, t=8, b=0), plot_bgcolor="#111", paper_bgcolor="#111", font_color="#ccc")
    st.plotly_chart(fig_tl, use_container_width=True)

    if all(c in df.columns for c in ["yaw", "pitch", "roll"]):
        pose_df = df.dropna(subset=["yaw", "pitch", "roll"])
        if not pose_df.empty:
            st.subheader("Head Angles")
            fig_ang = go.Figure()
            for col_name, color in [("yaw", "#4fc3f7"), ("pitch", "#81c784"), ("roll", "#ffb74d")]:
                fig_ang.add_trace(go.Scatter(x=pose_df["elapsed_s"], y=pose_df[col_name], mode="lines", name=col_name.capitalize(), line=dict(color=color, width=1.5)))
            fig_ang.update_layout(height=260, margin=dict(l=0, r=0, t=8, b=0), plot_bgcolor="#111", paper_bgcolor="#111", font_color="#ccc")
            st.plotly_chart(fig_ang, use_container_width=True)

    st.subheader("State Distribution")
    label_counts = df["label"].value_counts().reset_index()
    label_counts.columns = ["label", "count"]
    fig_pie = px.pie(label_counts, names="label", values="count", color="label", color_discrete_map=COLOUR_MAP, height=320)
    fig_pie.update_layout(margin=dict(l=0, r=0, t=8, b=0))
    st.plotly_chart(fig_pie, use_container_width=True)