"""
Unit tests for ReviewClassifier.
Tests regex multi-label classification, safety triggers, and fallback handling.
"""

import pytest
from src.review_classifier import ReviewClassifier


def test_safety_classification():
    clf = ReviewClassifier()
    res = clf.classify_review(
        text="App crashed when clicking SOS button during late night drop. Very unsafe!",
        score=1
    )
    assert "safety_verification" in res["categories"] or "app_performance" in res["categories"]
    assert res["severity"] == "critical"


def test_gps_tracking_classification():
    clf = ReviewClassifier()
    res = clf.classify_review(
        text="Live tracking map shows vehicle stationary 5km away, but driver calls saying he is at gate.",
        score=1
    )
    assert "gps_tracking" in res["categories"]


def test_login_otp_classification():
    clf = ReviewClassifier()
    res = clf.classify_review(
        text="Cannot login after latest update. OTP SMS arrives after 15 minutes by which time the session expires.",
        score=2
    )
    assert "login_otp_auth" in res["categories"]


def test_unclassified_fallback():
    clf = ReviewClassifier()
    res = clf.classify_review(
        text="Random string xyz completely unrelated to transit.",
        score=3
    )
    assert "other" in res["categories"]
    assert res["classification_method"] == "rule_based_fallback"
