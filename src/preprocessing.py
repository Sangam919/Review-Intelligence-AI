"""
Preprocessing and data quality assurance module.
Handles text normalization, rating validation, deduplication, missing values, and date parsing.
"""

import re
import hashlib
import unicodedata
from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np


class ReviewPreprocessor:
    """
    Robust data cleaning and provenance pipeline for app reviews.
    Preserves meaningful review content while normalizing structural defects.
    """

    def __init__(self):
        pass

    def clean_text_for_display(self, text: Any) -> str:
        """
        Clean text for safe display without stripping semantic context.
        """
        if pd.isna(text) or text is None:
            return ""
        
        text = str(text)
        # Normalize unicode (NFKC to keep standard glyphs)
        text = unicodedata.normalize("NFKC", text)
        # Clean control characters except line feeds/tabs
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Collapse excessive whitespace
        text = re.sub(r"[ \t]+", " ", text).strip()
        return text

    def clean_text_for_matching(self, text: Any) -> str:
        """
        Normalize text specifically for classification keyword matching.
        """
        cleaned = self.clean_text_for_display(text).lower()
        # Remove URLs
        cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)
        # Remove standalone punctuation but retain alphanumerics and basic contractions
        cleaned = re.sub(r"[^\w\s\-\']", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def validate_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure score is integer in [1, 5]. Flag or clean invalid rows.
        """
        df = df.copy()
        if "score" not in df.columns:
            df["score"] = np.nan
            return df
        
        # Coerce to numeric
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        # Identify invalid scores
        invalid_mask = df["score"].isna() | (df["score"] < 1) | (df["score"] > 5)
        # Flag and drop or clamp
        df["is_valid_score"] = ~invalid_mask
        # For pipeline continuity, filter out rows without a valid score
        df = df[df["is_valid_score"]].copy()
        df["score"] = df["score"].astype(int)
        return df

    def parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse review dates reliably with timezone awareness.
        """
        df = df.copy()
        if "date" not in df.columns:
            df["date"] = pd.Timestamp.now(tz="UTC")
            df["has_date"] = False
            return df

        # Parse with flexible format guessing and coerce invalid
        parsed_dates = pd.to_datetime(df["date"], errors="coerce")
        df["has_date"] = ~parsed_dates.isna()
        
        # Fill missing dates with modern fallback or NaT
        df["parsed_date"] = parsed_dates
        # Standardize date string representation
        df["date_str"] = df["parsed_date"].dt.strftime("%Y-%m-%d %H:%M")
        return df

    def compute_fingerprint(self, row: pd.Series) -> str:
        """
        Computes a stable deterministic fingerprint for deduplication.
        Combines score, normalized text, and approximate date if available.
        """
        text_part = self.clean_text_for_matching(row.get("text", ""))
        score_part = str(row.get("score", ""))
        date_part = str(row.get("date", ""))[:10] # Date slice
        user_part = str(row.get("user_name", "")).strip().lower()

        combined = f"{score_part}|{user_part}|{date_part}|{text_part}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def deduplicate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Deduplicates reviews based on 'id' if present, or stable content fingerprint.
        Returns cleaned DataFrame and number of duplicates removed.
        """
        df = df.copy()
        initial_len = len(df)
        if initial_len == 0:
            return df, 0

        # Step 1: Dedup by non-null 'id' if present
        if "id" in df.columns:
            # Only apply id-dedup where id is non-empty string
            has_id_mask = df["id"].notna() & (df["id"].astype(str).str.strip() != "")
            df_with_id = df[has_id_mask].drop_duplicates(subset=["id"], keep="first")
            df_no_id = df[~has_id_mask]
            df = pd.concat([df_with_id, df_no_id], ignore_index=True)

        # Step 2: Content-based fingerprint dedup
        df["_fingerprint"] = df.apply(self.compute_fingerprint, axis=1)
        df_dedup = df.drop_duplicates(subset=["_fingerprint"], keep="first").copy()
        df_dedup.drop(columns=["_fingerprint"], inplace=True)

        duplicates_removed = initial_len - len(df_dedup)
        return df_dedup, duplicates_removed

    def process(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes end-to-end preprocessing pipeline.
        Returns:
            processed_df: Cleaned and normalized DataFrame
            quality_metrics: Quality report dictionary
        """
        if df is None or df.empty:
            return pd.DataFrame(), {
                "initial_count": 0,
                "final_count": 0,
                "duplicates_removed": 0,
                "missing_text_count": 0,
                "missing_date_count": 0,
                "invalid_ratings_dropped": 0,
                "data_provenance": "empty",
            }

        initial_count = len(df)

        # Ensure baseline schema exists
        expected_cols = ["id", "user_name", "score", "text", "date", "version", "thumbs_up", "reply_text", "reply_date", "data_type"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None

        # 1. Rating validation
        validated_df = self.validate_ratings(df)
        invalid_ratings_dropped = initial_count - len(validated_df)

        # 2. Text normalization
        validated_df["display_text"] = validated_df["text"].apply(self.clean_text_for_display)
        validated_df["match_text"] = validated_df["text"].apply(self.clean_text_for_matching)
        validated_df["has_text"] = validated_df["display_text"].str.len() > 0

        missing_text_count = int((~validated_df["has_text"]).sum())

        # 3. Date parsing
        date_parsed_df = self.parse_dates(validated_df)
        missing_date_count = int((~date_parsed_df["has_date"]).sum())

        # 4. Deduplication
        deduped_df, duplicates_removed = self.deduplicate(date_parsed_df)

        # 5. Provenance tracking
        if "data_type" not in deduped_df.columns or deduped_df["data_type"].isna().all():
            deduped_df["data_type"] = "imported"

        data_provenance = deduped_df["data_type"].iloc[0] if not deduped_df.empty else "unknown"

        quality_metrics = {
            "initial_count": initial_count,
            "final_count": len(deduped_df),
            "duplicates_removed": duplicates_removed,
            "missing_text_count": missing_text_count,
            "missing_date_count": missing_date_count,
            "invalid_ratings_dropped": invalid_ratings_dropped,
            "data_provenance": data_provenance,
        }

        return deduped_df, quality_metrics
