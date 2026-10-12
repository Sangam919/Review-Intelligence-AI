"""
Public Play Store review collection module for MoveInSync ETS (com.moveinsync.ets).
Fetches reviews with pagination, handles network faults, captures rich metadata,
and preserves audit provenance.
"""

import time
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from config import DEFAULT_APP_ID, DEFAULT_COUNTRY, DEFAULT_LANGUAGE


class ReviewCollector:
    """
    Public Play Store review scraper using google-play-scraper.
    Fetches real customer reviews, tracks collection errors,
    and returns a normalized DataFrame.
    """

    def __init__(
        self,
        app_id: str = DEFAULT_APP_ID,
        country: str = DEFAULT_COUNTRY,
        language: str = DEFAULT_LANGUAGE
    ):
        self.app_id = app_id
        self.country = country
        self.language = language
        self.errors: List[str] = []

    def fetch_app_details(self) -> Dict[str, Any]:
        """
        Fetches official store metadata (title, aggregate score, total reviews, version).
        """
        try:
            from google_play_scraper import app
            info = app(
                self.app_id,
                lang=self.language,
                country=self.country
            )
            return {
                "title": info.get("title", "MoveInSync"),
                "score": round(info.get("score", 0.0), 2),
                "ratings_count": info.get("ratings", 0),
                "reviews_count": info.get("reviews", 0),
                "version": info.get("version", "Varies with device"),
                "installs": info.get("installs", "N/A"),
                "genre": info.get("genre", "Business"),
                "status": "success",
            }
        except Exception as e:
            self.errors.append(f"App details fetch error: {str(e)}")
            return {
                "title": "MoveInSync",
                "score": 0.0,
                "ratings_count": 0,
                "reviews_count": 0,
                "version": "N/A",
                "installs": "N/A",
                "genre": "Transportation",
                "status": "failed",
                "error": str(e)
            }

    def collect_reviews(
        self,
        count: int = 150,
        sort_order: str = "newest"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Fetches reviews with pagination and rate-limit backoff.
        Parameters:
            count: Target number of reviews (default 150)
            sort_order: 'newest' or 'most_relevant'
        Returns:
            (reviews_df, collection_metadata)
        """
        self.errors.clear()
        collected_raw = []
        continuation_token = None
        timestamp_now = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            from google_play_scraper import reviews, Sort
            sort_enum = Sort.NEWEST if sort_order.lower() == "newest" else Sort.MOST_RELEVANT

            # Calculate pages needed (each batch max 100)
            remaining = count
            while remaining > 0:
                batch_size = min(100, remaining)
                try:
                    batch_reviews, continuation_token = reviews(
                        self.app_id,
                        lang=self.language,
                        country=self.country,
                        sort=sort_enum,
                        count=batch_size,
                        continuation_token=continuation_token
                    )
                except Exception as batch_err:
                    self.errors.append(f"Network / Play Store API error: {str(batch_err)}")
                    break

                if not batch_reviews:
                    break

                collected_raw.extend(batch_reviews)
                remaining -= len(batch_reviews)

                if not continuation_token or len(batch_reviews) < batch_size:
                    break

                # Polite pause to avoid rate limiting
                time.sleep(1.0)

        except ImportError:
            self.errors.append("google-play-scraper library is not installed in the active environment.")
        except Exception as e:
            self.errors.append(f"Unhandled collection failure: {str(e)}")

        # Convert to standardized DataFrame
        records = []
        for r in collected_raw:
            records.append({
                "id": str(r.get("reviewId", "")),
                "user_name": str(r.get("userName", "Anonymous")),
                "score": int(r.get("score", 0)),
                "text": str(r.get("content", "")),
                "date": str(r.get("at", "")),
                "version": str(r.get("reviewCreatedVersion", "")),
                "thumbs_up": int(r.get("thumbsUpCount", 0)),
                "reply_text": str(r.get("replyContent", "")) if r.get("replyContent") else None,
                "reply_date": str(r.get("repliedAt", "")) if r.get("repliedAt") else None,
                "data_type": "collected",
                "collection_source": "google_play_store",
                "collection_timestamp": timestamp_now,
            })

        df = pd.DataFrame(records)

        metadata = {
            "requested_count": count,
            "collected_count": len(df),
            "app_id": self.app_id,
            "country": self.country,
            "language": self.language,
            "sort_order": sort_order,
            "timestamp": timestamp_now,
            "errors": self.errors.copy(),
            "status": "success" if len(df) > 0 else ("failed" if self.errors else "empty"),
        }

        return df, metadata
