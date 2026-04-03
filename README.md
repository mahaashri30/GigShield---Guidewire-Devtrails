# Susanoo — "The Ultimate Defense"
### AI-Powered Parametric Income Insurance for Gig Economy Delivery Workers

![Flutter](https://img.shields.io/badge/Flutter-3.19+-02569B?style=flat-square&logo=flutter&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Python_3.11-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Valkey_8-DC382D?style=flat-square&logo=redis&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-MAE_₹1.30-FF6600?style=flat-square)
![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat-square&logo=render&logoColor=white)
![Razorpay](https://img.shields.io/badge/Razorpay-X_Payouts-02042B?style=flat-square&logo=razorpay&logoColor=white)

> **Guidewire DEVTrails 2026 Hackathon — Phase 2 Submission**
> *"The worker does nothing. Trigger fires → system pays → done in minutes."*

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [Persona — Meet Arun](#2-persona--meet-arun)
3. [Solution — Susanoo](#3-solution--susanoo)
4. [Live Demo](#4-live-demo)
5. [Registration & Underwriting](#5-registration--underwriting)
6. [Insurance Policy Management](#6-insurance-policy-management)
7. [Dynamic Premium Calculation](#7-dynamic-premium-calculation)
8. [5 Automated Disruption Triggers](#8-5-automated-disruption-triggers)
9. [Zero-Touch Claims & Settlement](#9-zero-touch-claims--settlement)
10. [AI / ML Models](#10-ai--ml-models)
11. [Actuarial Engine](#11-actuarial-engine)
12. [Fraud Defense & GPS Anti-Spoofing](#12-fraud-defense--gps-anti-spoofing)
13. [Tech Stack](#13-tech-stack)
14. [System Architecture](#14-system-architecture)
15. [Repository Structure](#15-repository-structure)

---

## 1. The Problem

India's gig economy employs over **15 million delivery workers** across Zomato, Swiggy, Blinkit, Zepto, and Amazon. These workers earn purely per delivery — no delivery, no income.

When disruptions hit — heavy rain, extreme heat, AQI spikes, traffic blockages, civic emergencies — **orders drop sharply and roads become impassable**. A worker earning ₹900/day can see income fall to ₹150 on a disrupted day.

**No insurance product in India protects gig workers against income loss due to environmental or civic disruptions. Susanoo fills this gap.**

---

## 2. Persona — Meet Arun

```
┌─────────────────────────────────────────────────────────┐
│  Name        : Arun Kumar                               │
│  Age         : 24                                       │
│  Location    : Bangalore, Karnataka (Pincode: 560001)   │
│  Role        : Quick-Commerce Grocery Delivery Partner  │
│  Platform    : Blinkit / Zepto / Swiggy Instamart       │
│  Earnings    : ₹800–₹1,200/day  |  ₹5,600–₹8,400/week  │
│  Active Days : 22 days in last 30 (eligible for cover)  │
│  Dependents  : Wife + 1 child. Monthly rent: ₹6,500     │
│  Savings     : Less than ₹2,000 at any given time       │
│  Insurance   : None. Never had any.                     │
└─────────────────────────────────────────────────────────┘
```

### Arun's Day With Susanoo

- Arun pays ₹49/week for Smart Shield — deducted from weekly platform settlement
- At 8:00 AM, Susanoo detects 80mm/hr rainfall in Bangalore (OpenWeather API)
- `HEAVY_RAIN / EXTREME` disruption event created automatically
- Arun's claim triggered — **he does nothing**
- Fraud engine: city match ✅, active policy ✅, no duplicate ✅, fraud score 0/100
- Payout = ₹925 × 0.58 (Bangalore infra-adjusted DSS) × 0.75 (active hours) = ₹403
- **₹403 credited to his UPI ID. SMS confirmation sent. Done.**

---

## 3. Solution — Susanoo

Susanoo is an **AI-powered parametric income insurance platform** for gig delivery workers.

### Core Principles

- **Parametric** — Payouts triggered by objective, measurable conditions. No claim filing.
- **Hyper-local** — DSS adjusted by city infrastructure quality, not just city name. Delhi's good drainage = lower DSS for same rainfall vs rural area.
- **Actuarially sound** — BCR target 0.55–0.70. Loss ratio >85% auto-suspends new enrolments.
- **Weekly** — Aligned with gig worker payment cycles. Never monthly.
- **Zero-touch** — Trigger fires → fraud check → payout → SMS. Worker does nothing.

---

## 4. Live Demo

| Component | URL |
|-----------|-----|
| Backend API | https://gigshield-guidewire-devtrails.onrender.com |
| API Docs | https://gigshield-guidewire-devtrails.onrender.com/docs |
| Android APK | Build from `mobile/` with `flutter build apk --release` |

**Demo credentials:**
- Phone number: `9999999999` (or any 10-digit number)
- OTP: `123456` (dev mode — unlocks Simulate Event button)
- Real OTP via 2Factor.in for actual phone numbers

### Dev Mode vs Production Mode

| Feature | Dev Mode (OTP: 123456) | Production Mode (Real OTP) |
|---------|----------------------|---------------------------|
| Phone | Any number e.g. `9999999999` | Your real registered number |
| OTP | `123456` — bypass | Real SMS via 2Factor.in |
| Simulate Event button | ✅ Visible on home screen | ❌ Hidden |
| Disruption creation | Manual tap → instant event | Celery auto-poll every 15 min |
| Payout | Mock Razorpay sandbox | Real Razorpay X UPI/IMPS |
| SMS confirmation | Printed in server logs | Sent to worker's phone |

> Dev mode is automatically activated when OTP `123456` is entered. The `devModeProvider` flag in Flutter shows/hides the Simulate Event button. Real users who receive a genuine OTP via SMS never see the simulate button.

---

## 5. Registration & Underwriting

### Onboarding Flow (4 steps)
1. Phone number → Real OTP via 2Factor.in SMS
2. Platform selection (Blinkit, Zepto, Swiggy Instamart, Zomato, Amazon, BigBasket)
3. Auto-fetch avg daily earnings from platform mock API
4. City + pincode + UPI ID

### Underwriting Rules (IRDAI-aligned)
- **Minimum 7 active delivery days** in last 30 days before cover eligibility
- Workers with <7 active days → `is_verified=False` → cannot purchase policy
- **City-based pools** — Delhi AQI pool ≠ Mumbai rain pool (different trigger eligibility per city)
- Workers with <5 active days in 30 → eligible for Basic tier only

### Platform Data Contract
```python
# What platform API returns (mock — same structure as real B2B API)
{
  "avg_daily_earnings": 925.69,     # Weekly settlement / active days
  "active_days_last_week": 6,       # Days with ≥1 delivery
  "active_days_30": 22,             # Last 30 days activity
  "weekly_settlement": 5554.14,     # Gross weekly earnings
  "verified": True
}
```

---

## 6. Insurance Policy Management

### Tier Structure

| Plan | Weekly Premium | Max Daily Payout | Max Weekly Payout | Triggers Covered |
|------|---------------|-----------------|-------------------|-----------------|
| Basic Shield | ₹29 | ₹300 | ₹600 | Heavy Rain only |
| Smart Shield | ₹49 | ₹550 | ₹1,100 | Rain + Heat + AQI |
| Pro Shield | ₹79 | ₹750 | ₹1,500 | All 5 triggers |

### Policy Features
- Razorpay payment integration (test mode sandbox)
- Weekly cycle — 7-day coverage from purchase date
- Auto-expiry with status tracking
- **Loss ratio gate** — if BCR >85% across all policies → new enrolments suspended automatically

---

## 7. Dynamic Premium Calculation

### Actuarial Base Formula
```
Premium = Σ [P(trigger) × avg_income_lost_per_day × days_exposed] × safety_loading

Where safety_loading = 1.35 (15% expenses + 10% profit + 10% reserve)
```

### AI Model (XGBoost) — Live in Production
- **MAE: ₹1.30** on test set
- 11 features: pincode prefix, month, tier, tenure weeks, activity score, zone risk, season factor, disruption type, severity, DSS multiplier, civic emergency flag
- Falls back to rule-based formula if model file not found

### Hyper-Local Infrastructure Scoring
Same rainfall = different DSS based on city drainage quality:

| Location | Infra Score | 45mm/hr Rain DSS | Payout on ₹600/day |
|----------|------------|-----------------|-------------------|
| Delhi central (110xxx) | 0.30 | 0.18 | ₹108 |
| Hyderabad (500xxx) | 0.42 | 0.22 | ₹132 |
| Chennai (600xxx) | 0.48 | 0.24 | ₹144 |
| Mumbai (400xxx) | 0.50 | 0.25 | ₹150 |
| Bangalore (560xxx) | 0.58 | 0.27 | ₹162 |
| Patna (800xxx) | 0.82 | 0.37 | ₹222 |
| Rural | 0.90 | 0.41 | ₹246 |

### Zone Risk & Season Multipliers

| City | Zone Risk | Peak Season |
|------|-----------|-------------|
| Mumbai | 1.35× | Jun–Sep |
| Bangalore | 1.20× | Jun–Sep |
| Delhi | 1.15× | May, Nov–Jan |
| Chennai | 1.10× | Oct–Dec |
| Hyderabad | 1.05× | Jun–Sep |

---

## 8. Five Automated Disruption Triggers

### Trigger Architecture
- Celery polls every **15 minutes** for all 5 cities
- On threshold breach → `DisruptionEvent` created → auto-claim for all active policy holders
- **City pools**: Delhi covers AQI+Heat, Mumbai covers Rain, all cities cover Civic+Traffic
- **Active hours check**: triggers only valid 6am–10pm IST (delivery hours)
- **Ward-level matching**: different pincode prefix → 30% payout reduction

### Trigger Table

| # | Trigger | Data Source | Threshold | DSS Range |
|---|---------|------------|-----------|-----------|
| 1 | Heavy Rain | OpenWeather API ✅ Real | >35mm/hr Moderate, >64.5mm/hr Severe, >115mm/day Extreme | 0.18–1.0 |
| 2 | Extreme Heat | OpenWeather API ✅ Real | >42°C Moderate, >44°C Severe, >46°C Extreme | 0.24–1.0 |
| 3 | AQI Spike | OpenWeather Air Pollution API ✅ Real | >200 Poor, >300 Very Poor (GRAP Stage 3), >400 Hazardous (GRAP Stage 4) | 0.20–1.0 |
| 4 | Traffic Disruption | Mock (realistic scenarios) | Congestion index >60 — VIP convoys, protests, accidents | 0.30–0.80 |
| 5 | Civic Emergency | NewsAPI ✅ Real (Twitter/X API as premium alternative) | Scans live news for bandh/curfew/strike/Section 144 keywords | 0.50–1.0 |

### Trigger Probability (10-year historical data)

| City | Rain | Heat | AQI | Traffic | Civic |
|------|------|------|-----|---------|-------|
| Delhi | 4% | 12% | 18% | 8% | 3% |
| Mumbai | 14% | 2% | 6% | 10% | 4% |
| Bangalore | 12% | 2% | 5% | 9% | 4% |
| Chennai | 10% | 6% | 4% | 6% | 3% |

---

## 9. Zero-Touch Claims & Settlement

### Settlement Flow
```
1. Trigger confirmed (API threshold crossed)
        ↓
2. Worker eligibility check (active policy, correct city pool, active hours, no duplicate)
        ↓
3. Fraud verified BEFORE payment (score 0–100)
        ↓
4. Payout calculated (income shortfall × active hours ratio × ward proximity)
        ↓
5. UPI transfer via Razorpay X (primary)
        ↓ if UPI fails
   IMPS bank transfer (fallback)
        ↓ if both fail
   Rollback → claim stays APPROVED for retry
        ↓ on success
6. SMS confirmation sent via 2Factor.in
        ↓
7. Record updated (settlement_seconds tracked, reconciled=true)
```

### Payout Formula
```
Income Shortfall = worker_daily_avg × DSS × active_hours_ratio × ward_factor

Where:
  DSS              = hyper-local infrastructure-adjusted disruption severity score
  active_hours_ratio = remaining delivery hours after event / total daily hours (6am-10pm)
  ward_factor      = 1.0 (same pincode prefix) or 0.7 (different ward, same city)

Capped at: tier daily cap and weekly cap
```

### Payout Channels

| Channel | Condition | Speed |
|---------|-----------|-------|
| UPI (Razorpay X) | Primary — worker has UPI ID | <2 minutes |
| IMPS Bank Transfer | Fallback — UPI fails | 2–4 hours |
| Razorpay Sandbox | Demo mode | Instant (mock) |

### SMS Confirmation
```
"Susanoo: Rs.403 credited to worker@upi for heavy rain
disruption. Ref:GS12345678. Income protected. -Susanoo"
```

---

## 10. AI / ML Models

### XGBoost Premium Engine
- **Purpose**: Predict weekly premium based on 11 risk features
- **Training data**: 5,000 synthetic records covering all 5 disruption types
- **MAE**: ₹1.30 (within ₹1.30 of correct premium on average)
- **Features**: pincode prefix, month, tier, tenure, activity score, zone risk, season, disruption type, severity, DSS, civic flag
- **Fallback**: Rule-based formula if model file unavailable

### Isolation Forest Fraud Detection
- **Purpose**: Unsupervised anomaly detection on claim behaviour
- **Training data**: 4,500 clean + 500 fraudulent synthetic claims
- **Civic fraud catch rate**: 73.1%
- **Features**: city match, platform active, claims frequency, time delta, active hours ratio, claim amount ratio, disruption type, location consistency
- **Verdict**: Score <30 → auto-approve, 30–69 → hold for review, ≥70 → auto-reject

---

## 11. Actuarial Engine

### BCR (Burning Cost Rate)
```
BCR = total claims paid / total premium collected
Target: 0.55–0.70 (65 paise per ₹1 goes to payouts)
```

| BCR | Status | Action |
|-----|--------|--------|
| <0.55 | Low | Consider premium reduction |
| 0.55–0.70 | Healthy | Maintain |
| 0.70–0.85 | Elevated | Increase premium next cycle |
| >0.85 | Critical | **Auto-suspend new enrolments** |

### 14-Day Monsoon Stress Test
```
Scenario: Continuous monsoon, 14 days, Bangalore, Smart Shield worker

Monsoon trigger probability: 80% daily
Expected trigger days: 11.2 of 14
Daily income loss: ₹925 × 0.70 DSS = ₹647
Expected total loss: ₹7,247
Max liability (2 weekly caps): ₹2,200
Stress BCR: 1.04 → SOLVENT
```

### Actuarial Premium vs Charged Premium
```
Actuarial base (Smart Shield, Bangalore, ₹925/day):
  Rain:    0.12 × ₹508 × 7 = ₹426
  Heat:    0.02 × ₹508 × 7 = ₹71
  AQI:     0.05 × ₹370 × 7 = ₹129
  Pure risk premium = ₹626 / 4 weeks = ₹156/week
  With 1.35× safety loading = ₹211/week

Charged: ₹49/week (subsidised for adoption — cross-subsidised by Pro tier)
```

---

## 12. Fraud Defense & GPS Anti-Spoofing

### Rule-Based Scoring (Live)

| Rule | Score | Rationale |
|------|-------|-----------|
| City mismatch | +40 | Worker in Delhi cannot claim Chennai flood |
| GPS location mismatch | +35 | Last GPS ping shows different city than event |
| GPS spoof detected | +30 | Impossible movement speed >200 km/h between pings |
| Platform inactive | +25 | Offline during disruption = not affected |
| High claim frequency ≥5/week | +20 | Statistically anomalous |
| Duplicate claim | +50 | Hard block — same event claimed twice |
| Suspicious speed <30s | +15 | Bot-filed claim |

### GPS Location Tracking (Anti-Spoofing)
Susanoo tracks worker location every **10 minutes** during active delivery hours (6am–10pm IST):

```
Flutter app (background) → GPS ping every 10 min → POST /api/v1/location/ping
        ↓
Backend calculates:
  distance_km = haversine(last_ping, current_ping)
  speed_kmh   = distance_km / time_elapsed_hours
  is_suspicious = speed_kmh > 200 km/h  ← physically impossible for delivery worker
        ↓
On claim trigger:
  last_known_city checked against event city  (+35 if mismatch)
  suspicious ping in last 30 min             (+30 if detected)
```

**Why 200 km/h threshold?**
- Delivery bike max speed: ~60 km/h
- Car max speed: ~120 km/h
- Anything >200 km/h = GPS coordinates were teleported = spoof

**Worker privacy:**
- Location only tracked during active hours (6am–10pm)
- Only city-level data used for fraud check
- Worker can deny permission — app still works, but fraud score sensitivity increases
- "You can change this anytime in Settings" shown in permission dialog

### Network-Level Fraud Ring Detection
```
Flag cluster if ALL true:
→ ≥10 accounts claimed same event within 5 minutes
→ ≥70% registered within last 7 days
→ ≥60% share same device subnet or IP range
→ Payouts route to ≤5 unique UPI IDs

Action: Freeze all payouts → manual review → 50% provisional payout to genuine workers
```

### Honest Worker Protection
- Workers flagged for review receive **50% provisional payout immediately**
- Review completed within 24 hours
- Clean claim history reduces fraud score sensitivity over time
- Location permission denial does not block claims — only increases scrutiny

---

## 13. Tech Stack

### Mobile
| Technology | Purpose |
|-----------|---------|
| Flutter 3.19+ | Cross-platform Android/iOS app |
| Riverpod 2.x | State management |
| GoRouter | Navigation |
| Dio | HTTP client with JWT interceptor + auto-refresh |
| flutter_secure_storage | Secure token storage |
| Razorpay Flutter SDK | In-app payment sheet |
| Pinput | OTP input UI |
| permission_handler | Location permission dialog |
| geolocator | GPS coordinates every 10 min |

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI (Python 3.11) | REST API |
| SQLAlchemy 2.0 async | ORM |
| asyncpg | Async PostgreSQL driver |
| Celery + Redis (Valkey 8) | Background polling every 15 min |
| python-jose | JWT tokens |
| httpx | Async HTTP for external APIs |
| Razorpay Python SDK | UPI + IMPS payouts |

### AI / ML
| Technology | Purpose |
|-----------|---------|
| XGBoost | Dynamic premium regression (MAE ₹1.30) |
| Isolation Forest (scikit-learn) | Fraud anomaly detection (73.1% civic fraud catch) |
| Pandas + NumPy | Feature engineering |
| joblib | Model serialization |

### External APIs
| API | Purpose | Mode |
|-----|---------|------|
| OpenWeather API | Rain + Heat triggers | ✅ Real |
| OpenWeather Air Pollution API | AQI trigger | ✅ Real |
| NewsAPI | Civic emergency detection | ✅ Real |
| 2Factor.in | OTP SMS + payout confirmation SMS | ✅ Real |
| Razorpay X | UPI + IMPS payouts | Sandbox |

### Infrastructure
| Component | Provider |
|-----------|---------|
| Backend | Render (Docker) |
| Database | Render PostgreSQL 18 |
| Redis | Render Valkey 8 |
| Uptime monitoring | UptimeRobot (5-min ping) |

---

## 14. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter Mobile App                        │
│  Phone OTP → Register → Buy Policy → Dashboard → Claims         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / REST
┌──────────────────────────▼──────────────────────────────────────┐
│                     FastAPI Backend (Render)                      │
│                                                                   │
│  /auth    /workers    /policies    /claims    /disruptions        │
│  /payouts /actuarial  /admin                                      │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Premium Engine  │  │  Fraud Engine    │  │ Actuarial      │  │
│  │ XGBoost ML      │  │  Isolation Forest│  │ BCR / Stress   │  │
│  │ MAE ₹1.30       │  │  73.1% catch     │  │ Test / Suspend │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Celery Workers (every 15 min)                  │ │
│  │  poll_weather → DisruptionEvent → auto_claim → UPI payout  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
  PostgreSQL      Valkey 8      OpenWeather    NewsAPI
  (Render)        Redis         + AQI API      Civic alerts
                               (Real data)    (Real data)
                                    │
                              2Factor.in
                              OTP + SMS
                                    │
                            Razorpay X
                            UPI + IMPS
```

---

## 15. Repository Structure

```
susanoo/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py           # OTP login, JWT tokens
│   │   │   ├── workers.py        # Registration, dashboard, earnings
│   │   │   ├── policies.py       # Buy policy, Razorpay, quote
│   │   │   ├── claims.py         # Trigger claim, city pools, active hours, GPS fraud
│   │   │   ├── disruptions.py    # Simulate, list active events
│   │   │   ├── payouts.py        # Payout history
│   │   │   ├── actuarial.py      # BCR, stress test, premium formula
│   │   │   ├── location.py       # GPS ping every 10min + spoof detection
│   │   │   └── admin.py          # Clear test data
│   │   ├── models/models.py      # SQLAlchemy ORM
│   │   ├── schemas/schemas.py    # Pydantic schemas
│   │   ├── services/
│   │   │   ├── premium_service.py    # XGBoost + rule-based premium
│   │   │   ├── disruption_service.py # 5 triggers + hyper-local DSS
│   │   │   ├── fraud_service.py      # Rule-based fraud scoring
│   │   │   ├── payout_service.py     # UPI + IMPS + rollback + SMS
│   │   │   ├── actuarial_service.py  # BCR, stress test, base formula
│   │   │   ├── auth_service.py       # OTP, JWT, 2Factor.in
│   │   │   └── platform_service.py   # Mock platform earnings API
│   │   ├── workers/
│   │   │   ├── celery_app.py     # Beat schedule (15min, 60min, daily)
│   │   │   └── tasks.py          # Auto-poll + auto-claim all cities
│   │   ├── config.py             # Environment settings
│   │   ├── database.py           # Async SQLAlchemy engine
│   │   └── main.py               # FastAPI app + auto-migration
│   ├── ml/
│   │   ├── premium_engine/train.py   # XGBoost training (MAE ₹1.30)
│   │   └── fraud_detection/train.py  # Isolation Forest training
│   ├── .env.example              # Safe placeholder (never commit .env)
│   ├── requirements.txt
│   └── Dockerfile
├── mobile/
│   └── lib/
│       ├── main.dart
│       ├── router/app_router.dart
│       ├── providers/app_providers.dart  # devModeProvider + location tracking start
│       ├── services/api_service.dart     # HTTP client + location ping
│       ├── services/location_service.dart # GPS ping every 10min background service
│       ├── screens/
│       │   ├── onboarding/       # Phone, OTP (dev mode detection), Register
│       │   ├── home/             # Dashboard, disruptions (auto-claimed badge)
│       │   ├── policy/           # View + Buy (AI premium breakdown)
│       │   ├── claims/           # Claims history with DSS + fraud score
│       │   └── profile/
│       ├── theme/app_theme.dart
│       └── utils/constants.dart
├── dashboard/                    # React admin panel
├── assets/diagrams/              # Architecture + flow diagrams
├── .gitignore                    # .env, *.joblib, tok.json excluded
└── README.md
```

---

## Conclusion

Susanoo — "The Ultimate Defense" — addresses a real, unmet financial need for India's 15 million gig delivery workers.

By combining **parametric insurance mechanics**, **hyper-local infrastructure-aware DSS**, **AI-driven pricing**, **actuarially sound BCR monitoring**, **automated fraud detection**, and **instant UPI payouts with SMS confirmation**, it delivers a product that is:

- **Affordable** — ₹29–₹79/week, aligned with weekly earnings cycles
- **Automatic** — Zero manual claim filing. Trigger fires → system pays → done in minutes
- **Hyper-local** — Same rainfall = different payout based on city drainage quality
- **Actuarially sound** — BCR target 0.55–0.70, stress-tested for 14-day monsoon
- **Fraud-resistant** — Network-level ring detection, not just account-level checks
- **Scalable** — Celery workers handle city-wide events for thousands of workers simultaneously

---

*Built for Guidewire DEVTrails 2026 | Team Susanoo*
*"The Ultimate Defense for India's Delivery Heroes"*
