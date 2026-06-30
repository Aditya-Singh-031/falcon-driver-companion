import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def render_analytics():
    st.markdown("<div class='section-label'>SESSION LOGS</div>", unsafe_allow_html=True)

    csvs = sorted(LOGS_DIR.glob("session_*.csv"), reverse=True) if LOGS_DIR.exists() else []

    if not csvs:
        st.info(
            "No session logs yet. Start a live inference session above — "
            "each frame is appended to a CSV in `dashboard/logs/` in real-time."
        )
        return

    selected = st.sidebar.selectbox(
        "Session",
        options=csvs,
        format_func=lambda p: p.stem.replace("session_", ""),
    )

    try:
        df = pd.read_csv(selected)
    except Exception as exc:
        st.error(f"Could not read {selected.name}: {exc}")
        return

    if "label" in df.columns and "driver_state" not in df.columns:
        df = df.rename(columns={"label": "driver_state"})

    summary_path = selected.parent / (selected.stem + "_summary.json")
    summary: dict = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
        except Exception:
            pass

    # ── KPI row ───────────────────────────────────────────────────────────────
    kc1, kc2, kc3, kc4, kc5 = st.columns(5)
    kc1.metric("Duration", f"{summary.get('duration_sec', 0):.0f} s")
    kc2.metric("Attentive", f"{summary.get('attentive_pct', 0):.1f}%")
    kc3.metric("Alerts", summary.get("alert_count", "—"))
    kc4.metric("Frames", summary.get("total_frames", len(df)))
    kc5.metric("Avg Latency", f"{summary.get('mean_latency_ms', 0):.0f} ms")

    st.divider()

    COLOUR_MAP = {
        "safe": "#50c864",
        "attentive": "#50c864",
        "distracted": "#e03c3c",
        "distracted_left": "#e03c3c",
        "distracted_right": "#e03c3c",
        "distracted_down": "#ff9020",
        "distracted_up": "#ff9020",
        "drowsy": "#f0e040",
        "critical": "#ff2020",
        "no_face": "#808080",
        "unknown": "#555555",
    }

    # ── State Timeline ────────────────────────────────────────────────────────
    if "driver_state" in df.columns and "elapsed_s" in df.columns:
        st.subheader("State Timeline")
        fig_tl = px.scatter(
            df,
            x="elapsed_s",
            y="driver_state",
            color="driver_state",
            color_discrete_map=COLOUR_MAP,
            height=280,
            labels={"elapsed_s": "Elapsed (s)", "driver_state": "State"},
        )
        fig_tl.update_traces(marker=dict(size=4, opacity=0.8))
        fig_tl.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111",
            paper_bgcolor="#111",
            font_color="#ccc",
        )
        st.plotly_chart(fig_tl, use_container_width=True)

    # ── Latency over time ─────────────────────────────────────────────────────
    if "latency_ms" in df.columns and "elapsed_s" in df.columns:
        st.subheader("Inference Latency")
        fig_lat = go.Figure()
        fig_lat.add_trace(
            go.Scatter(
                x=df["elapsed_s"],
                y=df["latency_ms"],
                mode="lines",
                name="Latency (ms)",
                line=dict(color="#00F3FF", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(0,243,255,0.06)",
            )
        )
        fig_lat.add_hline(
            y=25,
            line_dash="dash",
            line_color="#D4F000",
            annotation_text="25 ms target",
            annotation_position="top left",
        )
        fig_lat.update_layout(
            height=240,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111",
            paper_bgcolor="#111",
            font_color="#ccc",
            yaxis_title="ms",
            xaxis_title="Elapsed (s)",
        )
        st.plotly_chart(fig_lat, use_container_width=True)

    # ── Confidence over time ──────────────────────────────────────────────────
    if all(c in df.columns for c in ["drowsiness_confidence", "distraction_confidence", "elapsed_s"]):
        st.subheader("Model Confidence")
        fig_conf = go.Figure()
        fig_conf.add_trace(
            go.Scatter(
                x=df["elapsed_s"],
                y=df["drowsiness_confidence"] * 100,
                mode="lines",
                name="Drowsiness",
                line=dict(color="#f0e040", width=1.5),
            )
        )
        fig_conf.add_trace(
            go.Scatter(
                x=df["elapsed_s"],
                y=df["distraction_confidence"] * 100,
                mode="lines",
                name="Distraction",
                line=dict(color="#e03c3c", width=1.5),
            )
        )
        fig_conf.update_layout(
            height=240,
            margin=dict(l=0, r=0, t=8, b=0),
            plot_bgcolor="#111",
            paper_bgcolor="#111",
            font_color="#ccc",
            yaxis_title="Confidence (%)",
            xaxis_title="Elapsed (s)",
        )
        st.plotly_chart(fig_conf, use_container_width=True)

    # ── Head pose angles ──────────────────────────────────────────────────────
    if all(c in df.columns for c in ["yaw", "pitch", "roll"]):
        pose_df = df.dropna(subset=["yaw", "pitch", "roll"])
        if not pose_df.empty:
            st.subheader("Head Pose Angles")
            fig_ang = go.Figure()
            for col_name, color in [
                ("yaw", "#4fc3f7"),
                ("pitch", "#81c784"),
                ("roll", "#ffb74d"),
            ]:
                fig_ang.add_trace(
                    go.Scatter(
                        x=pose_df["elapsed_s"],
                        y=pose_df[col_name],
                        mode="lines",
                        name=col_name.capitalize(),
                        line=dict(color=color, width=1.5),
                    )
                )
            fig_ang.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=8, b=0),
                plot_bgcolor="#111",
                paper_bgcolor="#111",
                font_color="#ccc",
                yaxis_title="Degrees",
                xaxis_title="Elapsed (s)",
            )
            st.plotly_chart(fig_ang, use_container_width=True)

    # ── State distribution pie ────────────────────────────────────────────────
    if "driver_state" in df.columns:
        st.subheader("State Distribution")
        label_counts = df["driver_state"].value_counts().reset_index()
        label_counts.columns = ["driver_state", "count"]
        fig_pie = px.pie(
            label_counts,
            names="driver_state",
            values="count",
            color="driver_state",
            color_discrete_map=COLOUR_MAP,
            height=320,
        )
        fig_pie.update_layout(margin=dict(l=0, r=0, t=8, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Raw data expander ─────────────────────────────────────────────────────
    with st.expander("Raw Session Data"):
        st.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button(
            "⬇ Download CSV",
            data=csv_bytes,
            file_name=selected.name,
            mime="text/csv",
        )
