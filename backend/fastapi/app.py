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
    try:
        Base.metadata.create_all(bind=engine)
        log.info("✅ PostgreSQL tables ready")
    except Exception as db_err:
        log.warning("⚠️ DB init failed: %s", db_err)

    log.info("⚡ RAG will be loaded on first /chat request")
    yield
    log.info("🛑 TaxAssist server shutting down.")


app = FastAPI(
    title="TaxAssist API",
    description="RAG + OCR + Auth backend for TaxEase UI",
    version="2.0.0",
    lifespan=lifespan,
)

# ✅ CORS (add your Vercel URL here)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-vercel-url.vercel.app",  # 🔥 REPLACE THIS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ FIXED ROUTES (IMPORTANT)
app.include_router(health.router, prefix="/api", tags=["system"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["rag"])
app.include_router(upload.router, prefix="/api", tags=["ocr"])