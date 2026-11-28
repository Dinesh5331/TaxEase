# Backend image. Build context is this folder: docker build -t taxassist-api .
# Needs about 1 GB RAM at runtime (the two sentence-transformer models alone are ~0.5 GB).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV HF_HOME=/app/.hf PYTHONUNBUFFERED=1 PYTHONUTF8=1

# CPU-only torch first, otherwise pip pulls the multi-GB CUDA build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Bake the models and the search index into the image so the first request is not minutes long.
# Only the corpus files present at build time are indexed (*.pdf is not in git).
RUN python -c "from rag.main import setup; from rag.reranker import get_reranker; setup(); get_reranker()"
# Some hosts (Hugging Face Spaces) run the container as a non-root user.
RUN chmod -R a+rwX /app

EXPOSE 7860
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
