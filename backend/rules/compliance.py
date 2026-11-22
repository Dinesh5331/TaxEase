"""
Missed / late / wrong-form return routing and cost, under the Income-tax Act 1961 (AY 2026-27 and earlier).
Sections: 139(1) timely, 139(4) belated, 139(5) revised, 139(8A)+140B updated (ITR-U), 139(9) defective,
234A interest, 234F late fee, 270A penalty. Act 2025 equivalents are in itr_rules.yaml (`act_2025_mapping`).

Dates/fees were taken from CBDT notifications as reported by secondary sources (see itr_rules.yaml `compliance`);
re-verify against incometax.gov.in before relying on them for a real filing.
"""
import calendar
from datetime import date

ITR_U_BANDS = [(12, 0.25), (24, 0.50), (36, 0.60), (48, 0.70)]   # months after end of AY -> additional tax rate
PENALTY_270A = {"under_reporting": 0.50, "misreporting": 2.00}


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def ay_dates(ay: str) -> dict:
    """ay like '2026-27'. Individuals/HUF non-audit ITR-1/2 due 31 Jul; business non-audit 31 Aug (AY 2026-27)."""
    y = int(ay[:4])
    return dict(
        due_itr1_2=date(y, 7, 31), due_non_audit_business=date(y, 8, 31), due_audit=date(y, 10, 31),
        due_transfer_pricing=date(y, 11, 30), belated=date(y, 12, 31), revised=date(y + 1, 3, 31),
        ay_end=date(y + 1, 3, 31), itr_u_last=add_months(date(y + 1, 3, 31), 48),
    )


def late_fee_234f(total_income: float, filed_on: date, due: date) -> int:
    if filed_on <= due:
        return 0
    return 1_000 if total_income <= 500_000 else 5_000


def interest_234a(unpaid_tax: float, due: date, paid_on: date) -> int:
    """1% per month or part of month on tax unpaid after the due date. All return due dates are month-ends."""
    if paid_on <= due or unpaid_tax <= 0:
        return 0
    months = (paid_on.year - due.year) * 12 + (paid_on.month - due.month)
    return round(unpaid_tax * 0.01 * months)


def itr_u_additional_rate(ay: str, filed_on: date):
    """Additional tax rate on tax+interest for an updated return, or None if outside the 48-month window."""
    end = ay_dates(ay)["ay_end"]
    for months, rate in ITR_U_BANDS:
        if filed_on <= add_months(end, months):
            return rate
    return None


def itr_u_additional_tax(tax_and_interest_payable: float, ay: str, filed_on: date):
    r = itr_u_additional_rate(ay, filed_on)
    return None if r is None else round(tax_and_interest_payable * r)


def penalty_270a(tax_on_under_reported_income: float, misreporting: bool = False) -> int:
    return round(tax_on_under_reported_income * PENALTY_270A["misreporting" if misreporting else "under_reporting"])


def route(ay: str, today: date, filed: bool, due_kind: str = "due_itr1_2", form_filed: str = None,
          correct_form: str = None, omitted_income: bool = False, notice_received: bool = False) -> dict:
    """Which filing route is open, its deadline, its extra cost and its restrictions."""
    d = ay_dates(ay)
    due = d[due_kind]
    wrong_form = bool(filed and form_filed and correct_form and form_filed != correct_form)
    out = dict(assessment_year=ay, today=today.isoformat(), options=[], warnings=[])

    def opt(name, section, deadline, costs, restrictions=()):
        out["options"].append(dict(route=name, section=section, deadline=deadline.isoformat(), costs=list(costs),
                                   restrictions=list(restrictions)))

    if not filed:
        if today <= due:
            opt("File original return", "139(1)", due, ["No late fee or 234A interest"])
        elif today <= d["belated"]:
            opt("File belated return", "139(4)", d["belated"],
                ["Late fee u/s 234F: Rs 1,000 if total income <= Rs 5L else Rs 5,000 (even if no tax due)",
                 "Interest u/s 234A: 1% per month or part on unpaid tax from the due date"],
                ["Business and capital losses cannot be carried forward",
                 "Old regime unavailable to a non-business individual (opt-out must be on/before due date)  [verify]"])
        elif today <= d["itr_u_last"]:
            r = itr_u_additional_rate(ay, today)
            opt("File updated return (ITR-U)", "139(8A) + 140B", d["itr_u_last"],
                [f"Tax + 234A/B/C interest + 234F fee, plus additional tax of {int(r * 100)}% of tax+interest payable"],
                ["Cannot reduce tax, create a loss or claim/increase a refund", "Cannot be revised",
                 "Not available once certain proceedings/notices are pending  [verify]"])
        else:
            out["warnings"].append("All statutory windows have passed; only condonation of delay u/s 119(2)(b) is left, at the CBDT's discretion.")
        out["warnings"].append("A non-filer with significant AIS activity risks a notice (e.g. s.148/148A); filing sooner is cheaper.")
    else:
        if wrong_form or omitted_income:
            if today <= d["revised"]:
                opt("File revised return on the correct form" if wrong_form else "File revised return", "139(5)", d["revised"],
                    ["No additional tax; pay any extra tax with interest u/s 234B/234C",
                     "Reported: a fee applies if revised after 31 Dec of the AY  [verify, Finance Act 2026]"],
                    ["Original return must have been filed under 139(1)/(4); revised return can change the ITR form"])
            if today <= d["itr_u_last"] and omitted_income and today > d["revised"]:
                r = itr_u_additional_rate(ay, today)
                opt("File updated return (ITR-U)", "139(8A) + 140B", d["itr_u_last"],
                    [f"Additional tax of {int(r * 100)}% of tax+interest on the extra income"],
                    ["Only if it INCREASES tax; no refund claims"])
            if wrong_form:
                out["warnings"].append("Using an ineligible form makes the return defective (s.139(9)): fix within the notice period "
                                       "(15 days unless extended) or it may be treated as not filed, bringing back 234F/234A.  [verify]")
        if omitted_income:
            out["warnings"].append("If the department finds the omission first: penalty u/s 270A = 50% of tax on under-reported income "
                                   "(200% if misreporting) plus 234B/234C interest.")
        if notice_received:
            out["warnings"].append("A notice is pending: respond to it (139(9) rectification / 142(1) / 148) instead of filing ITR-U.")
    return out
