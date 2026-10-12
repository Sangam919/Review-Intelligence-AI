"""
Product Experience Analytics Page.
Maps review defect categories to the 9 stages of an employee corporate commute journey.
Visualizes stage-by-stage friction, representative evidence, and internal telemetry requirements.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.commute_journey import CommuteJourneyAnalyzer

render_enterprise_header("Product Experience Analytics", "Employee Commute Journey touchpoint friction, drop-off analysis, and telemetry requirements")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

analyzer = CommuteJourneyAnalyzer()
journey_stages = analyzer.analyze_journey(df)

# 1. High-Level Commute Journey Overview
st.subheader("🗺️ End-to-End Commute Journey Friction Index")
st.markdown("""
Corporate employee transportation is a mission-critical linear journey. A single failure at **Shift Booking** or **Live Tracking** 
cascades into employee missed shifts and customer dissatisfaction.
""")

journey_df = pd.DataFrame(journey_stages)

# Horizontal Bar Chart: Friction Index across stages
fig_journey = px.bar(
    journey_df,
    x="friction_index",
    y="title",
    orientation="h",
    color="friction_index",
    color_continuous_scale="Reds",
    labels={"friction_index": "Stage Friction Index (0-100)", "title": ""},
    text="friction_index"
)
fig_journey.update_layout(
    yaxis=dict(autorange="reversed"),
    margin=dict(l=20, r=20, t=20, b=20),
    height=360,
    coloraxis_showscale=False
)
st.plotly_chart(fig_journey, use_container_width=True)

st.divider()

# 2. Stage-by-Stage Detailed Breakdown
st.subheader("🚶 Stage-by-Stage Deep Dive")
st.caption("Select an employee commute phase to inspect matching review evidence, potential impact, and internal operational data required.")

selected_stage_title = st.selectbox(
    "Choose Commute Journey Phase:",
    options=[s["title"] for s in journey_stages]
)

selected_stage = next(s for s in journey_stages if s["title"] == selected_stage_title)

col_s_left, col_s_right = st.columns([3, 2])

with col_s_left:
    st.markdown(f"### {selected_stage['icon']} {selected_stage['title']}")
    st.markdown(f"**Commuter Experience Touchpoint:**\n{selected_stage['description']}")
    st.markdown(f"**Suggested Product / System Improvement:**\n{selected_stage['suggested_improvement']}")
    st.markdown(f"**Potential Business Impact:**\n{selected_stage['potential_impact']}")

    st.markdown("**Verbatim Commuter Review Excerpts:**")
    if selected_stage["representative_excerpts"]:
        for exc in selected_stage["representative_excerpts"]:
            st.markdown(f"- *{exc}*")
    else:
        st.info("No negative review excerpts recorded for this specific stage in the current dataset.")

with col_s_right:
    st.metric("Total Mentions in Buffer", f"{selected_stage['review_count']}")
    st.metric("Negative Complaints", f"{selected_stage['negative_count']} ({selected_stage['negative_pct']}%)")
    st.metric("Stage Average Rating", f"{selected_stage['avg_rating']} ★")

    st.markdown("---")
    st.markdown("**🔒 Operational Telemetry Required (Internal MoveInSync Data):**")
    st.caption("Public Play Store reviews cannot definitively establish internal conversion or telematics latency. Corroborate with:")
    for tel in selected_stage["internal_telemetry_required"]:
        st.markdown(f"- `{tel}`")
