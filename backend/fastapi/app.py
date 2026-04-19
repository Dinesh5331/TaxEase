# TaxAssist FastAPI Application -- v2
# Run from the backend/fastapi/ directory:
#   ..\myenv\Scripts\uvicorn.exe app:app --reload --port 8000 --reload-dir ..
#
# This adds backend/ to sys.path so rag/ and ocr/ modules are importable,
# without shadowing the installed 'fastapi' package.

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
        log.warning("⚠️  DB init failed (auth endpoints will be unavailable): %s", db_err)

    # ── 2. Pre-load RAG models ─────────────────────────────────────────────
    log.info("🔄 Loading RAG system — first run may take 30-60 seconds...")
    from rag.main import setup
    from rag.llm import get_model
    from rag.embedder import get_embedding_model
    from rag.reranker import get_reranker

    get_embedding_model()
    get_reranker()
    index, docs = setup()
    model = get_model()

    form_names = sorted(set(d.metadata.get("form_name", "unknown") for d in docs))
    log.info("✅ RAG ready | %d chunks | forms: %s", len(docs), form_names)

    state.app_state["index"] = index
    state.app_state["docs"] = docs
    state.app_state["model"] = model
    state.app_state["form_names"] = form_names
    state.app_state["chunk_count"] = len(docs)

    yield  # ── server is running ──────────────────────────────────────────

    log.info("🛑 TaxAssist server shutting down.")


app = FastAPI(
    title="TaxAssist API",
    description="RAG + OCR + Auth backend for TaxEase UI",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(health.router, tags=["system"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, tags=["rag"])
app.include_router(upload.router, tags=["ocr"])
