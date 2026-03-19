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
│  Name        : Arun Kumar                               │
│  Age         : 24                                       │
│  Location    : Chennai, Tamil Nadu (Pincode: 600001)    │
│  Role        : Quick-Commerce Grocery Delivery Partner  │
│  Platform    : Blinkit / Zepto / Swiggy Instamart       │
│  Earnings    : ₹800–₹1,200/day  |  ₹5,600–₹8,400/week  │
│  Payment     : Weekly settlement from platform          │
│  Zone        : 2–3 km radius from dark store            │
│  Dependents  : Wife + 1 child. Monthly rent: ₹6,500     │
│  Savings     : Less than ₹2,000 at any given time       │
│  Insurance   : None. Never had any.                     │
└─────────────────────────────────────────────────────────┘
```

### Why Arun Has No Insurance Today

Arun is not unaware of risk — he rides through flooded streets every monsoon. He has no insurance because:

- **No product exists** for income loss. Health and vehicle insurance don't pay him when he can't ride.
- **Premiums are annual** — he cannot afford ₹3,000–₹5,000 upfront. He lives week to week.
- **Claims require paperwork** — he has no time, no documents, no agent.
- **He doesn't trust the system** — he has seen colleagues file claims that were rejected months later.

GigShield is designed around every one of these barriers.

### Arun's Day Without GigShield

It's a Tuesday in October. Northeast monsoon hits Chennai. Rainfall crosses 90mm/hr.

- 7:00 AM — Arun checks the app. Orders have dropped 70%.
- 8:30 AM — Roads near his dark store are flooded. He cannot ride.
- 12:00 PM — He has completed 3 deliveries instead of his usual 22.
- End of day — Arun earns ₹180 instead of ₹950.
- **Weekly shortfall: ₹3,800. Rent is due in 4 days.**

No claim to file. No insurance to call. No safety net. He borrows from a colleague.

### Arun's Day With GigShield

- Arun pays ₹49/week for Smart Shield — deducted from his weekly platform settlement.
- At 8:00 AM, GigShield detects rainfall > 64mm/hr in Chennai (pincode 600001).
- A `HEAVY_RAIN / SEVERE` disruption event is created automatically.
- Arun's claim is triggered — he does nothing.
- Fraud engine runs in milliseconds: city match `[PASS]`, active policy `[PASS]`, no duplicate `[PASS]`, fraud score `12/100`.
- Payout = ₹950 × 0.60 × 1.0 = ₹570 → capped at ₹550 (Smart Shield daily cap).
- **₹550 is credited to his UPI ID by 9:00 AM.**
- He stays home. His family eats. Rent is safe.

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

Triggers are grouped into two categories based on the nature of the disruption:

### Category A — Environmental Disruptions

These are weather and air quality events that physically prevent outdoor delivery work.

| Trigger | Why It Stops Deliveries | Threshold | Severity Levels |
|---|---|---|---|
| Heavy Rainfall / Floods | Roads waterlogged, bikes stall, orders drop 60–80%, platforms reduce active zones | > 35 mm/hr (Moderate), > 64.5 mm/hr (Severe), > 115 mm/day (Extreme) | 3 |
| Extreme Heat | Outdoor riding becomes medically dangerous above 42°C, platforms issue heat advisories, order volumes drop | > 42°C (Moderate), > 44°C (Severe), > 46°C (Extreme) | 3 |
| Severe Pollution / AQI Spike | AQI > 300 triggers government outdoor activity bans, platforms reduce delivery radius, workers cannot breathe while riding — directly causes income loss | > 200 AQI (Moderate), > 300 AQI (Severe), > 400 AQI (Extreme) | 3 |

> **On AQI as a trigger:** This is not a secondary concern. Delhi's AQI regularly crosses 400 in November–January. When this happens, the NCR government issues GRAP Stage 3/4 restrictions, platforms like Zomato and Swiggy reduce active delivery zones, and workers who do ride face respiratory distress. The income loss is real, measurable, and directly tied to an objective index — making it a textbook parametric trigger.

### Category B — Social / Civic Disruptions

These are human-caused events that block access to pickup or drop locations.

| Trigger | Why It Stops Deliveries | Threshold | Severity Levels |
|---|---|---|---|
| Traffic Disruption | Protests, accidents, or VIP movement cause road blockages — workers cannot reach dark stores or customer locations | Congestion index > threshold for > 2 hours | 3 |
| Civic Emergency | Government-declared curfew, unplanned local strikes, sudden market/zone closures — pickup and drop locations become inaccessible | Official declaration or verified zone closure | 3 |

### DSS (Disruption Severity Score) Multiplier Table

The DSS multiplier is the core of the payout formula. A higher severity = higher income loss = higher payout.

| Trigger | Moderate | Severe | Extreme | Real-World Example |
|---|---|---|---|---|
| Heavy Rain | 0.30 | 0.60 | 1.00 | Mumbai July flooding — roads impassable |
| Extreme Heat | 0.30 | 0.60 | 1.00 | Delhi May heatwave — 46°C, advisories issued |
| AQI Spike | 0.20 | 0.50 | 1.00 | Delhi Nov AQI 450 — GRAP Stage 4 restrictions |
| Traffic Disruption | 0.30 | 0.50 | 0.80 | Bandh / VIP convoy blocking arterial roads |
| Civic Emergency | 0.50 | 0.80 | 1.00 | Curfew declared — zero deliveries possible |

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

GigShield's AI is not decorative. Every rupee paid out and every premium charged is computed by a model. Here is exactly how each model works, what data it uses, and how it gets built.

### 8.1 Dynamic Premium Engine

**Phase 1 — Rule-Based Formula (Live)**

The live premium engine in `backend/app/services/premium_service.py` computes:

```
Premium = Base × Zone Risk × Season Factor × Worker History Factor
```

Each factor is grounded in real actuarial logic:
- **Zone Risk** is derived from historical flood/heat/AQI incident frequency per pincode prefix. Mumbai (400xxx) carries 1.35× because it floods every monsoon. Hyderabad (500xxx) carries 1.05× because it rarely does.
- **Season Factor** peaks at 1.35 in July (peak monsoon) and drops to 1.0 in January. This mirrors IMD historical rainfall distribution.
- **Worker History Factor** rewards long-tenure workers with clean claim records (0.95×) — the same logic as no-claims bonus in motor insurance.

**Phase 2 — XGBoost Regression Model**

The training script at `backend/ml/premium_engine/train.py` generates 5,000 synthetic training samples with features:

| Feature | Why it matters |
|---|---|
| `pincode_prefix` | Encodes zone-level flood/heat risk |
| `month` | Captures seasonal disruption probability |
| `tier` | Base price anchor |
| `tenure_weeks` | Proxy for worker reliability |
| `activity_score` | Platform engagement — active workers are lower risk |
| `zone_risk` | Pre-computed multiplier |
| `season_factor` | Pre-computed multiplier |

The XGBoost model learns non-linear interactions between these features — for example, a Mumbai worker in July with low activity is disproportionately high risk compared to the sum of individual factors. The rule-based formula cannot capture this. The model can.

In Phase 2, the model is retrained weekly on real claims data, replacing synthetic samples with ground truth.

### 8.2 Fraud Detection Engine

**Phase 1 — Rule-Based Scoring (Live)**

Every claim that enters the system is scored 0–100 in `backend/app/services/fraud_service.py` before a single rupee moves:

| Rule | Score | Rationale |
|---|---|---|
| City Mismatch | +40 | Worker registered in Delhi cannot claim a Chennai flood |
| Platform Inactive | +25 | If the platform shows the worker offline, they weren’t affected |
| High Claim Frequency | +10 to +20 | ≥ 3 claims in 7 days is statistically anomalous |
| Duplicate Claim | +50 | Hard signal — same event cannot be claimed twice |
| Suspicious Speed | +15 | Filing < 30 seconds after event creation suggests automation |

**Verdict:**
- Score `< 30` → ![Auto Approved](https://img.shields.io/badge/AUTO-APPROVED-10B981?style=flat-square&logoColor=white)
- Score `30–70` → ![Manual Review](https://img.shields.io/badge/MANUAL-REVIEW-F59E0B?style=flat-square&logoColor=white)
- Score `≥ 70` → ![Auto Rejected](https://img.shields.io/badge/AUTO-REJECTED-EF4444?style=flat-square&logoColor=white)

**Phase 2 — Isolation Forest Anomaly Detection**

The training script at `backend/ml/fraud_detection/train.py` trains an unsupervised Isolation Forest on 5,000 synthetic claims (4,500 clean + 500 fraudulent). The model learns what a normal claim looks like across 6 dimensions:

| Feature | Normal Range | Fraud Pattern |
|---|---|---|
| `city_match` | 1.0 (always matches) | 0.0–0.2 (GPS spoofed) |
| `platform_active` | 0.95 (almost always online) | 0.3 (mostly offline) |
| `claims_this_week` | 1–2 | 5–15 (coordinated ring) |
| `time_delta_seconds` | 300–3600s | 0–10s (bot-filed) |
| `active_hours_ratio` | 0.5–1.0 | 0.0–0.3 |
| `claim_amount_ratio` | 0.3–1.0 | Always 1.0 (max claim) |

Isolation Forest assigns an anomaly score to each claim. Claims below the threshold are flagged for review regardless of rule-based score — this catches novel fraud patterns the rules haven’t seen before.

### 8.3 Risk Prediction (Phase 2)

A third model predicts disruption probability 24–48 hours ahead per city/pincode using:
- IMD historical rainfall data by district
- Flood zone shapefiles (NDMA open data)
- Seasonal decomposition of AQI time series
- Traffic incident frequency by day-of-week and hour

This enables **proactive premium adjustment** before a disruption hits and **worker alerts** the night before a high-risk day.

---

## 9. Adversarial Defense & Anti-Spoofing Strategy

> *Direct response to the Phase 1 "Market Crash" challenge — 500 delivery partners, fake GPS, coordinated fraud ring draining the liquidity pool.*

### Understanding the Attack

This is not a single bad actor. It is an **organised fraud ring** operating with a playbook:

1. Register 500 accounts using real SIM cards bought in bulk
2. All accounts claim the same disruption event within minutes of each other
3. GPS is spoofed to show all workers inside the affected city
4. All payouts are routed to 3–5 UPI IDs controlled by the ring
5. ₹2.5 lakh exits the liquidity pool before any alert fires

Simple GPS verification fails here because the GPS coordinates look valid — they’re just fabricated. The attack is designed to pass single-account checks. The defence must operate at the **network level**, not the account level.

### Defense Architecture — 5 Layers

#### Layer 1 — Registration-Time Signals (Stop fakes before they enter)

- **Platform Worker ID verification** — Every account must supply a valid Zomato/Swiggy/Blinkit partner ID. These IDs are cross-referenced via platform APIs. A fraud ring cannot generate 500 valid partner IDs.
- **Device fingerprinting** — One device = one account. The app captures a device fingerprint on first launch. Multiple accounts from the same device are hard-blocked.
- **OTP velocity** — More than 2 OTP requests from the same device in 24 hours triggers a soft block. Bulk SIM farms are detected here.
- **UPI ID uniqueness** — One UPI ID = one worker account. Fraud rings reuse UPI IDs across mule accounts. This is a hard constraint enforced at the DB level.

#### Layer 2 — Claim-Time Signals (Catch what slips through registration)

| Signal | What fraud looks like | How we detect it |
|---|---|---|
| GPS coordinates | Spoofed to match disruption city | Cross-check against registered pincode + cell tower data |
| Platform session | Worker offline during event | API call to platform: was this worker’s app active? |
| Claim velocity | 500 claims in 5 minutes | Rate limit: 1 claim per event per worker, enforced at DB |
| Payout destination | All route to same 3 UPIs | Graph query: flag any UPI receiving > 3 payouts in same event |
| Claim timing | Filed < 30s after event creation | Suspicious speed flag (+15 fraud score) |
| Duplicate claim | Same worker, same event | Hard block at DB level before fraud engine even runs |

#### Layer 3 — Network-Level Fraud Ring Detection (The key layer for coordinated attacks)

Individual account checks will not catch a ring. The ring is designed to pass them. The defence must look at the **cluster**:

```
Fraud Ring Detection Algorithm:

1. Build a bipartite graph every 5 minutes during an active disruption event:
   Nodes  : Worker accounts + Disruption events
   Edges  : Claims filed

2. Flag a cluster if ALL of the following are true:
   → ≥ 10 accounts claimed the same event within 5 minutes
   → ≥ 70% of those accounts were registered within the last 7 days
   → ≥ 60% share the same device subnet or IP range
   → Payouts from the cluster route to ≤ 5 unique UPI IDs

3. Action on flagged cluster:
   → Freeze ALL payouts in the cluster immediately
   → Escalate to manual review queue with full cluster graph
   → Blacklist device fingerprints, IP ranges, and UPI IDs
   → Genuine workers in the cluster receive provisional 50% payout
      pending review (completed within 24 hours)
```

This algorithm catches the Market Crash scenario directly: 500 accounts, same event, same time window, payouts to a handful of UPIs — every condition fires.

#### Layer 4 — Isolation Forest Anomaly Detection (Phase 2 ML)

The rule-based layers catch known patterns. The Isolation Forest catches **unknown patterns** — fraud rings that have learned to avoid the rules.

The model is trained on 6 behavioural features per claim. A fraud ring that spaces out its claims, uses different UPIs, and avoids speed flags will still produce an anomalous feature vector — because the combination of `city_match=0`, `platform_active=0`, `claim_amount_ratio=1.0` is statistically rare in clean data, even if no single rule fires.

#### Layer 5 — Honest Worker Protection (The hardest problem)

The hardest problem is not catching fraud. It is **not punishing genuine workers** in the process.

A worker in Chennai who files 3 claims in a week during the northeast monsoon is not committing fraud — it was a genuinely bad week. The system must know the difference.

| Signal | Genuine Worker | Fraud Account |
|---|---|---|
| Platform session | Active during every disruption | Offline or no session data |
| GPS history | Consistent with registered zone for months | Teleports between cities |
| Claim history | 1–2 claims/month, matches weather events | Sudden spike on a brand-new account |
| Device | Single device, used for months | New device, registered days before event |
| UPI destination | Personal UPI, used consistently | Shared with 10+ other claimants |
| Registration age | Weeks to months old | Registered 1–7 days before the event |
| Delivery history | Verifiable platform ID with order history | No platform ID or invalid ID |

**Protections for genuine workers:**
- Workers flagged for review receive **50% provisional payout immediately** — they are not left with nothing while we investigate.
- Review is completed within **24 hours**.
- Workers can appeal with a single tap — no paperwork, no calls.
- A clean claim history over time **reduces fraud score sensitivity** for that worker (history factor in the premium engine).
- Fraud thresholds are calibrated to minimise false positives — we accept a small increase in fraud loss to avoid wrongly rejecting genuine claims.

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
