"""
Priority Engine and Engineering Recommendation Generator.
Computes multi-attribute prioritization scores (Frequency, Severity, Trend, Confidence, Effort).
Assigns P0/P1/P2/P3 tiers and generates evidence-backed, actionable fix proposals.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from config import (
    CATEGORIES,
    PRIORITY_WEIGHTS,
    SEVERITY_WEIGHTS,
    EFFORT_SCORES,
    PRIORITY_THRESHOLDS,
)


class PriorityEngine:
    """
    Rigorously ranks product defect areas and generates engineering intervention proposals.
    Formula:
        Score = (W_freq * F) + (W_sev * S) + (W_trend * T) + (W_conf * C) + (W_effort * E)
    Never marks P0 solely due to volume; safety triggers or combined high-severity/high-volume required.
    """

    # Recommendation templates tailored for MoveInSync ETS platform
    FIX_TEMPLATES: Dict[str, Dict[str, str]] = {
        "safety_verification": {
            "problem": "Critical safety escalations: SOS button unresponsiveness, female drop-off escort discrepancies, and ride initiation without OTP verification.",
            "fix": "1. Re-architect SOS trigger with offline SMS fallback and dedicated low-latency gateway.\n2. Enforce strict cryptographic OTP handshake on driver terminal before ride status can transition to 'Active'.\n3. Mandate digital dual-signoff for female escort drop-offs before route closure.",
            "why_it_matters": "Employee safety is existential for corporate B2B contracts. Non-compliance risks severe legal liability, client breach of contract, and passenger harm.",
            "owner": "Safety Systems Engineering & Fleet Quality Operations",
            "effort": "Medium",
            "metric": "Zero ride initiations without verified OTP; <3 second SOS escalation acknowledgment SLA.",
        },
        "booking_reservation": {
            "problem": "Employees encounter server errors (500), frozen cutoff rosters, and inability to adjust pickup shifts during deadline hours.",
            "fix": "1. Implement idempotency and optimistic UI updates for roster booking requests.\n2. Decouple shift schedule write traffic with Redis-backed message queue to absorb peak shift-booking spikes.\n3. Add proactive push alerts 45 minutes prior to roster lock.",
            "why_it_matters": "Inability to book leads to employee no-shows, unexpected cab allocations, and heavy transport admin overhead.",
            "owner": "Roster & Scheduling Product Team / Platform Backend",
            "effort": "Medium",
            "metric": "99.9% booking request success rate; zero 500 error spikes during 2 PM roster cutoff windows.",
        },
        "login_otp_auth": {
            "problem": "Authentication barrier: Delayed or undelivered SMS OTPs cause session timeouts and prevent employees from accessing transport rosters.",
            "fix": "1. Implement multi-vendor SMS routing fallback (e.g., Twilio + AWS SNS) with automatic circuit breaker.\n2. Provide WhatsApp / Authenticator app / Email OTP as secondary authentication channels.\n3. Implement biometric (Fingerprint/FaceID) local token refresh to eliminate daily re-login friction.",
            "why_it_matters": "Auth friction at 7 AM causes missed shifts and generates immediate 1-star ratings from stranded users.",
            "owner": "Platform & Identity / Auth Engineering",
            "effort": "Medium",
            "metric": "<10 second OTP delivery latency (99th percentile); 80% reduction in login failure reviews.",
        },
        "pickup_eta": {
            "problem": "Inaccurate ETA forecasts with erratic fluctuations (5 min to 25 min) causing missed employee pickups or unnecessary waiting in unsafe areas.",
            "fix": "1. Upgrade ETA prediction engine with real-time traffic tile ingestion (Google Maps Routes / Mapbox Matrix API).\n2. Apply Kalman smoothing on vehicle velocity vectors to eliminate wild ETA jumps.\n3. Trigger proactive notification when cab is 5 minutes or 1.5 km away.",
            "why_it_matters": "Punctuality is the primary value proposition of managed enterprise employee transit.",
            "owner": "Routing & Dispatch Algorithm Team",
            "effort": "High",
            "metric": "85% ETA accuracy within ±3 minute window; 40% reduction in pickup delay complaints.",
        },
        "gps_tracking": {
            "problem": "Vehicle marker freezing, jumpy map icons, and mismatch between driver physical arrival and map coordinates.",
            "fix": "1. Modernize driver app telematics service with foreground location service and dead-reckoning.\n2. Implement WebSocket-based bi-directional pub/sub for low-latency vehicle location streaming to passenger apps.\n3. Add visual 'Last updated X seconds ago' indicator on passenger map.",
            "why_it_matters": "When GPS map appears frozen, employees lose trust in arrival times and panic call dispatch or drivers.",
            "owner": "Mobile Telematics Team / Infrastructure",
            "effort": "Medium",
            "metric": "<3 second vehicle marker location refresh latency; <1% driver GPS packet loss.",
        },
        "driver_vehicle": {
            "problem": "Negative passenger experiences regarding rash driving, refusal of air conditioning, unprofessional behavior, and broken seatbelts.",
            "fix": "1. Institute automated vendor scorecard penalizing fleet suppliers for verified driver misconduct.\n2. In-app post-ride granular feedback tags (AC, Punctuality, Safe Driving, Cleanliness).\n3. Mandatory quarterly defensive driving and passenger safety refresher audits for fleet vendors.",
            "why_it_matters": "Direct physical encounter influences corporate passenger sentiment more intensely than app aesthetics.",
            "owner": "Fleet Vendor Quality Operations",
            "effort": "Low",
            "metric": "Driver behavioral complaint incident rate < 1.5 per 1,000 completed rides.",
        },
        "notifications_checkin": {
            "problem": "Delayed cab arrival alerts and failure of in-cab beacon / QR code boarding verification.",
            "fix": "1. Migrate push notification pipeline to high-priority FCM / APNS channels with background wake.\n2. Provide high-contrast, offline-capable dynamic QR code for cab boarding check-in fallback.\n3. Auto-fallback to SMS alert if push delivery is not acknowledged within 60 seconds.",
            "why_it_matters": "Missed arrival notifications directly cause employee no-shows and driver wait-time penalties.",
            "owner": "Mobile Client Team / Communications Pipeline",
            "effort": "Low",
            "metric": "98% on-device delivery of arrival push notifications within 15 seconds of trigger.",
        },
        "app_performance": {
            "problem": "App crashes during peak morning hours, battery drain during background tracking, and UI freezes on newer Android devices.",
            "fix": "1. Profile and resolve ANR (Application Not Responding) threads and memory leaks using Sentry / Firebase Crashlytics.\n2. Optimize background location geofencing to use batch wakeups rather than continuous GPS polling.\n3. Refactor cold-start dependency injection to achieve sub-1.5s splash screen time.",
            "why_it_matters": "App unreliability directly leads to Play Store uninstalls and low rating review spam.",
            "owner": "Android Core Team & Mobile QA",
            "effort": "Medium",
            "metric": "Crash-free session rate >= 99.8%; cold start latency under 1.5s on mid-tier Android devices.",
        },
        "customer_support": {
            "problem": "Support tickets closed without resolution, unresponsive helpline, and automated bots unable to process disputed no-show penalties.",
            "fix": "1. Integrate Zendesk/Freshdesk in-app chat with live agent escalation during operational transit hours (6 AM - 11 PM).\n2. Automated 1-click penalty dispute review with ride telematics cross-verification.\n3. Publish SLA tracker directly on open support tickets inside the app.",
            "why_it_matters": "Unresolved customer grievances turn frustrated users into vocal Play Store 1-star reviewers.",
            "owner": "Customer Support Operations / Product Integration",
            "effort": "Low",
            "metric": "First response time < 10 minutes during shift windows; 80% first-contact resolution on penalty disputes.",
        },
        "other": {
            "problem": "Miscellaneous corporate policies, routing edge-cases, and unclassified feedback.",
            "fix": "1. Implement structured user feedback surveys at milestone intervals.\n2. Regular backlog grooming with enterprise client transport managers.",
            "why_it_matters": "Captures latent customer needs that do not map to standardized operational defect categories.",
            "owner": "Product Research & UX",
            "effort": "Low",
            "metric": "Unclassified review proportion < 5% of incoming feedback volume.",
        },
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = custom_weights or PRIORITY_WEIGHTS

    def calculate_category_metrics(self, df: pd.DataFrame, trend_surge_dict: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """
        Aggregates metrics for each category and calculates the normalized priority score.
        """
        if df.empty:
            return pd.DataFrame()

        total_reviews = len(df)
        negative_reviews = df[df["score"] <= 2]
        total_negative = len(negative_reviews)

        surge_dict = trend_surge_dict or {}

        metrics_list = []

        # Analyze each category
        for cat_key, cat_meta in CATEGORIES.items():
            # Match reviews where primary_category == cat_key OR cat_key in categories list
            cat_mask = df["primary_category"] == cat_key
            cat_df = df[cat_mask]
            count = len(cat_df)

            if count == 0:
                continue

            neg_count = int((cat_df["score"] <= 2).sum())
            avg_score = round(float(cat_df["score"].mean()), 2)
            
            # 1. Frequency Score (0 to 1): Share of negative complaints or total share
            freq_score = (neg_count / total_negative) if total_negative > 0 else (count / total_reviews)
            freq_score = min(1.0, freq_score * 2.0) # Scaled so 50% share hits 1.0

            # 2. Severity Score (0 to 1): Weighted average of severity ratings
            sev_scores = [SEVERITY_WEIGHTS.get(str(s).lower(), 0.5) for s in cat_df.get("severity", ["medium"] * count)]
            sev_score = float(np.mean(sev_scores)) if sev_scores else 0.5

            # If safety category with critical complaint, ensure severe score
            has_critical = any(str(s).lower() == "critical" for s in cat_df.get("severity", []))
            if has_critical:
                sev_score = max(sev_score, 0.90)

            # 3. Trend Score (0 to 1): Derived from surge multiplier or neutral
            surge_mult = surge_dict.get(cat_key, 1.0)
            trend_score = min(1.0, max(0.2, (surge_mult - 0.5) / 1.5))

            # 4. Confidence Score (0 to 1): Statistical sample size (capped at 10 reviews) * classifier confidence
            sample_conf = min(1.0, count / 8.0)
            avg_class_conf = float(cat_df["confidence"].mean()) if "confidence" in cat_df.columns else 0.8
            confidence_score = sample_conf * avg_class_conf

            # 5. Effort Inverse (0 to 1): Low effort -> higher score (quick wins favored)
            effort_label = cat_meta.get("default_effort", "Medium")
            effort_score = EFFORT_SCORES.get(effort_label, 0.65)

            # Overall Weighted Priority Score
            raw_score = (
                (self.weights["frequency"] * freq_score) +
                (self.weights["severity"] * sev_score) +
                (self.weights["trend"] * trend_score) +
                (self.weights["confidence"] * confidence_score) +
                (self.weights["effort_inverse"] * effort_score)
            )
            raw_score = round(min(1.0, max(0.0, raw_score)), 3)

            # Priority Label Assignment
            # Safety complaints with critical flags or safety category get expedited review
            if cat_key == "safety_verification" and (has_critical or neg_count >= 2):
                priority_label = "P0"
                rationale = "CRITICAL: Urgent safety/escort compliance issue with potential legal and passenger welfare risk."
            elif raw_score >= PRIORITY_THRESHOLDS["P0"]["min_score"] and neg_count >= PRIORITY_THRESHOLDS["P0"]["min_count"]:
                priority_label = "P0"
                rationale = "P0: Severe recurring service failure severely degrading app viability."
            elif raw_score >= PRIORITY_THRESHOLDS["P1"]["min_score"] and neg_count >= PRIORITY_THRESHOLDS["P1"]["min_count"]:
                priority_label = "P1"
                rationale = "P1: High-impact user friction affecting core daily transit operations."
            elif raw_score >= PRIORITY_THRESHOLDS["P2"]["min_score"]:
                priority_label = "P2"
                rationale = "P2: Important usability defect causing customer dissatisfaction."
            else:
                priority_label = "P3"
                rationale = "P3: Low-impact enhancement or low-confidence issue requiring more telemetry evidence."

            # Date range for evidence
            date_col = "parsed_date" if "parsed_date" in cat_df.columns else "date"
            try:
                dt_series = pd.to_datetime(cat_df[date_col], errors="coerce").dropna()
                dates_str = f"{dt_series.min().strftime('%Y-%m-%d')} to {dt_series.max().strftime('%Y-%m-%d')}" if not dt_series.empty else "N/A"
            except Exception:
                dates_str = "N/A"

            # Representative review excerpts (up to 3 negative/instructive reviews)
            neg_excerpts = cat_df.sort_values("score", ascending=True)
            excerpts = [
                f"[{r.get('score')}★] \"{str(r.get('display_text', r.get('text', '')))[:120]}...\""
                for _, r in neg_excerpts.head(3).iterrows()
                if str(r.get('display_text', r.get('text', ''))).strip()
            ]

            template = self.FIX_TEMPLATES.get(cat_key, self.FIX_TEMPLATES["other"])

            metrics_list.append({
                "category": cat_key,
                "category_label": cat_meta["label"],
                "priority_label": priority_label,
                "priority_score": raw_score,
                "review_count": count,
                "negative_count": neg_count,
                "negative_pct": round((neg_count / count) * 100, 1),
                "avg_rating": avg_score,
                "frequency_score": round(freq_score, 2),
                "severity_score": round(sev_score, 2),
                "trend_score": round(trend_score, 2),
                "confidence_score": round(confidence_score, 2),
                "effort_score": round(effort_score, 2),
                "estimated_effort": effort_label,
                "problem_statement": template["problem"],
                "proposed_fix": template["fix"],
                "why_it_matters": template["why_it_matters"],
                "suggested_owner": template["owner"],
                "success_metric": template["metric"],
                "priority_rationale": rationale,
                "evidence_dates": dates_str,
                "representative_excerpts": excerpts,
                "has_safety_flag": bool(cat_key == "safety_verification" or has_critical),
            })

        priority_df = pd.DataFrame(metrics_list)
        if not priority_df.empty:
            # Custom sorting: P0 -> P1 -> P2 -> P3, then score descending
            p_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
            priority_df["p_rank"] = priority_df["priority_label"].map(p_order)
            priority_df.sort_values(by=["p_rank", "priority_score"], ascending=[True, False], inplace=True)
            priority_df.drop(columns=["p_rank"], inplace=True)
            priority_df.reset_index(drop=True, inplace=True)

        return priority_df

    def get_ranked_recommendations(self, priority_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Returns clean dictionary records of prioritized recommendations ready for display.
        """
        if priority_df.empty:
            return []
        return priority_df.to_dict(orient="records")
