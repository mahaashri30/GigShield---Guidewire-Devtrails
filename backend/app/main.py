from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import traceback

from app.api import auth, workers, policies, claims, payouts, disruptions, actuarial, admin, location, notifications
from app.database import engine, Base
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — create tables and add any missing columns
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add new columns if they don't exist (safe migration)
        new_columns = [
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS avg_online_hours_per_day FLOAT DEFAULT 9.0",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS avg_orders_per_day FLOAT DEFAULT 18.0",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS active_days_30 INTEGER DEFAULT 0",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS last_known_lat FLOAT",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS last_known_lng FLOAT",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS last_location_at TIMESTAMPTZ",
            "ALTER TABLE payouts ADD COLUMN IF NOT EXISTS channel VARCHAR(20) DEFAULT 'UPI'",
            "ALTER TABLE payouts ADD COLUMN IF NOT EXISTS settlement_seconds INTEGER",
            "ALTER TABLE payouts ADD COLUMN IF NOT EXISTS rollback_at TIMESTAMPTZ",
            "ALTER TABLE payouts ADD COLUMN IF NOT EXISTS reconciled BOOLEAN DEFAULT FALSE",
            "ALTER TABLE disruption_events ADD COLUMN IF NOT EXISTS lat FLOAT",
            "ALTER TABLE disruption_events ADD COLUMN IF NOT EXISTS lng FLOAT",
            "ALTER TABLE disruption_events ADD COLUMN IF NOT EXISTS radius_km FLOAT DEFAULT 5.0",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS fcm_token VARCHAR(200)",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(200)",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS sim_hash VARCHAR(64)",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS sim_changed_at TIMESTAMPTZ",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL",
            "ALTER TABLE workers ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ",
            "CREATE TABLE IF NOT EXISTS worker_notifications (id VARCHAR PRIMARY KEY, worker_id VARCHAR REFERENCES workers(id), title VARCHAR(120) NOT NULL, body TEXT NOT NULL, notif_type VARCHAR(40) NOT NULL, ref_id VARCHAR(100), is_read BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS worker_delivery_grids (id VARCHAR PRIMARY KEY, worker_id VARCHAR REFERENCES workers(id) UNIQUE, bbox_lat_min FLOAT, bbox_lat_max FLOAT, bbox_lng_min FLOAT, bbox_lng_max FLOAT, center_lat FLOAT, center_lng FLOAT, radius_km FLOAT, p90_radius_km FLOAT, ping_count INTEGER DEFAULT 0, active_days INTEGER DEFAULT 0, dominant_pincode VARCHAR(10), dominant_city VARCHAR(100), first_ping_at TIMESTAMPTZ, last_ping_at TIMESTAMPTZ, updated_at TIMESTAMPTZ DEFAULT NOW())",
        ]
        for sql in new_columns:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass
                
    # Seed Admin User
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.models.models import Admin
    from app.services.auth_service import pwd_context
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Admin).where(Admin.email == "codethetrend@gmail.com"))
        admin = result.scalar_one_or_none()
        if not admin:
            new_admin = Admin(
                email="codethetrend@gmail.com",
                hashed_password=pwd_context.hash("admin"),
                name="System Admin"
            )
            session.add(new_admin)
            await session.commit()
            print("[SEED] Admin user created: codethetrend@gmail.com")

    yield
    await engine.dispose()


app = FastAPI(
    title="Susanoo API",
    description="The Ultimate Defense — AI-Powered Parametric Income Insurance for Delivery Partners",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"[500 ERROR] {request.method} {request.url.path}\n{tb}")
    
    response_content = {"detail": "Internal server error"}
    if settings.ENVIRONMENT == "development":
        response_content = {"detail": str(exc), "traceback": tb}
        
    return JSONResponse(
        status_code=500, 
        content=response_content
    )

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(workers.router, prefix="/api/v1/workers", tags=["Workers"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["Policies"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["Claims"])
app.include_router(payouts.router, prefix="/api/v1/payouts", tags=["Payouts"])
app.include_router(disruptions.router, prefix="/api/v1/disruptions", tags=["Disruptions"])
app.include_router(actuarial.router, prefix="/api/v1/actuarial", tags=["Actuarial"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(location.router, prefix="/api/v1/location", tags=["Location"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])


@app.get("/")
@app.head("/")
async def root():
    return {
        "app": "Susanoo",
        "tagline": "The Ultimate Defense",
        "version": "1.0.0",
        "status": "running",
        "message": "AI-Powered Parametric Income Insurance for Delivery Partners",
    }


@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "healthy"}
