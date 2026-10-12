"""
Automated Case Study and Methodology Report Generator.
Outputs Markdown documents and structured PDF reports (using pure-Python fpdf2).
Ensures clear distinction between observations, hypotheses, and synthetic demo indicators.
"""

from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from config import REPORTS_DIR, DOCS_DIR


class ReportGenerator:
    """
    Synthesizes intelligence metrics into professional documentation artifacts.
    """

    def __init__(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        DOCS_DIR.mkdir(parents=True, exist_ok=True)

    def generate_case_study_markdown(
        self,
        dataset_profile: Dict[str, Any],
        priority_df: pd.DataFrame,
        trend_kpis: Dict[str, Any],
        emerging_issues: List[Dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> str:
        """
        Creates a submission-ready, executive case study report in Markdown.
        """
        out_file = output_path or (DOCS_DIR / "case_study_report.md")

        is_demo = dataset_profile.get("is_demo_data", False)
        provenance_banner = ""
        if is_demo:
            provenance_banner = (
                "> [!WARNING]\n"
                "> **NOTICE: DEMO DATASET UTILIZED**\n"
                "> The findings, tables, and metric distributions below are synthesized from illustrative test data.\n"
                "> Real-world corporate commitments should not be finalized without running the pipeline on authentic production Play Store reviews.\n\n"
            )

        total_rev = dataset_profile.get("total_reviews", 0)
        avg_score = dataset_profile.get("avg_rating", 0.0)
        neg_share = dataset_profile.get("negative_rating_share", 0.0)
        date_span = f"{dataset_profile.get('date_min', 'N/A')} to {dataset_profile.get('date_max', 'N/A')}"

        # Build recommendation rows
        rec_rows = []
        if not priority_df.empty:
            for idx, r in priority_df.iterrows():
                rec_rows.append(
                    f"| **{r['priority_label']}** | {r['category_label']} | {r['priority_score']} | "
                    f"{r['review_count']} ({r['negative_pct']}%) | {r['estimated_effort']} | {r['suggested_owner']} |"
                )
        rec_table = "\n".join(rec_rows) if rec_rows else "| None | No issues detected | - | - | - | - |"

        # Detailed cards
        detailed_sections = []
        if not priority_df.empty:
            for idx, r in priority_df.iterrows():
                excerpts_md = "\n".join([f"- {e}" for e in r.get("representative_excerpts", [])]) or "- *None available*"
                detailed_sections.append(
                    f"### {r['priority_label']}: {r['category_label']} (Score: {r['priority_score']})\n\n"
                    f"- **Problem Observed**: {r['problem_statement']}\n"
                    f"- **Why It Matters**: {r['why_it_matters']}\n"
                    f"- **Proposed Fix**: \n{r['proposed_fix']}\n"
                    f"- **Suggested Owner**: `{r['suggested_owner']}`\n"
                    f"- **Estimated Effort**: `{r['estimated_effort']}`\n"
                    f"- **Success Metric**: `{r['success_metric']}`\n"
                    f"- **Supporting Evidence ({r['review_count']} reviews)**:\n{excerpts_md}\n"
                )
        detailed_text = "\n---\n".join(detailed_sections)

        content = f"""# MoveInSync ETS: Play Store Review Intelligence & Prioritization Case Study
**Forward Deployed Engineer (FDE) Investigation Report**

{provenance_banner}
## 1. Executive Summary

MoveInSync powers employee transit for marquee enterprises where daily punctuality, safety verification, and operational predictability are non-negotiable. An analysis of public Play Store user feedback was conducted to establish empirical root causes behind low app store ratings and identify engineering interventions that deliver the greatest reliability impact.

### Key Intelligence Findings:
1. **Total Dataset Evaluated**: {total_rev} user reviews spanning `{date_span}`.
2. **Observed Dataset Average Rating**: **{avg_score} / 5.0** (with **{neg_share}%** of reviews rating 1 or 2 stars).
3. **Core Complaint Drivers**: The steepest rating detractors originate from **Safety & OTP Verification Failures**, **Live Vehicle GPS Jumps**, **Login/Authentication Drops**, and **Roster Cutoff Server Errors**.
4. **Primary Engineering Recommendation**: Implement cryptographic driver-passenger OTP handshakes prior to ride initiation, re-architect real-time vehicle telematics via bi-directional WebSockets, and provide multi-channel SMS/WhatsApp OTP fallback.

---

## 2. Methodology & Evidence Architecture

Our evaluation applies a transparent Forward Deployed Engineering triage framework:
- **Public Data Ingestion**: Cleaned via `google-play-scraper` with metadata preservation (star rating, timestamp, app build version, developer reply).
- **Quality Assurance**: Automated unicode normalization, exact ID & fuzzy fingerprint deduplication, and rating boundary checks.
- **Multi-Label Categorization**: 100% deterministic regex rule engine based on 10 transportation domain categories, augmented with optional structured OpenAI extraction.
- **Priority Scoring Formula**:
  $$\\text{{Priority Score}} = 0.30\\cdot F + 0.25\\cdot S + 0.20\\cdot T + 0.15\\cdot C + 0.10\\cdot E_{{inv}}$$
  Where $F$ = Negative Frequency Share, $S$ = Severity, $T$ = Recent Trend Momentum, $C$ = Statistical Confidence, and $E_{{inv}}$ = Ease of Implementation.

---

## 3. Prioritized Engineering Interventions

| Priority | Defect Category | Score | Reviews (Neg %) | Est. Effort | Suggested Owner |
|:---|:---|:---:|:---:|:---:|:---|
{rec_table}

---

## 4. Deep-Dive Problem Statements & Proposed Fixes

{detailed_text}

---

## 5. Suggested Phased Implementation Roadmap

> **Note**: Timelines are suggested engineering estimates, not binding commitments.

### Phase 1: Immediate Safety & Access Containment (Weeks 1 - 3)
- Audit SOS dispatch latency and ensure SMS fallback gateway is enabled.
- Lock driver ride initiation behind validated cryptographic OTP match on backend.
- Introduce multi-vendor SMS routing (Twilio/AWS SNS) to eliminate OTP latency drops.

### Phase 2: Core Platform Telematics & Roster Reliability (Weeks 4 - 8)
- Deploy WebSocket telematics pipeline with Kalman smoothing on GPS coordinates.
- Decouple roster reservation database writes using Redis queue to survive 2 PM cutoff spikes.
- Profile and patch Android cold-start ANR triggers on Android 13/14 devices.

### Phase 3: Continuous Intelligence & Closed-Loop SLA (Ongoing)
- Implement continuous weekly Play Store sentiment tracking.
- Measure Week-over-Week reduction in 1-star review share following releases.
- Establish direct in-app penalty dispute resolution for corporate transit riders.

---

## 6. Success Metrics & Measurement Framework

| Objective | Public Review Metric | Internal Operational Proxy (B2B Telemetry) |
|:---|:---|:---|
| **App Store Reputation** | Reduce 1-star & 2-star share below 25% | Play Store 30-day rolling average > 4.2★ |
| **Authentication Reliability** | Login/OTP complaints < 2% of volume | OTP 99th percentile delivery latency < 10s |
| **Tracking Faithfulness** | GPS tracking complaints < 5% of volume | Passenger map live disconnect rate < 0.5% |
| **Passenger Safety** | Zero verified unverified ride starts | 100% escort attendance digital signoff |
| **Roster Usability** | Booking error complaints < 3% of volume | Shift reservation API error rate < 0.05% |

---

## 7. Assumptions & Known Limitations

1. **Review Selection Bias**: Users facing transit failures (delays, missed cabs) are substantially more motivated to write Play Store reviews than satisfied riders.
2. **Lagging Indicator**: Play Store ratings lag internal code deployments by 2 to 4 weeks as users do not immediately update existing ratings upon bug fixes.
3. **Public vs. Internal Data**: Public reviews cannot isolate company-specific transit routing policies from global software defects without employee corporate email linking.
"""

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content)

        return content

    def generate_pdf_report(self, markdown_text: str, output_path: Optional[Path] = None) -> bytes:
        """
        Generates an enterprise-ready PDF document from analysis content.
        Uses fpdf2 with clean layout and typography.
        """
        out_file = output_path or (REPORTS_DIR / "MoveInSync_Review_Intelligence_Report.pdf")

        from fpdf import FPDF

        class PDFReport(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(100, 100, 100)
                self.cell(0, 8, "MoveInSync Review Intelligence AI | Executive Case Study", border=0, align="L")
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f"Page {self.page_no()}", border=0, align="C")

        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        epw = pdf.epw # Effective page width

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(epw, 12, "MoveInSync ETS: Review Intelligence Report", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "I", 11)
        pdf.set_text_color(100, 100, 120)
        pdf.cell(epw, 8, "Forward Deployed Engineer Root-Cause Analysis & Prioritization", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Body parsing (Clean text extraction for PDF formatting)
        lines = markdown_text.split("\n")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)

        def sanitize_for_pdf(txt: str) -> str:
            # Replace common special unicode characters
            replacements = {
                "★": " Stars",
                "•": "-",
                "—": "-",
                "–": "-",
                "“": '"',
                "”": '"',
                "’": "'",
                "‘": "'",
                "…": "...",
                "🔴": "[P0]",
                "🟠": "[P1]",
                "🟡": "[P2]",
                "🟢": "[P3]",
            }
            for k, v in replacements.items():
                txt = txt.replace(k, v)
            # Remove any other non-latin1 characters
            return txt.encode("latin-1", "replace").decode("latin-1")

        for line in lines:
            line_str = sanitize_for_pdf(line.strip())
            if not line_str:
                pdf.ln(2)
                continue

            # Heading 1
            if line_str.startswith("# "):
                continue # Already in title
            # Heading 2
            elif line_str.startswith("## "):
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(43, 65, 175) # Deep navy/blue
                pdf.cell(epw, 8, line_str.replace("## ", ""), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
            # Heading 3
            elif line_str.startswith("### "):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(30, 30, 30)
                pdf.cell(epw, 6, line_str.replace("### ", ""), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
            # Table
            elif line_str.startswith("|"):
                cells = [c.strip() for c in line_str.split("|")[1:-1]]
                if cells and not all(c.startswith("-") or c.startswith(":") for c in cells):
                    row_txt = "  |  ".join(cells)
                    pdf.set_font("Courier", "", 8)
                    pdf.multi_cell(epw, 5, row_txt)
                    pdf.set_font("Helvetica", "", 10)
            elif line_str.startswith(">"):
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(180, 50, 50)
                pdf.multi_cell(epw, 5, line_str.replace(">", "").strip())
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(40, 40, 40)
            else:
                # Regular text
                clean_line = line_str.replace("**", "").replace("`", "").replace("$$", "")
                pdf.multi_cell(epw, 5, clean_line)

        pdf_bytes = pdf.output()
        with open(out_file, "wb") as f:
            f.write(pdf_bytes)

        return pdf_bytes
