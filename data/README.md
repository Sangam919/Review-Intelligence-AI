# MoveInSync Review Intelligence AI - Data Directory

This directory contains review datasets used by the intelligence pipeline.

## Dataset Types & Provenance

1. **`sample_reviews.csv` (Illustrative Demonstration Data)**
   - **Status**: SYNTHETIC / DEMO DATA - NOT VERIFIED REAL USER FEEDBACK.
   - **Purpose**: Provides realistic testing and exploratory capabilities for demonstration, automated integration testing, and UI validation without hitting external network endpoints.
   - **Provenance**: Synthetic scenarios designed around real-world corporate employee transportation logistics (cab rosters, OTP verification, live vehicle tracking, safety SOS alerts).
   - **Caution**: As highlighted in the system methodology, real-world business decisions must never be finalized solely from illustrative benchmark data.

2. **Collected Reviews (`reviews.sqlite` or exported CSVs)**
   - **Status**: PUBLIC PRODUCTION FEEDBACK.
   - **Source**: Google Play Store public review endpoint (`com.moveinsync.ets`).
   - **Collection Timestamp**: Dynamically recorded per scrape batch.
   - **Provenance**: Explicitly marked with `source="google_play"` and `data_type="collected"`.

3. **Imported Datasets**
   - **Status**: USER-PROVIDED DATA.
   - **Provenance**: Loaded via dashboard manual upload, marked with `source="manual_import"` and `data_type="imported"`.
