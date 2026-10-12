"""
Pipeline execution orchestrator for MoveInSync Review Intelligence.
Shared between app.py and child page modules to prevent circular imports.
"""

from typing import Tuple, Dict, Any
import pandas as pd
from src.preprocessing import ReviewPreprocessor
from src.review_classifier import ReviewClassifier
from src.sentiment_analyzer import SentimentAnalyzer


def execute_pipeline(
    raw_df: pd.DataFrame,
    use_ai: bool = False,
    category_overrides: Dict[str, str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes end-to-end data processing:
    1. Preprocessing (validation, deduplication, normalization)
    2. Multi-label classification (rule-based + optional OpenAI)
    3. Category override application
    4. Sentiment analysis
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(), {}

    overrides = category_overrides or {}

    # 1. Preprocessing
    prep = ReviewPreprocessor()
    clean_df, quality_metrics = prep.process(raw_df)

    if clean_df.empty:
        return pd.DataFrame(), quality_metrics

    # 2. Classification
    classifier = ReviewClassifier()
    classified_df = classifier.classify_dataframe(clean_df, use_ai=use_ai)

    # 3. Apply manual overrides
    for rev_id, new_cat in overrides.items():
        mask = classified_df["id"] == rev_id
        if mask.any():
            classified_df.loc[mask, "primary_category"] = new_cat

    # 4. Sentiment Analysis
    sentiment_analyzer = SentimentAnalyzer()
    enriched_df = sentiment_analyzer.analyze_dataframe(classified_df)

    return enriched_df, quality_metrics
