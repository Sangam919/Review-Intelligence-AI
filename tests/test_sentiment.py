"""
Unit tests for SentimentAnalyzer.
Tests star rating polarity, text modulation, and aggregate distribution metrics.
"""

import pytest
from src.sentiment_analyzer import SentimentAnalyzer


def test_rating_sentiment_polarity():
    analyzer = SentimentAnalyzer()
    
    # 1 star with negative text
    lbl1, score1 = analyzer.evaluate_sentiment(1, "Worst app ever, total waste.")
    assert lbl1 == "negative"
    assert score1 <= -0.5

    # 5 star with positive text
    lbl5, score5 = analyzer.evaluate_sentiment(5, "Excellent service, very smooth and reliable.")
    assert lbl5 == "positive"
    assert score5 >= 0.5

    # 3 star neutral
    lbl3, score3 = analyzer.evaluate_sentiment(3, "Average ride, nothing special.")
    assert lbl3 == "neutral"


def test_sentiment_dataframe(sample_reviews_df):
    analyzer = SentimentAnalyzer()
    enriched = analyzer.analyze_dataframe(sample_reviews_df)
    
    assert "sentiment_label" in enriched.columns
    assert "sentiment_score" in enriched.columns
    
    summary = analyzer.get_sentiment_summary(enriched)
    assert summary["positive"] + summary["neutral"] + summary["negative"] == len(sample_reviews_df)
