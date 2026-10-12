# MoveInSync Review Intelligence AI
**Enterprise Customer Experience & Product Reliability Analytics Platform**
*Forward Deployed Engineering (FDE) Case Study — End-to-End Upgrade*

An enterprise analytics and evidence-grounded prioritization platform built for **MoveInSync Employee Transportation Solutions (ETS)** (`com.moveinsync.ets`).

---

## 🌟 Upgraded Multi-Page Architecture

The platform features an 11-page navigation structure with visual hierarchy, global dataset switching, and evidence drill-downs:

1. **📊 Executive Overview**: High-level CX KPIs, dataset sample average vs. official Google Play store aggregate score (4.32★), 1-star share, star distribution, weekly volume timeline, and top-3 evidence-supported issues & actions.
2. **🔍 Review Explorer**: Full-text keyword search, multi-faceted filtering (star rating, category, sentiment, date, version), sorting, pagination (15 reviews/page), CSV export, and authorized manual re-classification.
3. **💬 Sentiment Intelligence**: Distribution across ratings and categories, net sentiment score, common complaint phrases, positive themes, and transparent estimation disclosures.
4. **📈 Issue Analysis**: Deep-dive operational defect taxonomy breakdown, category frequency horizontal bars, rating spread box plots, and verbatim quote inspections.
5. **🎯 Priority & Action Center**: Transparent 5-factor mathematical prioritization matrix ($0.30\cdot F + 0.25\cdot S + 0.20\cdot T + 0.15\cdot C + 0.10\cdot E_{inv}$) with `P0`, `P1`, `P2`, and `P3` tiers, local workflow status tracking (`proposed`, `under investigation`, `implemented`, `validated`), and action plan exports.
6. **🛣️ Product Experience Analytics**: Linear 9-stage **Employee Commute Journey** mapping (Login $\rightarrow$ Roster $\rightarrow$ Booking $\rightarrow$ Assignment $\rightarrow$ Notification $\rightarrow$ Live Tracking $\rightarrow$ OTP Safety $\rightarrow$ Boarding $\rightarrow$ Support) with touchpoint friction indices and internal operational telemetry disclosures.
7. **📡 Trend Monitoring**: Longitudinal review velocity, 30-day comparative period KPIs, category surge alerts ($>1.35\times$ velocity increases), and small-sample safeguards.
8. **🤖 AI Insights**: Executive briefing synthesis, natural language review queries, and structured engineering inquiries powered by `gpt-4o-mini` with a rule-based fallback when API keys are absent.
9. **💾 Data Collection & Quality**: Live Play Store scraper targeting `com.moveinsync.ets`, manual CSV uploader, and data cleansing audit logs.
10. **📄 Reports & Exports**: Automated generation of submission-ready Executive Case Study PDFs (`fpdf2`), Markdown reports, and tabular CSV exports.
11. **📖 Methodology & Settings**: Scoring formulas, dimensional weights, analytical bias disclosures (selection bias, lagging indicators), and runtime configuration.

---

## 🛡️ Critical Data Credibility & Dataset Separation

The platform supports two datasets switchable in the global sidebar:
1. **Live Scraped Play Store (200 Authentic Reviews)**: Verified recent customer feedback scraped from Google Play with review IDs, reviewer names, app versions, and developer responses.
2. **Illustrative Sample (50 Demo Reviews)**: Synthetic benchmark for testing pipeline edge cases. When active, prominent yellow **DEMO DATA** banners warn the user that findings are illustrative.

---

## 🛠️ Technology Stack

- **Python 3.10+**
- **Streamlit 1.40+** (Native multipage navigation via `st.Page` and `st.navigation`)
- **Pandas 2.2+ & NumPy**
- **Plotly 5.24+** (Interactive charts with enterprise styling)
- **google-play-scraper** (Google Play Store public RPC endpoint ingestion)
- **OpenAI Python SDK** (Optional `gpt-4o-mini` structured extraction)
- **fpdf2** (Pure-Python PDF generation with Unicode sanitization)
- **SQLite** (`reviews.sqlite` with UPSERT deduplication)
- **Pytest 8.3+** (18 automated tests)

---

## ⚡ Quick Start & Installation (Windows / PowerShell)

### 1. Launch Application
```powershell
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### 2. Run Automated Tests
```powershell
python -m pytest tests/ -v
```
All **18 automated tests** validate data ingestion, preprocessing, classification, priority formulas, commute journey stages, and AI fallbacks.
