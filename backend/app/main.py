from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import auth, workers, policies, claims, payouts, disruptions
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="GigShield API",
    description="AI-Powered Parametric Income Insurance for Delivery Partners",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(workers.router, prefix="/api/v1/workers", tags=["Workers"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["Policies"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["Claims"])
app.include_router(payouts.router, prefix="/api/v1/payouts", tags=["Payouts"])
app.include_router(disruptions.router, prefix="/api/v1/disruptions", tags=["Disruptions"])


@app.get("/")
async def root():
    return {
        "app": "GigShield",
        "version": "1.0.0",
        "status": "running",
        "message": "AI-Powered Parametric Income Insurance for Delivery Partners",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
