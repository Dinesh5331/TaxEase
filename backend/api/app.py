import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import auth, chat, upload, health, itr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        log.info("[OK] PostgreSQL tables ready")
    except Exception as db_err:
        log.warning("[WARN] DB init failed: %s", db_err)

    log.info("[INFO] RAG will be loaded on first /chat request")
    yield
    log.info("[INFO] TaxAssist server shutting down.")


app = FastAPI(
    title="TaxAssist API",
    description="RAG + OCR + Auth backend for TaxEase UI",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["system"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["rag"])
app.include_router(upload.router, prefix="/api", tags=["ocr"])
app.include_router(itr.router, prefix="/api", tags=["itr"])
