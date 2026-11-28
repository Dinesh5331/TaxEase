"""Evaluation harness. Three independent checks, cheapest first:

  python -m eval.run_eval engine            # rules engine vs golden_itr.json (no models, runs anywhere)
  python -m eval.run_eval answers  [--n 21] # runs /chat pipeline on golden_qa.json, checks must_include / must_not_include,
                                            # citation presence and Act routing (needs the index + GROQ_API_KEY)
  python -m eval.run_eval ragas             # RAGAS faithfulness / answer relevancy / context precision+recall
                                            # (needs `pip install ragas datasets` and an LLM key; results are written to eval/out/)

Thresholds (the CI gate) live in THRESHOLDS. `engine` is the one that must be 100%.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).with_name("out")

THRESHOLDS = {"engine_accuracy": 1.0, "must_include_rate": 0.85, "must_not_violations": 0, "citation_rate": 0.9,
              "ragas_faithfulness": 0.80, "ragas_context_precision": 0.60}


def engine_report() -> dict:
    from rules.engine import select_itr
    from tests.test_engine import facts_from_golden
    golden = json.loads((ROOT / "demo_data" / "golden_itr.json").read_text(encoding="utf-8"))
    rows, ok = [], 0
    for g in golden:
        r = select_itr(facts_from_golden(g))
        good = r.form == g["expected_itr"]
        ok += good
        rows.append({"id": g["id"], "expected": g["expected_itr"], "got": r.form, "ok": good, "failed_rules": r.failed_rules})
    return {"engine_accuracy": ok / len(golden), "n": len(golden), "rows": rows}


def load_questions(n=None):
    qs = json.loads((Path(__file__).with_name("golden_qa.json")).read_text(encoding="utf-8"))["questions"]
    return qs[:n] if n else qs


def answers_report(n=None) -> dict:
    from api.routers.chat import load_rag
    from api.state import app_state
    from rag.rag_pipeline import run_rag_result
    load_rag()
    rows, inc, inc_total, viol, cited, cited_total = [], 0, 0, 0, 0, 0
    for q in load_questions(n):
        result = run_rag_result(app_state["model"], app_state["index"], app_state["docs"], q["q"],
                                index_meta=app_state.get("index_meta"))
        answer, cites = result.answer, result.citations
        low = answer.lower()
        miss = [m for m in q["must_include"] if m not in low]
        bad = [m for m in q["must_not_include"] if m in low]
        inc_total += len(q["must_include"])
        inc += len(q["must_include"]) - len(miss)
        viol += len(bad)
        if q["type"] != "out_of_scope":
            cited_total += 1
            cited += bool(cites)
            if q["act"] and cites and not any(c["act_version"] in (q["act"], "unknown") or c["text_status"] in ("project-reference", "form-instructions") for c in cites):
                bad.append(f"no citation from Act {q['act']}")
                viol += 1
        rows.append({"id": q["id"], "status": result.status, "missing": miss, "violations": bad,
                     "citations": len(cites), "answer": answer[:400]})
    return {"must_include_rate": inc / max(inc_total, 1), "must_not_violations": viol,
            "citation_rate": cited / max(cited_total, 1), "rows": rows}


def ragas_report() -> dict:
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
    except ImportError as e:
        raise SystemExit(f"RAGAS not installed ({e}). pip install ragas datasets, and set the LLM key RAGAS should use.")
    from api.routers.chat import load_rag
    from api.state import app_state
    from rag.rag_pipeline import run_rag_cited
    load_rag()
    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
    for q in load_questions():
        if q["type"] == "out_of_scope":
            continue
        answer, cites = run_rag_cited(app_state["model"], app_state["index"], app_state["docs"], q["q"])
        rows["question"].append(q["q"])
        rows["answer"].append(answer)
        rows["contexts"].append([c["snippet"] for c in cites] or [""])
        rows["ground_truth"].append(q["reference"])
    res = evaluate(Dataset.from_dict(rows), metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
    return {"ragas_" + k: float(v) for k, v in res.items()}


def gate(report: dict) -> list:
    fails = []
    for k, floor in THRESHOLDS.items():
        if k not in report:
            continue
        v = report[k]
        if (k == "must_not_violations" and v > floor) or (k != "must_not_violations" and v < floor):
            fails.append(f"{k}={v} (threshold {floor})")
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["engine", "answers", "ragas"])
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args(argv)
    rep = {"engine": engine_report, "answers": lambda: answers_report(a.n), "ragas": ragas_report}[a.mode]()
    OUT.mkdir(exist_ok=True)
    (OUT / f"{a.mode}.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    fails = gate(rep)
    print({k: v for k, v in rep.items() if k != "rows"})
    if fails:
        print("GATE FAILED:", "; ".join(fails))
        return 1
    print("gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
