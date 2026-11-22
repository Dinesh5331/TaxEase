"""Deterministic ITR selection for AY 2026-27 (see rules/itr_rules.yaml, the source of truth).

    result = select_itr(Facts(...))

The YAML owns the rule ids and their wording; this module owns the predicates. A test asserts
that both sides list the same ids, so a rule cannot be edited in one place only.

No LLM is involved. Facts that no document can prove (director, unlisted shares, residency,
foreign assets, carry-forward losses, ...) are left as None when unknown; the result then says
which questions are still open and marks itself "provisional".
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Optional

import yaml

RULES_PATH = Path(__file__).with_name("itr_rules.yaml")

# Thresholds (AY 2026-27). Tags in itr_rules.yaml say how well each is verified.
INCOME_CAP = 5_000_000
LTCG_112A_CAP = 125_000
AGRI_CAP = 5_000
MAX_HOUSE_PROPERTIES = 2
LIMIT_44ADA = 5_000_000
LIMIT_44ADA_LOW_CASH = 7_500_000
LIMIT_44AD = 20_000_000
LIMIT_44AD_LOW_CASH = 30_000_000
LOW_CASH_PCT = 5
MAX_44AE_VEHICLES = 10

# Facts only the user can supply. None = not asked / not answered yet.
QUESTIONNAIRE_FIELDS = (
    "residential_status", "director", "unlisted_equity", "foreign_asset_or_income",
    "loss_carry_forward", "esop_deferral", "tds_194N", "partner_in_firm", "hp_count",
)

NON_INDIVIDUAL_FORM = {
    "company": "ITR-6",
    "trust_institution": "ITR-7",
    "firm": "ITR-5", "llp": "ITR-5", "aop_boi": "ITR-5", "other": "ITR-5",
}


@dataclass
class Facts:
    entity: str = "individual"                    # individual, huf, firm, llp, aop_boi, company, trust_institution, other
    total_income: float = 0
    # asked from the user (cannot be proven from documents)
    residential_status: Optional[str] = None      # ROR, RNOR, NR
    director: Optional[bool] = None
    unlisted_equity: Optional[bool] = None
    foreign_asset_or_income: Optional[bool] = None
    loss_carry_forward: Optional[bool] = None
    esop_deferral: Optional[bool] = None
    tds_194N: Optional[bool] = None
    partner_in_firm: Optional[bool] = None        # receives remuneration/interest from a firm
    hp_count: Optional[int] = None
    # from AIS / TIS / Form 16 (or broker P&L for the gain split)
    ltcg_112a: float = 0
    stcg_111a: float = 0
    ltcg_other: float = 0                         # property, unlisted shares, debt funds, ...
    stcg_other: float = 0
    vda_gain: float = 0
    vda_transferred: bool = False                 # any VDA transfer needs Schedule VDA, whatever the gain
    property_sold: bool = False                   # any transfer of immovable property needs Schedule CG, even at a loss
    agri_income: float = 0
    lottery_or_gambling: float = 0
    dividend_over_10L: bool = False
    # business or profession
    business_kind: Optional[str] = None           # 44AD, 44ADA, 44AE, NON_PRESUMPTIVE, SPECULATIVE
    business_receipts: float = 0
    cash_receipt_pct: Optional[float] = None
    goods_vehicles: int = 0
    opted_out_of_presumptive_within_5y: bool = False
    # unresolved from documents (set by the extractor, not by the user)
    securities_sold_gain_unknown: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "Facts":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class Result:
    form: str
    status: str                                   # final | provisional
    failed_rules: list = field(default_factory=list)       # ITR-1 (or ITR-4) rule ids that failed
    reasons: list = field(default_factory=list)            # plain-language reason per failed rule
    path: list = field(default_factory=list)               # decision trace
    schedules: list = field(default_factory=list)
    missing: list = field(default_factory=list)            # questionnaire fields still unknown
    notes: list = field(default_factory=list)
    alternatives: list = field(default_factory=list)       # other forms that would also be accepted

    def to_dict(self) -> dict:
        return self.__dict__.copy()


# ------------------------------------------------------------------ rule text from the YAML
def load_rules(path: Path = RULES_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


_RULES = None


def rules() -> dict:
    global _RULES
    if _RULES is None:
        _RULES = load_rules()
    return _RULES


def rule_text(rule_id: str) -> str:
    for form in ("ITR-1", "ITR-4"):
        for r in rules().get(form, {}).get("all_of", []):
            if r["id"] == rule_id:
                return r["rule"]
    return rule_id


# ------------------------------------------------------------------ predicates (True = rule satisfied)
def _no(v):                       # unknown counts as "no" for the provisional answer
    return not v


def _hp(f):
    return f.hp_count or 0


def _cg_ok(f):
    return (f.ltcg_112a <= LTCG_112A_CAP and f.stcg_111a == 0 and f.ltcg_other == 0 and f.stcg_other == 0
            and not f.property_sold)


def _vda(f):
    return bool(f.vda_gain or f.vda_transferred)


ITR1_PREDICATES = {
    "i1_resident":   lambda f: (f.residential_status or "ROR") == "ROR",
    "i1_income_cap": lambda f: f.total_income <= INCOME_CAP,
    "i1_sources":    lambda f: _hp(f) <= MAX_HOUSE_PROPERTIES and f.agri_income <= AGRI_CAP,
    "i1_cg":         _cg_ok,
    "i1_director":   lambda f: _no(f.director),
    "i1_unlisted":   lambda f: _no(f.unlisted_equity),
    "i1_194N":       lambda f: _no(f.tds_194N),
    "i1_esop":       lambda f: _no(f.esop_deferral),
    "i1_foreign":    lambda f: _no(f.foreign_asset_or_income),
    "i1_losses":     lambda f: _no(f.loss_carry_forward),
    # lottery/racehorse, s.115BBDA dividend and VDA (s.115BBH) all need ITR-2 or later.
    "i1_special":    lambda f: not _vda(f) and f.lottery_or_gambling == 0 and not f.dividend_over_10L,
}

ITR4_PREDICATES = {
    "i4_resident": lambda f: (f.residential_status or "ROR") == "ROR",     # RNOR treated as not eligible
    "i4_cap":      lambda f: f.total_income <= INCOME_CAP,
    "i4_income":   lambda f: _presumptive_within_limits(f),
    "i4_cg":       _cg_ok,
    "i4_director": lambda f: (_no(f.director) and _no(f.unlisted_equity) and _no(f.esop_deferral)
                              and f.agri_income <= AGRI_CAP and _no(f.foreign_asset_or_income)
                              and not _vda(f) and f.lottery_or_gambling == 0 and not f.dividend_over_10L),
    "i4_hp":       lambda f: _hp(f) <= MAX_HOUSE_PROPERTIES and _no(f.loss_carry_forward),
}


def _presumptive_within_limits(f: Facts) -> bool:
    if f.opted_out_of_presumptive_within_5y:
        return False
    low_cash = f.cash_receipt_pct is not None and f.cash_receipt_pct <= LOW_CASH_PCT
    r = f.business_receipts
    if f.business_kind == "44ADA":
        return r <= (LIMIT_44ADA_LOW_CASH if low_cash else LIMIT_44ADA)
    if f.business_kind == "44AD":
        return r <= (LIMIT_44AD_LOW_CASH if low_cash else LIMIT_44AD)
    if f.business_kind == "44AE":
        return f.goods_vehicles <= MAX_44AE_VEHICLES
    return False


def evaluate(preds: dict, f: Facts) -> list:
    """Ids of rules that FAIL, in yaml order."""
    return [rid for rid, p in preds.items() if not p(f)]


# ------------------------------------------------------------------ decision
def _schedules(f: Facts, form: str) -> list:
    s = []
    if form in ("ITR-2", "ITR-3"):
        if f.ltcg_112a or f.stcg_111a or f.ltcg_other or f.stcg_other or f.property_sold:
            s.append("Schedule CG")
        if _vda(f):
            s.append("Schedule VDA")
        if f.foreign_asset_or_income:
            s += ["Schedule FA", "Schedule FSI/TR"]
        if f.total_income > INCOME_CAP:
            s.append("Schedule AL")
        if f.loss_carry_forward:
            s.append("Schedule CFL")
        if f.agri_income > AGRI_CAP:
            s.append("Schedule EI")
        if f.director or f.unlisted_equity:
            s.append("Directorship / unlisted-share disclosure")
    if form == "ITR-3":
        s.append("Schedule BP" + ("" if f.business_kind in ("44AD", "44ADA", "44AE") else " + Balance sheet and P&L"))
        if f.partner_in_firm:
            s.append("Partner-in-firm details")
    return s


def missing_questions(f: Facts) -> list:
    """Questionnaire fields that are still None and could change the form."""
    return [k for k in QUESTIONNAIRE_FIELDS if getattr(f, k) is None]


def select_itr(f: Facts) -> Result:
    missing = missing_questions(f)
    res = Result(form="", status="provisional" if missing else "final", missing=missing)
    if f.securities_sold_gain_unknown:
        res.status = "provisional"
        res.missing.append("capital_gain_amounts")
        res.notes.append("AIS shows securities were sold but not the gain. Enter the gain from the broker's "
                         "capital-gains statement: ITR-1 allows only LTCG u/s 112A up to Rs 1.25 lakh.")

    # 1. entity
    if f.entity in NON_INDIVIDUAL_FORM:
        res.form = NON_INDIVIDUAL_FORM[f.entity]
        res.path.append(f"entity={f.entity} -> {res.form}")
        if f.entity in ("firm",) and f.business_kind in ("44AD", "44ADA", "44AE") and f.total_income <= INCOME_CAP:
            res.alternatives.append("ITR-4 (resident non-LLP firm with only presumptive income up to Rs 50 lakh)")
        res.status = "final"
        res.missing = []
        return res
    if f.entity != "huf" and f.entity != "individual":
        res.form = "ITR-5"
        res.path.append(f"unknown entity '{f.entity}' -> ITR-5; confirm")
        res.status = "provisional"
        return res

    # 2. business or profession income
    has_business = bool(f.business_kind) or bool(f.partner_in_firm)
    if has_business:
        if f.partner_in_firm and not f.business_kind:
            res.form = "ITR-3"
            res.path.append("partner receiving remuneration/interest from a firm -> ITR-3")
            res.reasons.append("Remuneration and interest from a partnership firm is business income; ITR-4 does not cover it.")
        elif f.business_kind in ("44AD", "44ADA", "44AE") and not f.partner_in_firm and f.entity == "individual":
            failed = evaluate(ITR4_PREDICATES, f)
            if not failed:
                res.form = "ITR-4"
                res.alternatives.append("ITR-3 (also accepted; needs the full business schedules)")
                res.path.append(f"presumptive {f.business_kind} and all ITR-4 conditions hold -> ITR-4")
            else:
                res.form = "ITR-3"
                res.failed_rules = failed
                res.reasons += [_itr4_reason(r, f) for r in failed]
                res.path.append(f"presumptive {f.business_kind} but ITR-4 fails {failed} -> ITR-3")
        elif f.business_kind in ("44AD", "44ADA", "44AE") and f.entity == "huf":
            failed = evaluate(ITR4_PREDICATES, f)
            res.form = "ITR-4" if not failed else "ITR-3"
            res.failed_rules = failed
            res.path.append(f"HUF presumptive -> {res.form}")
        else:
            res.form = "ITR-3"
            res.path.append(f"business kind {f.business_kind or 'partner'} is not presumptive -> ITR-3")
            res.reasons.append("Business or profession income that is not under 44AD/44ADA/44AE (including F&O and "
                               "speculative trading) must be reported in ITR-3 with Schedule BP.")
        res.schedules = _schedules(f, res.form)
        return res

    # 3. no business income
    if f.entity == "huf":
        res.form = "ITR-2"
        res.path.append("HUF without business income -> ITR-2 (ITR-1 is for individuals only)")
        res.schedules = _schedules(f, res.form)
        return res
    failed = evaluate(ITR1_PREDICATES, f)
    if not failed:
        res.form = "ITR-1"
        res.path.append("all ITR-1 conditions hold -> ITR-1")
    else:
        res.form = "ITR-2"
        res.failed_rules = failed
        res.reasons = [rule_text(r) for r in failed]
        res.path.append(f"ITR-1 fails {failed} -> ITR-2")
    res.schedules = _schedules(f, res.form)
    return res


_ITR4_REASON = {
    "i4_resident": "ITR-4 is for resident taxpayers; RNOR and non-residents file ITR-3.",
    "i4_cap": "Total income is above Rs 50 lakh.",
    "i4_income": "Receipts are above the presumptive limit for this scheme (44ADA: Rs 50 lakh, or Rs 75 lakh if cash "
                 "receipts are 5% or less; 44AD: Rs 2 crore, or Rs 3 crore at 5% cash).",
    "i4_cg": "Capital gains other than LTCG u/s 112A up to Rs 1.25 lakh are not allowed in ITR-4.",
    "i4_director": "Director, unlisted shares, ESOP deferral, agricultural income above Rs 5,000, foreign assets, "
                   "crypto or special-rate income are not allowed in ITR-4.",
    "i4_hp": "More than two house properties, or a loss to carry forward, is not allowed in ITR-4.",
}


def _itr4_reason(rule_id: str, f: Facts) -> str:
    return _ITR4_REASON.get(rule_id, rule_id)


def yaml_rule_ids() -> dict:
    r = rules()
    return {"ITR-1": [x["id"] for x in r["ITR-1"]["all_of"]], "ITR-4": [x["id"] for x in r["ITR-4"]["all_of"]]}
