import logging
import os
import sys
import threading

from fastapi import APIRouter, HTTPException

from rag.rag_pipeline import MAX_QUERY_CHARS, run_rag_result

from ..schemas import ChatRequest, ChatResponse
from ..state import app_state

# Ensure stdout uses UTF-8 to avoid charmap errors on Windows when printing emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

log = logging.getLogger(__name__)
router = APIRouter()

os.environ["CUDA_VISIBLE_DEVICES"] = ""

_load_lock = threading.Lock()


def load_rag():
    """Load models + index once per process. Safe to call from concurrent requests. A model that will not load
    is skipped (the pipeline falls back); only a missing index is fatal."""
    with _load_lock:
        if "index" in app_state:
            return

        from rag.main import setup
        from rag.llm import get_model
        from rag.embedder import get_embedding_model
        from rag.reranker import get_reranker

        for name, load in (("embedding model", get_embedding_model), ("reranker", get_reranker)):
            try:
                load()
            except Exception:
                log.exception("Could not load the %s; continuing without it", name)

        log.info("Loading/building FAISS index")
        index, docs, meta = setup()
        if meta.get("stale"):
            log.error("Serving an older index because the rebuild failed: %s", meta["stale"])

        try:
            app_state["model"] = get_model()
        except Exception:
            log.exception("Language model client unavailable; answers will list sources only")
            app_state["model"] = None
        app_state["docs"] = docs
        app_state["index_meta"] = meta
        app_state["index"] = index  # set last: its presence means everything is ready
        log.info("RAG ready: %d chunks, index %s", len(docs), meta.get("version"))


# Plain `def` (not async): the work is blocking (embeddings, reranker, Groq),
# so FastAPI runs it in its threadpool instead of freezing the event loop.
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(req.query) > MAX_QUERY_CHARS:
        raise HTTPException(status_code=413, detail=f"Query is longer than {MAX_QUERY_CHARS} characters.")

    if "index" not in app_state:
        try:
            load_rag()
        except Exception:
            log.exception("RAG initialization failed")
            raise HTTPException(status_code=503, detail="Search is unavailable right now. Try again later.")

    result = run_rag_result(
        app_state["model"],
        app_state["index"],
        app_state["docs"],
        req.query.strip(),
        debug=req.debug,
        index_meta=app_state.get("index_meta"),
    )
    return ChatResponse(answer=result.answer, citations=result.citations, status=result.status,
                        trace_id=result.trace_id)
