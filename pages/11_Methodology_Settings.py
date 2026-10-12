"""
Methodology & System Settings Page.
Mathematical formula documentation, data provenance, analytical biases, and runtime configuration.
"""

import streamlit as st
from config import PRIORITY_WEIGHTS, CATEGORIES
from src.ui_components import render_enterprise_header, render_provenance_callout

render_enterprise_header("Methodology & Settings", "Mathematical scoring formulas, operational taxonomies, bias disclosures, and runtime settings")
render_provenance_callout()

# Tab 1: Mathematical Formula & Weights
st.subheader("1. Priority Scoring Formula & Weights")
st.markdown("""
To eliminate arbitrary subjective prioritization, every complaint category is evaluated across 5 normalized dimensions ($[0.0, 1.0]$):

$$\\text{Priority Score} = w_F \\cdot F + w_S \\cdot S + w_T \\cdot T + w_C \\cdot C + w_E \\cdot E_{inv}$$

Where:
- **$F$ (Negative Frequency Share)**: $\\min\\left(1.0, 2.0 \\times \\frac{\\text{Negative Reviews in Category}}{\\text{Total Negative Reviews in Buffer}}\\right)$
- **$S$ (Severity Impact)**: Weighted average of reported user impact (Critical = 1.0, High = 0.75, Medium = 0.50, Low = 0.25).
- **$T$ (Trend Velocity)**: Acceleration factor derived from recent 45-day review volume relative to historical baseline.
- **$C$ (Confidence)**: Product of statistical sample size $\\min(1.0, N / 8)$ and average classifier confidence.
- **$E_{inv}$ (Ease of Implementation)**: Low effort = 1.0 (quick wins rewarded), Medium = 0.65, High = 0.30.
""")

cols = st.columns(5)
cols[0].metric("Frequency ($w_F$)", f"{int(PRIORITY_WEIGHTS['frequency']*100)}%")
cols[1].metric("Severity ($w_S$)", f"{int(PRIORITY_WEIGHTS['severity']*100)}%")
cols[2].metric("Trend ($w_T$)", f"{int(PRIORITY_WEIGHTS['trend']*100)}%")
cols[3].metric("Confidence ($w_C$)", f"{int(PRIORITY_WEIGHTS['confidence']*100)}%")
cols[4].metric("Effort Inverse ($w_E$)", f"{int(PRIORITY_WEIGHTS['effort_inverse']*100)}%")

st.divider()

# Tab 2: Priority Tier Definitions
st.subheader("2. Priority Tier Definitions")
st.markdown("""
- **🔴 P0 (Critical Safety / Severe Service Interruption)**:
  - *Criteria*: Safety triggers (SOS unresponsiveness, unverified ride initiation) OR (Score $\\ge 0.75$ and Negative Count $\\ge 3$).
  - *Action*: Emergency hotfix or executive operations intervention.
- **🟠 P1 (High-Impact Core Problem)**:
  - *Criteria*: Score $\\ge 0.55$ and Negative Count $\\ge 2$.
  - *Action*: Prioritize in upcoming engineering sprint.
- **🟡 P2 (Usability & Experience Defect)**:
  - *Criteria*: Score $\\ge 0.35$.
  - *Action*: Product backlog scheduling for next quarterly milestone.
- **🟢 P3 (Low Impact / Telemetry Needed)**:
  - *Criteria*: Score $< 0.35$ or single isolated complaint.
  - *Action*: Monitor telemetry for recurring signals before allocating engineering capacity.
""")

st.divider()

# Tab 3: Analytical Limitations & Known Biases
st.subheader("3. Analytical Limitations & Known Biases")
st.markdown("""
1. **Selection & Vocal Minority Bias**:
   - Commuters experiencing seamless, on-time cab rides rarely leave spontaneous Play Store reviews. Feedback skews heavily toward catastrophic transit failures.
2. **Lagging Indicator Dilemma**:
   - Play Store ratings reflect legacy software builds. When engineering deploys a hotfix, historical 1-star ratings remain permanently on the store unless users manually update them.
3. **Public Reviews vs Internal Telemetry**:
   - Public reviews do not contain device UDIDs or ride IDs. Root causes identified from review text are *strongly evidenced hypotheses* that must be verified against internal telemetry (Firebase Crashlytics, Kafka event streams, driver app logs).
""")

st.divider()

# Tab 4: Runtime System Configuration
st.subheader("4. Runtime System Settings")
st.caption("Inspect active environment parameters and configuration state.")

st.code(
    f"""
    Target App Package ID: com.moveinsync.ets
    Default Country / Language: in / en
    AI Model: gpt-4o-mini
    Active Operating System: Windows (PowerShell compatible)
    Local Relational Store: SQLite (reviews.sqlite)
    """,
    language="yaml"
)
