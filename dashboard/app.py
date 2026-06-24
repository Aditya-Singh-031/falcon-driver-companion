"""
Falcon — Session Dashboard
Streamlit app to visualise saved session logs.

Run:
  streamlit run dashboard/app.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Falcon Dashboard", page_icon="\U0001f985", layout="wide")

st.title("\U0001f985 Falcon — Driver Session Dashboard")

# ─── Session picker ───────────────────────────────────────────────────────────
logs_dir = Path("logs")
csvs = sorted(logs_dir.glob("session_*.csv"), reverse=True) if logs_dir.exists() else []

if not csvs:
    st.warning("No session logs found. Run `python src/models/test_distraction_live.py` first.")
    st.stop()

selected = st.sidebar.selectbox(
    "Session",
    options=csvs,
    format_func=lambda p: p.stem,
)

# ─── Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv(selected)
summary_path = selected.parent / (selected.stem + "_summary.json")
summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

# ─── KPIs ─────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Duration",    f"{summary.get('duration_sec', 0):.0f} s")
col2.metric("Attentive",   f"{summary.get('attentive_pct', 0):.1f} %")
col3.metric("Alerts",      summary.get('alert_count', 0))
col4.metric("Total Frames", summary.get('total_frames', len(df)))

st.divider()

# ─── Label timeline ───────────────────────────────────────────────────────────
st.subheader("State Timeline")
colour_map = {
    "attentive":        "#50c864",
    "distracted_left":  "#e03c3c",
    "distracted_right": "#e03c3c",
    "distracted_down":  "#ff9020",
    "distracted_up":    "#ff9020",
    "drowsy":           "#f0e040",
    "no_face":          "#808080",
}
fig_timeline = px.scatter(
    df, x="elapsed_s", y="label",
    color="label",
    color_discrete_map=colour_map,
    height=280,
)
fig_timeline.update_traces(marker=dict(size=4, opacity=0.7))
fig_timeline.update_layout(showlegend=False, margin=dict(l=0, r=0, t=8, b=0))
st.plotly_chart(fig_timeline, use_container_width=True)

# ─── Angles over time ─────────────────────────────────────────────────────────
pose_df = df.dropna(subset=["yaw", "pitch", "roll"])
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
        height=260,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="#111", paper_bgcolor="#111",
        font_color="#ccc",
        yaxis=dict(zeroline=True, zerolinecolor="#444"),
    )
    st.plotly_chart(fig_ang, use_container_width=True)

# ─── EAR over time ────────────────────────────────────────────────────────────
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
        height=220,
        margin=dict(l=0, r=0, t=8, b=0),
        plot_bgcolor="#111", paper_bgcolor="#111",
        font_color="#ccc",
    )
    st.plotly_chart(fig_ear, use_container_width=True)

# ─── Label distribution ───────────────────────────────────────────────────────
st.subheader("State Distribution")
label_counts = df["label"].value_counts().reset_index()
label_counts.columns = ["label", "count"]
fig_pie = px.pie(
    label_counts, names="label", values="count",
    color="label", color_discrete_map=colour_map,
    height=320,
)
fig_pie.update_layout(margin=dict(l=0, r=0, t=8, b=0))
st.plotly_chart(fig_pie, use_container_width=True)

# ─── Raw data ─────────────────────────────────────────────────────────────────
with st.expander("Raw frame data"):
    st.dataframe(df, use_container_width=True)
