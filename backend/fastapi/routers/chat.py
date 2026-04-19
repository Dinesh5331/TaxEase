from fastapi import APIRouter, HTTPException
from schemas import ChatRequest, ChatResponse
from state import app_state

import os
import requests
import zipfile

router = APIRouter()

os.environ["CUDA_VISIBLE_DEVICES"] = ""


def download_docs():
    if not os.path.exists("rag/docs") or not os.listdir("rag/docs"):
        print("⬇️ Downloading RAG docs...")

        url = "https://www.dropbox.com/scl/fi/1fvh9c3dtjzjsrm07w3qj/docs.zip?rlkey=79qr29zuakm0kf6ck4rp0szi6&st=9ubwk8o2&dl=1"

        r = requests.get(url, timeout=30)

        with open("docs.zip", "wb") as f:
            f.write(r.content)

        if not zipfile.is_zipfile("docs.zip"):
            raise Exception("❌ Not a valid zip")

        with zipfile.ZipFile("docs.zip", 'r') as zip_ref:
            zip_ref.extractall("rag/docs")

        print("✅ Docs ready")


def load_rag():
    from rag.main import setup
    from rag.llm import get_model
    from rag.embedder import get_embedding_model
    from rag.reranker import get_reranker

    download_docs()

    print("🔄 Loading embedding + reranker...")
    get_embedding_model()
    get_reranker()

    print("🔄 Building FAISS index...")
    index, docs = setup()

    print("🔄 Loading LLM...")
    model = get_model()

    app_state["index"] = index
    app_state["docs"] = docs
    app_state["model"] = model

    print("✅ FAISS RAG loaded successfully")


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if "index" not in app_state:
        try:
            load_rag()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"RAG initialization failed: {str(e)}")

    from rag.rag_pipeline import run_rag

    answer = run_rag(
        app_state["model"],
        app_state["index"],
        app_state["docs"],
        req.query.strip(),
        debug=req.debug,
    )

    return ChatResponse(answer=answer)