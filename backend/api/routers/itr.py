"""ITR selection, regime comparison and late-filing routes. All logic lives in services/ and rules/; this
module only validates input and shapes output. Uploaded files are parsed in memory / a temp file that is
removed before the response; nothing is stored and PAN is masked in every response."""
import json
import os
import tempfile
from dataclasses import asdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from extractors.ais import parse_ais
from extractors.form16 import ExtractionError
from extractors.questionnaire import QUESTIONS
from rules import compliance
from rules.engine import Facts, select_itr
from rules.regime import Inputs, compare
from services.analyze import analyze

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _read_limited(upload: UploadFile) -> bytes:
    data = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{upload.filename}: file larger than 10 MB.")
    return data


@router.get("/itr/questionnaire")
def questionnaire():
    """Questions for the facts no document proves. Answer keys are the question ids."""
    return {"assessment_year": "2026-27", "questions": QUESTIONS}


@router.post("/itr/select")
def select(facts: dict):
    """Rules engine on already-structured facts (no documents)."""
    try:
        return select_itr(Facts.from_dict(facts)).to_dict()
    except TypeError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/itr/analyze")
def analyze_documents(
    ais: UploadFile = File(..., description="AIS JSON downloaded from the e-filing portal"),
    form16: Optional[UploadFile] = File(None, description="Form 16 PDF (text layer)"),
    tis: Optional[UploadFile] = File(None, description="TIS JSON"),
    answers: str = Form("{}", description="JSON object with questionnaire answers"),
):
    try:
        ans = json.loads(answers)
        if not isinstance(ans, dict):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="'answers' must be a JSON object.")
    try:
        ais_json = json.loads(_read_limited(ais))
        tis_json = json.loads(_read_limited(tis)) if tis else None
    except ValueError:
        raise HTTPException(status_code=422, detail="AIS/TIS must be the JSON export from the portal.")

    tmp_path = None
    try:
        if form16:
            if not (form16.filename or "").lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Form 16 must be a PDF.")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(_read_limited(form16))
                tmp_path = tmp.name
        return analyze(tmp_path, ais_json, tis_json, ans)
    except ExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"Could not read the documents: {e}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.post("/regime/compare")
def regime_compare(inputs: Inputs):
    """Old vs new regime for an individual, FY 2025-26."""
    return compare(inputs)


class RouteRequest(BaseModel):
    assessment_year: str = "2026-27"
    today: Optional[date] = None
    filed: bool
    due_kind: str = Field("due_itr1_2", description="due_itr1_2 | due_non_audit_business | due_audit | due_transfer_pricing")
    form_filed: Optional[str] = None
    correct_form: Optional[str] = None
    omitted_income: bool = False
    notice_received: bool = False


@router.post("/compliance/route")
def compliance_route(req: RouteRequest):
    try:
        return compliance.route(req.assessment_year, req.today or date.today(), req.filed, req.due_kind,
                                req.form_filed, req.correct_form, req.omitted_income, req.notice_received)
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Unknown due_kind or assessment year: {e}")
