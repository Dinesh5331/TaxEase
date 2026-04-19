from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
from state import app_state

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Run a RAG query against the indexed tax documents."""
    if not app_state:
        raise HTTPException(status_code=503, detail="RAG system is still initializing. Please wait.")

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    from rag.rag_pipeline import run_rag

    answer = run_rag(
        app_state["model"],
        app_state["index"],
        app_state["docs"],
        req.query.strip(),
        debug=req.debug,
    )
    return ChatResponse(answer=answer)
