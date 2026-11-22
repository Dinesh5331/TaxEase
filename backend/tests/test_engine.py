"""Gate for the rules engine: it must reproduce every hand-written golden label."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rules.engine import Facts, ITR1_PREDICATES, ITR4_PREDICATES, select_itr, yaml_rule_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[1] / "demo_data"
GOLDEN = json.loads((ROOT / "golden_itr.json").read_text(encoding="utf-8"))


def facts_from_golden(g) -> Facts:
    """Build Facts straight from the label's own structured facts (independent of the extractors)."""
    f, q = g["facts"], g["questionnaire"]
    b = f["business"]
    kind = None
    if b:
        kind = {"44ADA": "44ADA", "44AD": "44AD", "FNO": "SPECULATIVE", "PARTNER": None}[b["kind"]]
    return Facts(
        entity="individual", total_income=g["approx_total_income"],
        residential_status=q["residential_status"], director=q["director"], unlisted_equity=q["unlisted_equity"],
        foreign_asset_or_income=q["foreign_asset_or_income"], loss_carry_forward=q["loss_carry_forward"],
        esop_deferral=q["esop_deferral"], tds_194N=False, partner_in_firm=q["partner_in_firm"], hp_count=f["hp_count"],
        ltcg_112a=f["ltcg_112a"], stcg_111a=f["stcg_111a"], ltcg_other=f["ltcg_property"], vda_gain=f["vda_transfer"] * 0.5,
        agri_income=f["agri_income"], business_kind=kind,
        business_receipts=(b or {}).get("receipts", 0) if kind else 0,
        cash_receipt_pct=(b or {}).get("cash_pct"),
    )


class EngineGate(unittest.TestCase):
    def test_all_golden_labels(self):
        wrong = []
        for g in GOLDEN:
            r = select_itr(facts_from_golden(g))
            if r.form != g["expected_itr"]:
                wrong.append((g["id"], g["expected_itr"], r.form, r.failed_rules))
        self.assertEqual(wrong, [], f"engine disagrees with labels: {wrong}")

    def test_itr2_reasons_match_labels(self):
        """For ITR-2 labels the named rule must be among those that failed; for ITR-1 labels nothing fails."""
        for g in GOLDEN:
            r = select_itr(facts_from_golden(g))
            if g["expected_itr"] == "ITR-2":
                self.assertTrue(set(g["reasons"]) <= set(r.failed_rules), (g["id"], g["reasons"], r.failed_rules))
            if g["expected_itr"] == "ITR-1":
                self.assertEqual(r.failed_rules, [], g["id"])

    def test_complete_answers_give_final_status(self):
        for g in GOLDEN:
            self.assertEqual(select_itr(facts_from_golden(g)).status, "final", g["id"])

    def test_yaml_and_predicates_list_the_same_rules(self):
        ids = yaml_rule_ids()
        self.assertEqual(set(ids["ITR-1"]), set(ITR1_PREDICATES))
        self.assertEqual(set(ids["ITR-4"]), set(ITR4_PREDICATES))


class Boundaries(unittest.TestCase):
    base = dict(residential_status="ROR", director=False, unlisted_equity=False, foreign_asset_or_income=False,
                loss_carry_forward=False, esop_deferral=False, tds_194N=False, partner_in_firm=False, hp_count=0,
                total_income=1_000_000)

    def form(self, **kw):
        return select_itr(Facts(**{**self.base, **kw})).form

    def test_112a_limit_is_inclusive(self):
        self.assertEqual(self.form(ltcg_112a=125_000), "ITR-1")
        self.assertEqual(self.form(ltcg_112a=125_001), "ITR-2")

    def test_income_cap_is_inclusive(self):
        self.assertEqual(self.form(total_income=5_000_000), "ITR-1")
        self.assertEqual(self.form(total_income=5_000_001), "ITR-2")

    def test_agri_and_house_property_limits(self):
        self.assertEqual(self.form(agri_income=5_000), "ITR-1")
        self.assertEqual(self.form(agri_income=5_001), "ITR-2")
        self.assertEqual(self.form(hp_count=2), "ITR-1")
        self.assertEqual(self.form(hp_count=3), "ITR-2")

    def test_rnor_goes_to_itr2(self):
        self.assertEqual(self.form(residential_status="RNOR"), "ITR-2")

    def test_44ada_limits(self):
        p = dict(business_kind="44ADA", total_income=3_000_000)
        self.assertEqual(self.form(business_receipts=5_000_000, cash_receipt_pct=10, **p), "ITR-4")
        self.assertEqual(self.form(business_receipts=5_000_001, cash_receipt_pct=10, **p), "ITR-3")
        self.assertEqual(self.form(business_receipts=7_500_000, cash_receipt_pct=5, **p), "ITR-4")
        self.assertEqual(self.form(business_receipts=7_500_001, cash_receipt_pct=5, **p), "ITR-3")
        # unknown cash share: do not assume the 75L limit
        self.assertEqual(self.form(business_receipts=6_000_000, cash_receipt_pct=None, **p), "ITR-3")

    def test_44ad_limits(self):
        p = dict(business_kind="44AD", total_income=1_000_000)
        self.assertEqual(self.form(business_receipts=20_000_000, cash_receipt_pct=40, **p), "ITR-4")
        self.assertEqual(self.form(business_receipts=20_000_001, cash_receipt_pct=40, **p), "ITR-3")
        self.assertEqual(self.form(business_receipts=30_000_000, cash_receipt_pct=5, **p), "ITR-4")

    def test_presumptive_with_disqualifier_goes_to_itr3(self):
        p = dict(business_kind="44AD", business_receipts=5_000_000, cash_receipt_pct=10)
        self.assertEqual(self.form(foreign_asset_or_income=True, **p), "ITR-3")
        self.assertEqual(self.form(stcg_111a=1, **p), "ITR-3")
        self.assertEqual(self.form(vda_gain=1, **p), "ITR-3")
        self.assertEqual(self.form(opted_out_of_presumptive_within_5y=True, **p), "ITR-3")

    def test_huf_never_itr1(self):
        self.assertEqual(self.form(entity="huf"), "ITR-2")

    def test_non_individuals(self):
        self.assertEqual(self.form(entity="company"), "ITR-6")
        self.assertEqual(self.form(entity="llp"), "ITR-5")
        self.assertEqual(self.form(entity="trust_institution"), "ITR-7")

    def test_unknown_questionnaire_is_provisional_not_wrong(self):
        r = select_itr(Facts(total_income=900_000))
        self.assertEqual(r.status, "provisional")
        self.assertIn("director", r.missing)
        self.assertEqual(r.form, "ITR-1")

    def test_unknown_gain_on_securities_is_flagged(self):
        r = select_itr(Facts(**{**self.base, "securities_sold_gain_unknown": True}))
        self.assertEqual(r.status, "provisional")
        self.assertIn("capital_gain_amounts", r.missing)


if __name__ == "__main__":
    unittest.main()
