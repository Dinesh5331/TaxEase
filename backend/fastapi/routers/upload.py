import os
import tempfile
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from state import app_state

log = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


@router.post("/upload")
async def upload_form16(file: UploadFile = File(...)):
    """Accept a Form 16 PDF/image, run OCR + AI extraction + RAG ITR recommendation."""
    if not app_state:
        raise HTTPException(status_code=503, detail="Server is still initializing.")

    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: PDF, PNG, JPG, JPEG.",
        )

    log.info("📄 Upload received: %s", file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext.lower()) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        log.info("🔍 Running OCR...")
        from ocr.ocr_loader import extract_text
        raw_text = extract_text(tmp_path)

        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract any text from the file.")

        log.info("🧠 Extracting structured data with AI...")
        from ocr.extractor import extract_form16_data
        from ocr.parser import parse_json
        structured_raw = extract_form16_data(raw_text)
        data = parse_json(structured_raw)

        log.info("📚 Running RAG for ITR recommendation...")
        from rag.rag_pipeline import run_rag

        itr_query = f"""
User financial details extracted from Form 16:
{data}

Based on the above financial details, determine:
1. Which ITR form should this person file and why?
2. What key eligibility conditions apply?
"""
        itr_recommendation = run_rag(
            app_state["model"],
            app_state["index"],
            app_state["docs"],
            itr_query,
        )

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
