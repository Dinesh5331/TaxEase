"""Citations returned with every answer: which document, section, Act and page each context chunk came from."""
from __future__ import annotations

SNIPPET_CHARS = 220


def build_citations(items) -> list:
    out, seen = [], set()
    for it in items:
        m = it["doc"].metadata
        key = (m.get("file"), m.get("section"), m.get("page"))
        if key in seen:
            continue
        seen.add(key)
        sec = m.get("section")
        unit = "rule" if m.get("text_status") == "rules" else "section"   # Rules are numbered, not sectioned
        out.append({
            "document": m.get("document_name") or m.get("file") or "unknown",
            "file": m.get("file"),
            "section": sec,
            "label": f"{m.get('document_name') or m.get('file')}" + (f", {unit} {sec}" if sec else "") + f", p.{m.get('page', '?')}",
            "act_version": m.get("act_version", "unknown"),
            "text_status": m.get("text_status", "unknown"),
            "page": m.get("page"),
            "source": m.get("source"),
            "score": round(float(it.get("rerank_score", it.get("hybrid_score", 0.0))), 3),
            "snippet": " ".join(it["doc"].page_content.split())[:SNIPPET_CHARS],
        })
    return out
