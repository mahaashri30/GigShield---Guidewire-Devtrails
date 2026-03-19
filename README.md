# GigShield — AI-Powered Parametric Income Insurance for Gig Economy Delivery Workers

![Flutter](https://img.shields.io/badge/Flutter-3.19+-02569B?style=flat-square&logo=flutter&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Python_3.11-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Razorpay](https://img.shields.io/badge/Razorpay-X_Payouts-02042B?style=flat-square&logo=razorpay&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-ML-FF6600?style=flat-square&logoColor=white)

> **Guidewire DEVTrails 2026 Hackathon Submission**
> *"Your income. Protected."*

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [Persona — Meet Arun](#2-persona--meet-arun)
3. [Proposed Solution](#3-proposed-solution)
4. [Application Workflow](#4-application-workflow)
5. [Weekly Premium Model](#5-weekly-premium-model)
6. [Parametric Triggers](#6-parametric-triggers)
7. [Payout Calculation Logic](#7-payout-calculation-logic)
8. [AI / ML Integration](#8-ai--ml-integration)
9. [Adversarial Defense & Anti-Spoofing Strategy](#9-adversarial-defense--anti-spoofing-strategy)
10. [Tech Stack](#10-tech-stack)
11. [System Architecture](#11-system-architecture)
12. [Platform Choice — Why Mobile](#12-platform-choice--why-mobile)
13. [Phase 1 Prototype Scope](#13-phase-1-prototype-scope)
14. [Future Roadmap](#14-future-roadmap)
15. [Repository Structure](#15-repository-structure)

---

## 1. The Problem

India's gig economy employs over **15 million delivery workers** across platforms like Zomato, Swiggy, Blinkit, Zepto, and Amazon. These workers are the backbone of quick-commerce — yet they operate with zero financial safety net.

### The Income Loss Crisis

Delivery workers earn purely on a **per-delivery basis**. Their income is entirely dependent on:
- Number of orders completed per day
- Hours they can actively ride

When external disruptions hit — heavy rain, flooding, extreme heat, AQI spikes, or civic emergencies — **orders drop sharply and roads become impassable**. A worker who earns ₹900/day can see their income fall to ₹150–₹200 on a disrupted day.

### What Insurance Exists Today?

| Insurance Type | Covers | Does NOT Cover |
|---|---|---|
| Health Insurance | Medical expenses | Income loss |
| Vehicle Insurance | Bike damage | Income loss |
| Accidental Insurance | Injury | Income loss |
| **GigShield** | **Income loss during disruptions** | — |

**There is currently no insurance product in India that protects gig workers against income loss due to environmental or civic disruptions.** GigShield fills this gap.

---

## 2. Persona — Meet Arun

```
┌─────────────────────────────────────────────────────────┐
│  Name     : Arun Kumar                                  │
│  Age      : 24                                          │
│  Location : Chennai, Tamil Nadu                         │
│  Role     : Quick-Commerce Grocery Delivery Partner     │
│  Platform : Blinkit / Zepto / Swiggy Instamart          │
│  Earnings : ₹800 – ₹1,200 per day (₹5,600–₹8,400/week) │
│  Payment  : Weekly settlement from platform             │
│  Zone     : Operates within 2–3 km of a dark store      │
└─────────────────────────────────────────────────────────┘
```

### Arun's Day Without GigShield

It's a Tuesday in October. Northeast monsoon hits Chennai. Rainfall crosses 90mm/hr.

- 7:00 AM — Arun checks the app. Orders have dropped 70%.
- 8:30 AM — Roads near his dark store are flooded. He cannot ride.
- 12:00 PM — He has completed 3 deliveries instead of his usual 22.
- End of day — Arun earns ₹180 instead of ₹950.
- **Weekly shortfall: ₹3,800. Rent is due in 4 days.**

No claim to file. No insurance to call. No safety net.

### Arun's Day With GigShield

- Arun pays ₹49/week for Smart Shield.
- At 8:00 AM, GigShield's system detects rainfall > 64mm/hr in Chennai.
- A disruption event is automatically created.
- Arun's claim is triggered without him doing anything.
- Fraud engine validates: city match `[PASS]`, active policy `[PASS]`, no duplicate `[PASS]`.
- **₹570 is credited to his UPI ID by 9:00 AM.**
- He can cover his daily expenses even without riding.

---

## 3. Proposed Solution

GigShield is an **AI-powered parametric income insurance platform** built specifically for gig economy delivery workers.

### Core Principles

- **Parametric** — Payouts are triggered by objective, measurable conditions (rainfall mm, AQI index, temperature °C), not by subjective claim assessment.
- **Automated** — Zero manual intervention. No forms, no documents, no waiting.
- **Hyper-local** — Risk is calculated at pincode level, not city level.
- **Weekly** — Affordable weekly subscriptions aligned with how gig workers are paid.
- **Instant** — Payouts reach the worker's UPI ID within minutes of a trigger.

### Key Features

| Feature | Description |
|---|---|
| OTP-based onboarding | Phone number login, no passwords |
| AI dynamic premium | Premium adjusts by zone, season, and worker history |
| 3 coverage tiers | Basic / Smart / Pro with different payout caps |
| Real-time disruption monitoring | Weather, AQI, traffic, civic events |
| Automatic claim triggering | No action needed from worker |
| Rule-based fraud engine | City match, frequency, duplicate, speed checks |
| Instant UPI payout | Via Razorpay X Payouts API |
| Worker dashboard | Active policy, claims history, disruption alerts |

---

## 4. Application Workflow

### Onboarding Flow

![Onboarding Flow](assets/diagrams/onboarding%20flow%20guide.png)

### Policy Purchase Flow

![Policy Purchase Flow](assets/diagrams/policy%20purchase%20flow%20guide.png)

### Disruption → Payout Flow

![Disruption Flow](assets/diagrams/distruption%20flow%20guide.png)

---

## 5. Weekly Premium Model

### Why Weekly?

Gig workers receive weekly settlements from their platforms. A weekly insurance premium aligns with their cash flow — they pay from what they just earned, not from savings.

### Tier Structure

| Plan | Weekly Premium | Max Daily Payout | Max Weekly Payout | Triggers Covered |
|---|---|---|---|---|
| Basic Shield | ₹29 | ₹300 | ₹600 | Heavy Rain only |
| Smart Shield | ₹49 | ₹550 | ₹1,100 | Rain + Heat + AQI |
| Pro Shield | ₹79 | ₹750 | ₹1,500 | All 5 triggers |

### AI Dynamic Pricing Formula

```
Weekly Premium = Base Premium × Zone Risk × Season Factor × Worker History Factor

Where:
  Base Premium     = Tier base price (₹29 / ₹49 / ₹79)
  Zone Risk        = Pincode-level historical disruption multiplier (1.0 – 1.35)
  Season Factor    = Monthly risk multiplier (1.0 – 1.35, peaks in Jun–Aug monsoon)
  Worker History   = Claims history adjustment (0.95 for long-tenure workers)
```

### Zone Risk Multipliers (by Pincode Prefix)

| City | Pincode Prefix | Zone Risk | Reason |
|---|---|---|---|
| Mumbai | 400 | 1.35 | Highest monsoon flood risk |
| Bangalore | 560 | 1.20 | Flash flood prone |
| Delhi | 110 | 1.15 | Extreme heat + AQI |
| Chennai | 600 | 1.10 | Cyclone + monsoon |
| Pune | 411 | 1.10 | Moderate risk |
| Hyderabad | 500 | 1.05 | Lower risk |

### Season Multipliers

| Month | Factor | Reason |
|---|---|---|
| Jun – Jul | 1.30 – 1.35 | Peak monsoon |
| May | 1.20 | Pre-monsoon heat |
| Aug – Sep | 1.20 – 1.30 | Active monsoon |
| Mar – Apr | 1.05 – 1.10 | Early summer |
| Oct – Feb | 1.00 | Low risk months |

---

## 6. Parametric Triggers

Parametric insurance pays out when a **pre-defined, objectively measurable condition** is met — no claim filing, no assessment, no delay.

### Trigger Definitions

| Trigger | Threshold | Severity Levels |
|---|---|---|
| Heavy Rainfall | > 35 mm/hr (Moderate), > 64.5 mm/hr (Severe), > 115 mm/day equivalent (Extreme) | 3 |
| Extreme Heat | > 42°C (Moderate), > 44°C (Severe), > 46°C (Extreme) | 3 |
| AQI Spike | > 200 (Moderate), > 300 (Severe), > 400 (Extreme) | 3 |
| Traffic Disruption | Congestion index threshold breach | 3 |
| Civic Emergency | Government-declared curfew / road blockage | 3 |

### DSS (Disruption Severity Score) Multiplier Table

| Trigger | Moderate | Severe | Extreme |
|---|---|---|---|
| Heavy Rain | 0.30 | 0.60 | 1.00 |
| Extreme Heat | 0.30 | 0.60 | 1.00 |
| AQI Spike | 0.20 | 0.50 | 1.00 |
| Traffic Disruption | 0.30 | 0.50 | 0.80 |
| Civic Emergency | 0.50 | 0.80 | 1.00 |

The DSS multiplier directly drives the payout amount — a more severe disruption results in a proportionally higher payout.

---

## 7. Payout Calculation Logic

### Formula

```
Payout = Worker Daily Average Earnings × DSS Multiplier × Active Hours Ratio

Capped at: Tier Max Daily Payout
```

### Example

```
Worker: Arun Kumar
Daily Average Earnings: ₹950
Disruption: Heavy Rain — Severe (DSS = 0.60)
Active Hours Ratio: 1.0 (full day affected)
Tier: Smart Shield (Max Daily Payout: ₹550)

Raw Payout = ₹950 × 0.60 × 1.0 = ₹570
Cap Check  = ₹570 < ₹550? No → Capped at ₹550
Final Payout = ₹550
```

### Payout Caps

| Plan | Daily Cap | Weekly Cap |
|---|---|---|
| Basic | ₹300 | ₹600 |
| Smart | ₹550 | ₹1,100 |
| Pro | ₹750 | ₹1,500 |

Weekly cap prevents over-claiming across multiple disruption events in the same week.

---

## 8. AI / ML Integration

### 8.1 Dynamic Premium Engine

**Phase 1 (Live):** Rule-based formula using zone risk, season factors, and worker history. Implemented in `backend/app/services/premium_service.py`.

**Phase 2 (Planned):** XGBoost regression model trained on:
- Historical disruption frequency by pincode
- Seasonal weather patterns
- Worker claim history
- Platform activity scores

Training script: `backend/ml/premium_engine/train.py`

### 8.2 Fraud Detection Engine

**Phase 1 (Live):** Rule-based scoring system. Each claim is scored 0–100 across 5 rules:

| Rule | Score Impact | Description |
|---|---|---|
| City Mismatch | +40 | Worker's registered city ≠ disruption event city |
| Platform Inactive | +25 | Worker not logged into platform during event window |
| High Claim Frequency | +10 to +20 | ≥ 3 claims in 7 days |
| Duplicate Claim | +50 | Same worker, same disruption event |
| Suspicious Speed | +15 | Claim filed < 30 seconds after event start |

**Verdict:**
- Score `< 30` → ![Auto Approved](https://img.shields.io/badge/AUTO-APPROVED-10B981?style=flat-square&logoColor=white)
- Score `30–70` → ![Manual Review](https://img.shields.io/badge/MANUAL-REVIEW-F59E0B?style=flat-square&logoColor=white)
- Score `≥ 70` → ![Auto Rejected](https://img.shields.io/badge/AUTO-REJECTED-EF4444?style=flat-square&logoColor=white)

**Phase 2 (Planned):** Isolation Forest unsupervised anomaly detection model trained on synthetic + real claim data. Training script: `backend/ml/fraud_detection/train.py`

### 8.3 Risk Prediction (Phase 2)

Predict disruption probability 24–48 hours ahead using:
- Historical weather data by city/pincode
- Flood zone mapping
- Seasonal patterns
- IMD (India Meteorological Department) data feeds

---

## 9. Adversarial Defense & Anti-Spoofing Strategy

> *Response to the Phase 1 "Market Crash" challenge — 500 delivery partners, fake GPS, coordinated fraud ring.*

### The Attack Vector

A coordinated fraud ring operates as follows:
1. Multiple fake/mule accounts are registered with real phone numbers
2. GPS is spoofed to place workers in a disruption-affected city
3. Claims are filed simultaneously across all accounts for the same event
4. Payouts drain the liquidity pool before detection

### Our Defense Architecture

#### Layer 1 — Registration-Time Signals

- **Platform Worker ID verification** — Cross-reference with delivery platform APIs (Zomato/Swiggy partner IDs). Fake accounts cannot produce valid platform IDs.
- **Device fingerprinting** — One device = one account. Multiple accounts on the same device are flagged immediately.
- **Phone number velocity** — More than 2 OTP requests from the same device in 24 hours triggers a soft block.
- **UPI ID uniqueness** — One UPI ID cannot be linked to more than one worker account. Fraud rings reuse UPI IDs.

#### Layer 2 — Claim-Time Signals

| Signal | Fraud Indicator | Detection Method |
|---|---|---|
| GPS coordinates | Spoofed location | Cross-check GPS with registered pincode + cell tower triangulation |
| Platform activity | Worker not online | API call to platform to verify active session during event window |
| Claim velocity | Ring files simultaneously | Rate limit: max 1 claim per disruption event per worker |
| Payout destination | Multiple accounts → same UPI | Graph analysis: flag UPI IDs receiving > 3 payouts in same event |
| Claim timing | Filed < 30s after event | Suspicious speed flag (+15 fraud score) |
| Duplicate event | Same event, same worker | Hard block — duplicate claims rejected at DB level |

#### Layer 3 — Network-Level Fraud Ring Detection

This is the key layer for coordinated attacks:

```
Fraud Ring Detection Algorithm:

1. Build a bipartite graph:
   - Nodes: Worker accounts + Disruption events
   - Edges: Claims filed

2. Flag clusters where:
   - ≥ 10 accounts claim the same event within 5 minutes
   - All accounts were registered within the last 7 days
   - All accounts share the same device subnet or IP range
   - All payouts route to ≤ 3 unique UPI IDs

3. Action:
   - Freeze all payouts in the cluster
   - Escalate to manual review queue
   - Blacklist device fingerprints and UPI IDs
```

#### Layer 4 — Behavioral Anomaly Detection (Phase 2 ML)

The Isolation Forest model is trained to detect anomalies across:
- `city_match` — GPS vs registered city
- `platform_active` — Platform session during event
- `claims_this_week` — Weekly claim frequency
- `time_delta_seconds` — Speed of claim after event
- `active_hours_ratio` — Proportion of day affected
- `claim_amount_ratio` — Claimed vs maximum possible

Workers whose feature vector is an outlier (Isolation Forest score < threshold) are flagged for review regardless of rule-based score.

#### Layer 5 — Honest Worker Protection

The most important design principle: **do not punish genuine workers**.

- A worker in a flood zone who files 3 claims in a week is NOT automatically fraud — it may be a genuinely bad week.
- Fraud score thresholds are calibrated to minimize false positives.
- Workers flagged for review receive a **provisional payout of 50%** immediately, with the remainder released after review (within 24 hours).
- Workers can appeal via the app with a single tap — no paperwork.
- Consistent clean history reduces fraud score sensitivity for that worker over time (history factor).

#### Distinguishing the Faker from the Genuinely Stranded Worker

| Signal | Genuine Worker | Fraud Account |
|---|---|---|
| Platform session | Active during disruption | Offline or no session |
| GPS history | Consistent with registered zone | Teleports between cities |
| Claim history | 1–2 claims/month, consistent | Sudden spike on new account |
| Device | Single device, long tenure | New device, multiple accounts |
| UPI destination | Personal UPI, consistent | Shared with other claimants |
| Registration age | Weeks to months old | Registered days before event |
| Delivery history | Verifiable via platform ID | No platform ID or invalid |

---

## 10. Tech Stack

### Mobile (Frontend)
| Technology | Purpose |
|---|---|
| Flutter 3.19+ | Cross-platform mobile app (Android/iOS) |
| Riverpod 2.x | State management |
| GoRouter | Navigation and deep linking |
| Dio | HTTP client with JWT interceptor |
| flutter_secure_storage | Secure token storage |
| Razorpay Flutter SDK | In-app payment sheet |
| Pinput | OTP input UI |
| Google Fonts (DM Sans) | Typography |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI (Python 3.11) | REST API framework |
| SQLAlchemy 2.0 (async) | ORM with async PostgreSQL |
| asyncpg | Async PostgreSQL driver |
| Alembic | Database migrations |
| python-jose | JWT token generation and validation |
| Celery + Redis | Background job scheduling (disruption polling) |
| Razorpay Python SDK | Payment order creation and payout initiation |
| httpx | Async HTTP client for external APIs |

### AI / ML
| Technology | Purpose |
|---|---|
| XGBoost | Dynamic premium regression model |
| Isolation Forest (scikit-learn) | Fraud anomaly detection |
| Pandas + NumPy | Feature engineering |
| joblib | Model serialization |

### Infrastructure
| Technology | Purpose |
|---|---|
| PostgreSQL 15 | Primary database |
| Redis 7 | Celery broker + result backend |
| Docker + Docker Compose | Local development environment |
| OpenWeather API | Real-time weather data |
| AQI India API | Real-time air quality data |
| Razorpay X | UPI payout disbursement |
| Firebase Cloud Messaging | Push notifications (Phase 2) |

---

## 11. System Architecture

![System Architecture](assets/diagrams/system%20architecture%20guide.png)

---

## 12. Platform Choice — Why Mobile

| Factor | Mobile (Flutter) | Web |
|---|---|---|
| Target users | Delivery workers on the road | — |
| Device availability | Every worker has a smartphone | Workers don't use laptops |
| UPI payment | Native Razorpay SDK | Requires browser redirect |
| Push notifications | FCM native support | Limited |
| GPS access | Native location APIs | Browser-limited |
| Offline resilience | Local storage possible | Requires connectivity |

Delivery workers operate entirely on mobile. A web platform would create a barrier to adoption. Flutter was chosen for a single codebase that targets both Android and iOS.

---

## 13. Phase 1 Prototype Scope

### ![Implemented](https://img.shields.io/badge/PHASE_1-IMPLEMENTED-1A56DB?style=flat-square) Implemented

| Feature | Status |
|---|---|
| OTP-based authentication (JWT) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Worker registration (name, platform, city, UPI) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| AI dynamic premium quote (zone + season) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| 3-tier weekly policy purchase (Razorpay test mode) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Disruption simulation (mock weather/AQI) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Active disruption display on home dashboard | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Rule-based fraud scoring on every claim | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Auto-approve / hold / reject claim logic | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Automatic UPI payout on claim approval | ![Live](https://img.shields.io/badge/LIVE-Razorpay_X-10B981?style=flat-square) |
| Claims history screen | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Worker dashboard (policy, claims, disruptions) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| Admin dashboard (React — metrics, charts, claims) | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |
| XGBoost premium model training script | ![Ready](https://img.shields.io/badge/READY-0EA5E9?style=flat-square) |
| Isolation Forest fraud model training script | ![Ready](https://img.shields.io/badge/READY-0EA5E9?style=flat-square) |
| Docker Compose full-stack setup | ![Live](https://img.shields.io/badge/LIVE-10B981?style=flat-square) |

### ![Phase 2](https://img.shields.io/badge/PHASE_2-ROADMAP-F59E0B?style=flat-square) Phase 2 Scope

| Feature | Target |
|---|---|
| Real OpenWeather + AQI API integration | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| Celery auto-claim trigger for all policy holders | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| XGBoost model serving in premium API | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| Isolation Forest in live fraud pipeline | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| GPS location validation in fraud engine | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| Platform activity API integration | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| FCM push notifications on payout | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |
| Fraud ring network graph detection | ![Phase 2](https://img.shields.io/badge/PHASE_2-F59E0B?style=flat-square) |

---

## 14. Future Roadmap

### Phase 3 — Scale & Integrate
- Direct API integration with Zomato/Swiggy/Blinkit partner platforms for real activity verification
- Real Razorpay X production payouts
- Expand to auto-rickshaw drivers, construction daily-wage workers, street vendors
- IRDAI regulatory compliance framework for parametric insurance products

### Phase 4 — Intelligence
- Retrain ML models weekly with real claims + weather data
- Predictive disruption alerts (24-hour advance warning)
- Personalized premium based on individual worker's delivery zone heatmap
- Peer comparison fraud detection (anomaly vs. cohort)

---

## 15. Repository Structure

```
gigshield/
├── backend/
│   ├── app/
│   │   ├── api/              # Route handlers (auth, workers, policies, claims, disruptions, payouts)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic (premium, fraud, disruption, payout)
│   │   ├── workers/          # Celery tasks and beat scheduler
│   │   ├── config.py         # Environment settings
│   │   ├── database.py       # Async SQLAlchemy engine
│   │   └── main.py           # FastAPI app entry point
│   ├── ml/
│   │   ├── premium_engine/   # XGBoost premium model training
│   │   └── fraud_detection/  # Isolation Forest fraud model training
│   ├── requirements.txt
│   └── Dockerfile
├── mobile/
│   └── lib/
│       ├── main.dart
│       ├── router/           # GoRouter navigation
│       ├── providers/        # Riverpod state management
│       ├── services/         # API service (Dio HTTP client)
│       ├── screens/          # UI screens
│       │   ├── onboarding/   # Phone, OTP, Register
│       │   ├── home/         # Dashboard
│       │   ├── policy/       # View + Buy policy
│       │   ├── claims/       # Claims history
│       │   └── profile/      # Worker profile
│       ├── theme/            # App theme (DM Sans, color palette)
│       └── utils/            # Constants
├── dashboard/                # React admin panel
├── docker-compose.yml
└── SETUP.md
```

---

## Conclusion

GigShield addresses a real, unmet financial need for India's 15 million gig delivery workers. By combining **parametric insurance mechanics**, **AI-driven pricing**, **automated fraud detection**, and **instant UPI payouts**, it delivers a product that is:

- **Affordable** — ₹29–₹79/week, aligned with weekly earnings cycles
- **Automatic** — Zero manual claim filing, zero paperwork
- **Fair** — Fraud detection that catches bad actors without punishing honest workers
- **Scalable** — Architecture designed to handle city-wide disruption events affecting thousands of workers simultaneously

This is not just a hackathon prototype. It is a blueprint for a product that can meaningfully improve the financial resilience of millions of workers who power India's delivery economy.

---

*Built for Guidewire DEVTrails 2026 | Team GigShield*
