# TaxAssist FastAPI Application -- v2 (DEPLOYMENT READY)

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add backend root to sys.path so rag/, ocr/ are importable
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import state
from database import engine, Base
from routers import auth, chat, upload, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 1. Create DB tables ────────────────────────────────────────────────
    try:
        Base.metadata.create_all(bind=engine)
        log.info("✅ PostgreSQL tables ready")
    except Exception as db_err:
        log.warning("⚠️ DB init failed: %s", db_err)

    # ── 2. DO NOT load RAG here (lazy loading instead) ─────────────────────
    log.info("⚡ RAG will be loaded on first /chat request")

    yield

    log.info("🛑 TaxAssist server shutting down.")


app = FastAPI(
    title="TaxAssist API",
    description="RAG + OCR + Auth backend for TaxEase UI",
    version="2.0.0",
    lifespan=lifespan,
)

# ✅ Add your frontend URL later here
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        # "https://your-frontend.vercel.app"  ← add after deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────
app.include_router(health.router, tags=["system"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, tags=["rag"])
app.include_router(upload.router, tags=["ocr"])