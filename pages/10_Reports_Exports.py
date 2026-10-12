"""
Reports & Exports Page.
Provides exportable deliverables: Executive Case Study PDF, Markdown briefs,
CSV datasets, action plans, and weekly monitoring logs.
"""

import streamlit as st
import pandas as pd
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.report_generator import ReportGenerator
from src.priority_engine import PriorityEngine
from src.data_loader import DataLoader
from src.trend_analyzer import TrendAnalyzer

render_enterprise_header("Reports & Exports", "Generate submission-ready FDE case study artifacts, PDF briefs, and tabular exports")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

loader = DataLoader()
p_engine = PriorityEngine()
p_df = p_engine.calculate_category_metrics(df)
trend_analyzer = TrendAnalyzer()
trend_kpis = trend_analyzer.compute_period_over_period_kpis(df)
emerging_issues = trend_analyzer.detect_emerging_issues(df)

st.subheader("📄 Automated Case Study Deliverables")
st.markdown("""
Synthesize all current intelligence findings into an executive-ready Forward Deployed Engineer case study report.
Dynamic findings and recommendations are automatically populated from the currently active review dataset.
""")

if st.button("🔨 Build Full Case Study Report (Markdown & PDF)", type="primary"):
    with st.spinner("Compiling metrics, structuring tables, and generating PDF..."):
        rep_gen = ReportGenerator()
        profile = loader.get_dataset_profile(df)

        md_content = rep_gen.generate_case_study_markdown(
            dataset_profile=profile,
            priority_df=p_df,
            trend_kpis=trend_kpis,
            emerging_issues=emerging_issues
        )
        pdf_bytes = rep_gen.generate_pdf_report(md_content)

        st.session_state["cached_md_report"] = md_content
        st.session_state["cached_pdf_report"] = pdf_bytes
        st.success("✅ Case study documents compiled successfully!")

# Download buttons if cached or build
if "cached_pdf_report" in st.session_state:
    c_pdf, c_md = st.columns(2)
    with c_pdf:
        st.download_button(
            label="📥 Download Case Study Report (PDF)",
            data=st.session_state["cached_pdf_report"],
            file_name="MoveInSync_Review_Intelligence_Case_Study.pdf",
            mime="application/pdf"
        )
    with c_md:
        st.download_button(
            label="📥 Download Case Study Report (Markdown)",
            data=st.session_state["cached_md_report"],
            file_name="case_study_report.md",
            mime="text/markdown"
        )

st.divider()

# Tabular Data Exports
st.subheader("📊 Tabular Data & Metrics Exports (CSV)")

e1, e2, e3 = st.columns(3)

with e1:
    st.markdown("**Cleaned & Classified Reviews**")
    csv_rev = loader.export_csv_bytes(df)
    st.download_button(
        label="📥 Download Reviews (CSV)",
        data=csv_rev,
        file_name="moveinsync_reviews_clean.csv",
        mime="text/csv"
    )

with e2:
    st.markdown("**Prioritized Action Matrix**")
    csv_action = loader.export_csv_bytes(p_df)
    st.download_button(
        label="📥 Download Action Plan (CSV)",
        data=csv_action,
        file_name="moveinsync_action_matrix.csv",
        mime="text/csv"
    )

with e3:
    st.markdown("**Weekly Sentiment Log**")
    weekly_df = trend_analyzer.compute_volume_and_rating_trend(df, freq="W")
    csv_trend = loader.export_csv_bytes(weekly_df)
    st.download_button(
        label="📥 Download Trend Log (CSV)",
        data=csv_trend,
        file_name="moveinsync_weekly_trends.csv",
        mime="text/csv"
    )
