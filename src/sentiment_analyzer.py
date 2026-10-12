"""
Sentiment Analyzer Module.
Combines star rating polarity, lexical sentiment scoring, and amplifier detection.
Treats sentiment as an analytical estimate, not absolute ground truth.
"""

from typing import Dict, Any, Tuple
import pandas as pd


class SentimentAnalyzer:
    """
    Hybrid sentiment evaluator combining explicit star ratings with textual sentiment polarity.
    Ensures ratings (user's explicit ground-truth evaluation) anchor the score,
    while text nuance modulates borderline cases.
    """

    POSITIVE_WORDS = {
        "good", "great", "excellent", "best", "smooth", "helpful", "friendly", "prompt",
        "punctual", "on time", "love", "awesome", "perfect", "seamless", "safe", "reliable",
        "superb", "satisfying", "convenient", "thank", "thanks", "appreciate"
    }

    NEGATIVE_WORDS = {
        "bad", "worst", "terrible", "horrible", "pathetic", "useless", "waste", "poor",
        "disgusting", "disaster", "hate", "uninstalled", "slow", "broken", "freeze", "crash",
        "fail", "failed", "unsafe", "rude", "abusive", "harass", "scam", "cheat", "cheat",
        "delay", "stuck", "frustrat", "annoy", "anger", "regret"
    }

    def __init__(self):
        # Optional TextBlob import if installed
        self.has_textblob = False
        try:
            from textblob import TextBlob
            self._textblob = TextBlob
            self.has_textblob = True
        except ImportError:
            self._textblob = None

    def compute_lexical_score(self, text: str) -> float:
        """
        Computes text sentiment polarity score in range [-1.0, 1.0].
        Uses TextBlob if available, otherwise fast deterministic keyword scoring.
        """
        if not text or not isinstance(text, str):
            return 0.0

        if self.has_textblob:
            try:
                blob = self._textblob(text)
                return float(blob.sentiment.polarity)
            except Exception:
                pass

        # Fallback deterministic keyword polarity
        text_lower = text.lower()
        pos_hits = sum(1 for w in self.POSITIVE_WORDS if w in text_lower)
        neg_hits = sum(1 for w in self.NEGATIVE_WORDS if w in text_lower)

        total_hits = pos_hits + neg_hits
        if total_hits == 0:
            return 0.0

        return (pos_hits - neg_hits) / total_hits

    def evaluate_sentiment(self, score: int, text: str) -> Tuple[str, float]:
        """
        Combines star rating with textual score.
        Star Rating:
          1 -> -0.9
          2 -> -0.5
          3 -> 0.0
          4 -> 0.5
          5 -> 0.9
        Rating weight: 0.75, Text polarity weight: 0.25
        """
        rating_map = {1: -0.9, 2: -0.5, 3: 0.0, 4: 0.5, 5: 0.9}
        rating_signal = rating_map.get(score, 0.0)
        text_signal = self.compute_lexical_score(text)

        # Weighted combination
        if text.strip():
            combined_score = (0.75 * rating_signal) + (0.25 * text_signal)
        else:
            combined_score = rating_signal

        combined_score = max(-1.0, min(1.0, round(combined_score, 2)))

        # Categorize label
        if combined_score <= -0.25:
            label = "negative"
        elif combined_score >= 0.25:
            label = "positive"
        else:
            label = "neutral"

        return label, combined_score

    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches review dataframe with 'sentiment_label' and 'sentiment_score'.
        """
        if df.empty:
            return df

        df = df.copy()
        labels = []
        scores = []

        for _, row in df.iterrows():
            star = int(row.get("score", 3)) if pd.notna(row.get("score")) else 3
            text = str(row.get("match_text", row.get("text", "")))
            label, val = self.evaluate_sentiment(star, text)
            labels.append(label)
            scores.append(val)

        df["sentiment_label"] = labels
        df["sentiment_score"] = scores
        return df

    def get_sentiment_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates aggregate sentiment distribution.
        """
        if df.empty or "sentiment_label" not in df.columns:
            return {
                "positive": 0, "neutral": 0, "negative": 0,
                "positive_pct": 0.0, "neutral_pct": 0.0, "negative_pct": 0.0,
                "average_sentiment_score": 0.0
            }

        total = len(df)
        counts = df["sentiment_label"].value_counts().to_dict()
        pos = counts.get("positive", 0)
        neu = counts.get("neutral", 0)
        neg = counts.get("negative", 0)

        avg_score = round(float(df["sentiment_score"].mean()), 2) if "sentiment_score" in df.columns else 0.0

        return {
            "positive": pos,
            "neutral": neu,
            "negative": neg,
            "positive_pct": round((pos / total) * 100, 1),
            "neutral_pct": round((neu / total) * 100, 1),
            "negative_pct": round((neg / total) * 100, 1),
            "average_sentiment_score": avg_score,
        }
