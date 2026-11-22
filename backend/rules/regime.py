"""
Old vs new tax regime comparison for a RESIDENT INDIVIDUAL, AY 2026-27 (FY 2025-26, Income-tax Act 1961).

Pure functions, no I/O. Cross-checked against published worked examples (see tests/test_regime.py).
Known simplifications (surfaced in `notes`): surcharge marginal relief is not computed; 87A marginal relief is
applied to normal-rate tax only; capital-gain special rates assume post-23-Jul-2024 rates (111A 20%, 112/112A 12.5%,
112A exemption 1.25L); VDA 30% flat; agricultural income, clubbing, set-off/carry-forward of losses are not modelled.
"""
from dataclasses import dataclass, asdict

NEW_SLABS = [(400_000, 0.0), (800_000, 0.05), (1_200_000, 0.10), (1_600_000, 0.15),
             (2_000_000, 0.20), (2_400_000, 0.25), (float("inf"), 0.30)]
OLD_SLABS = {  # keyed by age band
    "regular": [(250_000, 0.0), (500_000, 0.05), (1_000_000, 0.20), (float("inf"), 0.30)],
    "senior": [(300_000, 0.0), (500_000, 0.05), (1_000_000, 0.20), (float("inf"), 0.30)],       # 60-79
    "super_senior": [(500_000, 0.0), (1_000_000, 0.20), (float("inf"), 0.30)],                  # 80+
}
STD_DED = {"new": 75_000, "old": 50_000}
REBATE_87A = {"new": (1_200_000, 60_000), "old": (500_000, 12_500)}   # (total income limit, max rebate)
SURCHARGE = [(20_000_000, 0.25), (10_000_000, 0.15), (5_000_000, 0.10)]  # thresholds high->low; >5Cr handled below
CESS = 0.04


@dataclass
class Inputs:
    age: int = 30
    # --- salary
    salary: float = 0                 # gross salary: 17(1)+17(2)+17(3)
    basic_da: float = 0               # basic + DA (basis for HRA and employer-NPS cap)
    hra_received: float = 0
    rent_paid: float = 0              # annual
    metro: bool = False
    other_exempt_allowances: float = 0  # LTA, etc. exempt u/s 10 (old regime only)
    professional_tax: float = 0       # allowed only in old regime
    # --- house property
    rent_received: float = 0          # let-out, gross
    municipal_tax: float = 0
    let_out_interest: float = 0       # interest on loan for let-out property
    self_occ_interest: float = 0      # interest on loan, self-occupied (24(b), old regime only, cap 2L)
    # --- other income at normal rates
    interest_savings: float = 0
    interest_other: float = 0         # FD, RD, etc.
    dividend: float = 0
    other_income: float = 0
    # --- special-rate income
    stcg_111a: float = 0
    ltcg_112a: float = 0
    ltcg_other: float = 0             # s.112 (12.5%)
    vda_gain: float = 0               # s.115BBH 30%
    # --- deductions (claimed amounts; caps applied here)
    d80c: float = 0
    d80ccd_1b: float = 0
    d80ccd_2: float = 0               # employer NPS (allowed in both regimes)
    d80d_self: float = 0
    d80d_parents: float = 0
    parents_senior: bool = False
    d80e: float = 0
    d80g: float = 0                   # eligible amount after 50%/100% rules
    extra_old_deductions: float = 0   # any other Chapter VI-A deduction (old regime only)
    # --- filing context
    filing_on_time: bool = True       # return filed on/before the s.139(1) due date
    has_business_income: bool = False


def hra_exemption(basic_da, hra_received, rent_paid, metro):
    """Least of: actual HRA, rent paid - 10% of (basic+DA), 50% (metro) / 40% of (basic+DA)."""
    if not (hra_received and rent_paid):
        return 0.0
    return max(min(hra_received, rent_paid - 0.10 * basic_da, (0.50 if metro else 0.40) * basic_da), 0.0)


def _slab_tax(income, slabs):
    tax, lo = 0.0, 0.0
    for hi, rate in slabs:
        if income > lo:
            tax += (min(income, hi) - lo) * rate
        lo = hi
    return tax


def _band(age):
    return "super_senior" if age >= 80 else "senior" if age >= 60 else "regular"


def _surcharge_rate(total_income, regime):
    for thr, rate in SURCHARGE:
        if total_income > thr:
            return rate
    if total_income > 50_000_000:
        return 0.25 if regime == "new" else 0.37
    return 0.0


def compute(i: Inputs, regime: str):
    assert regime in ("old", "new")
    old = regime == "old"
    n = {}
    # ---- salary
    hra = hra_exemption(i.basic_da, i.hra_received, i.rent_paid, i.metro) if old else 0.0
    exempt = hra + (i.other_exempt_allowances if old else 0.0)
    std = min(STD_DED[regime], max(i.salary - exempt, 0)) if i.salary else 0.0
    ptax = i.professional_tax if old else 0.0
    salary_income = max(i.salary - exempt - std - ptax, 0.0)
    # ---- house property
    hp = 0.0
    if i.rent_received:
        nav = max(i.rent_received - i.municipal_tax, 0)
        hp += nav - 0.30 * nav - i.let_out_interest
    if old and i.self_occ_interest:
        hp -= min(i.self_occ_interest, 200_000)
    hp_loss_disallowed = 0.0
    if hp < 0:
        capped = -200_000 if old else 0.0          # new regime: no set-off of HP loss against other heads
        hp_loss_disallowed = capped - hp if old else -hp
        hp = max(hp, capped)
    other_src = i.interest_savings + i.interest_other + i.dividend + i.other_income
    gti = salary_income + hp + other_src
    # ---- deductions (Chapter VI-A)
    cap_nps = (0.10 if old else 0.14) * i.basic_da
    ded = min(i.d80ccd_2, cap_nps) if i.basic_da else 0.0
    if old:
        senior = i.age >= 60
        ded += min(i.d80c, 150_000) + min(i.d80ccd_1b, 50_000)
        ded += min(i.d80d_self, 50_000 if senior else 25_000) + min(i.d80d_parents, 50_000 if i.parents_senior else 25_000)
        ded += i.d80e + i.d80g + i.extra_old_deductions
        if senior:
            ded += min(i.interest_savings + i.interest_other, 50_000)       # 80TTB
        else:
            ded += min(i.interest_savings, 10_000)                          # 80TTA
    taxable_normal = max(gti - ded, 0.0)
    # ---- special-rate income, with unexhausted basic exemption adjusted against it (residents)
    slabs = OLD_SLABS[_band(i.age)] if old else NEW_SLABS
    basic_exemption = slabs[0][0]
    shortfall = max(basic_exemption - taxable_normal, 0.0)
    stcg = i.stcg_111a
    adj = min(shortfall, stcg); stcg -= adj; shortfall -= adj
    ltcg_o = i.ltcg_other
    adj = min(shortfall, ltcg_o); ltcg_o -= adj; shortfall -= adj
    ltcg_a = i.ltcg_112a
    adj = min(shortfall, ltcg_a); ltcg_a -= adj
    special_tax = stcg * 0.20 + ltcg_o * 0.125 + max(ltcg_a - 125_000, 0) * 0.125
    vda_tax = i.vda_gain * 0.30
    total_income = taxable_normal + i.stcg_111a + i.ltcg_112a + i.ltcg_other + i.vda_gain
    # ---- normal tax, rebate, marginal relief
    normal_tax = _slab_tax(taxable_normal, slabs)
    limit, max_rebate = REBATE_87A[regime]
    rebate = 0.0
    if total_income <= limit:
        rebate = min(normal_tax, max_rebate)
    elif not old and normal_tax > total_income - limit > 0 and taxable_normal > limit - 1:   # marginal relief just above 12L
        rebate = normal_tax - (total_income - limit)
    normal_after = normal_tax - rebate
    # ---- surcharge (rate capped at 15% on special-rate CG; not on VDA cap) and cess
    sr = _surcharge_rate(total_income, regime)
    surcharge = normal_after * sr + (special_tax * min(sr, 0.15)) + vda_tax * sr
    tax_before_cess = normal_after + special_tax + vda_tax + surcharge
    cess = tax_before_cess * CESS
    total = round(tax_before_cess + cess)
    return dict(regime=regime, gross_total_income=round(gti), deductions=round(ded), taxable_income=round(total_income),
                salary_exemptions=round(exempt), standard_deduction=round(std), hra_exemption=round(hra),
                house_property_income=round(hp), hp_loss_not_set_off=round(hp_loss_disallowed),
                normal_tax=round(normal_tax), rebate_87a=round(rebate), special_rate_tax=round(special_tax + vda_tax),
                surcharge=round(surcharge), cess=round(cess), total_tax=total)


def compare(i: Inputs):
    new, old = compute(i, "new"), compute(i, "old")
    notes = []
    best = "new" if new["total_tax"] <= old["total_tax"] else "old"
    savings = abs(new["total_tax"] - old["total_tax"])
    if not i.filing_on_time and not i.has_business_income:
        if best == "old":
            notes.append("Old regime would save %s but a non-business individual must opt out of the new regime on or before "
                         "the s.139(1) due date (s.115BAC(6), Form 10-IEA); a belated return is assessed under the new regime. "
                         "[verify against current CBDT guidance]" % f"{savings:,}")
        best = "new"
    if i.has_business_income and best == "old":
        notes.append("Business/profession income: opting out needs Form 10-IEA by the due date, and returning to the new regime "
                     "later is allowed only once.")
    if new["total_tax"] == old["total_tax"]:
        notes.append("Tie: choose the new regime (default, no Form 10-IEA needed).")
    # extra old-regime deductions at which old would beat new
    need = 0
    if old["total_tax"] > new["total_tax"]:
        lo, hi = 0.0, max(old["taxable_income"], 1.0)
        for _ in range(40):
            mid = (lo + hi) / 2
            j = Inputs(**{**asdict(i), "extra_old_deductions": i.extra_old_deductions + mid})
            if compute(j, "old")["total_tax"] > new["total_tax"]:
                lo = mid
            else:
                hi = mid
        need = round(hi, -2)
    notes.append("Surcharge marginal relief and loss carry-forward are not modelled; special-rate tax uses post 23-Jul-2024 rates.")
    return dict(recommended=best, tax_saving=savings if best != "tie" else 0, new=new, old=old,
                extra_old_deductions_needed_for_old_to_win=need, notes=notes)
