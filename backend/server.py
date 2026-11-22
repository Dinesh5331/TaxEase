# server.py – entry point for: uvicorn server:app --reload
# This re-exports the FastAPI app from api.app so uvicorn can find it.
from api.app import app  # noqa: F401
