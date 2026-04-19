from fastapi import APIRouter, HTTPException
from schemas import HealthResponse
from state import app_state

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check — returns loaded index metadata."""
    if not app_state:
        raise HTTPException(status_code=503, detail="Server is still loading.")
    return HealthResponse(
        status="ok",
        chunk_count=app_state.get("chunk_count", 0),
        forms_indexed=app_state.get("form_names", []),
    )
