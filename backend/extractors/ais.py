"""AIS / TIS parsers. Input is the JSON the portal offers (the PDF is password protected).

Real AIS JSON could not be obtained for this project: the layout below follows the portal's documented
tabs (Part A; Part B: TDS/TCS, SFT, Payment of Taxes, Demand and Refund, Other Information; reported
vs modified value). Harden against a real file before launch.

Rules: use the modified value when the taxpayer gave feedback, skip rows whose status is not Active,
and never drop an unknown code silently: it is listed in `unmapped`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

# information code -> bucket name. Exact match only: a prefix match would file TDS-194C under dividend (TDS-194).
CODE_MAP = {
    "TDS-192": "salary",
    "TDS-194A": "interest_other",
    "TDS-194": "dividend",
    "TDS-194IA": "property_sale",
    "TDS-194S": "vda_transfer",
    "TDS-194J": "professional_fees_tds",
    "TDS-194N": "cash_withdrawal_194N",
    "TDS-194B": "lottery_gambling",
    "TDS-194BB": "lottery_gambling",
    "SFT-016(SB)": "interest_savings",
    "SFT-016(TD)": "interest_other",
    "SFT-017": "securities_sale_consideration",
    "SFT-015": "mf_purchase",
    "SFT-012": "foreign_remittance_sft",
    "OTH-RENT": "rent_received",
    "OTH-GST": "gst_turnover",
    "OTH-FIRM": "firm_income",
    "TCS-206C(1G)": "lrs_remittance",
    "TAX-ADV": "advance_tax_paid",
    "TAX-SELF": "self_assessment_tax_paid",
}

TIS_TO_BUCKET = {
    "Salary": ["salary"],
    "Interest from savings bank": ["interest_savings"],
    "Interest from deposit / other": ["interest_other"],
    "Dividend": ["dividend"],
    "Rent received": ["rent_received"],
    "Sale of securities and units of mutual fund": ["securities_sale_consideration"],
    "Purchase of units of mutual fund": ["mf_purchase"],
    "Sale of immovable property": ["property_sale"],
    "Virtual digital asset transfer": ["vda_transfer"],
    "Business receipts (GST / TDS 194J)": ["gst_turnover", "professional_fees_tds", "firm_income"],
    "Foreign remittance (LRS)": ["lrs_remittance"],
}


def bucket_for(code: str):
    return CODE_MAP.get(code)


def _value(row: dict) -> float:
    """Modified value if the taxpayer gave feedback, else reported value, else the raw amount."""
    for k in ("modified_value", "reported_value", "amount_paid", "amount"):
        if row.get(k) is not None:
            return float(row[k])
    return 0.0


@dataclass
class Ais:
    pan: str = ""
    name: str = ""
    dob: str = ""
    assessment_year: str = ""
    totals: dict = field(default_factory=dict)       # bucket -> amount
    tds_total: float = 0.0
    rows_used: int = 0
    unmapped: list = field(default_factory=list)     # rows with an unknown information code
    disputed: list = field(default_factory=list)     # rows where modified != reported
    skipped: list = field(default_factory=list)      # rows that are not Active

    def amount(self, bucket: str) -> float:
        return self.totals.get(bucket, 0.0)

    def has(self, bucket: str) -> bool:
        return self.totals.get(bucket, 0.0) > 0


def parse_ais(data) -> Ais:
    if isinstance(data, (str, bytes)):
        data = json.loads(data)
    if "part_b" not in data or "part_a" not in data:
        raise ValueError("Not an AIS JSON: expected 'part_a' and 'part_b'.")
    a = Ais(pan=data["part_a"].get("pan", ""), name=data["part_a"].get("name", ""),
            dob=data["part_a"].get("date_of_birth", ""),
            assessment_year=data.get("meta", {}).get("assessment_year", ""))
    for tab, rows in data["part_b"].items():
        for r in rows:
            code = r.get("information_code", "")
            if r.get("status", "Active") != "Active":
                a.skipped.append({"tab": tab, "code": code, "status": r.get("status")})
                continue
            b = bucket_for(code)
            if b is None:
                a.unmapped.append({"tab": tab, "code": code, "description": r.get("description"), "amount": _value(r)})
                continue
            v = _value(r)
            a.totals[b] = a.totals.get(b, 0.0) + v
            a.rows_used += 1
            a.tds_total += float(r.get("tax_deducted") or 0)
            if r.get("reported_value") is not None and r.get("modified_value") is not None \
                    and r["reported_value"] != r["modified_value"]:
                a.disputed.append({"code": code, "reported": r["reported_value"], "modified": r["modified_value"]})
    return a


@dataclass
class Tis:
    pan: str = ""
    categories: dict = field(default_factory=dict)   # category -> {"processed": x, "derived": y}


def parse_tis(data) -> Tis:
    if isinstance(data, (str, bytes)):
        data = json.loads(data)
    if "summary" not in data:
        raise ValueError("Not a TIS JSON: expected 'summary'.")
    t = Tis(pan=data.get("pan", ""))
    for r in data["summary"]:
        t.categories[r["category"]] = {"processed": float(r.get("processed_value", 0)),
                                       "derived": float(r.get("derived_value", 0))}
    return t


def cross_check(ais: Ais, tis: Tis) -> list:
    """Differences between AIS totals and the TIS derived values; the TIS is what the department will compare."""
    issues = []
    if ais.pan and tis.pan and ais.pan != tis.pan:
        issues.append(f"PAN differs between AIS and TIS ({ais.pan[:2]}***{ais.pan[-2:]} vs {tis.pan[:2]}***{tis.pan[-2:]}).")
    for cat, v in tis.categories.items():
        buckets = TIS_TO_BUCKET.get(cat)
        if buckets is None:
            issues.append(f"TIS category '{cat}' is not mapped; check it by hand.")
            continue
        got = sum(ais.amount(b) for b in buckets)
        if abs(got - v["derived"]) > 1:
            issues.append(f"{cat}: AIS rows total {got:,.0f} but TIS derived value is {v['derived']:,.0f}.")
    return issues
