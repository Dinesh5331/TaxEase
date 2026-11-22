import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval import run_eval  # noqa: E402


class EvalSet(unittest.TestCase):
    def test_engine_gate_is_100_percent(self):
        rep = run_eval.engine_report()
        self.assertEqual(rep["engine_accuracy"], 1.0, [r for r in rep["rows"] if not r["ok"]])
        self.assertEqual(run_eval.gate(rep), [])

    def test_gate_catches_regressions(self):
        self.assertTrue(run_eval.gate({"engine_accuracy": 0.95}))
        self.assertTrue(run_eval.gate({"must_not_violations": 1}))
        self.assertEqual(run_eval.gate({"must_include_rate": 0.9, "citation_rate": 1.0, "must_not_violations": 0}), [])

    def test_golden_qa_is_well_formed(self):
        qs = run_eval.load_questions()
        self.assertGreaterEqual(len(qs), 20)
        self.assertEqual(len({q["id"] for q in qs}), len(qs))
        for q in qs:
            self.assertTrue({"id", "q", "type", "reference", "must_include", "must_not_include", "tag"} <= set(q), q["id"])
            self.assertTrue(all(m == m.lower() for m in q["must_include"] + q["must_not_include"]), q["id"])
            self.assertIn(q["type"], {"itr_selection", "compliance", "tax_regime", "law", "out_of_scope"})
        # statements that must agree with the rules file
        by = {q["id"]: q for q in qs}
        self.assertIn("1.25", by["q01"]["reference"])
        self.assertIn("two", by["q02"]["reference"].lower())
        self.assertIn("50 lakh", by["q07"]["reference"])
        self.assertNotIn("150", by["q07"]["reference"])
        self.assertIn("business trust", by["q19"]["must_not_include"])


if __name__ == "__main__":
    unittest.main()
