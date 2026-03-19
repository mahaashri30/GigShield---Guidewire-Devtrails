# GigShield — Setup & Run Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | python.org |
| Flutter | 3.19+ | flutter.dev |
| Docker + Compose | Latest | docker.com |
| Node.js | 20+ | nodejs.org |
| PostgreSQL | 15 (via Docker) | included |
| Redis | 7 (via Docker) | included |

---

## Option A — Docker (Recommended, Fastest)

```bash
# 1. Clone / unzip the project
cd gigshield

# 2. Copy env file
cp backend/.env.example backend/.env
# Edit backend/.env and add your OpenWeather API key (free tier OK)

# 3. Start all services
docker-compose up --build

# Services started:
#   API:       http://localhost:8000
#   Swagger:   http://localhost:8000/docs
#   Dashboard: http://localhost:3000
#   DB:        localhost:5432
#   Redis:     localhost:6379
```

---

## Option B — Manual Setup

### 1. Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and REDIS_URL

# Run database migrations (auto-creates tables on startup)
# Tables are created automatically via SQLAlchemy on first run

# Start API server
uvicorn app.main:app --reload --port 8000

# API docs: http://localhost:8000/docs
```

### 2. Train ML Models (Optional for Phase 1)

```bash
cd backend

# Train premium engine
python -m ml.premium_engine.train

# Train fraud detection model
python -m ml.fraud_detection.train
```

### 3. Celery Worker (Optional for Phase 1)

```bash
cd backend

# Start Redis first (or use Docker: docker run -p 6379:6379 redis:alpine)

# Worker
celery -A app.workers.celery_app worker --loglevel=info

# Beat scheduler (separate terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

### 4. Admin Dashboard (React)

```bash
cd dashboard
npm install
npm run dev
# Open: http://localhost:3000
```

### 5. Flutter Mobile App

```bash
cd mobile

# Install Flutter dependencies
flutter pub get

# Run on connected Android device / emulator
flutter run

# Build APK for demo
flutter build apk --debug
# APK at: build/app/outputs/flutter-apk/app-debug.apk
```

---

## API Quick Test (Phase 1 Demo Flow)

```bash
BASE=http://localhost:8000/api/v1

# 1. Send OTP (returns dev_otp: 123456)
curl -X POST $BASE/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210"}'

# 2. Verify OTP → get JWT token
TOKEN=$(curl -s -X POST $BASE/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "otp": "123456"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Register worker profile
curl -X POST $BASE/workers/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone":"+919876543210","name":"Ravi Kumar","platform":"zomato","city":"Bangalore","pincode":"560001","upi_id":"ravi@upi"}'

# 4. Get premium quote
curl "$BASE/policies/quote?tier=smart" \
  -H "Authorization: Bearer $TOKEN"

# 5. Buy a weekly policy
curl -X POST $BASE/policies/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"smart"}'

# 6. Simulate a disruption event (triggers mock weather check)
curl -X POST "$BASE/disruptions/simulate?city=Bangalore&pincode=560001" \
  -H "Authorization: Bearer $TOKEN"

# 7. Get active disruptions
curl "$BASE/disruptions/active?city=Bangalore"

# 8. Trigger a claim (use disruption event ID from step 6)
curl -X POST $BASE/claims/trigger/<EVENT_ID> \
  -H "Authorization: Bearer $TOKEN"

# 9. View dashboard
curl $BASE/workers/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key | Change in production! |
| `OPENWEATHER_API_KEY` | Free tier at openweathermap.org | `mock_key` (uses mock data) |
| `RAZORPAY_KEY_ID` | Razorpay test key | `rzp_test_mock` |
| `ENVIRONMENT` | `development` or `production` | `development` |

> **Dev mode shortcut:** If `OPENWEATHER_API_KEY` is `mock_key`, the system uses randomised mock weather data automatically. No API key needed for Phase 1 demo.

---

## Project Structure

```
gigshield/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry point
│   │   ├── config.py            Settings / env vars
│   │   ├── database.py          SQLAlchemy async engine
│   │   ├── api/                 Route handlers
│   │   │   ├── auth.py          OTP + JWT auth
│   │   │   ├── workers.py       Worker registration + dashboard
│   │   │   ├── policies.py      Weekly policy CRUD
│   │   │   ├── claims.py        Auto-claim trigger + fraud check
│   │   │   ├── disruptions.py   Event monitoring + simulation
│   │   │   └── payouts.py       Payout history
│   │   ├── models/models.py     All SQLAlchemy models
│   │   ├── schemas/schemas.py   All Pydantic schemas
│   │   ├── services/
│   │   │   ├── auth_service.py  JWT + OTP logic
│   │   │   ├── premium_service.py  Dynamic premium calc
│   │   │   ├── disruption_service.py  Weather/AQI/triggers
│   │   │   ├── fraud_service.py    Rule-based fraud scoring
│   │   │   └── payout_service.py   Mock UPI payout
│   │   └── workers/
│   │       ├── celery_app.py    Celery config + beat schedule
│   │       └── tasks.py         Background polling tasks
│   ├── ml/
│   │   ├── premium_engine/train.py   XGBoost premium model
│   │   └── fraud_detection/train.py  Isolation Forest fraud model
│   ├── alembic/                 DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── mobile/                      Flutter app
│   └── lib/
│       ├── main.dart
│       ├── theme/app_theme.dart
│       ├── utils/constants.dart
│       ├── services/api_service.dart
│       ├── providers/app_providers.dart
│       ├── router/app_router.dart
│       └── screens/
│           ├── splash_screen.dart
│           ├── shell_screen.dart
│           ├── onboarding/      phone, otp, register
│           ├── home/            dashboard
│           ├── policy/          view + buy
│           ├── claims/          history
│           └── profile/         worker profile
├── dashboard/                   React admin panel
│   └── src/
│       ├── App.jsx              Full dashboard UI
│       └── main.jsx
├── docker-compose.yml
└── SETUP.md
```

---

## Phase 1 Demo Checklist ✅

- [x] OTP-based auth (dev OTP: `123456`)
- [x] Worker registration (name, platform, city, UPI)
- [x] AI dynamic premium quote (zone + season factors)
- [x] Weekly policy creation (3 tiers)
- [x] Weather/AQI disruption simulation (mock APIs)
- [x] Auto-claim trigger on disruption event
- [x] Rule-based fraud scoring
- [x] Mock UPI payout (Razorpay simulation)
- [x] Worker dashboard (active policy, claims, disruptions)
- [x] Admin dashboard (metrics, charts, claims table)
- [x] ML model training scripts (XGBoost + Isolation Forest)
- [x] Celery worker scaffolding for Phase 2

---

## Phase 2 Roadmap (March 21 – April 4)

- [ ] Real OpenWeather API integration with Celery polling
- [ ] Auto-claim Celery task (fires for all active policies in affected city)
- [ ] Isolation Forest ML fraud model in claim pipeline
- [ ] Full XGBoost premium model serving via FastAPI
- [ ] Razorpay test mode real API integration
- [ ] Flutter push notifications (FCM) on claim payout
- [ ] GPS location validation in fraud engine
