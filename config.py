"""
Configuration module for MoveInSync Review Intelligence AI.
Centralizes constants, taxonomies, scoring weights, paths, and environment settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# Database path
DEFAULT_DB_PATH = BASE_DIR / "data" / "reviews.sqlite"

# Target Application
DEFAULT_APP_ID = os.getenv("PLAY_STORE_APP_ID", "com.moveinsync.ets")
DEFAULT_COUNTRY = os.getenv("DEFAULT_COUNTRY", "in")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
HAS_OPENAI_KEY = bool(OPENAI_API_KEY)
DEFAULT_AI_MODEL = "gpt-4o-mini"

# Review Categories Definition (10 standard categories for Employee Transportation System)
CATEGORIES = {
    "booking_reservation": {
        "label": "Booking and Reservation",
        "description": "Issues scheduling rides, selecting shifts, cancelling, roster modifications, or booking deadlines.",
        "default_effort": "Medium",
        "suggested_owner": "Product (Roster & Scheduling) / Backend Engineering",
    },
    "login_otp_auth": {
        "label": "Login, OTP, and Authentication",
        "description": "Login failures, missing or delayed SMS/Email OTP, SSO auth errors, session timeouts.",
        "default_effort": "Medium",
        "suggested_owner": "Platform / Security & Auth Engineering",
    },
    "pickup_eta": {
        "label": "Pickup Time and ETA Accuracy",
        "description": "Inaccurate ETA forecasts, delayed pickups, unexpected early arrivals, routing inefficiencies.",
        "default_effort": "High",
        "suggested_owner": "Dispatch & Routing Algorithm Team / Operations",
    },
    "gps_tracking": {
        "label": "GPS and Live Vehicle Tracking",
        "description": "Vehicle map jump, frozen driver marker, inaccurate distance calculations, driver app location sync.",
        "default_effort": "Medium",
        "suggested_owner": "Mobile Platform & Geo-telematics Engineering",
    },
    "driver_vehicle": {
        "label": "Driver Behavior and Vehicle Experience",
        "description": "Rude behavior, rash driving, refusing rides, vehicle AC or cleanliness, route deviation.",
        "default_effort": "Low", # Operational vendor management rather than core app code
        "suggested_owner": "Fleet Operations & Vendor Quality Team",
    },
    "safety_verification": {
        "label": "Safety and Verification",
        "description": "SOS button issues, female employee drop-off security confirmation, escort guard, OTP ride start verification.",
        "default_effort": "Medium",
        "suggested_owner": "Safety Systems & Incident Escalation Engineering",
    },
    "notifications_checkin": {
        "label": "Notifications and Check-In",
        "description": "Missed push notifications, boarding check-in QR / beacon failure, ride cancellation alerts not received.",
        "default_effort": "Low",
        "suggested_owner": "Mobile Client Team / Notification Pipeline",
    },
    "app_performance": {
        "label": "App Crash, Performance, and Usability",
        "description": "App crashing on launch, battery drain, unresponsive UI screens, slow rendering, phone overheating.",
        "default_effort": "Medium",
        "suggested_owner": "Android Core Experience / Mobile QA",
    },
    "customer_support": {
        "label": "Customer Support and Issue Resolution",
        "description": "Unresponsive helpdesk, automated responses without resolution, unaddressed complaints, ticket closures.",
        "default_effort": "Low",
        "suggested_owner": "Customer Support Operations & Ticketing Integration",
    },
    "other": {
        "label": "Other or Unclassified",
        "description": "General feedback, corporate office comments, policy queries, or ambiguous feedback.",
        "default_effort": "Low",
        "suggested_owner": "Product Research & UX",
    },
}

# Priority Engine Scoring Weights (Must sum to 1.0)
PRIORITY_WEIGHTS = {
    "frequency": 0.30,      # Share of negative sentiment complaints
    "severity": 0.25,       # Severity impact (Critical/High/Med/Low)
    "trend": 0.20,          # Recent trajectory / momentum
    "confidence": 0.15,     # Statistical sample size & classifier confidence
    "effort_inverse": 0.10, # Ease of implementation (Low effort gets bonus)
}

# Severity numeric weights
SEVERITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.50,
    "low": 0.25,
}

# Effort penalty / score factor
EFFORT_SCORES = {
    "Low": 1.0,       # Quick win
    "Medium": 0.65,   # Moderate engineering investment
    "High": 0.30,     # Multi-sprint or architectural shift
}

# Category severity keywords (Used for deterministic severity assessment)
CRITICAL_KEYWORDS = [
    "safety", "emergency", "danger", "sos", "harass", "accident", "unsafe", 
    "threat", "scared", "police", "illegal", "left stranded", "alone at night"
]

HIGH_SEVERITY_KEYWORDS = [
    "crash", "freeze", "fail", "missed cab", "missed ride", "not working", "unable to login", 
    "stranded", "stuck", "late to office", "escalate", "uninstalled", "pathetic", "worst app",
    "otp never", "cannot book", "fake location"
]

MEDIUM_SEVERITY_KEYWORDS = [
    "delay", "slow", "wrong eta", "bug", "glitch", "notification late", "ui bad", 
    "driver rude", "ac not working", "confusing", "support no response"
]

# Priority Label Thresholds
PRIORITY_THRESHOLDS = {
    "P0": {"min_score": 0.75, "min_count": 3},
    "P1": {"min_score": 0.55, "min_count": 2},
    "P2": {"min_score": 0.35, "min_count": 1},
    "P3": {"min_score": 0.00, "min_count": 0},
}
