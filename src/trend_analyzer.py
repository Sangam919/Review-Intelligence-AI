"""
Trend Analyzer Module.
Performs time-series aggregation, week-over-week velocity calculation, and emerging issue alerts.
Ensures sample size sufficiency safeguards to prevent spurious volatility warnings.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class TrendAnalyzer:
    """
    Analyzes temporal patterns, complaint acceleration rates, and newly surging defect categories.
    """

    def __init__(self, min_sample_for_trend: int = 10):
        self.min_sample_for_trend = min_sample_for_trend

    def prepare_timeseries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validates and standardizes parsed datetime column for rolling aggregations.
        """
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        date_col = "parsed_date" if "parsed_date" in df.columns else "date"
        df["ts"] = pd.to_datetime(df[date_col], errors="coerce")
        df = df[df["ts"].notna()].sort_values("ts")
        return df

    def compute_volume_and_rating_trend(self, df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
        """
        Aggregates review volume and average star rating over calendar intervals (Weekly 'W', Monthly 'M').
        """
        df_ts = self.prepare_timeseries(df)
        if df_ts.empty:
            return pd.DataFrame(columns=["period", "review_count", "avg_rating", "negative_count", "negative_pct"])

        # Resample by period
        df_ts.set_index("ts", inplace=True)
        resampled = df_ts.resample(freq)

        stats = []
        for period, group in resampled:
            count = len(group)
            if count == 0:
                continue
            
            avg_score = round(float(group["score"].mean()), 2)
            neg_count = int((group["score"] <= 2).sum())
            neg_pct = round((neg_count / count) * 100, 1)

            stats.append({
                "period": period.strftime("%Y-%m-%d"),
                "review_count": count,
                "avg_rating": avg_score,
                "negative_count": neg_count,
                "negative_pct": neg_pct,
            })

        return pd.DataFrame(stats)

    def compute_category_trends(self, df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
        """
        Computes review frequency per primary category over time.
        """
        df_ts = self.prepare_timeseries(df)
        if df_ts.empty or "primary_category" not in df_ts.columns:
            return pd.DataFrame()

        df_ts["period"] = df_ts["ts"].dt.to_period(freq).astype(str)
        pivot = pd.crosstab(df_ts["period"], df_ts["primary_category"]).reset_index()
        return pivot

    def detect_emerging_issues(self, df: pd.DataFrame, lookback_days: int = 45) -> List[Dict[str, Any]]:
        """
        Identifies complaint categories experiencing statistical acceleration.
        Splits data into 'recent' (last N days) vs 'baseline' (prior period).
        Emerging trigger: Recent share >= 1.4x baseline share with minimum volume threshold.
        """
        df_ts = self.prepare_timeseries(df)
        if len(df_ts) < self.min_sample_for_trend:
            return []

        max_date = df_ts["ts"].max()
        cutoff_date = max_date - pd.Timedelta(days=lookback_days)

        recent_df = df_ts[df_ts["ts"] >= cutoff_date]
        baseline_df = df_ts[df_ts["ts"] < cutoff_date]

        if len(recent_df) < 5 or len(baseline_df) < 5:
            return []

        recent_total = len(recent_df)
        baseline_total = len(baseline_df)

        emerging = []
        recent_counts = recent_df["primary_category"].value_counts()
        baseline_counts = baseline_df["primary_category"].value_counts()

        for cat, rec_cnt in recent_counts.items():
            if cat == "other":
                continue
            
            rec_share = rec_cnt / recent_total
            base_cnt = baseline_counts.get(cat, 0)
            base_share = (base_cnt / baseline_total) if baseline_total > 0 else 0.001

            ratio = rec_share / base_share if base_share > 0 else 2.5

            # Significant surge criteria
            if rec_cnt >= 2 and ratio >= 1.35:
                emerging.append({
                    "category": cat,
                    "recent_count": int(rec_cnt),
                    "baseline_count": int(base_cnt),
                    "recent_share_pct": round(rec_share * 100, 1),
                    "baseline_share_pct": round(base_share * 100, 1),
                    "surge_multiplier": round(ratio, 2),
                    "is_critical_spike": ratio >= 2.0 or ("safety" in cat),
                })

        # Sort by surge multiplier descending
        emerging.sort(key=lambda x: x["surge_multiplier"], reverse=True)
        return emerging

    def compute_period_over_period_kpis(self, df: pd.DataFrame, days_window: int = 30) -> Dict[str, Any]:
        """
        Computes comparative KPIs between the current window and the preceding window.
        """
        df_ts = self.prepare_timeseries(df)
        if len(df_ts) < 10:
            return {
                "sufficient_data": False,
                "note": "Insufficient historical data for period comparison (requires >=10 timestamps)."
            }

        max_date = df_ts["ts"].max()
        current_start = max_date - pd.Timedelta(days=days_window)
        prev_start = current_start - pd.Timedelta(days=days_window)

        current_period = df_ts[(df_ts["ts"] >= current_start) & (df_ts["ts"] <= max_date)]
        prev_period = df_ts[(df_ts["ts"] >= prev_start) & (df_ts["ts"] < current_start)]

        if len(current_period) == 0 or len(prev_period) == 0:
            return {
                "sufficient_data": False,
                "note": f"Not enough reviews spanning both 30-day windows (Current: {len(current_period)}, Prior: {len(prev_period)})."
            }

        curr_avg = current_period["score"].mean()
        prev_avg = prev_period["score"].mean()
        rating_delta = round(curr_avg - prev_avg, 2)

        curr_neg_pct = (current_period["score"] <= 2).mean() * 100
        prev_neg_pct = (prev_period["score"] <= 2).mean() * 100
        neg_pct_delta = round(curr_neg_pct - prev_neg_pct, 1)

        return {
            "sufficient_data": True,
            "current_review_count": len(current_period),
            "prev_review_count": len(prev_period),
            "current_avg_rating": round(curr_avg, 2),
            "prev_avg_rating": round(prev_avg, 2),
            "rating_delta": rating_delta,
            "current_negative_pct": round(curr_neg_pct, 1),
            "prev_negative_pct": round(prev_neg_pct, 1),
            "negative_pct_delta": neg_pct_delta,
        }
