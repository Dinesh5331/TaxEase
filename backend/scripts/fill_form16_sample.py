from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[2]
INPUT_PDF = ROOT / "backend" / "docs" / "forms" / "form-16.pdf"
OUTPUT_PDF = ROOT / "backend" / "docs" / "forms" / "form-16-filled-sample.pdf"


SAMPLE = {
    "certificate_no": "TDSF16/2025-26/00941",
    "last_updated_on": "19/04/2026",
    "employer_name": "BluePeak Analytics Private Limited",
    "employer_addr_1": "45, Residency Tech Park, Richmond Road",
    "employer_addr_2": "Bengaluru, Karnataka - 560025",
    "employee_name": "Karan Malhotra",
    "employee_addr_1": "A-804, Maple Heights, Sector 62",
    "employee_addr_2": "Noida, Uttar Pradesh - 201309",
    "deductor_pan": "AABCB4521M",
    "deductor_tan": "BLRB05231B",
    "employee_pan": "DPSPK7843L",
    "employee_ref": "EMP-24017",
    "cit_address_1": "CIT (TDS), Bengaluru",
    "cit_address_2": "Address: BMTC Complex, Koramangala  ",
    "cit_address_3": "City: Bengaluru      Pin code: 560095",
    "assessment_year": "2025-26",
    "period_from": "01/04/2024",
    "period_to": "31/03/2025",
    "quarters": [
        ("Q1", "24Q-Q1-874210", "255000", "20000", "20000"),
        ("Q2", "24Q-Q2-874211", "255000", "20000", "20000"),
        ("Q3", "24Q-Q3-874212", "255000", "20000", "20000"),
        ("Q4", "24Q-Q4-874213", "255000", "23430", "23430"),
    ],
    "summary_total": ("1020000", "83430", "83430"),
    "challan_rows": [
        ("1", "40000", "0510032", "07/08/2024", "12874", "Matched"),
        ("2", "43430", "0510032", "07/03/2025", "24591", "Matched"),
    ],
    "challan_total": "83430",
    "verifier_name": "Ananya Rao",
    "verifier_parent": "Suresh Rao",
    "verifier_designation": "Finance Manager",
    "verification_amount": "83430",
    "verification_amount_words": "Eighty Three Thousand Four Hundred Thirty Only",
    "place": "Bengaluru",
    "date": "19/04/2026",
    "part_b": {
        "1a": "960000",
        "1b": "60000",
        "1c": "0",
        "1d": "1020000",
        "allowance_label": "House Rent Allowance",
        "allowance_value": "120000",
        "allowance_2": "Leave Travel Allowance",
        "allowance_2_value": "30000",
        "2_total": "150000",
        "3": "870000",
        "4a": "0",
        "4b": "2400",
        "5": "2400",
        "6": "867600",
        "other_income_label": "Savings Bank Interest",
        "other_income_value": "12400",
        "7": "12400",
        "8": "880000",
        "80c_items": [
            ("Employee Provident Fund", "72000"),
            ("Public Provident Fund", "18000"),
            ("Life Insurance Premium", "10000"),
        ],
        "80ccc_gross": "0",
        "80ccc_deduct": "0",
        "80ccd_gross": "0",
        "80ccd_deduct": "0",
        "10": "100000",
        "11": "780000",
        "12": "81000",
        "13": "2430",
        "14": "83430",
        "15": "0",
        "16": "83430",
    },
}


def draw_text(page, rect, text, fontsize=9, align=0, fontname="helv"):
    page.insert_textbox(
        fitz.Rect(*rect),
        str(text),
        fontsize=fontsize,
        fontname=fontname,
        color=(0, 0, 0),
        align=align,
    )


def draw_text_at(page, point, text, fontsize=9, fontname="helv"):
    page.insert_text(
        fitz.Point(*point),
        str(text),
        fontsize=fontsize,
        fontname=fontname,
        color=(0, 0, 0),
    )


def fill_page_1(page):
    s = SAMPLE

    draw_text(page, (110, 138, 290, 153), s["certificate_no"], fontsize=8)
    draw_text(page, (360, 138, 520, 153), s["last_updated_on"], fontsize=8)

    draw_text(page, (90, 167, 310, 208), f'{s["employer_name"]}\n{s["employer_addr_1"]}\n{s["employer_addr_2"]}', fontsize=8, align=1)
    draw_text(page, (333, 167, 570, 208), f'{s["employee_name"]}\n{s["employee_addr_1"]}\n{s["employee_addr_2"]}', fontsize=8, align=1)

    draw_text(page, (95, 208, 220, 228), s["deductor_pan"], fontsize=9, align=1)
    draw_text(page, (257, 208, 383, 228), s["deductor_tan"], fontsize=9, align=1)
    draw_text(page, (390, 208, 454, 228), s["employee_pan"], fontsize=9, align=1)
    draw_text(page, (455, 208, 580, 228), s["employee_ref"], fontsize=8, align=1)

    draw_text(page, (10, 247, 323, 298), f'{s["cit_address_1"]}\n{s["cit_address_2"]}\n{s["cit_address_3"]}', fontsize=8)
    draw_text(page, (340, 248, 448, 266), s["assessment_year"], fontsize=9, align=1)
    draw_text(page, (456, 267, 523, 286), s["period_from"], fontsize=8, align=1)
    draw_text(page, (524, 267, 590, 286), s["period_to"], fontsize=8, align=1)

    quarter_y = [307, 333, 359, 385]
    for y, row in zip(quarter_y, s["quarters"]):
        q, receipt, amount, tax_deducted, tax_deposited = row
        draw_text(page, (12, y, 124, y + 18), q, fontsize=8, align=1)
        draw_text(page, (126, y, 260, y + 18), receipt, fontsize=7, align=1)
        draw_text(page, (261, y, 358, y + 18), amount, fontsize=8, align=1)
        draw_text(page, (359, y, 490, y + 18), tax_deducted, fontsize=8, align=1)
        draw_text(page, (491, y, 602, y + 18), tax_deposited, fontsize=8, align=1)

    draw_text(page, (262, 411, 358, 429), s["summary_total"][0], fontsize=8, align=1)
    draw_text(page, (359, 411, 490, 429), s["summary_total"][1], fontsize=8, align=1)
    draw_text(page, (491, 411, 602, 429), s["summary_total"][2], fontsize=8, align=1)

    challan_y = [595, 621]
    for y, row in zip(challan_y, s["challan_rows"]):
        sl, tax_amt, bsr, dep_date, challan_no, status = row
        draw_text(page, (12, y, 100, y + 18), sl, fontsize=8, align=1)
        draw_text(page, (101, y, 205, y + 18), tax_amt, fontsize=8, align=1)
        draw_text(page, (206, y, 304, y + 18), bsr, fontsize=8, align=1)
        draw_text(page, (305, y, 470, y + 18), dep_date, fontsize=8, align=1)
        draw_text(page, (471, y, 539, y + 18), challan_no, fontsize=8, align=1)
        draw_text(page, (540, y, 606, y + 18), status, fontsize=7, align=1)

    draw_text(page, (100, 648, 205, 665), s["challan_total"], fontsize=8, align=1)

    verification = (
        f'I, {s["verifier_name"]}, son/daughter of {s["verifier_parent"]} working in the capacity of '
        f'{s["verifier_designation"]} do hereby certify that a sum of Rs. {s["verification_amount"]} '
        f'[Rs. {s["verification_amount_words"]} (in words)] has been deducted and deposited to the '
        f'credit of the Central Government.'
    )
    draw_text(page, (13, 705, 598, 744), verification, fontsize=7.5)
    draw_text(page, (15, 747, 82, 762), s["place"], fontsize=8)
    draw_text(page, (15, 765, 82, 780), s["date"], fontsize=8)
    draw_text(page, (440, 765, 595, 780), s["verifier_designation"], fontsize=8, align=1)
    draw_text(page, (470, 782, 598, 792), s["verifier_name"], fontsize=8, align=1)


def fill_page_2(page):
    b = SAMPLE["part_b"]

    draw_text_at(page, (355, 104), b["1a"], fontsize=8)
    draw_text_at(page, (355, 135), b["1b"], fontsize=8)
    draw_text_at(page, (355, 166), b["1c"], fontsize=8)
    draw_text_at(page, (355, 196), b["1d"], fontsize=8)

    draw_text_at(page, (120, 243), b["allowance_label"], fontsize=6.2)
    draw_text_at(page, (292, 243), b["allowance_value"], fontsize=8)
    draw_text_at(page, (120, 263), b["allowance_2"], fontsize=6.2)
    draw_text_at(page, (292, 263), b["allowance_2_value"], fontsize=8)
    draw_text_at(page, (355, 260), b["2_total"], fontsize=8)

    draw_text_at(page, (355, 323), b["3"], fontsize=8)
    draw_text_at(page, (355, 375), b["4a"], fontsize=8)
    draw_text_at(page, (355, 404), b["4b"], fontsize=8)
    draw_text_at(page, (355, 425), b["5"], fontsize=8)
    draw_text_at(page, (355, 458), b["6"], fontsize=8)

    draw_text_at(page, (120, 503), b["other_income_label"], fontsize=6.2)
    draw_text_at(page, (292, 503), b["other_income_value"], fontsize=8)
    draw_text_at(page, (355, 559), b["7"], fontsize=8)
    draw_text_at(page, (355, 611), b["8"], fontsize=8)

    item_y = [459, 473, 487]
    for y, (label, amount) in zip(item_y, b["80c_items"]):
        draw_text_at(page, (150, y), label, fontsize=6.2)
        draw_text_at(page, (406, y), amount, fontsize=8)
        draw_text_at(page, (481, y), amount, fontsize=8)

    draw_text_at(page, (406, 555), b["80ccc_gross"], fontsize=8)
    draw_text_at(page, (481, 555), b["80ccc_deduct"], fontsize=8)
    draw_text_at(page, (406, 574), b["80ccd_gross"], fontsize=8)
    draw_text_at(page, (481, 574), b["80ccd_deduct"], fontsize=8)


def fill_page_3(page):
    b = SAMPLE["part_b"]
    draw_text_at(page, (355, 175), b["10"], fontsize=8)
    draw_text_at(page, (355, 200), b["11"], fontsize=8)
    draw_text_at(page, (355, 219), b["12"], fontsize=8)
    draw_text_at(page, (355, 238), b["13"], fontsize=8)
    draw_text_at(page, (355, 257), b["14"], fontsize=8)
    draw_text_at(page, (355, 276), b["15"], fontsize=8)
    draw_text_at(page, (355, 295), b["16"], fontsize=8)

    verification = (
        f'I, {SAMPLE["verifier_name"]}, son/daughter of {SAMPLE["verifier_parent"]} '
        f'working in the capacity of {SAMPLE["verifier_designation"]} do hereby certify '
        f'that the information given above is true, complete and correct.'
    )
    draw_text(page, (14, 322, 598, 343), verification, fontsize=7.5)
    draw_text_at(page, (70, 357), SAMPLE["place"], fontsize=8)
    draw_text_at(page, (70, 383), SAMPLE["date"], fontsize=8)
    draw_text_at(page, (15, 406), SAMPLE["verifier_designation"], fontsize=8)
    draw_text_at(page, (280, 406), SAMPLE["verifier_name"], fontsize=8)


def main():
    doc = fitz.open(INPUT_PDF)
    fill_page_1(doc[0])
    fill_page_2(doc[1])
    fill_page_3(doc[2])
    doc.save(OUTPUT_PDF)
    print(OUTPUT_PDF)


if __name__ == "__main__":
    main()
