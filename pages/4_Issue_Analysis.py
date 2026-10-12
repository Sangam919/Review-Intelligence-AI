"""
Issue Analysis Deep-Dive Page.
Analyzes complaint frequency, rating distribution by category, multi-label overlap,
and representative verbatim excerpts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import CATEGORIES
from src.ui_components import render_enterprise_header, render_provenance_callout

render_enterprise_header("Issue Analysis", "Deep-dive operational taxonomy breakdown, rating distribution, and multi-label overlap")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

# 1. Multi-Label Taxonomy Summary Table
cat_stats = []
total_rev = len(df)
total_neg = len(df[df["score"] <= 2])

for k, meta in CATEGORIES.items():
    sub = df[df["primary_category"] == k]
    cnt = len(sub)
    if cnt == 0:
        continue
    neg_cnt = int((sub["score"] <= 2).sum())
    avg_s = round(float(sub["score"].mean()), 2)
    cat_stats.append({
        "category_key": k,
        "category_label": meta["label"],
        "total_reviews": cnt,
        "share_of_dataset": round((cnt / total_rev) * 100, 1),
        "negative_reviews": neg_cnt,
        "negative_pct": round((neg_cnt / cnt) * 100, 1),
        "avg_rating": avg_s,
    })

cat_df = pd.DataFrame(cat_stats).sort_values("negative_reviews", ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Complaint Volume by Category")
    fig_bar = px.bar(
        cat_df,
        x="negative_reviews",
        y="category_label",
        orientation="h",
        color="negative_reviews",
        color_continuous_scale="Reds",
        labels={"negative_reviews": "1★ & 2★ Complaints", "category_label": ""},
        text="negative_reviews"
    )
    fig_bar.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=380,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("Rating Spread by Category (Box Plot)")
    fig_box = px.box(
        df,
        x="primary_category",
        y="score",
        color="primary_category",
        labels={"primary_category": "Category", "score": "Star Rating (1-5)"},
    )
    fig_box.update_layout(
        xaxis=dict(tickangle=-45, title=None),
        yaxis=dict(range=[0.5, 5.5], dtick=1),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=380,
    )
    st.plotly_chart(fig_box, use_container_width=True)

st.divider()

# 2. Multi-Label Overlap & Investigation Questions
st.subheader("🧩 Multi-Label Classification & Correlation")
st.markdown("""
A single commuter review frequently addresses multiple operational defects simultaneously (e.g., *delayed OTP combined with missed pickup*).
Our classifier assigns multi-label tags to preserve cross-cutting systemic failures.
""")

# Correlation between top categories
top_cats = cat_df["category_key"].head(6).tolist()
st.dataframe(
    cat_df[["category_label", "total_reviews", "share_of_dataset", "negative_reviews", "negative_pct", "avg_rating"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "category_label": st.column_config.TextColumn("Operational Domain", width="medium"),
        "total_reviews": st.column_config.NumberColumn("Mentions", format="%d"),
        "share_of_dataset": st.column_config.NumberColumn("Dataset Share", format="%.1f%%"),
        "negative_reviews": st.column_config.NumberColumn("Negative Complaints", format="%d"),
        "negative_pct": st.column_config.NumberColumn("Negative Share", format="%.1f%%"),
        "avg_rating": st.column_config.NumberColumn("Avg Rating", format="%.2f ★"),
    }
)

st.divider()

# 3. Verbatim Evidence Browser by Category
st.subheader("💬 Representative Customer Excerpts")
selected_cat = st.selectbox(
    "Choose Category to Inspect Verbatim Evidence:",
    options=list(CATEGORIES.keys()),
    format_func=lambda k: CATEGORIES[k]["label"]
)

sub_reviews = df[df["primary_category"] == selected_cat]

if sub_reviews.empty:
    st.info(f"No reviews categorized under '{CATEGORIES[selected_cat]['label']}'.")
else:
    c_neg, c_pos = st.columns(2)

    with c_neg:
        st.markdown("**🚨 Negative Feedback (1★ - 2★)**")
        neg_subset = sub_reviews[sub_reviews["score"] <= 2].sort_values("score", ascending=True)
        if neg_subset.empty:
            st.caption("No negative reviews recorded in this category.")
        else:
            for _, r in neg_subset.head(5).iterrows():
                with st.expander(f"{r['score']}★ | {r.get('user_name', 'User')} ({r.get('date', 'N/A')})"):
                    st.write(r.get("display_text", r.get("text", "")))
                    st.caption(f"Version: {r.get('version', 'N/A')} | Severity: {r.get('severity', 'medium')}")

    with c_pos:
        st.markdown("**⭐ Positive & Neutral Feedback (3★ - 5★)**")
        pos_subset = sub_reviews[sub_reviews["score"] >= 3].sort_values("score", ascending=False)
        if pos_subset.empty:
            st.caption("No positive reviews recorded in this category.")
        else:
            for _, r in pos_subset.head(5).iterrows():
                with st.expander(f"{r['score']}★ | {r.get('user_name', 'User')} ({r.get('date', 'N/A')})"):
                    st.write(r.get("display_text", r.get("text", "")))
                    st.caption(f"Version: {r.get('version', 'N/A')} | Sentiment: {r.get('sentiment_label', 'positive')}")
