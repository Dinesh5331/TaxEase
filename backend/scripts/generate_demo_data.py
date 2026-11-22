"""
Synthetic taxpayer documents for demos and tests (FY 2025-26 / AY 2026-27).

Writes backend/demo_data/<persona_id>/{form16.pdf, ais.json, ais.pdf, tis.json, tis.pdf}
and backend/demo_data/golden_itr.json (ground-truth ITR per persona, hand-labelled, NOT computed
by the rules engine so that Phase 3 can be tested against it).

Everything is fictional: names, PANs, TANs, employers. PDFs carry a SAMPLE banner.
AIS/TIS are SIMPLIFIED models of the portal documents (same categories, simpler layout).
Run:  python scripts/generate_demo_data.py
"""
import json
import random
import string
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "demo_data"
FY, AY = "2025-26", "2026-27"
STYLES = getSampleStyleSheet()
rnd = random.Random(2026)

# ----------------------------------------------------------------------------- personas
# expected_itr + reasons are HAND-LABELLED ground truth. reasons use rule ids from rules/itr_rules.yaml.
# Amounts in rupees. 'salary' = gross salary u/s 17(1). 'q' = facts that documents cannot prove
# (asked via questionnaire in the app).
def P(id, title, expected, reasons, name, **kw):
    base = dict(id=id, title=title, expected_itr=expected, reasons=reasons, name=name, dob="1990-06-15",
                salary=0, perqs=0, nps_employer=0, interest_savings=0, interest_fd=0, dividend=0,
                rent_received=0, hp_count=0, ltcg_112a=0, stcg_111a=0, ltcg_property=0, property_sale=0,
                vda_transfer=0, agri_income=0, lrs_remittance=0, business=None,
                q=dict(residential_status="ROR", director=False, unlisted_equity=False,
                       foreign_asset_or_income=False, loss_carry_forward=False, esop_deferral=False,
                       partner_in_firm=False))
    q = base["q"]; q.update(kw.pop("q", {}))
    base.update(kw); base["q"] = q
    return base

PERSONAS = [
    P("p01_salaried_simple", "Salaried, savings interest only", "ITR-1", ["i1_sources"], "Aarav Mehta",
      salary=1_450_000, interest_savings=18_000),
    P("p02_two_house_props", "Salaried + 1 let-out and 1 self-occupied property + dividends", "ITR-1", ["i1_sources"],
      "Nisha Rao", salary=1_900_000, hp_count=2, rent_received=360_000, dividend=24_000, interest_fd=42_000),
    P("p03_small_ltcg_112a", "Salaried + LTCG 112A of 90k (within 1.25L)", "ITR-1", ["i1_cg"], "Rohit Iyer",
      salary=1_200_000, ltcg_112a=90_000, interest_savings=9_000),
    P("p04_ltcg_112a_over_limit", "Salaried + LTCG 112A of 1.8L (over 1.25L)", "ITR-2", ["i1_cg"], "Sana Qureshi",
      salary=1_600_000, ltcg_112a=180_000),
    P("p05_three_house_props", "Salaried + 3 house properties", "ITR-2", ["i1_sources"], "Vikram Nair",
      salary=2_400_000, hp_count=3, rent_received=540_000),
    P("p06_stcg_equity", "Salaried + STCG on equity (111A) and MF redemption", "ITR-2", ["i1_cg"], "Pooja Desai",
      salary=1_100_000, stcg_111a=140_000),
    P("p07_income_over_50l", "Salaried, total income above 50 lakh", "ITR-2", ["i1_income_cap"], "Arjun Kapoor",
      salary=6_200_000),
    P("p08_foreign_assets", "Salaried with foreign brokerage account (LRS remittances)", "ITR-2", ["i1_foreign"],
      "Meera Joshi", salary=2_800_000, lrs_remittance=900_000, q=dict(foreign_asset_or_income=True)),
    P("p09_nri_salary", "Non-resident, India-sourced interest and rent", "ITR-2", ["i1_resident"], "Karthik Menon",
      interest_fd=380_000, hp_count=1, rent_received=420_000, q=dict(residential_status="NR")),
    P("p10_freelancer_44ada", "Freelance consultant, receipts 38L, 44ADA", "ITR-4", [], "Ishita Bose",
      business=dict(kind="44ADA", receipts=3_800_000, cash_pct=2, profession="Consulting")),
    P("p11_trader_44ad", "Retail trader, turnover 1.4 Cr, 44AD", "ITR-4", [], "Harish Patel",
      business=dict(kind="44AD", receipts=14_000_000, cash_pct=30, profession="Retail trade"), interest_savings=12_000),
    P("p12_fno_trader_salaried", "Salaried + F&O trading (non-presumptive)", "ITR-3", [], "Dev Malhotra",
      salary=1_800_000, business=dict(kind="FNO", receipts=2_600_000, cash_pct=0, profession="F&O trading")),
    P("p13_director", "Salaried and director in a private company", "ITR-2", ["i1_director"], "Anjali Verma",
      salary=2_000_000, q=dict(director=True)),
    P("p14_crypto_vda", "Salaried + crypto (VDA) transfer", "ITR-2", ["i1_special"], "Rahul Singhania",
      salary=1_300_000, vda_transfer=420_000),
    P("p15_44ada_75l_limit_ok", "Architect, receipts 62L, cash 3% (limit is 75L)", "ITR-4", [], "Tara Pillai",
      business=dict(kind="44ADA", receipts=6_200_000, cash_pct=3, profession="Architect")),
    P("p16_44ada_over_limit", "Architect, receipts 62L, cash 8% (limit stays 50L)", "ITR-3", [], "Neel Kulkarni",
      business=dict(kind="44ADA", receipts=6_200_000, cash_pct=8, profession="Architect")),
    P("p17_partner_in_firm", "Partner in a firm (remuneration + interest) + salary", "ITR-3", [], "Gauri Shetty",
      salary=900_000, q=dict(partner_in_firm=True),
      business=dict(kind="PARTNER", receipts=1_200_000, cash_pct=0, profession="Partner remuneration")),
    P("p18_property_sale", "Salaried + sold a flat (LTCG on property)", "ITR-2", ["i1_cg"], "Sameer Khan",
      salary=1_700_000, ltcg_property=2_300_000, property_sale=6_800_000),
    P("p19_senior_pension", "Senior citizen: pension + FD interest", "ITR-1", ["i1_sources"], "Ramesh Subramanian",
      dob="1958-03-02", salary=420_000, interest_fd=310_000, interest_savings=22_000),
    P("p20_agri_income", "Salaried + agricultural income of 40k", "ITR-2", ["i1_sources"], "Lakshmi Naidu",
      salary=1_050_000, agri_income=40_000),
    P("p21_loss_carry_forward", "Salaried with a capital loss to carry forward", "ITR-2", ["i1_losses"], "Yash Agarwal",
      salary=1_400_000, q=dict(loss_carry_forward=True)),
]

# ----------------------------------------------------------------------------- helpers
def fake_pan(p):
    last = p["name"].split()[-1][0].upper()
    pre = "".join(rnd.choice(string.ascii_uppercase) for _ in range(3))
    return f"{pre}P{last}{rnd.randint(1000, 9999)}{rnd.choice(string.ascii_uppercase)}"

def fake_tan():
    return "".join(rnd.choice(string.ascii_uppercase) for _ in range(4)) + f"{rnd.randint(10000, 99999)}" + rnd.choice(string.ascii_uppercase)

def inr(n):
    n = int(round(n)); neg = n < 0; n = abs(n)
    t = str(n)
    if len(t) > 3:
        head, tail = t[:-3], t[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        t = ",".join(parts + [tail])
    return ("-" if neg else "") + t

def slab_tax(taxable):
    slabs = [(400_000, 0), (800_000, .05), (1_200_000, .10), (1_600_000, .15), (2_000_000, .20), (2_400_000, .25), (1e18, .30)]
    tax, lo = 0.0, 0
    for hi, r in slabs:
        if taxable > lo:
            tax += (min(taxable, hi) - lo) * r
        lo = hi
    return round(tax)

def new_regime_tax(taxable):
    """Individual, new regime FY 2025-26: slabs, 87A rebate with marginal relief, surcharge, 4% cess."""
    slabs = [(400_000, 0), (800_000, .05), (1_200_000, .10), (1_600_000, .15), (2_000_000, .20), (2_400_000, .25), (1e18, .30)]
    tax, lo = 0.0, 0
    for hi, r in slabs:
        if taxable > lo:
            tax += (min(taxable, hi) - lo) * r
        lo = hi
    if taxable <= 1_200_000:
        tax = 0.0                                       # 87A rebate up to Rs 60,000
    elif taxable - 1_200_000 < tax:
        tax = taxable - 1_200_000                       # marginal relief
    sur = 0.10 if 5_000_000 < taxable <= 10_000_000 else 0.0
    tax *= 1 + sur
    return round(tax * 1.04)

def salary_figures(p):
    gross = p["salary"]
    std = 75_000 if gross else 0
    ptax = 0   # s.16(ii)/(iii) are not allowed under the new regime (115BAC(1A)); only 16(ia) standard deduction
    net = max(gross - std - ptax, 0)
    nps = min(p["nps_employer"], int(gross * 0.14))
    taxable = max(net - nps, 0)
    tax = new_regime_tax(taxable)
    # presentation split of the final figure (slab tax / rebate / surcharge / cess) for Form 16 items 13-17
    cess = round(tax - tax / 1.04) if tax else 0
    pre_cess = tax - cess
    gross_slab = slab_tax(taxable)
    rebate = max(gross_slab - min(gross_slab, pre_cess), 0) if taxable <= 1_260_000 else 0
    surcharge = max(pre_cess - (gross_slab - rebate), 0)
    return dict(gross=gross, std=std, ptax=ptax, net=net, nps=nps, taxable=taxable, tax=tax,
                base_tax=gross_slab, rebate=rebate, surcharge=surcharge, cess=cess)

def total_income(p):
    s = salary_figures(p)["taxable"]
    hp = int(p["rent_received"] * 0.7) if p["rent_received"] else 0
    biz = 0
    b = p["business"]
    if b:
        biz = {"44ADA": 0.5, "44AD": 0.06, "FNO": 0.35, "PARTNER": 1.0}[b["kind"]] * b["receipts"]
    cg = p["ltcg_112a"] + p["stcg_111a"] + p["ltcg_property"]
    return int(s + hp + biz + cg + p["interest_savings"] + p["interest_fd"] + p["dividend"] + p["vda_transfer"] * 0.5)

# ----------------------------------------------------------------------------- AIS / TIS
def build_ais(p, pan, employer):
    tds, sft, other = [], [], []
    sal = salary_figures(p)
    if p["salary"]:
        tds.append(dict(information_code="TDS-192", description="Salary", source=employer["name"], tan=employer["tan"],
                        amount_paid=p["salary"], tax_deducted=sal["tax"]))
    if p["interest_fd"]:
        tds.append(dict(information_code="TDS-194A", description="Interest other than securities", source="Fictional Bank Ltd",
                        tan=fake_tan(), amount_paid=p["interest_fd"], tax_deducted=round(p["interest_fd"] * 0.10)))
    if p["dividend"]:
        tds.append(dict(information_code="TDS-194", description="Dividend", source="Fictional Industries Ltd", tan=fake_tan(),
                        amount_paid=p["dividend"], tax_deducted=round(p["dividend"] * 0.10)))
    if p["rent_received"]:
        other.append(dict(information_code="OTH-RENT", description="Rent received (194-I / 194-IB)", amount=p["rent_received"]))
    if p["interest_savings"]:
        sft.append(dict(information_code="SFT-016(SB)", description="Interest from savings bank account", source="Fictional Bank Ltd",
                        amount=p["interest_savings"]))
    sale = p["ltcg_112a"] + p["stcg_111a"]
    if sale:
        sft.append(dict(information_code="SFT-017", description="Sale of securities and units of mutual fund",
                        source="Fictional Securities Pvt Ltd", amount=int(sale * 4.2),
                        note="sale consideration; cost and gain not reported in AIS"))
        sft.append(dict(information_code="SFT-015", description="Purchase of units of mutual fund", source="Fictional AMC",
                        amount=int(sale * 2.0)))
    if p["property_sale"]:
        tds.append(dict(information_code="TDS-194IA", description="Transfer of immovable property other than agricultural land",
                        source="Buyer (individual)", tan="PAN-based", amount_paid=p["property_sale"],
                        tax_deducted=round(p["property_sale"] * 0.01)))
    if p["vda_transfer"]:
        tds.append(dict(information_code="TDS-194S", description="Transfer of virtual digital asset", source="Fictional Exchange",
                        tan=fake_tan(), amount_paid=p["vda_transfer"], tax_deducted=round(p["vda_transfer"] * 0.01)))
    if p["lrs_remittance"]:
        other.append(dict(information_code="TCS-206C(1G)", description="Remittance under Liberalised Remittance Scheme",
                          amount=p["lrs_remittance"]))
    b = p["business"]
    if b:
        if b["kind"] in ("44ADA", "44AD", "FNO"):
            other.append(dict(information_code="OTH-GST", description="Turnover as per GST returns (GSTR-3B)", amount=b["receipts"]))
        if b["kind"] == "44ADA":
            tds.append(dict(information_code="TDS-194J", description="Fees for professional or technical services",
                            source="Fictional Clients Pvt Ltd", tan=fake_tan(), amount_paid=int(b["receipts"] * .7),
                            tax_deducted=round(b["receipts"] * .7 * .10)))
        if b["kind"] == "PARTNER":
            other.append(dict(information_code="OTH-FIRM", description="Remuneration and interest from partnership firm",
                              amount=b["receipts"]))
    paid = []
    if b:
        paid.append(dict(information_code="TAX-ADV", description="Advance tax", source="Income Tax Department",
                         amount=round(total_income(p) * 0.08), date="15/03/2026"))
    for rows_ in (tds, sft, other, paid):
        for r in rows_:
            r.setdefault("status", "Active")
            v = r.get("amount_paid", r.get("amount", 0))
            r["reported_value"] = v
            r["modified_value"] = v      # taxpayer feedback; equals reported value unless the user disputes a row
    return dict(
        meta=dict(synthetic=True, document="Annual Information Statement (simplified model of the 5 portal tabs)",
                  financial_year=FY, assessment_year=AY),
        part_a=dict(pan=pan, aadhaar_masked="XXXXXXXX" + str(rnd.randint(1000, 9999)), name=p["name"],
                    date_of_birth=p["dob"], mobile="XXXXXX" + str(rnd.randint(1000, 9999)), email="sample@example.invalid"),
        part_b=dict(tds_tcs_information=tds, sft_information=sft, payment_of_taxes=paid,
                    demand_and_refund=[], other_information=other))

TIS_MAP = [  # (TIS category, AIS information_code prefixes)
    ("Salary", ["TDS-192"]), ("Interest from savings bank", ["SFT-016(SB)"]),
    ("Interest from deposit / other", ["TDS-194A"]), ("Dividend", ["TDS-194"]),
    ("Rent received", ["OTH-RENT"]), ("Sale of securities and units of mutual fund", ["SFT-017"]),
    ("Purchase of units of mutual fund", ["SFT-015"]),
    ("Sale of immovable property", ["TDS-194IA"]), ("Virtual digital asset transfer", ["TDS-194S"]),
    ("Business receipts (GST / TDS 194J)", ["OTH-GST", "TDS-194J", "OTH-FIRM"]),
    ("Foreign remittance (LRS)", ["TCS-206C(1G)"]),
]

def build_tis(ais):
    pb_ = ais["part_b"]
    rows = pb_["tds_tcs_information"] + pb_["sft_information"] + pb_["other_information"]
    out = []
    for cat, codes in TIS_MAP:
        amt = sum(r.get("amount_paid", r.get("amount", 0)) for r in rows if r["information_code"] in codes)
        if amt:
            out.append(dict(category=cat, information_value=amt, processed_value=amt, derived_value=amt))
    return dict(meta=dict(synthetic=True, document="Taxpayer Information Summary (simplified model)",
                          financial_year=FY, assessment_year=AY),
                pan=ais["part_a"]["pan"], name=ais["part_a"]["name"], summary=out)

# ----------------------------------------------------------------------------- PDF rendering
def _table(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), .4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 8),
             ("VALIGN", (0, 0), (-1, -1), "TOP")]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style)); return t

def _banner(c, d):
    # footer only: a diagonal watermark would sit on top of the tables and corrupt text extraction
    c.saveState(); c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.red)
    c.drawCentredString(A4[0] / 2, 8 * mm, "SAMPLE - SYNTHETIC DEMO DATA - NOT A REAL TAX DOCUMENT"); c.restoreState()

def _pdf(path, story):
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm,
                      bottomMargin=14 * mm).build(story, onFirstPage=_banner, onLaterPages=_banner)

def render_form16(p, pan, employer, path):
    s = salary_figures(p); H = STYLES["Heading3"]; N = STYLES["BodyText"]
    q_tax = [s["tax"] // 4] * 3 + [s["tax"] - 3 * (s["tax"] // 4)]
    q_amt = [s["gross"] // 4] * 3 + [s["gross"] - 3 * (s["gross"] // 4)]
    story = [Paragraph("FORM NO. 16", STYLES["Title"]),
             Paragraph("[See rule 31(1)(a)]  PART A  -  Certificate under section 203 of the Income-tax Act, 1961 for tax "
                       "deducted at source on salary. <b>SYNTHETIC DEMO DOCUMENT - NOT A REAL CERTIFICATE</b>", N),
             Spacer(1, 6),
             _table([["Employer", "Employee"],
                     [f"{employer['name']}\n{employer['addr']}", f"{p['name']}\n{employer['emp_addr']}"],
                     ["PAN of the Deductor", "TAN of the Deductor"], [employer["pan"], employer["tan"]],
                     ["PAN of the Employee", "Assessment Year"], [pan, AY],
                     ["Period with the Employer: From", "To"], ["01/04/2025", "31/03/2026"]],
                    [90 * mm, 90 * mm]),
             Spacer(1, 8), Paragraph("Summary of amount paid/credited and tax deducted at source", H),
             _table([["Quarter", "Receipt Number", "Amount paid/credited", "Amount of tax deducted", "Amount of tax deposited"]] +
                    [[f"Q{i+1}", f"24Q-Q{i+1}-{rnd.randint(100000, 999999)}", inr(q_amt[i]), inr(q_tax[i]), inr(q_tax[i])]
                     for i in range(4)] +
                    [["Total (Rs.)", "", inr(s["gross"]), inr(s["tax"]), inr(s["tax"])]],
                    [25 * mm, 45 * mm, 38 * mm, 38 * mm, 38 * mm]),
             Spacer(1, 10), Paragraph("PART B (Annexure)  -  Details of salary paid and tax deducted", H),
             _table([["Particulars", "Amount (Rs.)"],
                     ["Whether opting out of taxation u/s 115BAC(1A)?", "NO"],
                     ["1. Gross Salary (a) Salary as per section 17(1)", inr(p["salary"])],
                     ["   (b) Value of perquisites u/s 17(2) (as per Form 12BA)", inr(p["perqs"])],
                     ["   (c) Profits in lieu of salary u/s 17(3)", "0"],
                     ["   (d) Total", inr(p["salary"] + p["perqs"])],
                     ["2. Less: Allowances to the extent exempt u/s 10 (total)", "0"],
                     ["3. Total amount of salary received from current employer [1(d) - 2]", inr(p["salary"] + p["perqs"])],
                     ["4. Less: Deductions u/s 16 (a) Standard deduction u/s 16(ia)", inr(s["std"])],
                     ["   (b) Entertainment allowance u/s 16(ii)   (c) Tax on employment u/s 16(iii)", "0 / 0"],
                     ["5. Total amount of deductions under section 16 [4(a)+4(b)+4(c)]", inr(s["std"])],
                     ["6. Income chargeable under the head 'Salaries' [3 - 5]", inr(s["net"])],
                     ["7. Add: Any other income reported by the employee (house property / other sources)", "0"],
                     ["8. Total amount of other income reported by the employee", "0"],
                     ["9. Gross total income [6 + 8]", inr(s["net"])],
                     ["10. Deductions under Chapter VI-A: 80CCD(2) employer contribution to NPS", inr(s["nps"])],
                     ["11. Aggregate of deductible amount under Chapter VI-A", inr(s["nps"])],
                     ["12. Total taxable income [9 - 11]", inr(s["taxable"])],
                     ["13. Tax on total income", inr(s["base_tax"])],
                     ["14. Rebate under section 87A", inr(s["rebate"])],
                     ["15. Surcharge", inr(s["surcharge"])],
                     ["16. Health and education cess @4%", inr(s["cess"])],
                     ["17. Tax payable [13 - 14 + 15 + 16]", inr(s["tax"])],
                     ["18. Less: Relief under section 89", "0"],
                     ["19. Net tax payable [17 - 18]", inr(s["tax"])]],
                    [135 * mm, 45 * mm]),
             Spacer(1, 8), Paragraph(f"Verification: I, {employer['signatory']}, working as Manager - Payroll, certify that the "
                                     "information given above is true (sample data).", N)]
    _pdf(path, story)

# ----------------------------------------------------------------------------- main
def main():
    OUT.mkdir(exist_ok=True)
    golden = []
    for p in PERSONAS:
        d = OUT / p["id"]; d.mkdir(exist_ok=True)
        pan = fake_pan(p)
        employer = dict(name=f"{rnd.choice(['BluePeak','Northwind','Zenith','Kestrel','Orchid'])} "
                             f"{rnd.choice(['Analytics','Systems','Labs','Industries'])} Pvt Ltd",
                        addr="12, Sample Tech Park, Bengaluru - 560001", emp_addr="Flat 4B, Sample Residency, Pune - 411001",
                        tan=fake_tan(), pan="AAACB" + str(rnd.randint(1000, 9999)) + "X", signatory="A. Sample")
        ais = build_ais(p, pan, employer); tis = build_tis(ais)
        (d / "ais.json").write_text(json.dumps(ais, indent=2), encoding="utf-8")
        (d / "tis.json").write_text(json.dumps(tis, indent=2), encoding="utf-8")
        if p["salary"]:
            render_form16(p, pan, employer, d / "form16.pdf")
        pb = ais["part_b"]
        def rows(items, cols):
            return [[c[0] for c in cols]] + [[str(i.get(c[1], "")) if not isinstance(i.get(c[1]), (int, float)) else inr(i[c[1]]) for c in cols] for i in items]
        secs = []
        if pb["tds_tcs_information"]: secs.append(("Part B - TDS/TCS Information", rows(pb["tds_tcs_information"], [("Code", "information_code"), ("Description", "description"), ("Source", "source"), ("Amount (Rs.)", "amount_paid"), ("Tax deducted", "tax_deducted")])))
        if pb["payment_of_taxes"]: secs.append(("Part B - Payment of Taxes", rows(pb["payment_of_taxes"], [("Code", "information_code"), ("Description", "description"), ("Date", "date"), ("Amount (Rs.)", "amount")])))
        if pb["sft_information"]: secs.append(("Part B - SFT Information", rows(pb["sft_information"], [("Code", "information_code"), ("Description", "description"), ("Source", "source"), ("Amount (Rs.)", "amount")])))
        if pb["other_information"]: secs.append(("Part B - Other Information", rows(pb["other_information"], [("Code", "information_code"), ("Description", "description"), ("Amount (Rs.)", "amount")])))
        story = [Paragraph("Annual Information Statement (AIS)", STYLES["Title"]),
                 Paragraph(f"Name: {p['name']}  PAN: {pan}  FY {FY} (AY {AY}). <b>SYNTHETIC DEMO DOCUMENT - simplified model.</b>", STYLES["BodyText"]), Spacer(1, 8)]
        for head, r in secs:
            story += [Paragraph(head, STYLES["Heading3"]), _table(r, None), Spacer(1, 6)]
        if not secs: story.append(Paragraph("No information reported.", STYLES["BodyText"]))
        _pdf(d / "ais.pdf", story)
        tstory = [Paragraph("Taxpayer Information Summary (TIS)", STYLES["Title"]),
                  Paragraph(f"Name: {p['name']}  PAN: {pan}  FY {FY} (AY {AY}). <b>SYNTHETIC DEMO DOCUMENT - simplified model.</b>", STYLES["BodyText"]), Spacer(1, 8),
                  _table([["Information category", "Information value (Rs.)", "Processed value (Rs.)", "Derived value (Rs.)"]] +
                         [[r["category"], inr(r["information_value"]), inr(r["processed_value"]), inr(r["derived_value"])] for r in tis["summary"]] or [["-", "-", "-", "-"]], None)]
        _pdf(d / "tis.pdf", tstory)
        golden.append(dict(id=p["id"], title=p["title"], expected_itr=p["expected_itr"], reasons=p["reasons"],
                           pan=pan, name=p["name"], dob=p["dob"], approx_total_income=total_income(p),
                           questionnaire=p["q"],
                           facts=dict(salary=p["salary"], hp_count=p["hp_count"], rent_received=p["rent_received"],
                                      interest_savings=p["interest_savings"], interest_fd=p["interest_fd"], dividend=p["dividend"],
                                      ltcg_112a=p["ltcg_112a"], stcg_111a=p["stcg_111a"], ltcg_property=p["ltcg_property"],
                                      vda_transfer=p["vda_transfer"], agri_income=p["agri_income"], lrs_remittance=p["lrs_remittance"],
                                      business=p["business"]),
                           files=[f for f in ("form16.pdf", "ais.json", "ais.pdf", "tis.json", "tis.pdf") if (d / f).exists()]))
    (OUT / "golden_itr.json").write_text(json.dumps(golden, indent=2), encoding="utf-8")
    print(f"wrote {len(golden)} personas to {OUT}")

if __name__ == "__main__":
    main()
