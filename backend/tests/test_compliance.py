"""Late/missed-return calculators. ITR-U band dates reproduce the table published for AY 2022-23..2025-26."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rules import compliance as c  # noqa: E402


class Compliance(unittest.TestCase):
    def test_ay_dates(self):
        d = c.ay_dates("2026-27")
        self.assertEqual(d["due_itr1_2"], date(2026, 7, 31))
        self.assertEqual(d["belated"], date(2026, 12, 31))
        self.assertEqual(d["revised"], date(2027, 3, 31))
        self.assertEqual(d["itr_u_last"], date(2031, 3, 31))            # published: 31 Mar 2031

    def test_itr_u_last_dates_for_older_years(self):                    # published: AY22-23 -> 31 Mar 2027, AY25-26 -> 31 Mar 2030
        self.assertEqual(c.ay_dates("2022-23")["itr_u_last"], date(2027, 3, 31))
        self.assertEqual(c.ay_dates("2025-26")["itr_u_last"], date(2030, 3, 31))

    def test_itr_u_rate_bands(self):
        ay = "2026-27"
        self.assertEqual(c.itr_u_additional_rate(ay, date(2027, 2, 1)), 0.25)
        self.assertEqual(c.itr_u_additional_rate(ay, date(2028, 3, 31)), 0.25)
        self.assertEqual(c.itr_u_additional_rate(ay, date(2028, 4, 1)), 0.50)
        self.assertEqual(c.itr_u_additional_rate(ay, date(2029, 4, 1)), 0.60)
        self.assertEqual(c.itr_u_additional_rate(ay, date(2031, 3, 31)), 0.70)
        self.assertIsNone(c.itr_u_additional_rate(ay, date(2031, 4, 1)))
        # as of Oct 2026, AY 2022-23 is in the 70% band, AY 2025-26 in the 25% band (published table)
        self.assertEqual(c.itr_u_additional_rate("2022-23", date(2026, 10, 12)), 0.70)
        self.assertEqual(c.itr_u_additional_rate("2025-26", date(2026, 10, 12)), 0.25)
        self.assertEqual(c.itr_u_additional_rate("2023-24", date(2026, 10, 12)), 0.60)
        self.assertEqual(c.itr_u_additional_rate("2024-25", date(2026, 10, 12)), 0.50)

    def test_late_fee_234f(self):
        due = date(2026, 7, 31)
        self.assertEqual(c.late_fee_234f(900_000, date(2026, 7, 31), due), 0)
        self.assertEqual(c.late_fee_234f(900_000, date(2026, 8, 1), due), 5_000)
        self.assertEqual(c.late_fee_234f(500_000, date(2026, 12, 31), due), 1_000)

    def test_interest_234a(self):
        due = date(2026, 7, 31)
        self.assertEqual(c.interest_234a(100_000, due, date(2026, 7, 31)), 0)
        self.assertEqual(c.interest_234a(100_000, due, date(2026, 8, 1)), 1_000)      # 1 month or part
        self.assertEqual(c.interest_234a(100_000, due, date(2026, 8, 31)), 1_000)
        self.assertEqual(c.interest_234a(100_000, due, date(2026, 9, 1)), 2_000)
        self.assertEqual(c.interest_234a(100_000, due, date(2026, 12, 31)), 5_000)

    def test_penalty_270a(self):
        self.assertEqual(c.penalty_270a(30_000), 15_000)                              # published example
        self.assertEqual(c.penalty_270a(120_000), 60_000)
        self.assertEqual(c.penalty_270a(120_000, misreporting=True), 240_000)         # published: 2,40,000

    def test_itr_u_additional_tax(self):
        self.assertEqual(c.itr_u_additional_tax(100_000, "2026-27", date(2027, 6, 1)), 25_000)
        self.assertEqual(c.itr_u_additional_tax(100_000, "2026-27", date(2029, 6, 1)), 60_000)

    def test_route_not_filed_today(self):                                             # today in this project: 18 Nov 2026
        r = c.route("2026-27", date(2026, 11, 18), filed=False)
        self.assertEqual([o["route"] for o in r["options"]], ["File belated return"])
        self.assertEqual(r["options"][0]["deadline"], "2026-12-31")

    def test_route_not_filed_after_belated(self):
        r = c.route("2026-27", date(2027, 1, 15), filed=False)
        self.assertEqual(r["options"][0]["section"], "139(8A) + 140B")

    def test_route_wrong_form(self):
        r = c.route("2026-27", date(2026, 11, 18), filed=True, form_filed="ITR-1", correct_form="ITR-2")
        self.assertEqual(r["options"][0]["section"], "139(5)")
        self.assertTrue(any("139(9)" in w for w in r["warnings"]))

    def test_route_omitted_income_after_revised_deadline(self):
        r = c.route("2026-27", date(2027, 6, 1), filed=True, omitted_income=True)
        self.assertEqual([o["section"] for o in r["options"]], ["139(8A) + 140B"])


if __name__ == "__main__":
    unittest.main()
