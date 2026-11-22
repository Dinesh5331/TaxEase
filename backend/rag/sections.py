"""Section-aware splitting and legal-version metadata for the law corpus.

Statutes are cited by section, so a chunk must not straddle two sections and must carry the Act it
belongs to; otherwise a question about "section 139" can be answered from the 2025 Bill's numbering.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# A statute heading line: "139. (1) Every person ...", "18. (1) For the purposes ...", "234F. Fee for ..."
HEADING = re.compile(r"^\s*(\d{1,3})([A-Z]{0,3})\.\s+(?:\(\d+\)|[A-Z“\"])")
NOISE_LINE = re.compile(r"^\s*\d{1,3}\s*$")           # margin line numbers in the Bill PDFs
MAX_JUMP = 30                                         # a new heading may not skip more than this many sections

# filename -> legal metadata. Explicit, because the filenames in the corpus are misleading
# ("Income-tax_Bill(1962)" is the 1961 Act text).
DOC_META = {
    "Income-tax_Bill(2025).pdf": {"act_version": "2025", "text_status": "bill-as-introduced-superseded", "tax_year": "2026-27"},
    "Income-tax_Bill(1962).pdf": {"act_version": "1961", "text_status": "act", "tax_year": None},
    "Finance_Bill-2026.pdf": {"act_version": "finance-bill-2026", "text_status": "bill", "tax_year": "2026-27"},
    "itr_eligibility_reference.txt": {"act_version": "1961", "text_status": "project-reference", "tax_year": "AY 2026-27"},
    "tax_regime_comparison.txt": {"act_version": "1961", "text_status": "project-reference", "tax_year": "AY 2026-27"},
}


def legal_meta(file_name: str) -> dict:
    if file_name in DOC_META:
        return dict(DOC_META[file_name])
    if file_name.lower().startswith("itr_") and file_name.lower().endswith(".pdf"):
        return {"act_version": "1961", "text_status": "form-instructions", "tax_year": None}
    return {"act_version": "unknown", "text_status": "unknown", "tax_year": None}


@dataclass
class Section:
    number: str            # "139", "234F"
    heading: str           # first line, for display
    text: str
    first_page: int


def _key(num: int, suffix: str):
    return (num, suffix)


def split_sections(pages: list) -> list:
    """pages: list of (page_number, raw_text_with_newlines). Returns Sections in document order.
    Lines before the first heading are kept as a preamble section with number ''."""
    sections, cur = [], None
    prev = None
    for page_no, raw in pages:
        for line in raw.splitlines():
            if NOISE_LINE.match(line):
                continue
            m = HEADING.match(line)
            if m:
                num, suf = int(m.group(1)), m.group(2)
                ok = prev is None or (num > prev[0] and num - prev[0] <= MAX_JUMP) or (num == prev[0] and suf > prev[1])
                if ok:
                    cur = Section(number=f"{num}{suf}", heading=line.strip()[:120], text="", first_page=page_no)
                    sections.append(cur)
                    prev = _key(num, suf)
            if cur is None:
                cur = Section(number="", heading="", text="", first_page=page_no)
                sections.append(cur)
            cur.text += line.strip() + "\n"
    return sections


def chunk_section(sec: Section, max_chars: int = 1400, overlap: int = 150) -> list:
    """Split one section on paragraph/sub-section boundaries; chunks never cross a section."""
    text = " ".join(sec.text.split())
    if len(text) <= max_chars:
        return [text] if text else []
    parts = re.split(r"(?<=[.;:—])\s+(?=\(\d+\)|\([a-z]\)|\([ivx]+\))", text)   # at (2), (a), (iv)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) + 1 > max_chars:
            chunks.append(cur)
            cur = cur[-overlap:] + " " + p if overlap else p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:                                   # a single over-long paragraph: hard split
        while len(c) > max_chars * 1.5:
            out.append(c[:max_chars])
            c = c[max_chars - overlap:]
        out.append(c)
    return out


def section_chunks(pages: list, base_meta: dict) -> list:
    """-> list of (text, metadata) with section, act_version, tax_year, text_status on each chunk."""
    meta = {**base_meta, **legal_meta(base_meta.get("file", ""))}
    out = []
    for sec in split_sections(pages):
        for i, c in enumerate(chunk_section(sec)):
            out.append((c, {**meta, "section": sec.number or None, "section_heading": sec.heading,
                            "page": sec.first_page, "chunk_in_section": i}))
    return out


# ---------------------------------------------------------------- which Act should answer this question?
_NEW_ACT = re.compile(r"income[\s-]*tax act,?\s*2025|new (income[\s-]*tax )?act|tax year 2026-27|tax year 2027|section 263|\bact 30 of 2025\b", re.I)
_OLD_ACT = re.compile(r"assessment year|\bay\b\s*20\d\d|1961|139\(|section 80c\b|itr-?\s?[1-7]\b|form 16|ais\b", re.I)


def choose_act(query: str):
    """'2025', '1961' or None (no filter: both, and the answer must label which Act each rule comes from).
    Returns are for FY 2025-26 / AY 2026-27 filings: the 1961 Act is the default for ITR questions."""
    new, old = bool(_NEW_ACT.search(query)), bool(_OLD_ACT.search(query))
    if new and not old:
        return "2025"
    if old and not new:
        return "1961"
    return None


def filter_by_act(items: list, act: str):
    """Keep chunks of that Act (plus act-neutral project references and form instructions). Never returns empty."""
    if not act:
        return items
    keep = [i for i in items if i["doc"].metadata.get("act_version") in (act, "unknown")
            or i["doc"].metadata.get("text_status") in ("project-reference", "form-instructions")]
    return keep or items
