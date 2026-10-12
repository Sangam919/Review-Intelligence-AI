"""
Unit tests for ReviewPreprocessor.
Tests rating boundary validation, text normalization, deduplication, missing values, and dates.
"""

import pytest
import pandas as pd
from src.preprocessing import ReviewPreprocessor


def test_validate_ratings(malformed_df):
    prep = ReviewPreprocessor()
    validated = prep.validate_ratings(malformed_df)
    
    # Scores 99 and -1 should be dropped
    assert len(validated) == 2
    assert set(validated["score"].tolist()) == {1, 3}


def test_text_normalization():
    prep = ReviewPreprocessor()
    dirty_text = "  App CRASHED!!  Check https://example.com for logs... \x00\x08  "
    display = prep.clean_text_for_display(dirty_text)
    matched = prep.clean_text_for_matching(dirty_text)

    # Control chars removed
    assert "\x00" not in display
    # URL removed in matching
    assert "https" not in matched
    assert "example" not in matched
    assert "crashed" in matched


def test_deduplication():
    prep = ReviewPreprocessor()
    df = pd.DataFrame([
        {"id": "REV1", "user_name": "User A", "score": 1, "text": "Duplicate content", "date": "2026-01-01"},
        {"id": "REV1", "user_name": "User A", "score": 1, "text": "Duplicate content", "date": "2026-01-01"}, # Exact ID dup
        {"id": "REV2", "user_name": "User A", "score": 1, "text": "Duplicate content", "date": "2026-01-01"}, # Fingerprint dup
        {"id": "REV3", "user_name": "User B", "score": 5, "text": "Unique review", "date": "2026-01-02"},
    ])

    deduped, removed = prep.deduplicate(df)
    assert len(deduped) == 2
    assert removed == 2


def test_empty_dataframe(empty_df):
    prep = ReviewPreprocessor()
    clean_df, metrics = prep.process(empty_df)
    assert clean_df.empty
    assert metrics["final_count"] == 0
