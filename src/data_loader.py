"""
Data loader and persistence manager for MoveInSync Review Intelligence.
Supports CSV ingestion, SQLite storage, sample data loading, and formatted data exports.
"""

import io
import sqlite3
from pathlib import Path
from typing import Dict, Any, Union, Optional
import pandas as pd
from config import DATA_DIR, DEFAULT_DB_PATH


class DataLoader:
    """
    Manages review data ingestion, validation, persistence, and exports.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def load_csv(self, file_source: Union[str, Path, io.BytesIO]) -> pd.DataFrame:
        """
        Loads reviews from a CSV file path or file buffer (e.g., Streamlit uploader).
        Marks data_type as 'imported'.
        """
        try:
            df = pd.read_csv(file_source)
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {str(e)}")

        if "data_type" not in df.columns or df["data_type"].isna().all():
            df["data_type"] = "imported"
        
        return df

    def load_sample_data(self) -> pd.DataFrame:
        """
        Loads the pre-packaged sample dataset.
        Always flags reviews with data_type='sample'.
        """
        sample_path = DATA_DIR / "sample_reviews.csv"
        if not sample_path.exists():
            raise FileNotFoundError(f"Sample data file missing at: {sample_path}")

        df = pd.read_csv(sample_path)
        df["data_type"] = "sample"
        return df

    def init_sqlite_db(self):
        """
        Creates SQLite schema if not already initialized.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                user_name TEXT,
                score INTEGER,
                text TEXT,
                date TEXT,
                version TEXT,
                thumbs_up INTEGER,
                reply_text TEXT,
                reply_date TEXT,
                data_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def save_to_sqlite(self, df: pd.DataFrame, table: str = "reviews") -> int:
        """
        Upserts reviews into local SQLite database.
        Returns number of records saved/updated.
        """
        if df.empty:
            return 0

        self.init_sqlite_db()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for _, row in df.iterrows():
            review_id = str(row.get("id", "")) if pd.notna(row.get("id")) else None
            if not review_id:
                # Generate unique ID if absent
                review_id = f"ROW_{saved_count}_{int(pd.Timestamp.now().timestamp())}"

            cursor.execute(
                f"""
                INSERT INTO {table} (id, user_name, score, text, date, version, thumbs_up, reply_text, reply_date, data_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_name=excluded.user_name,
                    score=excluded.score,
                    text=excluded.text,
                    date=excluded.date,
                    version=excluded.version,
                    thumbs_up=excluded.thumbs_up,
                    reply_text=excluded.reply_text,
                    reply_date=excluded.reply_date,
                    data_type=excluded.data_type
                """,
                (
                    review_id,
                    str(row.get("user_name", "")),
                    int(row.get("score", 0)) if pd.notna(row.get("score")) else None,
                    str(row.get("text", "")),
                    str(row.get("date", "")),
                    str(row.get("version", "")),
                    int(row.get("thumbs_up", 0)) if pd.notna(row.get("thumbs_up")) else 0,
                    str(row.get("reply_text", "")),
                    str(row.get("reply_date", "")),
                    str(row.get("data_type", "collected")),
                ),
            )
            saved_count += 1

        conn.commit()
        conn.close()
        return saved_count

    def load_from_sqlite(self, table: str = "reviews") -> pd.DataFrame:
        """
        Loads all stored reviews from SQLite.
        """
        if not Path(self.db_path).exists():
            return pd.DataFrame()

        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        except Exception:
            df = pd.DataFrame()
        finally:
            conn.close()

        return df

    def export_csv_bytes(self, df: pd.DataFrame) -> bytes:
        """
        Serializes DataFrame to UTF-8 CSV bytes suitable for download buttons.
        """
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8")

    def get_dataset_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extracts provenance, date range, null ratios, and data verification state.
        """
        if df.empty:
            return {
                "total_reviews": 0,
                "is_empty": True,
                "data_type": "none",
                "is_demo_data": False,
                "date_min": "N/A",
                "date_max": "N/A",
                "avg_rating": 0.0,
                "negative_rating_share": 0.0,
            }

        total = len(df)
        data_type = df["data_type"].iloc[0] if "data_type" in df.columns else "unknown"
        is_demo = bool((data_type == "sample") or ("SAMPLE_" in str(df["id"].iloc[0])))

        avg_score = round(float(df["score"].mean()), 2) if "score" in df.columns and not df["score"].isna().all() else 0.0
        neg_count = int((df["score"] <= 2).sum()) if "score" in df.columns else 0
        neg_share = round((neg_count / total) * 100, 1) if total > 0 else 0.0

        # Date range
        date_col = "parsed_date" if "parsed_date" in df.columns else "date"
        try:
            dt_series = pd.to_datetime(df[date_col], errors="coerce").dropna()
            date_min = dt_series.min().strftime("%Y-%m-%d") if not dt_series.empty else "N/A"
            date_max = dt_series.max().strftime("%Y-%m-%d") if not dt_series.empty else "N/A"
        except Exception:
            date_min = "N/A"
            date_max = "N/A"

        return {
            "total_reviews": total,
            "is_empty": False,
            "data_type": data_type,
            "is_demo_data": is_demo,
            "date_min": date_min,
            "date_max": date_max,
            "avg_rating": avg_score,
            "negative_rating_share": neg_share,
        }
