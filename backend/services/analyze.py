"""One call from documents + answers to a recommendation. No web framework in here, so the same code
serves the FastAPI routes, tests and (Phase 7) an MCP server."""
from __future__ import annotations

from typing import Optional

from extractors.ais import parse_ais, parse_tis
from extractors.facts import build_facts
from extractors.form16 import extract_form16, Form16
from rules.engine import select_itr


def _mask(pan: str) -> str:
    return f"{pan[:2]}{'*' * 6}{pan[-2:]}" if pan and len(pan) == 10 else ""


def _mask_form16(d: dict) -> dict:
    for k in ("employee_pan", "employer_pan"):
        if k in d["fields"]:
            d["fields"][k]["value"] = _mask(d["fields"][k]["value"])
    return d


def analyze(form16_path=None, ais_json=None, tis_json=None, answers: Optional[dict] = None) -> dict:
    """Returns the recommendation, the extracted facts, what is still unknown and what conflicts.
    PAN is masked in the output; the raw documents are not retained."""
    f16: Optional[Form16] = extract_form16(form16_path) if form16_path else None
    ais = parse_ais(ais_json) if ais_json else None
    tis = parse_tis(tis_json) if tis_json else None
    if not (f16 or ais):
        raise ValueError("Provide at least a Form 16 or an AIS.")
    facts, report = build_facts(f16, ais, tis, answers)
    result = select_itr(facts)
    # open questions = engine's missing fields + document-driven gaps already in the report
    return {
        "recommendation": result.to_dict(),
        "facts": {k: v for k, v in facts.__dict__.items()},
        "report": report.to_dict(),
        "taxpayer": {"pan_masked": _mask((ais.pan if ais else "") or (f16.get("employee_pan") if f16 else "")),
                     "assessment_year": (ais.assessment_year if ais else "") or (f16.get("assessment_year") if f16 else "")},
        "form16": _mask_form16(f16.to_dict()) if f16 else None,
        "disclaimer": "Decision support for AY 2026-27 based on the documents and answers given. Rules are tagged by how well "
                      "they are verified in rules/itr_rules.yaml; confirm at incometax.gov.in before filing.",
    }
