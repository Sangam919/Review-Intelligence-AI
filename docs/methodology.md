# MoveInSync Review Intelligence AI: Methodology & Architectural Specification

This document provides a formal technical specification of the MoveInSync Review Intelligence system built by the Forward Deployed Engineering (FDE) team.

---

## 1. Executive Problem Formulation

MoveInSync operates an enterprise employee transportation platform servicing over 500,000 corporate daily rides. Employees book rides, confirm roster shifts, receive pickup schedules, monitor live vehicle progress, complete boarding security checks, and escalate emergencies.

Public Google Play Store reviews represent an unfiltered, critical barometer of daily user trust. However, raw review feedback presents significant data quality challenges:
1. **Severe Negative Selection Bias**: Disgruntled commuters with delayed rides submit reviews at a 10x higher rate than satisfied riders.
2. **Lagging Indicator Latency**: Store ratings reflect legacy versions; a patch shipped today will not change 1-star reviews written 6 months ago unless actively resolved.
3. **Noisy, Unstructured Signals**: Commuters combine emotional expressions with specific technical bugs (e.g., "pathetic app, otp never arrived").

The objective of this architecture is to transform messy public text into traceable, statistically grounded, and prioritized engineering interventions.

---

## 2. Ingestion & Provenance Architecture

### 2.1 Public Data Sourcing
- Public endpoints are scraped via `google-play-scraper` querying Google Play's batch RPC endpoint for `com.moveinsync.ets`.
- Metadata captured includes:
  - `reviewId`: Unique persistent Play Store identifier.
  - `userName`: Reviewer pseudonym.
  - `score`: Explicit user rating $\in \{1, 2, 3, 4, 5\}$.
  - `content`: Unstructured feedback text.
  - `at`: Timestamp with timezone awareness.
  - `reviewCreatedVersion`: App client build version active when review was authored.
  - `replyContent` & `repliedAt`: Developer response audit history.

### 2.2 Deduplication Strategy
1. **Primary Key Match**: Reviews with identical `id` strings are deduplicated, preserving the latest instance.
2. **Deterministic Cryptographic Fingerprinting**: For legacy imports or reviews missing unique IDs, a SHA-256 hash is computed:
   $$\text{Fingerprint} = \text{SHA256}(\text{score} \parallel \text{user\_name} \parallel \text{date}_{[:10]} \parallel \text{normalized\_text})$$

### 2.3 Provenance Labeling
Every review record carries a mandatory `data_type` enum:
- `collected`: Live public Play Store scrape.
- `imported`: User-provided CSV upload.
- `sample`: Illustrative synthetic benchmark. If active, UI prominently displays: **"DEMO DATA — NOT VERIFIED REAL USER FEEDBACK."**

---

## 3. Classification & Sentiment Pipeline

### 3.1 Taxonomy Design
Reviews are mapped into 10 multi-label operational domains tailored for Employee Transportation Systems:
1. `booking_reservation`: Roster shift selection, cancellation, deadlines.
2. `login_otp_auth`: SSO, SMS/Email OTP delivery, session expiry.
3. `pickup_eta`: Punctuality, ETA forecasting, routing delays.
4. `gps_tracking`: Map marker freezing, telematics packet drops, dead reckoning.
5. `driver_vehicle`: Cab cleanliness, driver behavior, AC, route deviations.
6. `safety_verification`: Escort guard attendance, SOS triggers, OTP ride initiation.
7. `notifications_checkin`: Push alerts, Bluetooth beacon check-in, dynamic QR boarding.
8. `app_performance`: ANR crashes, cold-start latency, memory leaks, battery drain.
9. `customer_support`: Support ticket closure, grievance response, penalty disputes.
10. `other`: Unclassified or general corporate feedback.

### 3.2 Dual Classification Engine
- **Deterministic Rule Baseline**: Highly optimized regex word boundary patterns. Fast, 100% explainable, zero external cost, reproducible across test suites.
- **Optional OpenAI Structured Enrichment**: If enabled by the user with an OpenAI key, reviews with borderline confidence ($<0.70$) or marked as `other` are parsed via `gpt-4o-mini` with strict JSON schema constraints. Text is isolated as untrusted data in the user message block to eliminate prompt injection risks.

### 3.3 Sentiment Polarity Estimation
Sentiment is modeled as an analytical estimate, anchored primarily by explicit star rating:
$$\text{Sentiment Score} = 0.75 \cdot R_{\text{signal}} + 0.25 \cdot T_{\text{lexical}}$$
Where $R_{\text{signal}} \in \{-0.9, -0.5, 0.0, 0.5, 0.9\}$ for ratings 1 through 5, and $T_{\text{lexical}} \in [-1.0, 1.0]$ is computed via TextBlob or lexical keyword amplifiers.

---

## 4. Multi-Attribute Prioritization Engine

To avoid arbitrary "P0" assignments based solely on complaint volume, our formula evaluates five distinct operational criteria:

$$\text{Priority Score} = w_F \cdot F + w_S \cdot S + w_T \cdot T + w_C \cdot C + w_E \cdot E_{inv}$$

### Dimension Formulations:
1. **Frequency Share ($F \in [0.0, 1.0]$)**:
   $$F = \min\left(1.0, 2.0 \times \frac{\text{Negative Complaints in Category}}{\text{Total Negative Reviews in Buffer}}\right)$$
2. **Severity Impact ($S \in [0.0, 1.0]$)**:
   $$S = \frac{1}{N} \sum_{i=1}^N \text{SeverityWeight}(\text{review}_i)$$
   Where Critical = 1.0, High = 0.75, Medium = 0.50, Low = 0.25.
3. **Trend Acceleration ($T \in [0.0, 1.0]$)**:
   $$T = \min\left(1.0, \max\left(0.2, \frac{\text{Surge Multiplier} - 0.5}{1.5}\right)\right)$$
4. **Statistical Confidence ($C \in [0.0, 1.0]$)**:
   $$C = \min\left(1.0, \frac{N}{8}\right) \times \text{Mean}(\text{Classifier Confidence})$$
5. **Ease of Implementation ($E_{inv} \in [0.0, 1.0]$)**:
   Low effort = 1.0, Medium effort = 0.65, High effort = 0.30.

### Tier Definitions:
- **P0**: Critical passenger safety escalations OR ($\text{Score} \ge 0.75 \land \text{Negative Count} \ge 3$).
- **P1**: High-impact recurring service failures ($\text{Score} \ge 0.55 \land \text{Negative Count} \ge 2$).
- **P2**: Experience & usability defect ($\text{Score} \ge 0.35$).
- **P3**: Low-impact enhancement or low-confidence issue needing internal telemetry corroboration.
