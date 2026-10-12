"""
Executive Overview Dashboard Page.
High-level KPIs, official Play Store comparison, rating distribution, timeline charts,
top complaint categories, auto-generated executive findings, and direct drill-downs.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import CATEGORIES
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.priority_engine import PriorityEngine

render_enterprise_header("Executive Overview", "High-level CX performance, rating distribution, and critical operational bottlenecks")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No review data is currently loaded in the pipeline buffer.")
    st.stop()

# Interactive Filter Controls
with st.expander("🔍 Filter View by Date Range & Rating", expanded=False):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        date_col = "parsed_date" if "parsed_date" in df.columns else "date"
        try:
            min_d = pd.to_datetime(df[date_col]).min().date()
            max_d = pd.to_datetime(df[date_col]).max().date()
            date_filter = st.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        except Exception:
            date_filter = None
    with f_col2:
        selected_scores = st.multiselect("Filter Star Ratings", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
    with f_col3:
        all_cats = list(CATEGORIES.keys())
        selected_cats = st.multiselect(
            "Filter Complaint Categories",
            options=all_cats,
            default=all_cats,
            format_func=lambda k: CATEGORIES[k]["label"]
        )

# Apply filters
df_view = df.copy()
if selected_scores:
    df_view = df_view[df_view["score"].isin(selected_scores)]
if selected_cats:
    df_view = df_view[df_view["primary_category"].isin(selected_cats)]

# Core Calculated KPIs
total_count = len(df_view)
dataset_avg = round(float(df_view["score"].mean()), 2) if total_count > 0 else 0.0
one_star_count = int((df_view["score"] == 1).sum())
one_star_pct = round((one_star_count / total_count) * 100, 1) if total_count > 0 else 0.0
neg_count = int((df_view["score"] <= 2).sum())
neg_pct = round((neg_count / total_count) * 100, 1) if total_count > 0 else 0.0
distinct_cats = df_view["primary_category"].nunique()

# 1. Executive Metric Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Reviews Analyzed", f"{total_count:,}", help="Count of cleaned and validated reviews in active view.")
with kpi2:
    st.metric(
        "Sample Average Rating",
        f"{dataset_avg} ★",
        help="Arithmetic mean of current review sample. Note: Official Play Store aggregate rating is 4.32★."
    )
with kpi3:
    st.metric(
        "1-Star Share",
        f"{one_star_pct}%",
        f"{one_star_count} reviews",
        delta_color="inverse"
    )
with kpi4:
    st.metric(
        "1★ & 2★ Complaint Share",
        f"{neg_pct}%",
        f"{neg_count} negative reviews",
        delta_color="inverse"
    )
with kpi5:
    st.metric(
        "Active Defect Categories",
        f"{distinct_cats} of 10",
        help="Number of distinct operational failure domains triggered in current view."
    )

st.caption(
    "💡 **Transparency Note:** Official MoveInSync Google Play Lifetime Rating is **4.32★** (114,879 ratings). "
    "The dataset average above reflects the collected sample of recent reviews, which naturally skews lower due to complaint reporting behavior."
)

st.divider()

# 2. Charts: Star Rating Spread & Review Volume Timeline
col_chart_left, col_chart_right = st.columns(2)

with col_chart_left:
    st.subheader("Star Rating Distribution")
    score_counts = df_view["score"].value_counts().sort_index().reset_index()
    score_counts.columns = ["Star Rating", "Count"]
    score_counts["Rating Label"] = score_counts["Star Rating"].apply(lambda s: f"{s} Star{'s' if s>1 else ''}")
    
    colors = ["#ef4444", "#f97316", "#eab308", "#10b981", "#059669"]
    fig_stars = px.bar(
        score_counts,
        x="Rating Label",
        y="Count",
        color="Rating Label",
        color_discrete_sequence=colors,
        text="Count",
    )
    fig_stars.update_layout(
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Review Count",
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
    )
    st.plotly_chart(fig_stars, use_container_width=True)

with col_chart_right:
    st.subheader("Review Volume & Sentiment Timeline")
    df_chart = df_view.copy()
    date_col = "parsed_date" if "parsed_date" in df_chart.columns else "date"
    df_chart["date_period"] = pd.to_datetime(df_chart[date_col], errors="coerce").dt.to_period("W").dt.start_time
    
    timeline = df_chart.groupby("date_period").agg(
        volume=("id", "count"),
        avg_rating=("score", "mean")
    ).reset_index().dropna()

    if not timeline.empty:
        fig_time = go.Figure()
        fig_time.add_trace(go.Bar(
            x=timeline["date_period"],
            y=timeline["volume"],
            name="Weekly Volume",
            marker_color="#3b82f6",
            opacity=0.75
        ))
        fig_time.add_trace(go.Scatter(
            x=timeline["date_period"],
            y=timeline["avg_rating"],
            name="Avg Rating (★)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#f59e0b", width=3)
        ))
        fig_time.update_layout(
            yaxis=dict(title="Review Count"),
            yaxis2=dict(title="Average Rating", overlaying="y", side="right", range=[1, 5]),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=320,
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Insufficient timestamps to generate timeline chart.")

st.divider()

# 3. Top Complaint Categories & Severity Matrix
c_cat_l, c_cat_r = st.columns(2)

with c_cat_l:
    st.subheader("Top Complaint Categories (1★ & 2★)")
    neg_sub = df_view[df_view["score"] <= 2]
    cat_counts = neg_sub["primary_category"].value_counts().reset_index()
    cat_counts.columns = ["Category Key", "Complaints"]
    cat_counts["Category Name"] = cat_counts["Category Key"].apply(lambda k: CATEGORIES.get(k, {}).get("label", k))

    fig_cat_bar = px.bar(
        cat_counts.head(7),
        x="Complaints",
        y="Category Name",
        orientation="h",
        color="Complaints",
        color_continuous_scale="Reds",
        text="Complaints"
    )
    fig_cat_bar.update_layout(
        yaxis=dict(autorange="reversed", title=None),
        xaxis_title="1★ & 2★ Complaints Count",
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_cat_bar, use_container_width=True)

with c_cat_r:
    st.subheader("Category-Wise Average Star Rating")
    cat_avg = df_view.groupby("primary_category")["score"].mean().reset_index()
    cat_avg.columns = ["Category Key", "Avg Rating"]
    cat_avg["Category Name"] = cat_avg["Category Key"].apply(lambda k: CATEGORIES.get(k, {}).get("label", k))
    cat_avg.sort_values("Avg Rating", ascending=True, inplace=True)
    cat_avg_top = cat_avg.head(7).copy()
    cat_avg_top["Rating Text"] = cat_avg_top["Avg Rating"].round(2).astype(str) + " ★"

    fig_cat_avg = px.bar(
        cat_avg_top,
        x="Avg Rating",
        y="Category Name",
        orientation="h",
        color="Avg Rating",
        color_continuous_scale="RdYlGn",
        text="Rating Text"
    )
    fig_cat_avg.update_layout(
        yaxis=dict(autorange="reversed", title=None),
        xaxis=dict(title="Average Rating (1-5)", range=[1, 5]),
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_cat_avg, use_container_width=True)

st.divider()

# 4. Top 3 Evidence-Backed Issues & Top 3 Recommended Next Actions
st.subheader("📌 Executive Intelligence Briefing")

p_engine = PriorityEngine()
p_df = p_engine.calculate_category_metrics(df_view)

col_findings, col_actions = st.columns(2)

with col_findings:
    st.markdown("#### 🚨 Top 3 Critical Customer Issues")
    if not p_df.empty:
        for idx, row in p_df.head(3).iterrows():
            st.markdown(
                f"**{idx+1}. [{row['priority_label']}] {row['category_label']}** "
                f"*(Score: {row['priority_score']}, {row['review_count']} reviews, {row['negative_pct']}% negative)*\n"
                f"- **Observed Problem:** {row['problem_statement']}\n"
                f"- **Supporting Evidence Excerpt:** *{row.get('representative_excerpts', [''])[0] if row.get('representative_excerpts') else 'N/A'}*"
            )
    else:
        st.info("No prioritized issues detected.")

with col_actions:
    st.markdown("#### 🎯 Top 3 Recommended Engineering Interventions")
    if not p_df.empty:
        for idx, row in p_df.head(3).iterrows():
            st.markdown(
                f"**{idx+1}. Fix for {row['category_label']}** *(Owner: `{row['suggested_owner']}` | Effort: `{row['estimated_effort']}`)*\n"
                f"- **Proposed Solution:** {row['proposed_fix'].splitlines()[0]}\n"
                f"- **Success Metric:** `{row['success_metric']}`"
            )
    else:
        st.info("No recommendations available.")
