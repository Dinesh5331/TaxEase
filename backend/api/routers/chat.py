import logging
import os
import sys
import threading

from fastapi import APIRouter, HTTPException

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
    """Load models + index once per process. Safe to call from concurrent requests."""
    with _load_lock:
        if "index" in app_state:
            return

        from rag.main import setup
        from rag.llm import get_model
        from rag.embedder import get_embedding_model
        from rag.reranker import get_reranker

        log.info("Loading embedding model + reranker")
        get_embedding_model()
        get_reranker()

        log.info("Loading/building FAISS index")
        index, docs = setup()

        app_state["model"] = get_model()
        app_state["docs"] = docs
        app_state["index"] = index  # set last: its presence means everything is ready
        log.info("RAG ready: %d chunks", len(docs))


# Plain `def` (not async): the work is blocking (embeddings, reranker, Groq),
# so FastAPI runs it in its threadpool instead of freezing the event loop.
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if "index" not in app_state:
        try:
            load_rag()
        except Exception as e:
            log.exception("RAG initialization failed")
            raise HTTPException(status_code=500, detail=f"RAG initialization failed: {e}")

    from rag.rag_pipeline import run_rag_cited

    answer, citations = run_rag_cited(
        app_state["model"],
        app_state["index"],
        app_state["docs"],
        req.query.strip(),
        debug=req.debug,
    )
    return ChatResponse(answer=answer, citations=citations)
