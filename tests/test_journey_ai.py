"""
Unit tests for CommuteJourneyAnalyzer and AIAssistant.
Validates 9-stage friction calculation and structured AI response fallback mechanisms.
"""

import pytest
import pandas as pd
from src.commute_journey import CommuteJourneyAnalyzer, JOURNEY_STAGES
from src.ai_assistant import AIAssistant


def test_commute_journey_analyzer(sample_reviews_df):
    analyzer = CommuteJourneyAnalyzer()
    
    df = sample_reviews_df.copy()
    df["primary_category"] = [
        "safety_verification",
        "safety_verification",
        "gps_tracking",
        "login_otp_auth",
        "booking_reservation"
    ]
    df["display_text"] = df["text"]
    
    stages = analyzer.analyze_journey(df)
    assert len(stages) == len(JOURNEY_STAGES)
    
    # Check that safety stage captured safety reviews
    safety_stage = next(s for s in stages if s["stage_key"] == "otp_safety_verification")
    assert safety_stage["review_count"] == 2
    assert safety_stage["negative_count"] == 2
    assert safety_stage["friction_index"] > 0
    assert len(safety_stage["internal_telemetry_required"]) >= 2


def test_ai_assistant_fallback():
    assistant = AIAssistant()
    profile = {
        "total_reviews": 50,
        "avg_rating": 2.1,
        "negative_rating_share": 65.0,
        "is_demo_data": True
    }
    top_issues = [
        {"category_label": "Safety and Verification", "priority_label": "P0"}
    ]
    
    brief = assistant.generate_executive_brief(profile, top_issues)
    assert "summary" in brief
    assert "core_findings" in brief
    assert len(brief["core_findings"]) == 3
    assert "critical_risks" in brief
    assert "recommended_next_step" in brief


def test_ai_assistant_review_query(sample_reviews_df):
    assistant = AIAssistant()
    df = sample_reviews_df.copy()
    df["display_text"] = df["text"]
    
    res = assistant.answer_review_query("crashed", df)
    assert "answer" in res
    assert "evidence_summary" in res
    assert len(res["evidence_quotes"]) >= 1
