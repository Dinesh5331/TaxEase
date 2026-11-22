"""Regime comparator tests. Worked examples marked [CT] reproduce the figures published by ClearTax for FY 2025-26."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rules.regime import Inputs, compute, compare, hra_exemption  # noqa: E402


class Regime(unittest.TestCase):
    def test_zero_tax_up_to_12_75_lakh_salary_new(self):                          # [CT] salary 12.75L -> nil
        self.assertEqual(compute(Inputs(salary=1_275_000), "new")["total_tax"], 0)

    def test_salary_15_lakh_new(self):                                            # [CT] Mr Raj: 97,500
        self.assertEqual(compute(Inputs(salary=1_500_000), "new")["total_tax"], 97_500)

    def test_salary_25_lakh_both_regimes(self):                                   # [CT] Mr Anban: new 3,19,800 / old 3,90,000
        i = Inputs(salary=2_500_000, other_exempt_allowances=400_000, d80c=150_000, d80d_self=25_000)
        self.assertEqual(compute(i, "new")["total_tax"], 319_800)
        self.assertEqual(compute(i, "old")["total_tax"], 390_000)
        self.assertEqual(compare(i)["recommended"], "new")

    def test_hra_least_of_three(self):
        self.assertEqual(hra_exemption(600_000, 300_000, 360_000, True), 300_000)
        self.assertEqual(hra_exemption(600_000, 300_000, 120_000, True), 60_000)       # rent - 10% basic
        self.assertEqual(hra_exemption(600_000, 300_000, 360_000, False), 240_000)     # 40% non-metro
        self.assertEqual(hra_exemption(600_000, 0, 360_000, True), 0)

    def test_old_wins_with_heavy_deductions(self):
        i = Inputs(salary=2_000_000, basic_da=1_000_000, hra_received=400_000, rent_paid=480_000, metro=True,
                   d80c=150_000, d80d_self=25_000, d80d_parents=25_000, d80ccd_1b=50_000, self_occ_interest=200_000)
        r = compare(i)
        self.assertEqual(r["recommended"], "old")
        self.assertLess(r["old"]["total_tax"], r["new"]["total_tax"])
        self.assertEqual(r["extra_old_deductions_needed_for_old_to_win"], 0)

    def test_belated_filer_is_forced_to_new(self):
        i = Inputs(salary=2_000_000, basic_da=1_000_000, hra_received=400_000, rent_paid=480_000, metro=True,
                   d80c=150_000, d80d_self=25_000, d80d_parents=25_000, d80ccd_1b=50_000, self_occ_interest=200_000,
                   filing_on_time=False)
        r = compare(i)
        self.assertEqual(r["recommended"], "new")
        self.assertTrue(any("10-IEA" in n for n in r["notes"]))

    def test_breakeven_deduction_found_when_new_wins(self):
        r = compare(Inputs(salary=2_500_000))
        self.assertEqual(r["recommended"], "new")
        self.assertGreater(r["extra_old_deductions_needed_for_old_to_win"], 0)
        # adding exactly that much extra deduction should make old no worse than new
        j = Inputs(salary=2_500_000, extra_old_deductions=r["extra_old_deductions_needed_for_old_to_win"])
        self.assertLessEqual(compute(j, "old")["total_tax"], compute(j, "new")["total_tax"] + 50)

    def test_ltcg_112a_with_rebate_new(self):
        # salary 10L -> taxable normal 9.25L, total income 11.25L <= 12L so normal tax is rebated; only 112A tax remains
        r = compute(Inputs(salary=1_000_000, ltcg_112a=200_000), "new")
        self.assertEqual(r["total_tax"], round((200_000 - 125_000) * 0.125 * 1.04))

    def test_hp_loss_not_set_off_in_new_regime(self):
        i = Inputs(salary=1_500_000, rent_received=300_000, let_out_interest=500_000)
        self.assertGreaterEqual(compute(i, "new")["house_property_income"], 0)
        self.assertEqual(compute(i, "old")["house_property_income"], -200_000)

    def test_surcharge_applies_above_50_lakh(self):
        a, b = compute(Inputs(salary=5_500_000), "new"), compute(Inputs(salary=5_500_000), "old")
        self.assertGreater(a["surcharge"], 0)
        self.assertGreater(b["surcharge"], 0)

    def test_senior_old_slab_and_80ttb(self):
        r = compute(Inputs(age=65, salary=300_000, interest_other=400_000), "old")
        self.assertGreater(r["deductions"], 0)    # 80TTB up to 50k
        self.assertLess(r["total_tax"], compute(Inputs(age=30, salary=300_000, interest_other=400_000), "old")["total_tax"])


if __name__ == "__main__":
    unittest.main()
