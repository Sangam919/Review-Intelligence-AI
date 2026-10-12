"""
Priority and Action Center Page.
Ranked P0-P3 matrix, detailed factor inspection, local workflow status updates,
resolution note logging, and action plan exports.
"""

import streamlit as st
import pandas as pd
from config import CATEGORIES, PRIORITY_WEIGHTS
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.priority_engine import PriorityEngine
from src.trend_analyzer import TrendAnalyzer
from src.data_loader import DataLoader

render_enterprise_header("Priority & Action Center", "Evidence-based prioritization matrix, implementation roadmaps, and local workflow tracking")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

# 1. Calculate Priority Metrics
trend_analyzer = TrendAnalyzer()
emerging_issues = trend_analyzer.detect_emerging_issues(df)
surge_dict = {item["category"]: item["surge_multiplier"] for item in emerging_issues}

engine = PriorityEngine()
priority_df = engine.calculate_category_metrics(df, trend_surge_dict=surge_dict)

if priority_df.empty:
    st.info("No actionable issues identified.")
    st.stop()

# 2. Priority Summary KPI Cards
p_counts = priority_df["priority_label"].value_counts().to_dict()
c0, c1, c2, c3 = st.columns(4)
with c0:
    st.metric("P0 (Critical / Safety)", p_counts.get("P0", 0), help="Critical safety hazards or service-breaking lockouts.")
with c1:
    st.metric("P1 (High-Impact Recurring)", p_counts.get("P1", 0), help="Frequent operational friction with high user churn risk.")
with c2:
    st.metric("P2 (Experience & Usability)", p_counts.get("P2", 0), help="Important quality-of-life enhancements.")
with c3:
    st.metric("P3 (Low / Need Telemetry)", p_counts.get("P3", 0), help="Minor or low-evidence defects.")

st.divider()

# 3. Filtering & Action Plan Export Bar
f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
with f_col1:
    tier_filter = st.multiselect("Filter Priority Tier", ["P0", "P1", "P2", "P3"], default=["P0", "P1", "P2", "P3"])
with f_col2:
    owners = sorted(priority_df["suggested_owner"].unique().tolist())
    owner_filter = st.multiselect("Filter Suggested Owner", owners, default=owners)

view_p_df = priority_df[
    priority_df["priority_label"].isin(tier_filter) &
    priority_df["suggested_owner"].isin(owner_filter)
]

# Action plan CSV export
loader = DataLoader()
csv_action_bytes = loader.export_csv_bytes(view_p_df)
st.download_button(
    label="📥 Export Prioritized Action Plan (CSV)",
    data=csv_action_bytes,
    file_name="moveinsync_prioritized_action_plan.csv",
    mime="text/csv",
)

st.divider()

# 4. Ranked Table View
st.subheader("📋 Ranked Engineering Priority Matrix")

table_cols = [
    "priority_label", "category_label", "priority_score",
    "review_count", "negative_pct", "estimated_effort",
    "suggested_owner", "success_metric"
]

st.dataframe(
    view_p_df[table_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "priority_label": st.column_config.TextColumn("Tier", width="small"),
        "category_label": st.column_config.TextColumn("Defect Category", width="medium"),
        "priority_score": st.column_config.NumberColumn("Priority Score", format="%.3f"),
        "review_count": st.column_config.NumberColumn("Mentions", format="%d"),
        "negative_pct": st.column_config.NumberColumn("Neg %", format="%.1f%%"),
        "estimated_effort": st.column_config.TextColumn("Est. Effort", width="small"),
        "suggested_owner": st.column_config.TextColumn("Owner", width="medium"),
        "success_metric": st.column_config.TextColumn("Target Success Metric", width="large"),
    }
)

st.divider()

# 5. Expandable Recommendation Cards & Local Workflow Status Tracking
st.subheader("🛠️ Deep-Dive Fix Proposals & Local Status Tracking")
st.caption("Inspect problem statements, assign local workflow states (proposed / investigating / implemented), and log resolution notes.")

status_options = ["proposed", "under investigation", "implemented", "validated"]

for _, row in view_p_df.iterrows():
    cat_k = row["category"]
    p_badge = row["priority_label"]
    badge_icon = "🔴" if p_badge == "P0" else ("🟠" if p_badge == "P1" else ("🟡" if p_badge == "P2" else "🟢"))
    
    current_status = st.session_state["recommendation_statuses"].get(cat_k, "proposed")
    current_notes = st.session_state["resolution_notes"].get(cat_k, "")

    with st.expander(f"{badge_icon} **{row['priority_label']}**: {row['category_label']} (Score: {row['priority_score']}) — Status: [{current_status.upper()}]"):
        col_main, col_workflow = st.columns([3, 2])

        with col_main:
            st.markdown(f"**Observed Problem Statement:**\n{row['problem_statement']}")
            st.markdown(f"**Proposed Engineering Intervention:**\n{row['proposed_fix']}")
            st.markdown(f"**Business Impact Rationale:**\n{row['why_it_matters']}")

        with col_workflow:
            st.markdown(f"**Suggested Owner:** `{row['suggested_owner']}`")
            st.markdown(f"**Estimated Effort:** `{row['estimated_effort']}`")
            st.markdown(f"**Target Metric:** `{row['success_metric']}`")
            
            st.markdown("**Workflow Status (Local Case-Study Tracking):**")
            new_status = st.selectbox(
                "Update Status:",
                options=status_options,
                index=status_options.index(current_status),
                key=f"status_{cat_k}"
            )
            note_text = st.text_input("Resolution Note:", value=current_notes, key=f"note_{cat_k}")

            if st.button("Save Local Update", key=f"btn_save_{cat_k}"):
                st.session_state["recommendation_statuses"][cat_k] = new_status
                st.session_state["resolution_notes"][cat_k] = note_text
                st.success(f"Updated status for '{row['category_label']}' to '{new_status}'.")
                st.rerun()

        st.markdown("**Scoring Breakdown (Formula Inspection):**")
        st.caption(
            f"Frequency: {row['frequency_score']} | Severity: {row['severity_score']} | "
            f"Trend: {row['trend_score']} | Confidence: {row['confidence_score']} | Effort Inverse: {row['effort_score']}"
        )

        st.markdown("**Representative Review Excerpts:**")
        for exc in row.get("representative_excerpts", []):
            st.markdown(f"- *{exc}*")
