"""
MoveInSync Review Intelligence AI - Interactive Streamlit Application.
Multi-page corporate intelligence portal for engineering and product decision-makers.
Upgraded with full 11-page navigation architecture, global dataset switcher, and enterprise aesthetics.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Configure page layout first
st.set_page_config(
    page_title="MoveInSync Review Intelligence AI",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import pipeline modules
from config import (
    CATEGORIES,
    DEFAULT_APP_ID,
    HAS_OPENAI_KEY,
    PRIORITY_WEIGHTS,
    DATA_DIR
)
from src.data_loader import DataLoader
from src.preprocessing import ReviewPreprocessor
from src.review_classifier import ReviewClassifier
from src.sentiment_analyzer import SentimentAnalyzer
from src.priority_engine import PriorityEngine
from src.trend_analyzer import TrendAnalyzer
from src.report_generator import ReportGenerator
from src.review_collector import ReviewCollector


# 1. Initialize Global Session State
loader = DataLoader()

if "available_datasets" not in st.session_state:
    st.session_state["available_datasets"] = {
        "Illustrative Sample (50 Demo Reviews)": "sample",
        "Live Scraped Play Store (200 Authentic Reviews)": "live",
        "Custom Upload / Buffer": "custom"
    }

if "active_dataset_choice" not in st.session_state:
    # Prefer live scraped dataset if it exists, else sample
    live_path = DATA_DIR / "live_scraped_reviews.csv"
    if live_path.exists():
        st.session_state["active_dataset_choice"] = "Live Scraped Play Store (200 Authentic Reviews)"
    else:
        st.session_state["active_dataset_choice"] = "Illustrative Sample (50 Demo Reviews)"

if "active_dataset_name" not in st.session_state:
    st.session_state["active_dataset_name"] = st.session_state["active_dataset_choice"]

if "is_demo_mode" not in st.session_state:
    st.session_state["is_demo_mode"] = "Sample" in st.session_state["active_dataset_choice"]

if "raw_df" not in st.session_state:
    st.session_state["raw_df"] = pd.DataFrame()

if "processed_df" not in st.session_state:
    st.session_state["processed_df"] = pd.DataFrame()

if "quality_metrics" not in st.session_state:
    st.session_state["quality_metrics"] = {}

if "use_ai_classification" not in st.session_state:
    st.session_state["use_ai_classification"] = False

if "category_overrides" not in st.session_state:
    st.session_state["category_overrides"] = {}

if "recommendation_statuses" not in st.session_state:
    # Local tracking of recommendation workflow: 'proposed', 'investigating', 'implemented', 'validated'
    st.session_state["recommendation_statuses"] = {}

if "resolution_notes" not in st.session_state:
    st.session_state["resolution_notes"] = {}


# 2. Pipeline Execution Function
from src.pipeline_runner import execute_pipeline

def run_pipeline():
    raw = st.session_state["raw_df"]
    processed, q_metrics = execute_pipeline(
        raw_df=raw,
        use_ai=st.session_state["use_ai_classification"],
        category_overrides=st.session_state["category_overrides"]
    )
    st.session_state["processed_df"] = processed
    st.session_state["quality_metrics"] = q_metrics


# 3. Dataset Loader Helper
def switch_active_dataset(choice: str):
    st.session_state["active_dataset_choice"] = choice
    st.session_state["active_dataset_name"] = choice
    st.session_state["category_overrides"] = {}

    if "Sample" in choice:
        df = loader.load_sample_data()
        st.session_state["is_demo_mode"] = True
    elif "Live" in choice:
        live_path = DATA_DIR / "live_scraped_reviews.csv"
        if live_path.exists():
            df = pd.read_csv(live_path)
            df["data_type"] = "collected"
        else:
            # Fallback to scraping or sample
            df = loader.load_sample_data()
        st.session_state["is_demo_mode"] = False
    else:
        # Custom buffer remains
        df = st.session_state.get("raw_df", loader.load_sample_data())
        st.session_state["is_demo_mode"] = False

    st.session_state["raw_df"] = df
    run_pipeline()


# Initial load if uninitialized
if st.session_state["raw_df"].empty:
    switch_active_dataset(st.session_state["active_dataset_choice"])


# Inject Compact Enterprise Sidebar CSS so all navigation and controls fit without scrolling
st.markdown(
    """
    <style>
    /* Compact the sidebar padding and layout */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    
    /* Navigation list item compacting */
    ul[data-testid="stSidebarNavItems"] {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }
    ul[data-testid="stSidebarNavItems"] li {
        margin-bottom: 0px !important;
        padding-top: 1px !important;
        padding-bottom: 1px !important;
    }
    ul[data-testid="stSidebarNavItems"] a {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
        font-size: 0.85rem !important;
    }
    
    /* Compact dividers and margins in sidebar */
    section[data-testid="stSidebar"] hr {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
    }
    
    /* Compact metric cards in sidebar */
    section[data-testid="stSidebar"] [data-testid="stMetric"] {
        padding: 2px 0px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }
    
    /* Compact alert / badges */
    section[data-testid="stSidebar"] [data-testid="stAlert"] {
        padding: 4px 8px !important;
        margin-bottom: 4px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 4. Global Sidebar Controls & Navigation Telemetry
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="font-size: 20px;">🚐</span>
            <span style="font-size: 16px; font-weight: 700; color: #f1f5f9;">MoveInSync Intelligence</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Global Dataset Selector
    dataset_keys = list(st.session_state["available_datasets"].keys())
    selected_ds = st.selectbox(
        "Active Dataset:",
        options=dataset_keys,
        index=dataset_keys.index(st.session_state["active_dataset_choice"]) if st.session_state["active_dataset_choice"] in dataset_keys else 0,
        label_visibility="visible"
    )
    if selected_ds != st.session_state["active_dataset_choice"]:
        switch_active_dataset(selected_ds)
        st.rerun()

    # Provenance Badge & Quick Compact Stats
    df_curr = st.session_state.get("processed_df", pd.DataFrame())
    if not df_curr.empty:
        if st.session_state["is_demo_mode"]:
            st.caption("⚠️ **DEMO BENCHMARK** (50 synthetic records)")
        else:
            st.caption("🟢 **AUTHENTIC PLAY STORE** (Verified feedback)")

        m_c1, m_c2 = st.columns(2)
        with m_c1:
            st.metric("Total Reviews", f"{len(df_curr):,}")
        with m_c2:
            avg_s = round(df_curr["score"].mean(), 2) if "score" in df_curr.columns else 0.0
            st.metric("Sample Avg", f"{avg_s} ★")

    # Optional AI Toggle (Compact)
    if HAS_OPENAI_KEY:
        ai_toggle = st.toggle("OpenAI gpt-4o-mini", value=st.session_state["use_ai_classification"])
        if ai_toggle != st.session_state["use_ai_classification"]:
            st.session_state["use_ai_classification"] = ai_toggle
            run_pipeline()
            st.rerun()

    st.caption("FDE Case Study System v2.0 • Windows")


# 5. Define All 11 Required Multi-Page Views
pages = [
    st.Page("pages/1_Executive_Overview.py", title="Executive Overview", icon="📊", default=True),
    st.Page("pages/2_Review_Explorer.py", title="Review Explorer", icon="🔍"),
    st.Page("pages/3_Sentiment_Intelligence.py", title="Sentiment Intelligence", icon="💬"),
    st.Page("pages/4_Issue_Analysis.py", title="Issue Analysis", icon="📈"),
    st.Page("pages/5_Priority_Action_Center.py", title="Priority & Action Center", icon="🎯"),
    st.Page("pages/6_Product_Experience_Analytics.py", title="Product Experience Analytics", icon="🛣️"),
    st.Page("pages/7_Trend_Monitoring.py", title="Trend Monitoring", icon="📡"),
    st.Page("pages/8_AI_Insights.py", title="AI Insights", icon="🤖"),
    st.Page("pages/9_Data_Collection_Quality.py", title="Data Collection & Quality", icon="💾"),
    st.Page("pages/10_Reports_Exports.py", title="Reports & Exports", icon="📄"),
    st.Page("pages/11_Methodology_Settings.py", title="Methodology & Settings", icon="📖"),
]

pg = st.navigation(pages)
pg.run()
