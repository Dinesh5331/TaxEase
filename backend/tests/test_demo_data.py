"""Consistency checks for the synthetic taxpayer data. Run: python -m unittest discover -s tests"""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "demo_data"
GOLDEN = json.loads((ROOT / "golden_itr.json").read_text(encoding="utf-8"))
ITRS = {"ITR-1", "ITR-2", "ITR-3", "ITR-4"}
PAN = re.compile(r"^[A-Z]{3}P[A-Z][0-9]{4}[A-Z]$")


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True).stdout


class DemoData(unittest.TestCase):
    def test_golden_covers_every_form_and_edge_cases(self):
        self.assertEqual({g["expected_itr"] for g in GOLDEN}, ITRS)
        self.assertGreaterEqual(len(GOLDEN), 20)
        self.assertEqual(len({g["id"] for g in GOLDEN}), len(GOLDEN))

    def test_files_exist_and_pan_valid(self):
        for g in GOLDEN:
            self.assertRegex(g["pan"], PAN, g["id"])
            for f in g["files"]:
                self.assertTrue((ROOT / g["id"] / f).exists(), f"{g['id']}/{f}")
            self.assertEqual("form16.pdf" in g["files"], g["facts"]["salary"] > 0, g["id"])

    def test_tis_matches_ais_and_form16_matches_ais(self):
        for g in GOLDEN:
            d = ROOT / g["id"]
            ais = json.loads((d / "ais.json").read_text(encoding="utf-8"))
            tis = json.loads((d / "tis.json").read_text(encoding="utf-8"))
            self.assertEqual(ais["part_a"]["pan"], g["pan"])
            self.assertEqual(tis["pan"], g["pan"])
            for r in tis["summary"]:
                self.assertEqual(r["information_value"], r["processed_value"], g["id"])
            sal = [r for r in ais["part_b"]["tds_tcs_information"] if r["information_code"] == "TDS-192"]
            if g["facts"]["salary"]:
                self.assertEqual(sal[0]["amount_paid"], g["facts"]["salary"])
                txt = pdf_text(d / "form16.pdf")
                self.assertIn("FORM NO. 16", txt)
                self.assertIn(g["pan"], txt)
                self.assertIn("SYNTHETIC", txt)
            else:
                self.assertFalse(sal, g["id"])

    def test_signals_present_for_disqualifiers(self):
        by = {g["id"]: g for g in GOLDEN}
        def codes(i):
            a = json.loads((ROOT / i / "ais.json").read_text(encoding="utf-8"))["part_b"]
            return {r["information_code"] for k in a for r in a[k]}
        self.assertIn("SFT-017", codes("p04_ltcg_112a_over_limit"))
        self.assertIn("TDS-194S", codes("p14_crypto_vda"))
        self.assertIn("TDS-194IA", codes("p18_property_sale"))
        self.assertIn("TCS-206C(1G)", codes("p08_foreign_assets"))
        self.assertIn("OTH-GST", codes("p10_freelancer_44ada"))
        self.assertGreater(by["p07_income_over_50l"]["approx_total_income"], 5_000_000)
        self.assertLessEqual(by["p01_salaried_simple"]["approx_total_income"], 5_000_000)


if __name__ == "__main__":
    unittest.main()
