"""Turn Form 16 + AIS + TIS + the user's answers into engine Facts, plus a report of what is shaky.

Priority for each number: the user's explicit answer, then AIS (modified value), then Form 16.
The report lists conflicts between documents and the questions still open; nothing is guessed silently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from rules.engine import Facts, missing_questions
from .ais import Ais, Tis, cross_check
from .form16 import Form16
from .questionnaire import questions_for

STD_DEDUCTION_NEW = 75_000
PRESUMPTIVE_RATE = {"44ADA": 0.50, "44AD": 0.08, "44AE": 0.0}      # conservative: used only for the 50L cap test
BOOL_FIELDS = ("director", "unlisted_equity", "foreign_asset_or_income", "loss_carry_forward", "esop_deferral",
               "tds_194N", "partner_in_firm")


@dataclass
class Report:
    sources: dict = field(default_factory=dict)          # fact -> where it came from
    conflicts: list = field(default_factory=list)
    hints: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)
    total_income_estimate: dict = field(default_factory=dict)
    unmapped_ais_rows: list = field(default_factory=list)

    def to_dict(self):
        return self.__dict__.copy()


def _mask(pan: str) -> str:
    return f"{pan[:2]}{'*' * 6}{pan[-2:]}" if pan and len(pan) == 10 else "***"


def build_facts(form16: Optional[Form16], ais: Optional[Ais], tis: Optional[Tis], answers: Optional[dict] = None):
    answers = dict(answers or {})
    rep = Report()
    f = Facts()
    f.entity = answers.get("entity", "individual")

    # ---- documents agree with each other?
    pans = {}
    if form16 and form16.get("employee_pan"):
        pans["Form 16"] = form16.get("employee_pan")
    if ais and ais.pan:
        pans["AIS"] = ais.pan
    if tis and tis.pan:
        pans["TIS"] = tis.pan
    if len(set(pans.values())) > 1:
        rep.conflicts.append("PAN differs between documents: " + ", ".join(f"{k} {_mask(v)}" for k, v in pans.items()))
    if form16 and ais and ais.assessment_year and form16.get("assessment_year") \
            and ais.assessment_year != form16.get("assessment_year"):
        rep.conflicts.append(f"Assessment year differs: Form 16 {form16.get('assessment_year')}, AIS {ais.assessment_year}.")
    if ais and tis:
        rep.conflicts += cross_check(ais, tis)
    if ais:
        for d in ais.disputed:
            rep.hints.append(f"AIS row {d['code']} was modified by the taxpayer ({d['reported']:,.0f} -> {d['modified']:,.0f}); "
                             "the modified value is used.")
        rep.unmapped_ais_rows = ais.unmapped
        if ais.unmapped:
            rep.hints.append(f"{len(ais.unmapped)} AIS row(s) have an information code this tool does not know; review them by hand.")
    if form16:
        rep.conflicts += [f"Form 16 arithmetic: {w}" for w in form16.warnings]

    # ---- salary
    f16_sal = form16.get("gross_salary") if form16 else None
    ais_sal = ais.amount("salary") if ais else 0
    if f16_sal is not None and ais_sal and abs(f16_sal - ais_sal) > 1:
        rep.conflicts.append(f"Salary differs: Form 16 {f16_sal:,.0f} vs AIS {ais_sal:,.0f}.")
    salary = f16_sal if f16_sal is not None else ais_sal
    rep.sources["salary"] = "Form 16 item 1(d)" if f16_sal is not None else ("AIS TDS-192" if ais_sal else "none")

    # ---- user-only facts
    for k in ("residential_status", "hp_count"):
        if k in answers:
            setattr(f, k, answers[k])
    for k in BOOL_FIELDS:
        if k in answers:
            setattr(f, k, bool(answers[k]))
    for k in ("agri_income", "lottery_or_gambling", "ltcg_112a", "stcg_111a", "ltcg_other", "stcg_other", "vda_gain",
              "business_receipts", "cash_receipt_pct", "goods_vehicles"):
        if k in answers and answers[k] is not None:
            setattr(f, k, float(answers[k]))
    for k in ("business_kind", "opted_out_of_presumptive_within_5y", "dividend_over_10L"):
        if k in answers:
            setattr(f, k, answers[k])

    # ---- signals from AIS
    cg_missing = []
    if ais:
        if ais.has("securities_sale_consideration") and not any(k in answers for k in ("ltcg_112a", "stcg_111a", "ltcg_other")):
            f.securities_sold_gain_unknown = True
            cg_missing.append("capital_gain_amounts")
        if ais.has("property_sale"):
            f.property_sold = True
            if "ltcg_other" not in answers:
                cg_missing.append("property_gain")
        if ais.has("vda_transfer"):
            f.vda_transferred = True
            if "vda_gain" not in answers:
                cg_missing.append("vda_gain")
        if ais.has("lottery_gambling") and not f.lottery_or_gambling:
            f.lottery_or_gambling = ais.amount("lottery_gambling")
        if ais.has("cash_withdrawal_194N") and f.tds_194N is None:
            f.tds_194N = True
            rep.hints.append("AIS shows TDS 194N on cash withdrawals: ITR-1 is not allowed.")
        if ais.has("lrs_remittance"):
            rep.hints.append("AIS shows a foreign remittance (LRS). If it bought foreign assets or you have a foreign account, "
                             "answer 'yes' to the foreign-asset question.")
            if f.foreign_asset_or_income is False:
                rep.conflicts.append("You answered 'no foreign assets' but AIS shows an LRS remittance. Please confirm.")
        if ais.has("dividend") and ais.amount("dividend") > 1_000_000:
            f.dividend_over_10L = True
        # business signal
        biz_signal = ais.has("gst_turnover") or ais.has("professional_fees_tds") or ais.has("firm_income")
        if ais.has("firm_income") and f.partner_in_firm is None:
            f.partner_in_firm = True
            rep.hints.append("AIS shows remuneration/interest from a firm; treated as partner income (ITR-3).")
        if biz_signal and not f.business_kind and not f.partner_in_firm:
            cg_missing.append("business_kind")
        if f.business_kind and not f.business_receipts:
            f.business_receipts = ais.amount("gst_turnover") or ais.amount("professional_fees_tds")
            rep.sources["business_receipts"] = "AIS GST turnover / 194J"

    # ---- total income estimate (only the 50-lakh test and Schedule AL depend on it)
    parts = {}
    if form16 and form16.get("income_from_salary") is not None:
        parts["salary (Form 16 item 6)"] = form16.get("income_from_salary")
    elif salary:
        parts["salary (gross less std deduction)"] = max(salary - STD_DEDUCTION_NEW, 0)
    if ais:
        for label, bucket in (("savings interest", "interest_savings"), ("other interest", "interest_other"), ("dividend", "dividend")):
            if ais.has(bucket):
                parts[label] = ais.amount(bucket)
        if ais.has("rent_received"):
            parts["house property (rent less 30%)"] = ais.amount("rent_received") * 0.7
        if ais.has("firm_income"):
            parts["firm income"] = ais.amount("firm_income")
    if f.business_kind in PRESUMPTIVE_RATE and f.business_receipts:
        parts[f"business ({f.business_kind} at {PRESUMPTIVE_RATE[f.business_kind]:.0%})"] = f.business_receipts * PRESUMPTIVE_RATE[f.business_kind]
    elif f.business_kind in ("NON_PRESUMPTIVE", "SPECULATIVE") and "business_profit" in answers:
        parts["business profit"] = float(answers["business_profit"])
    cg = f.ltcg_112a + f.stcg_111a + f.ltcg_other + f.stcg_other
    if cg:
        parts["capital gains"] = cg
    if f.vda_gain:
        parts["VDA gain"] = f.vda_gain
    elif f.vda_transferred and ais:
        parts["VDA (assumed 50% of sale value)"] = ais.amount("vda_transfer") * 0.5
    if f.agri_income:
        parts["agricultural income"] = f.agri_income
    est = sum(parts.values())
    f.total_income = float(answers["total_income"]) if "total_income" in answers else est
    rep.total_income_estimate = {"total": round(est), "parts": {k: round(v) for k, v in parts.items()},
                                 "used": round(f.total_income),
                                 "note": "Estimate for the Rs 50 lakh test; deductions are ignored. Replace with your computed total income if close to the cap."}
    if abs(f.total_income - 5_000_000) <= 250_000:
        rep.hints.append("Estimated total income is within Rs 2.5 lakh of the Rs 50 lakh ITR-1 limit; enter your exact figure (answers.total_income).")

    # ---- open questions
    missing = missing_questions(f) + cg_missing
    rep.open_questions = questions_for(missing, {})
    rep.sources.update({k: "user answer" for k in answers})
    return f, rep
