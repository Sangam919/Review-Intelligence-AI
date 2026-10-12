"""
Unit tests for DataLoader.
Tests CSV parsing, sample loading, SQLite round-trip persistence, and dataset profiling.
"""

import pytest
import io
import pandas as pd
from pathlib import Path
from src.data_loader import DataLoader


def test_load_sample_data():
    loader = DataLoader()
    df = loader.load_sample_data()
    assert not df.empty
    assert len(df) == 50
    assert (df["data_type"] == "sample").all()


def test_load_csv_buffer():
    loader = DataLoader()
    csv_text = "id,user_name,score,text,date\nT1,Alice,5,Great service,2026-03-01\nT2,Bob,1,Late cab,2026-03-02\n"
    buffer = io.BytesIO(csv_text.encode("utf-8"))
    
    df = loader.load_csv(buffer)
    assert len(df) == 2
    assert "data_type" in df.columns
    assert df["data_type"].iloc[0] == "imported"


def test_sqlite_persistence(tmp_path):
    test_db = tmp_path / "test_reviews.sqlite"
    loader = DataLoader(db_path=test_db)
    
    df = pd.DataFrame([
        {"id": "SQL_1", "user_name": "Test User", "score": 2, "text": "App lag", "date": "2026-01-01", "version": "1.0", "data_type": "collected"}
    ])
    
    saved_count = loader.save_to_sqlite(df)
    assert saved_count == 1
    
    loaded_df = loader.load_from_sqlite()
    assert len(loaded_df) == 1
    assert loaded_df["id"].iloc[0] == "SQL_1"
