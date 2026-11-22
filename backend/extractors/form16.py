"""Form 16 extractor: regex over laid-out text, no LLM.

Every value comes back with the line it was read from, so the UI can show "read from: <line>" and
flag anything that failed an arithmetic cross-check. A field that is not found is reported as
missing, never guessed. (The old LLM extractor stays in ocr/ as a fallback for scanned certificates.)
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

PAN_RE = r"[A-Z]{5}[0-9]{4}[A-Z]"
NUM = r"-?[\d,]+(?:\.\d+)?"


class ExtractionError(Exception):
    pass


def pdf_layout_text(path) -> str:
    """Text with columns kept on one line. poppler first (most faithful), then PyMuPDF words, then pypdf."""
    path = str(path)
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=60)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        import fitz  # PyMuPDF
        lines = []
        for page in fitz.open(path):
            words = page.get_text("words")                       # x0, y0, x1, y1, word, block, line, wno
            rows = {}
            for w in words:
                rows.setdefault(round(w[3] / 3), []).append(w)    # bucket by baseline
            for _, ws in sorted(rows.items()):
                ws.sort(key=lambda w: w[0])
                line, last = "", None
                for w in ws:
                    gap = 0 if last is None else max(1, int((w[0] - last) / 4))
                    line += (" " * gap if gap < 3 else "   ") + w[4]
                    last = w[2]
                lines.append(line)
        text = "\n".join(lines)
        if text.strip():
            return text
    except ImportError:
        pass
    try:
        import pypdf
        r = pypdf.PdfReader(path)
        text = "\n".join(p.extract_text(extraction_mode="layout") or "" for p in r.pages)
        if text.strip():
            return text
    except ImportError:
        pass
    raise ExtractionError("No text layer found. Scanned Form 16 needs the OCR fallback.")


def _num(s: str) -> float:
    return float(s.replace(",", ""))


@dataclass
class Field:
    value: object
    source: str            # the line the value was read from
    confidence: float = 1.0


@dataclass
class Form16:
    fields: dict = field(default_factory=dict)       # name -> Field
    missing: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def get(self, name, default=None):
        f = self.fields.get(name)
        return f.value if f else default

    def to_dict(self):
        return {"fields": {k: {"value": v.value, "source": v.source, "confidence": v.confidence}
                           for k, v in self.fields.items()},
                "missing": self.missing, "warnings": self.warnings}


# name -> regex over a single laid-out line; the amount is the last number on the line.
ITEMS = {
    "gross_salary":        r"\(d\)\s+Total\s+(NUM)\s*$",
    "exempt_allowances":   r"^\s*2\.\s+Less: Allowances.*?\s{2,}(NUM)\s*$",
    "salary_received":     r"^\s*3\.\s+Total amount of salary received.*?\s{2,}(NUM)\s*$",
    "standard_deduction":  r"\(a\)\s+Standard deduction.*?\s{2,}(NUM)\s*$",
    "deductions_sec16":    r"^\s*5\.\s+Total amount of deductions under section 16.*?\s{2,}(NUM)\s*$",
    "income_from_salary":  r"^\s*6\.\s+Income chargeable under the head.*?\s{2,}(NUM)\s*$",
    "other_income_reported": r"^\s*8\.\s+Total amount of other income.*?\s{2,}(NUM)\s*$",
    "gross_total_income":  r"^\s*9\.\s+Gross total income.*?\s{2,}(NUM)\s*$",
    "chapter_vi_a_total":  r"^\s*11\.\s+Aggregate of deductible amount.*?\s{2,}(NUM)\s*$",
    "nps_employer_80ccd2": r"^\s*10\.\s+Deductions under Chapter VI-A.*?\s{2,}(NUM)\s*$",
    "total_taxable_income": r"^\s*12\.\s+Total taxable income.*?\s{2,}(NUM)\s*$",
    "tax_on_total_income": r"^\s*13\.\s+Tax on total income.*?\s{2,}(NUM)\s*$",
    "rebate_87a":          r"^\s*14\.\s+Rebate under section 87A.*?\s{2,}(NUM)\s*$",
    "surcharge":           r"^\s*15\.\s+Surcharge.*?\s{2,}(NUM)\s*$",
    "cess":                r"^\s*16\.\s+Health and education cess.*?\s{2,}(NUM)\s*$",
    "tax_payable":         r"^\s*17\.\s+Tax payable.*?\s{2,}(NUM)\s*$",
    "relief_89":           r"^\s*18\.\s+Less: Relief under section 89.*?\s{2,}(NUM)\s*$",
    "net_tax_payable":     r"^\s*19\.\s+Net tax payable.*?\s{2,}(NUM)\s*$",
}
REQUIRED = ("gross_salary", "income_from_salary", "total_taxable_income", "net_tax_payable")


def parse_form16_text(text: str) -> Form16:
    out = Form16()
    lines = text.splitlines()

    for name, pat in ITEMS.items():
        rx = re.compile(pat.replace("NUM", NUM))
        for ln in lines:
            m = rx.search(ln)
            if m:
                out.fields[name] = Field(_num(m.group(1)), ln.strip())
                break

    # Total row of the quarterly TDS table: amount paid, tax deducted, tax deposited
    rx = re.compile(rf"Total \(Rs\.\)\s+({NUM})\s+({NUM})\s+({NUM})")
    for ln in lines:
        m = rx.search(ln)
        if m:
            out.fields["amount_paid_total"] = Field(_num(m.group(1)), ln.strip())
            out.fields["tds_deducted_total"] = Field(_num(m.group(2)), ln.strip())
            out.fields["tds_deposited_total"] = Field(_num(m.group(3)), ln.strip())
            break

    m = re.search(r"opting out of taxation u/s 115BAC\(1A\)\?\s+(YES|NO)", text, re.I)
    if m:
        out.fields["opted_out_of_new_regime"] = Field(m.group(1).upper() == "YES", m.group(0))

    m = re.search(r"PAN of the Employee.*?(" + PAN_RE + ")", text, re.S)
    if m:
        out.fields["employee_pan"] = Field(m.group(1), "PAN of the Employee")
    m = re.search(r"PAN of the Deductor.*?(" + PAN_RE + ")", text, re.S)
    if m:
        out.fields["employer_pan"] = Field(m.group(1), "PAN of the Deductor")
    m = re.search(r"Assessment Year.*?(\d{4}-\d{2})", text, re.S)
    if m:
        out.fields["assessment_year"] = Field(m.group(1), "Assessment Year")
    m = re.search(r"TAN of the Deductor.*?([A-Z]{4}\d{5}[A-Z])", text, re.S)
    if m:
        out.fields["employer_tan"] = Field(m.group(1), "TAN of the Deductor")

    out.missing = [k for k in REQUIRED if k not in out.fields]
    out.warnings = _cross_checks(out)
    if out.missing:
        out.warnings.append("Required fields not found: " + ", ".join(out.missing) +
                            ". The document may be scanned or a different Form 16 layout.")
    return out


def _cross_checks(f: Form16) -> list:
    """Arithmetic the certificate must satisfy. A failure lowers confidence of the fields involved."""
    w = []
    g = f.get

    def check(label, left, right, names):
        if left is None or right is None:
            return
        if abs(left - right) > 1:
            w.append(f"{label}: {left:,.0f} != {right:,.0f}")
            for n in names:
                if n in f.fields:
                    f.fields[n].confidence = min(f.fields[n].confidence, 0.5)

    if None not in (g("salary_received"), g("deductions_sec16"), g("income_from_salary")):
        check("item 3 - item 5 != item 6", g("salary_received") - g("deductions_sec16"), g("income_from_salary"),
              ["salary_received", "deductions_sec16", "income_from_salary"])
    if None not in (g("income_from_salary"), g("other_income_reported"), g("gross_total_income")):
        check("item 6 + item 8 != item 9", g("income_from_salary") + g("other_income_reported"), g("gross_total_income"),
              ["income_from_salary", "gross_total_income"])
    if None not in (g("gross_total_income"), g("chapter_vi_a_total"), g("total_taxable_income")):
        check("item 9 - item 11 != item 12", g("gross_total_income") - g("chapter_vi_a_total"), g("total_taxable_income"),
              ["gross_total_income", "total_taxable_income"])
    if None not in (g("tax_payable"), g("relief_89"), g("net_tax_payable")):
        check("item 17 - item 18 != item 19", g("tax_payable") - g("relief_89"), g("net_tax_payable"),
              ["tax_payable", "net_tax_payable"])
    if g("tds_deducted_total") is not None and g("net_tax_payable") is not None:
        check("TDS deducted != net tax payable", g("tds_deducted_total"), g("net_tax_payable"),
              ["tds_deducted_total", "net_tax_payable"])
    return w


def extract_form16(path) -> Form16:
    return parse_form16_text(pdf_layout_text(Path(path)))
