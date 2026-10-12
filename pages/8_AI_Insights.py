"""
AI Insights and Investigation Page.
Generates structured executive summaries, answers natural language inquiries over review evidence,
drafts engineering action plans, and operates reliably with or without an active OpenAI API key.
"""

import streamlit as st
import pandas as pd
from config import HAS_OPENAI_KEY
from src.ui_components import render_enterprise_header, render_provenance_callout
from src.ai_assistant import AIAssistant
from src.priority_engine import PriorityEngine
from src.data_loader import DataLoader

render_enterprise_header("AI Insights", "AI-assisted synthesis, custom review inquiries, and structured engineering briefings")
render_provenance_callout()

df = st.session_state.get("processed_df", pd.DataFrame())

if df.empty:
    st.warning("⚠️ No reviews loaded in buffer.")
    st.stop()

assistant = AIAssistant()

# API Key Status Banner
if assistant.is_available():
    st.success("🤖 **OpenAI Assistant Active:** Utilizing `gpt-4o-mini` with structured JSON output and prompt injection defenses.", icon="✅")
else:
    st.info("🔒 **Deterministic Analytical Mode Active:** Running on rule-based synthesis. (To enable OpenAI, add `OPENAI_API_KEY` to your `.env` file).", icon="ℹ️")

st.divider()

# 1. Executive Briefing Synthesis
st.subheader("📋 Automated Executive Briefing")
st.caption("Synthesizes overall customer sentiment, top risks to corporate enterprise contracts, and next action items.")

loader = DataLoader()
profile = loader.get_dataset_profile(df)
p_engine = PriorityEngine()
p_df = p_engine.calculate_category_metrics(df)
top_issues = p_df.to_dict(orient="records")[:3] if not p_df.empty else []

if st.button("⚡ Synthesize Executive Brief", type="primary"):
    with st.spinner("Analyzing review metrics and structuring briefing..."):
        brief = assistant.generate_executive_brief(profile, top_issues)
        st.session_state["cached_executive_brief"] = brief

if "cached_executive_brief" in st.session_state:
    b = st.session_state["cached_executive_brief"]
    st.markdown(f"**Executive Synopsis:**\n{b.get('summary', '')}")
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("**Core Observed Findings:**")
        for f in b.get("core_findings", []):
            st.markdown(f"- {f}")
    with b_col2:
        st.markdown("**Critical Enterprise Risks:**")
        for r in b.get("critical_risks", []):
            st.markdown(f"- ⚠️ {r}")

    st.info(f"**Recommended Action Item:** {b.get('recommended_next_step', '')}")

st.divider()

# 2. Ask Questions Over Review Evidence
st.subheader("💬 Ask Questions Over Review Evidence")
st.markdown("Query the active review buffer regarding specific failure modes, driver complaints, or platform bugs.")

user_q = st.text_input(
    "Enter Question:",
    placeholder="e.g., What are commuters saying about OTP delays? Are drivers refusing air conditioning?"
)

if st.button("🔎 Investigate Question", key="btn_ask_ai"):
    if not user_q.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Scanning review text buffer for citations..."):
            ans = assistant.answer_review_query(user_q, df)
            
            st.markdown(f"**Answer:**\n{ans.get('answer', '')}")
            st.caption(f"Evidence Status: {ans.get('evidence_summary', '')}")

            if ans.get("suggested_engineering_inquiry"):
                st.markdown(f"**Suggested Engineering Inquiry:** `{ans.get('suggested_engineering_inquiry')}`")

            if ans.get("evidence_quotes"):
                st.markdown("**Supporting Review Excerpts:**")
                for q in ans.get("evidence_quotes", []):
                    st.markdown(f"- *{q}*")
