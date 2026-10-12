"""
Shared test fixtures for MoveInSync Review Intelligence unit tests.
"""

import pytest
import pandas as pd


@pytest.fixture
def sample_reviews_df():
    """
    Returns a small, rich test DataFrame covering various categories and ratings.
    """
    return pd.DataFrame([
        {
            "id": "T001",
            "user_name": "Test User 1",
            "score": 1,
            "text": "App crashed when clicking SOS button during late night drop. Very unsafe!",
            "date": "2026-03-25 22:00:00",
            "version": "12.4.1",
            "thumbs_up": 10,
            "reply_text": None,
            "reply_date": None,
            "data_type": "sample"
        },
        {
            "id": "T002",
            "user_name": "Test User 2",
            "score": 1,
            "text": "Driver started ride without OTP verification while I was not even in the cab.",
            "date": "2026-03-24 18:30:00",
            "version": "12.4.0",
            "thumbs_up": 5,
            "reply_text": None,
            "reply_date": None,
            "data_type": "sample"
        },
        {
            "id": "T003",
            "user_name": "Test User 3",
            "score": 1,
            "text": "Live tracking GPS map is completely frozen and vehicle marker jumps around.",
            "date": "2026-03-23 09:15:00",
            "version": "12.3.9",
            "thumbs_up": 8,
            "reply_text": None,
            "reply_date": None,
            "data_type": "sample"
        },
        {
            "id": "T004",
            "user_name": "Test User 4",
            "score": 2,
            "text": "Cannot login. SMS OTP arrives 20 minutes late after session is expired.",
            "date": "2026-03-22 08:00:00",
            "version": "12.3.8",
            "thumbs_up": 12,
            "reply_text": None,
            "reply_date": None,
            "data_type": "sample"
        },
        {
            "id": "T005",
            "user_name": "Test User 5",
            "score": 5,
            "text": "Excellent corporate transport app. Clean cabs and timely pickup alerts.",
            "date": "2026-03-21 07:45:00",
            "version": "12.3.7",
            "thumbs_up": 2,
            "reply_text": None,
            "reply_date": None,
            "data_type": "sample"
        },
    ])


@pytest.fixture
def empty_df():
    """Returns an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def malformed_df():
    """
    Returns a DataFrame with invalid scores, missing texts, and corrupt dates.
    """
    return pd.DataFrame([
        {"id": "M1", "user_name": "Bad Rating", "score": 99, "text": "Valid text", "date": "invalid_date"},
        {"id": "M2", "user_name": "Negative Score", "score": -1, "text": "Some text", "date": "2026-01-01"},
        {"id": "M3", "user_name": "Missing Text", "score": 1, "text": None, "date": "2026-01-01"},
        {"id": "M4", "user_name": "Valid Row", "score": 3, "text": "Normal text", "date": "2026-01-01 10:00:00"},
    ])
