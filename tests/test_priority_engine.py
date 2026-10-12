"""
Unit tests for PriorityEngine.
Tests multi-attribute weighting, P0/P1/P2/P3 thresholds, and safety escalation overrides.
"""

import pytest
import pandas as pd
from src.priority_engine import PriorityEngine


def test_priority_calculation(sample_reviews_df):
    engine = PriorityEngine()
    
    # Enrich sample reviews with category and severity
    df = sample_reviews_df.copy()
    df["primary_category"] = [
        "safety_verification",
        "safety_verification",
        "gps_tracking",
        "login_otp_auth",
        "booking_reservation"
    ]
    df["severity"] = ["critical", "high", "high", "medium", "low"]
    df["confidence"] = [0.9, 0.85, 0.8, 0.8, 0.9]

    p_df = engine.calculate_category_metrics(df)
    assert not p_df.empty
    
    # Safety should be ranked P0 due to critical flag & safety category
    safety_row = p_df[p_df["category"] == "safety_verification"].iloc[0]
    assert safety_row["priority_label"] == "P0"
    assert bool(safety_row["has_safety_flag"]) is True


def test_empty_dataframe_priority(empty_df):
    engine = PriorityEngine()
    p_df = engine.calculate_category_metrics(empty_df)
    assert p_df.empty
