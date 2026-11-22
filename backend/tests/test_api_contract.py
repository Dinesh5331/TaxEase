"""HTTP contract for the ITR routes. Skipped when FastAPI is not installed (it was not in the build sandbox);
run it locally after `pip install -r requirements.txt`."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECRET_KEY", "test-only-secret")

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.routers import itr
    HAVE_API = True
except Exception:            # missing fastapi/httpx/jose/bcrypt: skip rather than fail
    HAVE_API = False

ROOT = Path(__file__).resolve().parents[1] / "demo_data"


@unittest.skipUnless(HAVE_API, "fastapi / httpx not installed")
class ItrRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(itr.router, prefix="/api")
        cls.c = TestClient(app)

    def test_questionnaire(self):
        r = self.c.get("/api/itr/questionnaire")
        self.assertEqual(r.status_code, 200)
        self.assertIn("director", {q["id"] for q in r.json()["questions"]})

    def test_select(self):
        r = self.c.post("/api/itr/select", json={"total_income": 900000, "residential_status": "ROR", "director": False,
                        "unlisted_equity": False, "foreign_asset_or_income": False, "loss_carry_forward": False,
                        "esop_deferral": False, "tds_194N": False, "partner_in_firm": False, "hp_count": 1})
        self.assertEqual(r.json()["form"], "ITR-1")

    def test_analyze_upload(self):
        d = ROOT / "p04_ltcg_112a_over_limit"
        files = {"ais": ("ais.json", (d / "ais.json").read_bytes(), "application/json"),
                 "form16": ("form16.pdf", (d / "form16.pdf").read_bytes(), "application/pdf")}
        ans = {"residential_status": "ROR", "director": False, "unlisted_equity": False, "foreign_asset_or_income": False,
               "loss_carry_forward": False, "esop_deferral": False, "tds_194N": False, "partner_in_firm": False,
               "hp_count": 0, "ltcg_112a": 180000, "stcg_111a": 0, "ltcg_other": 0}
        r = self.c.post("/api/itr/analyze", files=files, data={"answers": json.dumps(ans)})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["recommendation"]["form"], "ITR-2")

    def test_bad_answers_and_non_json_ais(self):
        d = ROOT / "p01_salaried_simple"
        r = self.c.post("/api/itr/analyze", files={"ais": ("a.json", b"not json")}, data={"answers": "{}"})
        self.assertEqual(r.status_code, 422)
        r = self.c.post("/api/itr/analyze", files={"ais": ("a.json", (d / "ais.json").read_bytes())}, data={"answers": "[1]"})
        self.assertEqual(r.status_code, 422)

    def test_regime(self):
        r = self.c.post("/api/regime/compare", json={"salary": 1500000, "basic_da": 600000})
        self.assertEqual(r.status_code, 200)
        self.assertIn(r.json()["recommended"], ("new", "old"))

    def test_compliance(self):
        r = self.c.post("/api/compliance/route", json={"filed": False, "today": "2026-11-18"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["options"][0]["section"], "139(4)")
        r = self.c.post("/api/compliance/route", json={"filed": False, "due_kind": "nope"})
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main()
