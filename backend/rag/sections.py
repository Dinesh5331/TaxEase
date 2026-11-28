"""Section-aware splitting and legal-version metadata for the law corpus.

Statutes are cited by section, so a chunk must not straddle two sections and must carry the Act it
belongs to; otherwise a question about "section 139" can be answered from the 2025 Bill's numbering.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# A statute heading line: "139. (1) Every person ...", "18. (1) For the purposes ...", "234F. Fee for ..."
HEADING = re.compile(r"^\s*(\d{1,3})((?:-?[A-Z]{1,5})?)\.(?:\s*(?:\d{0,3}\[)?\(\d+\)|\s+(?:\d{0,3}\[)?(?:[A-Z“\"]|\*\*\*))")      # "262.(1)" has no space
NOISE_LINE = re.compile(r"^\s*\d{1,3}\s*$")           # margin line numbers in the Bill PDFs
MAX_JUMP = 30                                         # a new heading may not skip more than this many sections

ENACTING = re.compile(r"BE it enacted", re.I)       # everything before this in a Bill is cover page + table of clauses
TOC_ENTRY = re.compile(r"^\s*(\d{1,3}[A-Z]{0,5})\.\s+([A-Z“].{3,200}?)\.\s*$")
SCHEDULE = re.compile(r"^\s*(?:THE\s+[A-Z]+\s+SCHEDULE|SCHEDULE\s+[IVXL]+|APPENDIX[\s-]*[IVX]*)\s*$")

# Amendment footnotes at the foot of a page ("  43.<tab>Substituted for ... by the Finance Act, 2026") are numbered
# like headings but indented; real headings start at the margin.
FOOTNOTE = re.compile(r"^[ \t]+\d{1,3}\.\s+(?:Substituted|Inserted|Omitted|Words?|Sub-|Clauses?|Sections?|Provisos?|"
                      r"Explanation|Shall|The |Figures|Item|Brackets|Renumbered)")

# The incometaxindia.gov.in copy of the 1961 Act: footnotes start at the margin ("4. Ins. by Act No. 7 of 2025,
# w.e.f. ...") and every page ends with a department footer.
PORTAL_FOOTNOTE = re.compile(r"^\d{1,3}[a-z]{0,2}\.\s*(?:Sub|Ins|Omtt|Omitted|Words?|Brackets|Figures|Clauses?|Section|"
                             r"Prior|Proviso|Explanation|Renumbered|The |Earlier|Second|Third|Fourth|First)")
AMENDING = re.compile(r"Act No\.|w\.(?:r\.)?e\.f|by the .{0,30}Act")
PAGE_FOOTER = re.compile(r"^\s*(?:Income Tax Department|Ministry of Finance, Government of India|Downloaded/Printed on .*)\s*$")

# filename -> display title used in the heading prefix of each chunk
TITLES = {"Income-tax_Bill(2025)-amended(2026).pdf": "Income-tax Act 2025 (as amended by Finance Act 2026)",
          "Income-tax_Bill(1961).pdf": "Income-tax Act 1961 (as amended by Finance Act 2026)",
          "Income-tax_Bill(1962).pdf": "Income-tax Rules 1962",
          "Finance_Bill-2026.pdf": "Finance Bill 2026"}

# filename -> legal metadata. Explicit, because the filenames in the corpus are misleading
# ("Income-tax_Bill(1962)" is the Income-tax Rules, 1962, made under the 1961 Act; it is NOT the Act itself).
DOC_META = {
    "Income-tax_Bill(2025)-amended(2026).pdf": {"act_version": "2025", "text_status": "act", "tax_year": "2026-27"},
    "Income-tax_Bill(1961).pdf": {"act_version": "1961", "text_status": "act", "tax_year": None},
    "Income-tax_Bill(1962).pdf": {"act_version": "1961", "text_status": "rules", "tax_year": None},
    "Finance_Bill-2026.pdf": {"act_version": "finance-bill-2026", "text_status": "bill", "tax_year": "2026-27"},
    "itr_eligibility_reference.txt": {"act_version": "1961", "text_status": "project-reference", "tax_year": "AY 2026-27"},
    "tax_regime_comparison.txt": {"act_version": "1961", "text_status": "project-reference", "tax_year": "AY 2026-27"},
}


# Corpus files that must never be indexed: answering from superseded law is worse than not answering.
EXCLUDED = {
    "Income_Tax_Act_1961.pdf": "text as amended by Finance Act 2008; no 115BAC, 234F, 270A, 44ADA or updated returns",
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


def strip_front_matter(pages: list):
    """-> (body_pages, {section_number: title}). A Bill opens with a table of clauses whose entries look exactly
    like headings; indexing it as the body once left most of the 2025 Bill labelled "section 536"."""
    for i, (page_no, raw) in enumerate(pages):
        m = ENACTING.search(raw)
        if m:
            titles = {}
            for _, front in pages[:i] + [(page_no, raw[:m.start()])]:
                for line in front.splitlines():
                    t = TOC_ENTRY.match(line)
                    if t:
                        titles.setdefault(t.group(1), t.group(2).strip())
            return [(page_no, raw[m.start():])] + pages[i + 1:], titles
    return pages, {}


def drop_footnotes(raw: str) -> str:
    """Cut the footnote block at the foot of a page. Also removes soft hyphens, which hide headings and words."""
    lines = raw.replace("­", "").splitlines()
    for i, line in enumerate(lines):
        if (FOOTNOTE.match(line) and "Finance Act" in " ".join(lines[i:i + 4])
                # a section heading (at the margin) further down means this was a table row, not the footnotes
                and not any(l[:1].isdigit() and HEADING.match(l) for l in lines[i + 1:])):
            return "\n".join(lines[:i])
    return "\n".join(lines)


def drop_portal_noise(raw: str) -> str:
    """Remove the page footer and cut the footnote block (which quotes repealed wording)."""
    lines = [l for l in raw.replace("­", "").replace(" ", " ").splitlines() if not PAGE_FOOTER.match(l)]
    for i, line in enumerate(lines):
        if (PORTAL_FOOTNOTE.match(line) and AMENDING.search(" ".join(lines[i:i + 3]))
                # "149. (1) ..." further down means this was not yet the footnote block
                and not any(re.match(r"\d{1,3}[A-Z]{0,5}\.\s*\(1\)", l) for l in lines[i + 1:])):
            return "\n".join(lines[:i])
    return "\n".join(lines)


def restore_displaced_pages(pages: list) -> list:
    """The portal copy puts section 139 in front of the title page. Move such pages back to where their first
    section number belongs; left in front, they would be discarded as front matter."""
    start = next((i for i, (_, raw) in enumerate(pages) if ENACTING.search(raw)), 0)
    front, body = pages[:start], pages[start:]
    first = next((m for _, raw in front for m in map(HEADING.match, raw.splitlines()) if m), None)
    if not first:
        return pages
    key = (int(first.group(1)), first.group(2))
    for i, (_, raw) in enumerate(body):
        for line in raw.splitlines():
            m = HEADING.match(line)
            # the first heading shortly after it, e.g. 139A after 139
            if m and key < (int(m.group(1)), m.group(2)) and int(m.group(1)) - key[0] <= 2:
                return body[:i] + front + body[i:]
    return pages


def swap_inverted_pages(pages: list) -> list:
    """The portal copy also prints a few neighbouring sections in the wrong order (150 before 149). Swap two
    adjacent pages when the second opens, within its first lines, with the section just below the first's."""
    pages = list(pages)
    for i in range(len(pages) - 1):
        here = next((m for m in map(HEADING.match, pages[i][1].splitlines()) if m), None)
        opening = next((m for m in map(HEADING.match, pages[i + 1][1].splitlines()[:3]) if m), None)
        if here and opening and int(here.group(1)) - int(opening.group(1)) == 1:
            pages[i], pages[i + 1] = pages[i + 1], pages[i]
    return pages


def margin_title(before: str) -> str:
    """The enacted Act prints each section's title on the line(s) above its number. `before` is the text of the
    preceding section; the title is its trailing sentence."""
    lines = [l.strip() for l in before.splitlines() if l.strip()]
    if not lines or not lines[-1].endswith(".") or not lines[-1][:1].isalpha():
        return ""
    title = [lines[-1]]
    for line in reversed(lines[-3:-1]):
        if title[0][:1].isupper() or line.endswith((".", ";", ":", "—", "-")) or line.isupper() or ".—" in line:
            break
        title.insert(0, line)
    text = " ".join(title).rstrip(".")
    return text if text[:1].isupper() and len(text) <= 200 else ""


def _heading_chain(candidates: list) -> set:
    """candidates: [(line_index, (number, suffix))]. Returns the line indexes of the longest increasing run with no
    jump above MAX_JUMP. A greedy scan lets one stray "99." in a table block every real heading after it."""
    best, prev = [], []
    for i, (_, (num, suf)) in enumerate(candidates):
        length, back = 1, None
        for j in range(i):
            n2, s2 = candidates[j][1]
            if (n2, s2) < (num, suf) and num - n2 <= MAX_JUMP and best[j] + 1 > length:
                length, back = best[j] + 1, j
        best.append(length)
        prev.append(back)
    if not best:
        return set()
    i = max(range(len(best)), key=best.__getitem__)
    chain = set()
    while i is not None:
        chain.add(candidates[i][0])
        i = prev[i]
    return chain


def split_sections(pages: list) -> list:
    """pages: list of (page_number, raw_text_with_newlines). Returns Sections in document order.
    Lines before the first heading are a preamble section with number ''; schedules/appendices after the last
    heading get number '' too, so they are never cited as the last section."""
    lines = [(page_no, line) for page_no, raw in pages for line in raw.splitlines() if not NOISE_LINE.match(line)]
    candidates = []
    for i, (_, line) in enumerate(lines):
        m = HEADING.match(line)
        if m:
            candidates.append((i, (int(m.group(1)), m.group(2).lstrip("-"))))
    chain = _heading_chain(candidates)
    last_heading = max(chain, default=-1)

    sections, cur = [], None
    for i, (page_no, line) in enumerate(lines):
        if i in chain:
            m = HEADING.match(line)
            cur = Section(number=f"{m.group(1)}{m.group(2).lstrip('-')}", heading=line.strip()[:120], text="", first_page=page_no)
            sections.append(cur)
        elif i > last_heading >= 0 and SCHEDULE.match(line):
            cur = Section(number="", heading=" ".join(line.split()), text="", first_page=page_no)
            sections.append(cur)
        if cur is None:
            cur = Section(number="", heading="", text="", first_page=page_no)
            sections.append(cur)
        cur.text += line.strip() + "\n"
    return sections


# all-MiniLM-L6-v2 reads at most 256 tokens; anything beyond is invisible to dense search. 800 characters plus the
# heading prefix stays within that for ordinary statute prose.
MAX_CHUNK_CHARS = 800


def chunk_section(sec: Section, max_chars: int = MAX_CHUNK_CHARS, overlap: int = 100) -> list:
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
        while len(c) > max_chars * 1.25:
            cut = c.rfind(" ", max_chars // 2, max_chars)
            cut = cut if cut > 0 else max_chars
            out.append(c[:cut])
            c = c[c.find(" ", cut - overlap) + 1 or cut:]
        out.append(c)
    return out


def section_chunks(pages: list, base_meta: dict) -> list:
    """-> list of (text, metadata) with section, act_version, tax_year, text_status on each chunk. Every chunk is
    prefixed with its document and section heading, so a later part of a long section still says what it is."""
    meta = {**base_meta, **legal_meta(base_meta.get("file", ""))}
    doc_title = TITLES.get(base_meta.get("file", ""), base_meta.get("file", ""))
    unit = "rule" if meta["text_status"] == "rules" else "section"
    if meta["text_status"] == "act":
        pages = swap_inverted_pages(restore_displaced_pages(
            [(n, drop_footnotes(drop_portal_noise(raw))) for n, raw in pages]))
    body, titles = strip_front_matter(pages)
    sections = split_sections(body)
    if meta["text_status"] == "act":                       # no table of sections: titles precede each section
        for before, sec in zip(sections, sections[1:]):
            if sec.number:
                titles[sec.number] = margin_title(before.text)
    out = []
    for sec in sections:
        title = titles.get(sec.number, "")
        if sec.number:
            label = f"{unit} {sec.number}" + (f": {title}" if title else "")
        else:
            label = sec.heading
        prefix = f"[{doc_title}{', ' + label if label else ''}] "
        for i, c in enumerate(chunk_section(sec)):
            out.append((prefix + c, {**meta, "section": sec.number or None, "section_heading": title or sec.heading,
                                     "page": sec.first_page, "chunk_in_section": i}))
    return out


# ---------------------------------------------------------------- which Act should answer this question?
_NEW_ACT = re.compile(r"income[\s-]*tax (?:act|bill),?\s*2025|\b2025 (?:act|bill)\b|new (income[\s-]*tax )?act|tax year 2026-27|tax year 2027|section 263|\bact 30 of 2025\b", re.I)
_OLD_ACT = re.compile(r"assessment year|\bay\b\s*20\d\d|1961|139\(|section 80c\b|\bitr\b|form 16|\bais\b|updated return|belated|"
                      r"revised return|late filing|due date|234[a-f]\b|270a\b", re.I)


def choose_act(query: str):
    """'2025', '1961' or None (no filter: both, and the answer must label which Act each rule comes from).
    Returns are for FY 2025-26 / AY 2026-27 filings: the 1961 Act is the default for ITR questions."""
    new, old = bool(_NEW_ACT.search(query)), bool(_OLD_ACT.search(query))
    if new and not old:
        return "2025"
    if old and not new:
        return "1961"
    return None


def matches_act(meta: dict, act: str) -> bool:
    """Is this chunk usable for a question about `act`? Project notes always are; ITR form instructions are
    1961-Act documents, so they never answer a 2025-Act question."""
    if not act:
        return True
    status = meta.get("text_status")
    if status == "project-reference" or (status == "form-instructions" and act == "1961"):
        return True
    return meta.get("act_version") in (act, "unknown")


def filter_by_act(items: list, act: str):
    """Keep items that match the Act. Never returns empty."""
    return [i for i in items if matches_act(i["doc"].metadata, act)] or items
