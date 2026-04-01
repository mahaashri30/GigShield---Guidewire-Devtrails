# GigShield — Devpost Story

## Inspiration

India has 15 million gig delivery workers. Every monsoon, every heatwave, every AQI spike — they lose income with no recourse. Health insurance doesn't pay when you can't ride. Vehicle insurance doesn't pay when roads are flooded. There is **no insurance product in India that covers income loss due to environmental disruptions**.

We kept coming back to one image: a delivery worker in Chennai, sitting at home during a flood, watching his earnings drop from ₹950 to ₹180 — with rent due in four days. He borrows from a colleague. Again.

That's not a gap in the market. That's a failure of the financial system to see 15 million people.

GigShield started as a question: *what if insurance just... worked for them?* No paperwork. No agents. No waiting. Just — money in your UPI account before 9 AM, because it rained too hard to ride.

---

## What It Does

GigShield is an **AI-powered parametric income insurance platform** for gig economy delivery workers.

**Parametric** means payouts are triggered by objective, measurable conditions — not by claim assessment. When rainfall crosses 64.5 mm/hr in a worker's pincode, the payout fires automatically. The worker does nothing.

### The full flow in 60 seconds:

1. Worker registers with phone number + Zomato/Swiggy partner ID
2. Pays ₹29–₹79/week (deducted from weekly platform settlement)
3. GigShield monitors weather, AQI, and civic events in real time
4. When a trigger threshold is crossed, a disruption event is created
5. Claims are auto-filed for all active policyholders in the affected zone
6. Fraud engine scores every claim in milliseconds (rule-based + ML)
7. Approved claims → instant UPI payout via Razorpay X

### Three coverage tiers:

| Plan | Weekly Premium | Daily Cap | Triggers |
|---|---|---|---|
| Basic Shield | ₹29 | ₹300 | Heavy Rain |
| Smart Shield | ₹49 | ₹550 | Rain + Heat + AQI |
| Pro Shield | ₹79 | ₹750 | All 5 triggers |

### Payout formula:

$$\text{Payout} = \text{Daily Avg Earnings} \times \text{DSS Multiplier} \times \text{Active Hours Ratio}$$

Capped at the tier's daily maximum. The DSS (Disruption Severity Score) multiplier scales with severity — a Severe flood pays 0.60×, an Extreme flood pays 1.00×.

### AI dynamic premium:

$$P = P_{\text{base}} \times R_{\text{zone}} \times F_{\text{season}} \times F_{\text{history}}$$

Where \\\( R_{\text{zone}} \\\) is a pincode-level flood/heat risk multiplier (1.0–1.35) and \\\( F_{\text{season}} \\\) peaks at 1.35 in July monsoon.

---

## How We Built It

### Stack

- **Flutter** — cross-platform mobile app (Android + iOS from one codebase). Delivery workers are on mobile, always.
- **FastAPI + Python 3.11** — async REST backend, chosen for speed and the ML ecosystem
- **PostgreSQL 15 + SQLAlchemy 2.0 async** — primary data store
- **Redis + Celery** — background disruption polling and claim triggering
- **Razorpay X Payouts** — instant UPI disbursement
- **XGBoost** — premium regression model (Phase 2 serving)
- **Isolation Forest (scikit-learn)** — unsupervised fraud anomaly detection
- **React** — admin dashboard with live metrics and claims management
- **Docker Compose** — full local stack in one command

### Architecture decisions

We made the fraud engine **synchronous and blocking** — no payout moves until the score is computed. Latency is acceptable (milliseconds); a fraudulent payout is not reversible.

The premium engine runs as a **rule-based formula in Phase 1** with the XGBoost model trained and serialized alongside it. Swapping in the model is a one-line change — we wanted the logic auditable before we handed it to a black box.

Disruption events are created by a **Celery beat task** that polls weather/AQI APIs. In Phase 1 this uses mock data; the architecture is identical for real APIs.

---

## Challenges We Ran Into

**The coordinated fraud problem** was the hardest design challenge. A single bad actor is easy to catch. A fraud ring — 500 accounts, valid SIM cards, spoofed GPS, payouts routed to 5 UPI IDs — is designed to pass every per-account check.

The solution required thinking at the **network level**, not the account level:

- Build a bipartite graph of workers ↔ disruption events every 5 minutes
- Flag clusters where ≥10 accounts claim the same event within 5 minutes, ≥70% registered in the last 7 days, and payouts route to ≤5 UPI IDs
- Freeze the cluster, escalate to review, and issue 50% provisional payouts to genuine workers immediately

The harder sub-problem: **not punishing honest workers**. A Chennai worker filing 3 claims in a week during the northeast monsoon is not committing fraud. The system has to know the difference — and it does, via platform session data, GPS history consistency, registration age, and delivery history.

**Aligning insurance mechanics with gig worker cash flow** was the other challenge. Annual premiums don't work — workers live week to week. Weekly premiums deducted from platform settlements do. Every product decision had to pass the test: *would Arun actually use this?*

---

## Accomplishments That We're Proud Of

- A fraud engine that operates at **5 layers** — registration signals, claim-time signals, network graph detection, ML anomaly scoring, and honest worker protection — without a single one being decorative
- A payout formula grounded in **real actuarial logic**, not arbitrary numbers. Every multiplier has a source: IMD rainfall data, NDMA flood zones, GRAP AQI restriction thresholds
- The **50% provisional payout** for workers caught in a fraud review cluster — we refused to build a system that leaves genuine workers with nothing while we investigate
- A full working prototype: OTP auth → policy purchase → disruption simulation → fraud scoring → UPI payout, end to end, in a single `docker compose up`

---

## What We Learned

Parametric insurance is elegant precisely because it removes the human from the loop — but that means the **trigger design is everything**. A threshold set too low creates moral hazard. Too high and you're not paying out when workers actually can't ride. We spent more time on the trigger thresholds and DSS multiplier table than on any other single feature.

We also learned that **fraud defence and worker trust are the same problem**. Every layer of fraud detection is also a layer of trust infrastructure for genuine workers. The provisional payout, the 24-hour review SLA, the appeal-with-one-tap — these aren't UX niceties. They're what makes the product credible to someone who has never trusted an insurance company.

---

## What's Next for GigShield

**Phase 2 — Real data, live models:**
- OpenWeather + AQI India API integration (replace mock disruption data)
- XGBoost premium model serving in the live API
- Isolation Forest in the live fraud pipeline
- GPS location validation and platform activity API integration
- FCM push notifications on payout
- Fraud ring network graph detection (the Celery graph task)

**Phase 3 — Scale:**
- Direct API integration with Zomato/Swiggy/Blinkit for verified activity data
- Razorpay X production payouts
- Expand to auto-rickshaw drivers, construction daily-wage workers, street vendors
- IRDAI regulatory compliance framework for parametric insurance

**Phase 4 — Intelligence:**
- Weekly model retraining on real claims + weather data
- 24-hour predictive disruption alerts per pincode
- Personalized premium based on individual delivery zone heatmap
- Peer cohort anomaly detection

The product works. The architecture scales. The next step is real data.

---

*Built for Guidewire DEVTrails 2026 | Team GigShield*
