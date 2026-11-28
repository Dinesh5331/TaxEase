"""Retrieval pieces that need no model, index or network."""
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.citations import build_citations  # noqa: E402
from rag.fusion import rrf_fuse  # noqa: E402
from rag.sections import (chunk_section, choose_act, filter_by_act, legal_meta, section_chunks,  # noqa: E402
                          split_sections, swap_inverted_pages, Section)

LAWS = Path(__file__).resolve().parents[1] / "docs" / "laws"


class Fusion(unittest.TestCase):
    def test_top_in_both_scores_one(self):
        s = rrf_fuse([["a", "b", "c"], ["a", "c", "b"]])
        self.assertAlmostEqual(s["a"], 1.0)
        self.assertGreater(s["a"], s["b"])
        self.assertGreater(s["c"], s["b"] - 1)  # sanity: all positive and < 1
        self.assertTrue(all(0 < v <= 1 for v in s.values()))

    def test_agreement_beats_single_list_win(self):
        s = rrf_fuse([["x", "y", "z"], ["y", "q", "x"]])
        self.assertGreater(s["y"], s["z"])
        self.assertGreater(s["x"], s["q"])

    def test_outlier_score_does_not_matter(self):
        # ranks only: the same order gives the same fused score whatever the raw scores were
        self.assertEqual(rrf_fuse([["a", "b"]]), rrf_fuse([["a", "b"]]))

    def test_duplicates_do_not_vote_twice(self):
        self.assertEqual(rrf_fuse([["a", "a", "b"]])["a"], rrf_fuse([["a", "b"]])["a"])

    def test_weights(self):
        s = rrf_fuse([["a"], ["b"]], weights=[2.0, 1.0])
        self.assertGreater(s["a"], s["b"])
        with self.assertRaises(ValueError):
            rrf_fuse([["a"]], weights=[1, 2])

    def test_empty(self):
        self.assertEqual(rrf_fuse([[], []]), {})


SAMPLE = [
    (10, "CHAPTER III\n5\nsome preamble text\n138. (1) The Board may furnish information.\n(2) Nothing herein.\n"),
    (11, "10\n139. (1) Every person shall furnish a return of income.\n(a) the first case;\n(b) the second case;\n"
         "139A. Permanent account number.\n(1) Every person shall obtain PAN.\n"),
    (12, "1. Short title\n20\n140. (1) Where a return is defective.\n"),     # '1.' after 139A is noise, not a heading
]


class Sections(unittest.TestCase):
    def test_headings_found_in_order_noise_ignored(self):
        secs = split_sections(SAMPLE)
        self.assertEqual([s.number for s in secs], ["", "138", "139", "139A", "140"])
        self.assertEqual([s.first_page for s in secs][1:], [10, 11, 11, 12])
        self.assertNotIn("\n5\n", secs[0].text)                 # margin line numbers removed
        self.assertIn("1. Short title", secs[3].text)           # ...but kept as text of 139A, not a new section

    def test_chunks_never_cross_sections(self):
        out = section_chunks(SAMPLE, {"file": "x.pdf", "source": "law"})
        by_sec = {}
        for text, meta in out:
            by_sec.setdefault(meta["section"], []).append(text)
        self.assertIn("furnish a return", " ".join(by_sec["139"]))
        self.assertNotIn("Permanent account number", " ".join(by_sec["139"]))
        self.assertTrue(all(m["act_version"] == "unknown" for _, m in out))

    def test_long_section_split_with_limit(self):
        body = " ".join(f"({i}) " + "word " * 60 + "." for i in range(1, 30))
        chunks = chunk_section(Section("9", "9. x", body, 1), max_chars=1000, overlap=100)
        self.assertGreater(len(chunks), 3)
        self.assertTrue(all(len(c) <= 1500 for c in chunks))
        self.assertIn("(29)", chunks[-1])

    def test_legal_meta_is_explicit(self):
        self.assertEqual(legal_meta("Income-tax_Bill(2025)-amended(2026).pdf")["text_status"], "act")
        self.assertEqual(legal_meta("Income-tax_Bill(1962).pdf")["act_version"], "1961")
        rules = {"file": "r.pdf", "section": "114B", "page": 1, **legal_meta("Income-tax_Bill(1962).pdf")}
        cite = build_citations([{"doc": SimpleNamespace(metadata=rules, page_content="x")}])[0]
        self.assertEqual(cite["label"], "r.pdf, rule 114B, p.1")
        self.assertEqual(legal_meta("itr_2-guidelines.pdf")["text_status"], "form-instructions")

    @unittest.skipUnless((LAWS / "Income-tax_Bill(2025)-amended(2026).pdf").exists(), "corpus PDF not present")
    def test_real_bill_pages_yield_sections(self):
        txt = subprocess.run(["pdftotext", "-f", "56", "-l", "75", str(LAWS / "Income-tax_Bill(2025)-amended(2026).pdf"), "-"],
                             capture_output=True, text=True, errors="replace").stdout
        secs = split_sections([(56, txt)])
        nums = [s.number for s in secs if s.number]
        self.assertIn("30", nums)
        ints = [int("".join(c for c in n if c.isdigit())) for n in nums]
        self.assertEqual(ints, sorted(ints))                    # monotonic: no noise headings accepted


class FrontMatter(unittest.TestCase):
    BILL = [(1, "ARRANGEMENT OF CLAUSES\n1. Short title.\n2. Definitions.\n3. Return of income.\n"),
            (2, "BE it enacted by Parliament\n1. (1) This Act may be called X.\n2. In this Act,\n"),
            (3, "3. (1) Every person shall furnish a return.\nSCHEDULE I\ntable text\n")]

    def test_table_of_clauses_is_not_the_body(self):
        out = section_chunks(self.BILL, {"file": "x.pdf", "source": "law"})
        self.assertEqual([m["section"] for _, m in out], [None, "1", "2", "3", None])
        text, meta = next((t, m) for t, m in out if m["section"] == "3")
        self.assertEqual(meta["page"], 3)
        self.assertEqual(meta["section_heading"], "Return of income")
        self.assertTrue(text.startswith("[x.pdf, section 3: Return of income] "))
        self.assertNotIn("table text", text)

    def test_stray_number_does_not_block_later_headings(self):
        pages = [(1, "1. (1) A\n2. (1) B\n29. (1) stray table row\n3. (1) C\n4. (1) D\n")]
        self.assertEqual([s.number for s in split_sections(pages)], ["1", "2", "3", "4"])


class EnactedActLayout(unittest.TestCase):
    PAGES = [(1, "BE it enacted\nShort title.\n1.\t(1) This Act may be called X.\n"
                 "  1.\t Substituted for \u201cold\u201d by the Finance Act, 2026.\n  2.\t Inserted by the Finance Act, 2026.\n"),
             (2, "Rebate of income-tax in case of certain\nindividuals.\n2.\t(1) A resident individual.\n")]

    def test_footnotes_are_dropped_and_margin_titles_used(self):
        out = section_chunks(self.PAGES, {"file": "Income-tax_Bill(2025)-amended(2026).pdf", "source": "law"})
        self.assertEqual([m["section"] for _, m in out if m["section"]], ["1", "2"])
        self.assertNotIn("Substituted", " ".join(t for t, _ in out))
        self.assertEqual(out[-1][1]["section_heading"], "Rebate of income-tax in case of certain individuals")


class PortalActLayout(unittest.TestCase):
    FOOT = "Income Tax Department\nMinistry of Finance, Government of India\n"
    PAGES = [(1, "Return of income.\n139. (1) Every person shall furnish.\n" + FOOT),
             (2, "INCOME-TAX ACT, 1961\nBE it enacted\n137. (1) Disclosure of.\n"),
             (3, "Disclosure.\n138. (1) The Board may.\n4. Ins. by Act No. 7 of 2025, w.e.f. 1-4-2025.\nold repealed words\n" + FOOT),
             (4, "Permanent account number.\n139A. (1) Every person,\n")]

    def test_displaced_section_is_restored_and_footnotes_dropped(self):
        out = section_chunks(self.PAGES, {"file": "Income-tax_Bill(1961).pdf", "source": "law"})
        self.assertEqual([m["section"] for _, m in out if m["section"]], ["137", "138", "139", "139A"])
        everything = " ".join(t for t, _ in out)
        self.assertNotIn("old repealed words", everything)
        self.assertNotIn("Ministry of Finance", everything)
        self.assertEqual(next(m for _, m in out if m["section"] == "139")["page"], 1)


class InvertedPages(unittest.TestCase):
    def test_section_printed_early_is_swapped_back(self):
        pages = [(1, "148. (1) a\n"), (2, "150.(1) c\n"), (3, "Time limit.\n149. (1) b\n"), (4, "151. d\n151A. (1) e\n")]
        self.assertEqual([n for n, _ in swap_inverted_pages(pages)], [1, 3, 2, 4])


class HyphenatedSections(unittest.TestCase):
    def test_80_IA_is_its_own_section(self):
        secs = split_sections([(1, "80HHF. (1) a\n80-I. (1) b\n80-IA. (1) c\n80JJA. (1) d\n")])
        self.assertEqual([s.number for s in secs], ["80HHF", "80I", "80IA", "80JJA"])


class ActChoice(unittest.TestCase):
    def test_routing(self):
        self.assertEqual(choose_act("What does the Income-tax Act, 2025 say about tax year 2026-27?"), "2025")
        self.assertEqual(choose_act("Which ITR for AY 2026-27 if I sold shares?"), "1961")
        self.assertEqual(choose_act("What is in the 2025 Act about rebate?"), "2025")
        self.assertEqual(choose_act("Explain section 139(4) belated return"), "1961")
        self.assertIsNone(choose_act("what is a house property"))
        self.assertIsNone(choose_act("Compare section 139(4) with section 263 under the 2025 Act for AY 2026-27"))

    def test_filter_keeps_references_and_never_empties(self):
        def item(act, status="act"):
            return {"doc": SimpleNamespace(metadata={"act_version": act, "text_status": status})}
        items = [item("1961"), item("2025"), item("1961", "project-reference"), item("1961", "form-instructions")]
        got = filter_by_act(items, "1961")
        self.assertEqual(len(got), 3)
        self.assertEqual(len(filter_by_act(items, "2025")), 2)   # 1961 form instructions excluded
        self.assertTrue(filter_by_act([item("2025")], "1961"))
        self.assertEqual(filter_by_act(items, None), items)


class Citations(unittest.TestCase):
    def test_dedup_and_label(self):
        def it(sec, page, score):
            return {"doc": SimpleNamespace(page_content="text " * 100, metadata={
                "file": "Income-tax_Bill(2025).pdf", "document_name": "Income-tax_Bill(2025)", "section": sec, "page": page,
                "act_version": "2025", "text_status": "bill-as-introduced-superseded", "source": "law"}), "rerank_score": score}
        c = build_citations([it("263", 5, 1.23456), it("263", 5, 0.5), it(None, 6, 0.1)])
        self.assertEqual(len(c), 2)
        self.assertEqual(c[0]["label"], "Income-tax_Bill(2025), section 263, p.5")
        self.assertEqual(c[0]["score"], 1.235)
        self.assertLessEqual(len(c[0]["snippet"]), 220)
        self.assertEqual(c[1]["label"], "Income-tax_Bill(2025), p.6")


if __name__ == "__main__":
    unittest.main()
