"""End to end: demo documents + the user's answers -> ITR. Labels come from golden_itr.json, not from the engine."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extractors.ais import parse_ais, parse_tis, cross_check, bucket_for  # noqa: E402
from extractors.form16 import extract_form16, parse_form16_text  # noqa: E402
from services.analyze import analyze  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "demo_data"
GOLDEN = json.loads((ROOT / "golden_itr.json").read_text(encoding="utf-8"))


def read(pid, name):
    return json.loads((ROOT / pid / name).read_text(encoding="utf-8"))


def answers_for(g) -> dict:
    """What a user would type into the questionnaire (capital gains come from their broker statement)."""
    q, f = g["questionnaire"], g["facts"]
    a = {**{k: v for k, v in q.items()}, "hp_count": f["hp_count"], "tds_194N": False, "agri_income": f["agri_income"],
         "ltcg_112a": f["ltcg_112a"], "stcg_111a": f["stcg_111a"], "ltcg_other": f["ltcg_property"],
         "vda_gain": f["vda_transfer"] * 0.5 if f["vda_transfer"] else 0}
    b = f["business"]
    if b and b["kind"] in ("44AD", "44ADA"):
        a.update(business_kind=b["kind"], cash_receipt_pct=b["cash_pct"])
    if b and b["kind"] == "FNO":
        a.update(business_kind="SPECULATIVE", business_profit=b["receipts"] * 0.35)
    return a


def run(g, answers):
    d = ROOT / g["id"]
    f16 = d / "form16.pdf" if "form16.pdf" in g["files"] else None
    return analyze(f16, read(g["id"], "ais.json"), read(g["id"], "tis.json"), answers)


class Form16Parse(unittest.TestCase):
    def test_every_form16_matches_its_label(self):
        n = 0
        for g in GOLDEN:
            if "form16.pdf" not in g["files"]:
                continue
            f = extract_form16(ROOT / g["id"] / "form16.pdf")
            n += 1
            self.assertEqual(f.missing, [], g["id"])
            self.assertEqual(f.warnings, [], (g["id"], f.warnings))
            self.assertEqual(f.get("gross_salary"), g["facts"]["salary"], g["id"])
            self.assertEqual(f.get("employee_pan"), g["pan"], g["id"])
            self.assertEqual(f.get("assessment_year"), "2026-27")
            self.assertFalse(f.get("opted_out_of_new_regime"), g["id"])
            self.assertEqual(f.get("income_from_salary"), g["facts"]["salary"] - 75_000, g["id"])
        self.assertEqual(n, 16)

    def test_pypdf_fallback_gives_same_numbers(self):
        import pypdf
        r = pypdf.PdfReader(str(ROOT / "p01_salaried_simple" / "form16.pdf"))
        text = "\n".join(p.extract_text(extraction_mode="layout") for p in r.pages)
        f = parse_form16_text(text)
        self.assertEqual(f.get("gross_salary"), 1_450_000)
        self.assertEqual(f.missing, [])

    def test_garbage_is_reported_as_missing_not_guessed(self):
        f = parse_form16_text("this is not a form 16")
        self.assertEqual(set(f.missing), {"gross_salary", "income_from_salary", "total_taxable_income", "net_tax_payable"})
        self.assertEqual(f.fields, {})

    def test_tampered_arithmetic_lowers_confidence(self):
        text = (ROOT / "p01_salaried_simple" / "form16.pdf")
        from extractors.form16 import pdf_layout_text
        t = pdf_layout_text(text).replace("13,75,000", "13,70,000", 1)
        f = parse_form16_text(t)
        self.assertTrue(f.warnings)


class AisParse(unittest.TestCase):
    def test_tis_agrees_with_ais_for_every_persona(self):
        for g in GOLDEN:
            ais, tis = parse_ais(read(g["id"], "ais.json")), parse_tis(read(g["id"], "tis.json"))
            self.assertEqual(cross_check(ais, tis), [], g["id"])

    def test_unknown_code_is_not_silently_dropped_or_misfiled(self):
        data = read("p01_salaried_simple", "ais.json")
        data["part_b"]["tds_tcs_information"].append({"information_code": "TDS-194C", "description": "Contractor", "amount_paid": 1000})
        a = parse_ais(data)
        self.assertEqual(a.unmapped[0]["code"], "TDS-194C")
        self.assertEqual(a.amount("dividend"), 0)
        self.assertIsNone(bucket_for("TDS-194C"))

    def test_inactive_rows_skipped_and_modified_value_used(self):
        data = read("p01_salaried_simple", "ais.json")
        data["part_b"]["sft_information"][0]["modified_value"] = 5000
        data["part_b"]["tds_tcs_information"].append({"information_code": "TDS-194", "amount_paid": 99, "status": "Inactive"})
        a = parse_ais(data)
        self.assertEqual(a.amount("interest_savings"), 5000)
        self.assertEqual(a.amount("dividend"), 0)
        self.assertEqual(len(a.skipped), 1)
        self.assertEqual(a.disputed[0]["code"], "SFT-016(SB)")


class Pipeline(unittest.TestCase):
    def test_all_21_personas_documents_plus_answers(self):
        wrong = []
        for g in GOLDEN:
            out = run(g, answers_for(g))
            rec = out["recommendation"]
            if rec["form"] != g["expected_itr"]:
                wrong.append((g["id"], g["expected_itr"], rec["form"], rec["failed_rules"], out["report"]["total_income_estimate"]["total"]))
            self.assertEqual(rec["status"], "final", (g["id"], rec["missing"]))
        self.assertEqual(wrong, [])

    def test_estimate_close_to_label_income(self):
        for g in GOLDEN:
            est = run(g, answers_for(g))["report"]["total_income_estimate"]["total"]
            lab = g["approx_total_income"]
            self.assertLess(abs(est - lab), max(0.35 * lab, 150_000), (g["id"], est, lab))

    def test_documents_alone_ask_for_the_unprovable_facts(self):
        out = run(GOLDEN[0], {})
        self.assertEqual(out["recommendation"]["status"], "provisional")
        ids = {q["id"] for q in out["report"]["open_questions"]}
        self.assertTrue({"residential_status", "director", "foreign_asset_or_income", "loss_carry_forward", "hp_count"} <= ids)

    def test_securities_sale_without_gain_is_not_called_itr1(self):
        g = next(x for x in GOLDEN if x["id"] == "p03_small_ltcg_112a")
        a = answers_for(g)
        for k in ("ltcg_112a", "stcg_111a", "ltcg_other"):
            a.pop(k)
        out = run(g, a)
        self.assertEqual(out["recommendation"]["status"], "provisional")
        self.assertIn("capital_gain_amounts", out["recommendation"]["missing"])
        self.assertIn("ltcg_112a", {q["id"] for q in out["report"]["open_questions"]})

    def test_property_sale_forces_itr2_even_without_gain_answer(self):
        g = next(x for x in GOLDEN if x["id"] == "p18_property_sale")
        a = answers_for(g)
        a.pop("ltcg_other")
        self.assertEqual(run(g, a)["recommendation"]["form"], "ITR-2")

    def test_vda_forces_itr2_even_with_zero_gain(self):
        g = next(x for x in GOLDEN if x["id"] == "p14_crypto_vda")
        a = answers_for(g)
        a["vda_gain"] = 0
        rec = run(g, a)["recommendation"]
        self.assertEqual(rec["form"], "ITR-2")
        self.assertIn("i1_special", rec["failed_rules"])

    def test_lrs_with_no_foreign_assets_answer_is_flagged(self):
        g = next(x for x in GOLDEN if x["id"] == "p08_foreign_assets")
        a = answers_for(g)
        a["foreign_asset_or_income"] = False
        out = run(g, a)
        self.assertTrue(any("LRS" in c for c in out["report"]["conflicts"]))

    def test_pan_is_masked_in_output(self):
        g = GOLDEN[0]
        out = run(g, answers_for(g))
        self.assertNotIn(g["pan"], json.dumps(out))
        self.assertEqual(out["taxpayer"]["pan_masked"], g["pan"][:2] + "******" + g["pan"][-2:])

    def test_document_mismatch_is_reported(self):
        g = GOLDEN[0]
        ais = read(g["id"], "ais.json")
        ais["part_b"]["tds_tcs_information"][0]["modified_value"] = 1_000_000
        out = analyze(ROOT / g["id"] / "form16.pdf", ais, None, answers_for(g))
        self.assertTrue(any("Salary differs" in c for c in out["report"]["conflicts"]))

    def test_requires_a_document(self):
        with self.assertRaises(ValueError):
            analyze(None, None, None, {})


if __name__ == "__main__":
    unittest.main()
