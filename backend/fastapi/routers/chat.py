from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
from state import app_state

import os
import requests
import zipfile

router = APIRouter()


# 🔥 Download docs (if not present)
def download_docs():
    if not os.path.exists("rag/docs"):
        print("⬇️ Downloading RAG docs...")

        url = "https://drive.google.com/file/d/1O1DVC9c-BOBqrojsSLsUCK9bIkDC4KhG"  # ← replace this

        r = requests.get(url)

        with open("docs.zip", "wb") as f:
            f.write(r.content)

        with zipfile.ZipFile("docs.zip", 'r') as zip_ref:
            zip_ref.extractall("rag/docs")

        print("✅ Docs ready")


# 🔥 Load RAG (FAISS)
def load_rag():
    from rag.main import setup
    from rag.llm import get_model
    from rag.embedder import get_embedding_model
    from rag.reranker import get_reranker

    download_docs()

    get_embedding_model()
    get_reranker()

    index, docs = setup()
    model = get_model()

    app_state["index"] = index
    app_state["docs"] = docs
    app_state["model"] = model

    print("✅ FAISS RAG loaded")


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 🔥 Lazy load RAG
    if "index" not in app_state:
        load_rag()

    from rag.rag_pipeline import run_rag

    answer = run_rag(
        app_state["model"],
        app_state["index"],
        app_state["docs"],
        req.query.strip(),
        debug=req.debug,
    )

    return ChatResponse(answer=answer)