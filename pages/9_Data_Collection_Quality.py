"""
Data Collection & Quality Page.
Scrapes live Google Play reviews, handles CSV imports, audits quality metrics,
and maintains clear separation between synthetic and authentic datasets.
"""

import streamlit as st
import pandas as pd
from config import DEFAULT_APP_ID, DEFAULT_COUNTRY, DEFAULT_LANGUAGE, DATA_DIR
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.review_collector import ReviewCollector
from src.data_loader import DataLoader

render_enterprise_header("Data Collection & Quality", "Ingest authentic Play Store reviews, upload CSVs, and audit data hygiene metrics")
render_provenance_callout()

loader = DataLoader()

tab_collect, tab_upload, tab_quality = st.tabs([
    "📥 Google Play Scraper",
    "📂 Manual CSV Import",
    "🛡️ Data Quality & Provenance Audit"
])

# 1. TAB: COLLECT FROM GOOGLE PLAY
with tab_collect:
    st.subheader("Collect Public Reviews from Google Play")
    st.markdown("Direct ingestion from official MoveInSync Play Store listing (`com.moveinsync.ets`).")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        app_id = st.text_input("App Package ID", value=DEFAULT_APP_ID, key="scrape_app_id_input")
    with col_b:
        scrape_count = st.number_input("Review Count to Collect", min_value=10, max_value=500, value=150, step=25, key="scrape_count_input")
    with col_c:
        sort_mode = st.selectbox("Sort Order", ["newest", "most_relevant"], key="scrape_sort_mode_select")

    if st.button("🚀 Scrape Google Play Store Now", type="primary", key="btn_scrape_play_store"):
        with st.spinner("Connecting to Google Play public batch endpoint..."):
            collector = ReviewCollector(app_id=app_id, country=DEFAULT_COUNTRY, language=DEFAULT_LANGUAGE)
            scraped_df, meta = collector.collect_reviews(count=scrape_count, sort_order=sort_mode)

            if not scraped_df.empty:
                # Save as live dataset
                live_file = DATA_DIR / "live_scraped_reviews.csv"
                scraped_df.to_csv(live_file, index=False)
                
                # Persist to SQLite
                loader.save_to_sqlite(scraped_df)

                # Set session state to live dataset
                st.session_state["raw_df"] = scraped_df
                st.session_state["active_dataset_choice"] = "Live Scraped Play Store (200 Authentic Reviews)"
                st.session_state["active_dataset_name"] = "Live Scraped Play Store"
                st.session_state["is_demo_mode"] = False
                st.session_state["category_overrides"] = {}

                # Trigger pipeline directly without circular import
                from src.pipeline_runner import execute_pipeline
                processed_df, q_metrics = execute_pipeline(
                    raw_df=scraped_df,
                    use_ai=st.session_state.get("use_ai_classification", False),
                    category_overrides=st.session_state.get("category_overrides", {})
                )
                st.session_state["processed_df"] = processed_df
                st.session_state["quality_metrics"] = q_metrics

                st.success(f"✅ Successfully collected {len(scraped_df)} authentic reviews from Google Play Store! Buffer updated.")
                st.rerun()
            else:
                err_msg = "\n".join(meta.get("errors", ["Unknown connection failure"]))
                st.error(f"❌ Review collection failed or returned empty.\n\nDetails: {err_msg}")
                st.info("💡 Tip: If Google Play blocks or rate-limits scraping, use the 'Manual CSV Import' tab or switch back to the demo benchmark.")

# 2. TAB: MANUAL CSV IMPORT
with tab_upload:
    st.subheader("Manual CSV Review Ingestion")
    st.markdown("Upload any CSV with columns: `id`, `user_name`, `score`, `text`, `date`, `version`.")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="csv_file_uploader")

    if uploaded_file is not None:
        try:
            imported_df = loader.load_csv(uploaded_file)
            st.write(f"Preview ({len(imported_df)} rows detected):")
            st.dataframe(imported_df.head(3), use_container_width=True)

            if st.button("Apply Uploaded Dataset", type="primary", key="btn_apply_uploaded_csv"):
                st.session_state["raw_df"] = imported_df
                st.session_state["active_dataset_choice"] = "Custom Upload / Buffer"
                st.session_state["active_dataset_name"] = uploaded_file.name
                st.session_state["is_demo_mode"] = False
                st.session_state["category_overrides"] = {}
                
                from src.pipeline_runner import execute_pipeline
                processed_df, q_metrics = execute_pipeline(
                    raw_df=imported_df,
                    use_ai=st.session_state.get("use_ai_classification", False),
                    category_overrides=st.session_state.get("category_overrides", {})
                )
                st.session_state["processed_df"] = processed_df
                st.session_state["quality_metrics"] = q_metrics

                st.success("✅ Custom CSV dataset loaded into pipeline buffer.")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to parse uploaded CSV: {str(e)}")

# 3. TAB: QUALITY AUDIT
with tab_quality:
    st.subheader("Data Hygiene & Cleansing Audit")
    q_metrics = st.session_state.get("quality_metrics", {})
    df_curr = st.session_state.get("processed_df", pd.DataFrame())

    if not q_metrics or df_curr.empty:
        st.info("No active pipeline execution metrics.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Raw Ingested Records", q_metrics.get("initial_count", 0))
        with m2:
            st.metric("Cleaned Records Output", q_metrics.get("final_count", 0))
        with m3:
            st.metric("Duplicates Removed", q_metrics.get("duplicates_removed", 0))
        with m4:
            st.metric("Invalid Ratings Dropped", q_metrics.get("invalid_ratings_dropped", 0))

        st.markdown("---")
        st.markdown(f"**Data Provenance Status:** `{q_metrics.get('data_provenance', 'unknown')}`")
        st.markdown(f"**Missing Text Records Handled:** `{q_metrics.get('missing_text_count', 0)}`")
        st.markdown(f"**Missing Date Records Handled:** `{q_metrics.get('missing_date_count', 0)}`")
