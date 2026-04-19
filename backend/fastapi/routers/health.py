from fastapi import APIRouter

from schemas import HealthResponse
from state import app_state

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check that reports API availability and lazy RAG readiness."""
    rag_loaded = "index" in app_state and "docs" in app_state and "model" in app_state
    return HealthResponse(
        status="ok",
        rag_loaded=rag_loaded,
        chunk_count=app_state.get("chunk_count", 0),
        forms_indexed=app_state.get("form_names", []),
    )
