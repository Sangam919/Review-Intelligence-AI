"""
Advanced Review Explorer Page.
Full-text search, multi-faceted filtering, sorting, pagination, CSV exports,
expandable detail inspection, and authorized local category corrections.
"""

import streamlit as st
import pandas as pd
from config import CATEGORIES
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.data_loader import DataLoader

render_enterprise_header("Review Explorer", "Granular full-text inspection, multi-dimensional filtering, and classification audit")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

# 1. Search & Filter Bar
f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([2, 1, 1, 1, 1])

with f_c1:
    search_query = st.text_input("🔎 Search text or reviewer", placeholder="e.g. otp, crash, late, map, driver...")

with f_c2:
    all_stars = [1, 2, 3, 4, 5]
    selected_stars = st.multiselect("Star Rating", all_stars, default=all_stars)

with f_c3:
    all_cats = list(CATEGORIES.keys())
    cat_labels = {k: CATEGORIES[k]["label"] for k in all_cats}
    selected_cats = st.multiselect(
        "Category",
        options=all_cats,
        format_func=lambda k: cat_labels.get(k, k),
        default=all_cats
    )

with f_c4:
    all_sentiments = ["positive", "neutral", "negative"]
    selected_sentiments = st.multiselect("Sentiment", all_sentiments, default=all_sentiments)

with f_c5:
    sort_option = st.selectbox(
        "Sort Order",
        ["Newest First", "Oldest First", "Rating: Low to High", "Rating: High to Low", "Most Thumbs Up"]
    )

# Apply Filters
filtered = df.copy()

if search_query.strip():
    q = search_query.strip().lower()
    filtered = filtered[
        filtered["text"].astype(str).str.lower().str.contains(q, na=False) |
        filtered["user_name"].astype(str).str.lower().str.contains(q, na=False)
    ]

if selected_stars:
    filtered = filtered[filtered["score"].isin(selected_stars)]

if selected_cats:
    filtered = filtered[filtered["primary_category"].isin(selected_cats)]

if selected_sentiments and "sentiment_label" in filtered.columns:
    filtered = filtered[filtered["sentiment_label"].isin(selected_sentiments)]

# Apply Sorting
date_col = "parsed_date" if "parsed_date" in filtered.columns else "date"
if sort_option == "Newest First":
    filtered = filtered.sort_values(date_col, ascending=False)
elif sort_option == "Oldest First":
    filtered = filtered.sort_values(date_col, ascending=True)
elif sort_option == "Rating: Low to High":
    filtered = filtered.sort_values("score", ascending=True)
elif sort_option == "Rating: High to Low":
    filtered = filtered.sort_values("score", ascending=False)
elif sort_option == "Most Thumbs Up":
    filtered = filtered.sort_values("thumbs_up", ascending=False)

# 2. Result Summary & Export Bar
st.markdown(f"**Found {len(filtered):,} reviews matching filter criteria**")

loader = DataLoader()
csv_filtered_bytes = loader.export_csv_bytes(filtered)

st.download_button(
    label="📥 Export Filtered Reviews (CSV)",
    data=csv_filtered_bytes,
    file_name="filtered_moveinsync_reviews.csv",
    mime="text/csv",
)

st.divider()

# 3. Pagination Controls
PAGE_SIZE = 15
total_records = len(filtered)
total_pages = max(1, (total_records + PAGE_SIZE - 1) // PAGE_SIZE)

p_col1, p_col2 = st.columns([1, 4])
with p_col1:
    page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
with p_col2:
    st.caption(f"Showing page {page_number} of {total_pages} ({PAGE_SIZE} reviews per page)")

start_idx = (page_number - 1) * PAGE_SIZE
end_idx = min(start_idx + PAGE_SIZE, total_records)
page_df = filtered.iloc[start_idx:end_idx]

# 4. Display Cards / Table
view_cols = ["id", "score", "primary_category", "sentiment_label", "severity", "user_name", "date", "text"]
available_cols = [c for c in view_cols if c in page_df.columns]

st.dataframe(
    page_df[available_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("ID", width="small"),
        "score": st.column_config.NumberColumn("Stars", format="%d ★", width="small"),
        "primary_category": st.column_config.TextColumn("Category", width="medium"),
        "sentiment_label": st.column_config.TextColumn("Sentiment", width="small"),
        "severity": st.column_config.TextColumn("Severity", width="small"),
        "user_name": st.column_config.TextColumn("User", width="medium"),
        "date": st.column_config.TextColumn("Date", width="medium"),
        "text": st.column_config.TextColumn("Review Text", width="large"),
    }
)

st.divider()

# 5. Inspection & Manual Re-Classification Panel
st.subheader("🛠️ Inspect & Correct Review Classification")
st.caption("Select a review ID from the current page to inspect telemetry details or adjust category tags.")

if not page_df.empty:
    page_ids = page_df["id"].tolist()
    inspect_id = st.selectbox("Select Review ID to inspect:", page_ids)

    sel_row = filtered[filtered["id"] == inspect_id].iloc[0]

    i_col_l, i_col_r = st.columns([3, 2])

    with i_col_l:
        st.markdown(f"**Reviewer:** `{sel_row.get('user_name', 'Anonymous')}` ({sel_row.get('score')} ★)")
        st.markdown(f"**Date:** `{sel_row.get('date', 'N/A')}` | **Version:** `{sel_row.get('version', 'N/A')}`")
        st.info(f"\"{sel_row.get('display_text', sel_row.get('text', ''))}\"")

        if pd.notna(sel_row.get("reply_text")) and sel_row.get("reply_text"):
            st.markdown(f"**Developer Response ({sel_row.get('reply_date', 'N/A')}):**")
            st.caption(f"\"{sel_row.get('reply_text')}\"")

    with i_col_r:
        cur_cat = sel_row.get("primary_category", "other")
        st.markdown(f"**Current Category:** `{cat_labels.get(cur_cat, cur_cat)}`")
        st.markdown(f"**Classification Method:** `{sel_row.get('classification_method', 'rule_based')}`")
        st.markdown(f"**Confidence:** `{sel_row.get('confidence', 0.8)}`")
        st.markdown(f"**Severity:** `{sel_row.get('severity', 'medium')}`")

        # Category reassignment selector
        new_category = st.selectbox(
            "Re-assign Category:",
            options=all_cats,
            index=all_cats.index(cur_cat) if cur_cat in all_cats else 0,
            format_func=lambda k: cat_labels.get(k, k),
            key=f"override_{inspect_id}"
        )

        if st.button("Apply Category Tag Correction", type="primary"):
            st.session_state["category_overrides"][inspect_id] = new_category
            mask = st.session_state["processed_df"]["id"] == inspect_id
            st.session_state["processed_df"].loc[mask, "primary_category"] = new_category
            st.success(f"Updated category for {inspect_id} to '{cat_labels.get(new_category)}'.")
            st.rerun()
