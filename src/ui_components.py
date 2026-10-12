"""
Reusable Enterprise Header and Navigation Components for Streamlit.
Provides consistent branding, dataset selector, provenance badges, and quick-status KPIs.
"""

import streamlit as st
import pandas as pd


def render_enterprise_header(page_title: str, page_subtitle: str):
    """
    Renders a unified, professional SaaS header across all dashboard views.
    Includes active dataset name, data provenance indicator, and data freshness.
    """
    # Top banner / application bar
    header_col1, header_col2 = st.columns([3, 1])

    with header_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 2px;">
                <span style="font-size: 26px;">🚐</span>
                <div>
                    <h2 style="margin: 0; padding: 0; font-size: 24px; font-weight: 700; color: #1e293b;">
                        MoveInSync Review Intelligence AI
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: #64748b;">
                        Customer Experience & Product Reliability Analytics — Forward Deployed Engineering
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with header_col2:
        df = st.session_state.get("processed_df", pd.DataFrame())
        active_name = st.session_state.get("active_dataset_name", "Illustrative Sample")
        is_demo = st.session_state.get("is_demo_mode", True)

        if not df.empty:
            badge_color = "#fef3c7" if is_demo else "#dcfce7"
            badge_border = "#f59e0b" if is_demo else "#22c55e"
            text_color = "#92400e" if is_demo else "#166534"
            badge_text = "⚠️ DEMO DATASET" if is_demo else "🟢 AUTHENTIC PLAY STORE"

            st.markdown(
                f"""
                <div style="text-align: right; background: {badge_color}; border: 1px solid {badge_border};
                            padding: 6px 12px; border-radius: 6px; display: inline-block; float: right;">
                    <div style="font-size: 11px; font-weight: 700; color: {text_color}; letter-spacing: 0.5px;">
                        {badge_text}
                    </div>
                    <div style="font-size: 10px; color: #475569;">
                        Dataset: {active_name} ({len(df)} records)
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        f"""
        <div style="border-bottom: 1px solid #e2e8f0; margin-top: 10px; margin-bottom: 18px; padding-bottom: 6px;">
            <span style="font-size: 18px; font-weight: 600; color: #0f172a;">{page_title}</span>
            <span style="font-size: 13px; color: #64748b; margin-left: 10px;">— {page_subtitle}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_provenance_callout():
    """
    Renders an explicit notice banner if demo dataset is active,
    preventing any confusion with genuine Play Store telemetry.
    """
    is_demo = st.session_state.get("is_demo_mode", True)
    if is_demo:
        st.warning(
            "**DEMO DATASET ACTIVE — NOT VERIFIED REAL USER FEEDBACK**\n\n"
            "This view is currently powered by a synthetic demonstration benchmark (50 reviews) designed to test pipeline "
            "classification and scoring mechanics. To analyze authentic MoveInSync user reviews, switch to the "
            "**'Live Scraped Play Store'** dataset in the sidebar selector or use **Data Collection & Quality**.",
            icon="⚠️"
        )
