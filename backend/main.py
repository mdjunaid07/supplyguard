"""
SupplyGuard — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.db.mongo import connect_db, close_db
from backend.webhook.router import router as webhook_router
from backend.api.router import router as api_router
from backend.utils.logger import get_logger

logger = get_logger("supplyguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    logger.info("🚀 SupplyGuard backend started")
    yield
    await close_db()
    logger.info("SupplyGuard backend stopped")


app = FastAPI(
    title="SupplyGuard API",
    description="AI Supply Chain Attack Intelligence Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://supplyguard.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "supplyguard"}
