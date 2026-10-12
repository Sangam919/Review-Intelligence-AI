"""
Commute Journey Mapping Module.
Maps review defect categories to the 9 stages of an enterprise employee commute journey.
Calculates stage-wise metrics, friction scores, representative evidence, suggested fixes,
and clearly distinguishes public review findings from metrics requiring internal company telemetry.
"""

from typing import Dict, Any, List, Optional
import pandas as pd


JOURNEY_STAGES = {
    "login_auth": {
        "title": "1. Login & Authentication",
        "description": "Employee opens app, enters credentials or corporate SSO, receives SMS/Email OTP.",
        "icon": "🔐",
        "related_categories": ["login_otp_auth"],
        "suggested_improvement": "Multi-vendor SMS routing, biometrics refresh token, WhatsApp OTP fallback.",
        "potential_impact": "Eliminates morning login blockades and prevents shift delay penalties.",
        "internal_telemetry_required": [
            "OTP delivery latency (p95/p99) across telecom operators",
            "SSO token validation failure rate by enterprise client ID",
            "Session timeout frequency during active use"
        ]
    },
    "roster_setup": {
        "title": "2. Shift & Roster Setup",
        "description": "Employee configures weekly roster shifts, transport requirements, and pickup addresses.",
        "icon": "📅",
        "related_categories": ["booking_reservation"],
        "suggested_improvement": "Optimistic UI booking updates, Redis write queues for 2 PM cutoff spikes, proactive lock reminders.",
        "potential_impact": "Reduces transport admin support escalations and prevents unexpected cab allocation mismatches.",
        "internal_telemetry_required": [
            "Roster write latency during peak 1-hour cutoff window",
            "Internal server error (500) rate on roster lock APIs",
            "Number of manual admin override requests per client"
        ]
    },
    "ride_booking": {
        "title": "3. Ride Booking & Confirmation",
        "description": "Daily ride scheduling, ad-hoc ride requests, and cancellation before cutoff.",
        "icon": "🎟️",
        "related_categories": ["booking_reservation"],
        "suggested_improvement": "Graceful cancellation workflows, clear penalty countdown timers, automated seat re-allocation.",
        "potential_impact": "Reduces unfair no-show penalties and improves employee trust.",
        "internal_telemetry_required": [
            "Ad-hoc ride request confirmation rate",
            "Cancellation rate before vs after cut-off time",
            "Seat utilization rate per scheduled route"
        ]
    },
    "cab_assignment": {
        "title": "4. Cab / Route Assignment",
        "description": "System pairs rider with cab route, vehicle details, driver partner, and co-passengers.",
        "icon": "🚐",
        "related_categories": ["pickup_eta", "driver_vehicle"],
        "suggested_improvement": "Route optimization algorithm accounting for hyper-local traffic and road blockages.",
        "potential_impact": "Minimizes unnecessary passenger ride duration and detour times.",
        "internal_telemetry_required": [
            "Driver assignment delay from scheduled dispatch time",
            "Re-routing frequency per trip",
            "Co-passenger detour detour-to-direct distance ratio"
        ]
    },
    "pickup_notification": {
        "title": "5. Pickup Notification & Alerts",
        "description": "Push alerts and SMS when cab is dispatched, nearby (1 km away), and arrived at gate.",
        "icon": "🔔",
        "related_categories": ["notifications_checkin", "pickup_eta"],
        "suggested_improvement": "High-priority FCM/APNs channels with SMS fallback if unacknowledged within 60s.",
        "potential_impact": "Directly reduces missed pickups and driver idle waiting times at gates.",
        "internal_telemetry_required": [
            "Push notification device delivery rate and latency",
            "SMS fallback trigger rate",
            "Employee boarding time after cab arrival notification"
        ]
    },
    "live_tracking": {
        "title": "6. Live Vehicle Tracking",
        "description": "Real-time map view showing driver location marker, route polyline, and estimated arrival time.",
        "icon": "📍",
        "related_categories": ["gps_tracking", "pickup_eta"],
        "suggested_improvement": "Bi-directional WebSocket streaming, Kalman smoothing, explicit 'Last updated X sec ago' badge.",
        "potential_impact": "Eliminates commuter anxiety and redundant phone calls to drivers.",
        "internal_telemetry_required": [
            "Driver telematics GPS packet drop rate",
            "Driver app foreground location service uptime",
            "WebSocket active connection disconnect / reconnect rate"
        ]
    },
    "otp_safety_verification": {
        "title": "7. OTP & Safety Verification",
        "description": "Driver passenger verification, OTP exchange, security guard escort confirmation for night shifts.",
        "icon": "🛡️",
        "related_categories": ["safety_verification"],
        "suggested_improvement": "Cryptographic driver app lockout until OTP is matched on backend; digital escort dual-signoff.",
        "potential_impact": "Eliminates unverified rides, guarantees female commuter safety compliance.",
        "internal_telemetry_required": [
            "Incident audit rate for rides initiated without passenger OTP",
            "Female commuter night drop security escort attendance rate",
            "SOS emergency alert trigger count and SOC response SLA"
        ]
    },
    "boarding_commute": {
        "title": "8. Boarding, Commute & Drop-Off",
        "description": "Physical ride experience, vehicle condition, AC, driver demeanor, route compliance, drop.",
        "icon": "🛣️",
        "related_categories": ["driver_vehicle", "safety_verification"],
        "suggested_improvement": "Granular post-ride tag ratings (AC, Rash Driving, Route), automated vendor SLA penalties.",
        "potential_impact": "Improves daily physical rider comfort and vendor accountability.",
        "internal_telemetry_required": [
            "Vehicle speed telematics violations (overspeeding events)",
            "Actual route deviation vs planned polyline variance",
            "Vendor fleet penalty deduction audit logs"
        ]
    },
    "issue_support": {
        "title": "9. Issue Reporting & Support",
        "description": "In-app helpline, disputing no-show penalties, reporting lost belongings, feedback.",
        "icon": "🎧",
        "related_categories": ["customer_support", "app_performance"],
        "suggested_improvement": "In-app live chat during transit hours, 1-click penalty dispute review with GPS check, SLA tracking.",
        "potential_impact": "Prevents unresolved grievances from converting into 1-star Play Store reviews.",
        "internal_telemetry_required": [
            "Customer support First Response Time (FRT) during commute hours",
            "Disputed penalty resolution turnaround time",
            "Escalation rate to client company transport managers"
        ]
    }
}


class CommuteJourneyAnalyzer:
    """
    Analyzes employee commute touchpoints across the 9 defined journey stages.
    """

    def __init__(self):
        self.stages = JOURNEY_STAGES

    def analyze_journey(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Calculates stage friction metrics, review counts, average ratings,
        and extracts representative verbatim evidence.
        """
        if df.empty:
            return []

        results = []
        total_reviews = len(df)
        total_negative = len(df[df["score"] <= 2])

        for stage_key, meta in self.stages.items():
            cats = meta["related_categories"]
            # Match reviews where primary_category is in cats OR categories list overlaps
            mask = df["primary_category"].isin(cats)
            stage_df = df[mask]
            count = len(stage_df)

            if count > 0:
                neg_count = int((stage_df["score"] <= 2).sum())
                avg_rating = round(float(stage_df["score"].mean()), 2)
                neg_pct = round((neg_count / count) * 100, 1)
                
                # Representative negative excerpts
                neg_samples = stage_df.sort_values("score", ascending=True)
                excerpts = [
                    f"[{r.get('score')}★] \"{str(r.get('display_text', r.get('text', '')))[:110]}...\""
                    for _, r in neg_samples.head(3).iterrows()
                    if str(r.get('display_text', r.get('text', ''))).strip()
                ]
            else:
                neg_count = 0
                avg_rating = 0.0
                neg_pct = 0.0
                excerpts = []

            # Compute Stage Friction Index (0-100)
            friction_index = 0
            if total_negative > 0:
                share_of_neg = (neg_count / total_negative)
                # Severity amplifier
                sev_amp = 1.5 if stage_key in ["otp_safety_verification", "live_tracking"] else 1.0
                friction_index = min(100, int(share_of_neg * 100 * sev_amp))

            results.append({
                "stage_key": stage_key,
                "title": meta["title"],
                "icon": meta["icon"],
                "description": meta["description"],
                "related_categories": cats,
                "review_count": count,
                "negative_count": neg_count,
                "negative_pct": neg_pct,
                "avg_rating": avg_rating,
                "friction_index": friction_index,
                "suggested_improvement": meta["suggested_improvement"],
                "potential_impact": meta["potential_impact"],
                "representative_excerpts": excerpts,
                "internal_telemetry_required": meta["internal_telemetry_required"],
            })

        return results
