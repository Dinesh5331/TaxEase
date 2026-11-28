import os
import tempfile
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from ..state import app_state

log = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/upload")
def upload_form16(file: UploadFile = File(...)):
    """Accept a Form 16 PDF/image, run OCR + AI extraction + RAG ITR recommendation."""
    if "index" not in app_state:
        log.info("[INFO] Initializing RAG pipeline...")
        try:
            from .chat import load_rag
            load_rag()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"RAG initialization failed: {str(e)}")

    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: PDF, PNG, JPG, JPEG.",
        )

    log.info("[INFO] Upload received: %s", file.filename)

    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File larger than 10 MB.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext.lower()) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        log.info("[INFO] Running OCR...")
        from ocr.ocr_loader import extract_text
        raw_text = extract_text(tmp_path)

        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract any text from the file.")

        from ocr.parser import mask_pans, parse_json
        raw_text = mask_pans(raw_text)   # PAN never leaves this process

        log.info("[INFO] Extracting structured data with AI...")
        from ocr.extractor import extract_form16_data
        structured_raw = extract_form16_data(raw_text)
        data = parse_json(structured_raw)

        log.info("[INFO] Running RAG for ITR recommendation...")
        from rag.rag_pipeline import run_rag_result

        itr_query = f"""
User financial details extracted from Form 16:
{data}

Based on the above financial details, determine:
1. Which ITR form should this person file and why?
2. What key eligibility conditions apply?
"""
        itr_recommendation = run_rag_result(
            app_state["model"],
            app_state["index"],
            app_state["docs"],
            itr_query,
            index_meta=app_state.get("index_meta"),
            search_query="Which ITR form should a salaried individual file for AY 2026-27, and who is eligible?",
        ).answer

        return {
            "success": True,
            "file_name": file.filename,
            "extracted_data": data,
            "itr_recommendation": itr_recommendation,
        }

    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Upload pipeline error")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
