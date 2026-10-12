"""
Trend Monitoring and Anomaly Detection Page.
Longitudinal aggregation, 30-day comparative period KPIs, category surge alerts,
and data sufficiency safeguards.
"""

import streamlit as st
import pandas as pd
from config import CATEGORIES
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.trend_analyzer import TrendAnalyzer
from src.data_loader import DataLoader

render_enterprise_header("Trend Monitoring", "Longitudinal sentiment velocity, period-over-period delta tracking, and surge alerts")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

analyzer = TrendAnalyzer()

# 1. Emerging Issue Alerts
st.subheader("🚨 Emerging Issues & Surge Detection")
st.caption("Identifies complaint categories experiencing acceleration in recent review batches relative to baseline.")

emerging = analyzer.detect_emerging_issues(df)

if not emerging:
    st.success("🟢 No sudden complaint surges detected across the current dataset window.")
else:
    for em in emerging:
        cat_meta = CATEGORIES.get(em["category"], {})
        label = cat_meta.get("label", em["category"])
        mult = em["surge_multiplier"]
        
        box_type = st.error if em["is_critical_spike"] else st.warning
        box_type(
            f"**SURGE ALERT: {label}** — {mult}x velocity increase\n\n"
            f"- **Recent Share:** {em['recent_share_pct']}% ({em['recent_count']} reviews in last 45 days)\n"
            f"- **Historical Share:** {em['baseline_share_pct']}% ({em['baseline_count']} reviews prior)\n"
            f"- **Owner:** `{cat_meta.get('suggested_owner', 'Product / Eng')}`"
        )

st.divider()

# 2. Period-over-Period Performance KPIs
st.subheader("📊 30-Day Window Comparative KPIs")

kpis = analyzer.compute_period_over_period_kpis(df, days_window=30)

if not kpis.get("sufficient_data", False):
    st.info(f"ℹ️ {kpis.get('note', 'Insufficient longitudinal spread to compute period comparisons.')}")
else:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Current Window Reviews", kpis["current_review_count"], f"{kpis['current_review_count'] - kpis['prev_review_count']} vs prior")
    with c2:
        st.metric("Current Window Avg Rating", f"{kpis['current_avg_rating']} ★", f"{kpis['rating_delta']} ★", delta_color="normal")
    with c3:
        st.metric("1★ & 2★ Complaint Share", f"{kpis['current_negative_pct']}%", f"{kpis['negative_pct_delta']}%", delta_color="inverse")
    with c4:
        st.metric("Prior Window Avg Rating", f"{kpis['prev_avg_rating']} ★")

st.divider()

# 3. Weekly Volume & Rating Aggregation Table
st.subheader("📅 Weekly Aggregation Log")
weekly_df = analyzer.compute_volume_and_rating_trend(df, freq="W")

if weekly_df.empty:
    st.info("No periodic data available.")
else:
    st.dataframe(
        weekly_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "period": st.column_config.TextColumn("Week Ending", width="medium"),
            "review_count": st.column_config.NumberColumn("Total Reviews", format="%d"),
            "avg_rating": st.column_config.NumberColumn("Average Rating", format="%.2f ★"),
            "negative_count": st.column_config.NumberColumn("1★ & 2★ Complaints", format="%d"),
            "negative_pct": st.column_config.NumberColumn("Negative Share", format="%.1f%%"),
        }
    )

    loader = DataLoader()
    st.download_button(
        label="📥 Export Weekly Trend Log (CSV)",
        data=loader.export_csv_bytes(weekly_df),
        file_name="weekly_trend_log.csv",
        mime="text/csv",
    )
