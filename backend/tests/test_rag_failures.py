"""What happens when parts of the RAG pipeline fail. No model, network or real corpus: retrievers, reranker and LLM
are replaced; the index tests use tiny hand-made vectors."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import numpy as np
    import rank_bm25  # noqa: F401
    from rag import hybrid_retriever, index_store, judge, rag_pipeline
    from rag.llm import Completion, EmptyAnswer
    HAVE_RAG = True
except ImportError:
    HAVE_RAG = False


def doc(text, **meta):
    base = {"source": "law", "file": "f.pdf", "document_name": "f", "page": 1, "act_version": "1961",
            "text_status": "form-instructions", "form_name": "unknown", "rel_path": "docs/f.pdf"}
    return SimpleNamespace(page_content=text, metadata={**base, **meta})


def corpus():
    return [doc("house property rent deduction rules"), doc("capital gains on listed shares"),
            doc("senior citizen interest deduction"),
            doc("rebate for individuals under the new act", act_version="2025", section="156",
                text_status="act")]


def scores(value):
    def fake(query, items, top_k=5):
        return [{**i, "rerank_score": value} for i in items][:top_k]
    return fake


def boom(*a, **k):
    raise RuntimeError("down")


def llm_ok(client, prompt):
    return Completion("an answer", "m", "stop", 10, 2)


@unittest.skipUnless(HAVE_RAG, "retrieval dependencies not installed")
class PipelineFailures(unittest.TestCase):
    def setUp(self):
        self.docs = corpus()
        rag_pipeline._retriever_cache.clear()

    def run_rag(self, query="capital gains on shares", rerank=None, llm=llm_ok, dense=None, model=object()):
        def dense_ok(q, index, docs, k):
            return [{"doc": d, "faiss_score": 0.5} for d in docs]
        with mock.patch.object(hybrid_retriever, "faiss_search", dense or dense_ok), \
             mock.patch.object(rag_pipeline, "rerank", rerank or scores(2.0)), \
             mock.patch.object(rag_pipeline, "complete", llm):
            return rag_pipeline.run_rag_result(model, None, self.docs, query)

    def test_healthy(self):
        r = self.run_rag()
        self.assertEqual((r.status, r.answer, r.degraded), ("ok", "an answer", []))
        self.assertTrue(r.citations and r.trace_id)

    def test_dense_search_down_falls_back_to_keywords(self):
        r = self.run_rag(dense=boom)
        self.assertEqual((r.status, r.degraded), ("ok", ["dense"]))

    def test_keyword_search_down_falls_back_to_dense(self):
        with mock.patch.object(hybrid_retriever.HybridRetriever, "_bm25_ranking", boom):
            r = self.run_rag()
        self.assertEqual((r.status, r.degraded), ("ok", ["bm25"]))

    def test_both_retrievers_down_never_calls_the_llm(self):
        llm = mock.Mock()
        with mock.patch.object(hybrid_retriever.HybridRetriever, "_bm25_ranking", boom):
            r = self.run_rag(dense=boom, llm=llm)
        self.assertEqual(r.status, "retrieval_failed")
        llm.assert_not_called()

    def test_irrelevant_results_abstain_without_calling_the_llm(self):
        llm = mock.Mock()
        r = self.run_rag("best pizza in town", rerank=scores(-11.0), llm=llm)
        self.assertEqual((r.status, r.citations), ("no_relevant_context", []))
        llm.assert_not_called()

    def test_reranker_down_still_answers(self):
        r = self.run_rag(rerank=boom)
        self.assertEqual((r.status, r.degraded), ("ok", ["rerank"]))

    def test_llm_failures_return_the_sources(self):
        def empty(client, prompt):
            raise EmptyAnswer("empty")
        for llm, model in ((boom, object()), (empty, object()), (llm_ok, None)):
            r = self.run_rag(llm=llm, model=model)
            self.assertEqual(r.status, "llm_unavailable")
            self.assertTrue(r.citations)
            self.assertIn("most relevant passages", r.answer)

    def test_form_names_are_not_invented_from_ordinary_words(self):
        self.assertEqual(rag_pipeline._extract_requested_forms("I missed the ITR due date, what do I do"), [])
        self.assertEqual(rag_pipeline._extract_requested_forms("ITR\u20111 or itr 2 or ITR-U?"), ["ITR-1", "ITR-2", "ITR-U"])

    def test_answer_is_plain_text_and_a_refusal_is_labelled(self):
        r = self.run_rag(llm=lambda c, p: Completion("**ITR\u20112** up to Rs\u202f50 lakh", "m"))
        self.assertEqual(r.answer, "ITR-2 up to Rs 50 lakh")
        r = self.run_rag(llm=lambda c, p: Completion("Not found in documents.", "m"))
        self.assertEqual(r.status, "not_in_documents")

    def test_search_query_drives_retrieval_and_the_full_query_reaches_the_llm(self):
        seen = {}

        def rerank(query, items, top_k=5):
            seen["rerank"] = query
            return scores(2.0)(query, items, top_k)

        def llm(client, prompt):
            seen["prompt"] = prompt
            return llm_ok(client, prompt)
        with mock.patch.object(hybrid_retriever, "faiss_search", lambda *a: []), \
             mock.patch.object(rag_pipeline, "rerank", rerank), mock.patch.object(rag_pipeline, "complete", llm):
            rag_pipeline.run_rag_result(object(), None, self.docs, "salary data 12345. which form?",
                                        search_query="capital gains on shares")
        self.assertEqual(seen["rerank"], "capital gains on shares")
        self.assertIn("salary data 12345", seen["prompt"])

    def test_bad_queries_and_empty_corpus(self):
        for q in ("", "   ", "???", "x" * 2001):
            self.assertEqual(self.run_rag(q).status, "invalid_query")
        self.docs = []
        self.assertEqual(self.run_rag().status, "retrieval_failed")

    def test_identifiers_never_reach_the_llm(self):
        seen = []

        def spy(client, prompt):
            seen.append(prompt)
            return llm_ok(client, prompt)
        self.run_rag("my PAN is ABCDE1234F and aadhaar 1234 5678 9012, capital gains?", llm=spy)
        self.assertNotIn("ABCDE1234F", seen[0])
        self.assertNotIn("1234 5678 9012", seen[0])

    def test_2025_question_uses_only_2025_text(self):
        r = self.run_rag("What does section 156 of the Income-tax Act 2025 say?")
        self.assertEqual({c["act_version"] for c in r.citations}, {"2025"})

    def test_named_section_picks_the_act_and_the_sub_section(self):
        docs = [doc("(1) opening", section="139", text_status="act"), doc("(5) revised return", section="139", text_status="act"),
                doc("new act", section="139", text_status="act", act_version="2025")]
        hits = rag_pipeline._named_provisions("what is section 139(5)", docs, "1961")
        self.assertEqual([h["doc"].page_content for h in hits], ["(5) revised return", "(1) opening"])
        self.assertEqual(len(rag_pipeline._named_provisions("revised return u/s 139(5)", docs, None)), 2)
        hits = rag_pipeline._named_provisions("section 139 of the 2025 act", docs, "2025")
        self.assertEqual([h["doc"].page_content for h in hits], ["new act"])

    def test_named_section_survives_a_low_rerank_score(self):
        r = self.run_rag("Explain section 156 of the 2025 Act", rerank=scores(-11.0))
        self.assertEqual((r.status, r.citations[0]["section"]), ("ok", "156"))

    def test_judge_is_off_by_default_and_parses_scores(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(judge.maybe_judge(object(), "t", "q", "c", "a"))
        self.assertEqual(judge.parse_scores('x {"faithfulness": 0.5, "relevance": 3}'),
                         {"faithfulness": 0.5, "relevance": 1.0})
        self.assertIsNone(judge.parse_scores("no json"))


@unittest.skipUnless(HAVE_RAG, "retrieval dependencies not installed")
class VersionedIndex(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Path(self.tmp.name)
        self.embedded = []

    def embed(self, texts):
        self.embedded += texts
        out = []
        for t in texts:
            raw = np.frombuffer(hashlib.sha256(t.encode()).digest(), dtype=np.uint8)[:16].astype("float32") - 127
            out.append(raw / np.linalg.norm(raw))
        return np.array(out)

    def open(self, texts, manifest_hash, model="m1", make=None):
        return index_store.open_index(self.store, {"docs/f.pdf": manifest_hash}, 1, model,
                                      make or (lambda: [doc(t) for t in texts]), self.embed)

    def test_only_changed_chunks_are_embedded_and_unchanged_corpus_is_reused(self):
        self.open(["a", "b"], "h1")
        self.assertEqual(self.embedded, ["a", "b"])
        self.embedded.clear()
        self.open(["a", "b"], "h1", make=boom)                  # same corpus: no rebuild
        _, docs, meta = self.open(["a", "b", "c"], "h2")
        self.assertEqual(self.embedded, ["c"])
        self.assertEqual((len(docs), meta["embedded"]), (3, 1))
        self.assertTrue(docs[0].metadata["chunk_id"] and docs[0].metadata["content_hash"])

    def test_failed_rebuild_keeps_serving_the_old_version(self):
        _, _, first = self.open(["a"], "h1")
        for bad in (boom, lambda: []):
            _, docs, meta = self.open(None, "h2", make=bad)
            self.assertEqual((meta["version"], len(docs)), (first["version"], 1))
            self.assertIn("stale", meta)

    def test_a_file_that_stops_producing_chunks_is_rejected(self):
        self.open(["a"], "h1")
        _, _, meta = self.open(None, "h2", make=lambda: [doc("z", rel_path="docs/other.pdf")])
        self.assertIn("no chunks extracted", meta["stale"])

    def test_corrupt_current_version_is_rebuilt(self):
        _, _, first = self.open(["a"], "h1")
        (self.store / "versions" / first["version"] / "index.faiss").write_bytes(b"junk")
        _, docs, meta = self.open(["a"], "h1")
        self.assertNotEqual(meta["version"], first["version"])
        self.assertNotIn("stale", meta)

    def test_other_embedding_model_is_never_served(self):
        self.open(["a"], "h1")
        with self.assertRaises(index_store.IndexUnavailable):
            self.open(None, "h1", model="m2", make=boom)
        self.embedded.clear()
        self.open(["a"], "h1", model="m2")
        self.assertEqual(self.embedded, ["a"])                   # old vectors are not reused across models

    def test_outdated_corpus_files_are_not_loaded(self):
        from rag import loader
        from rag.sections import EXCLUDED
        (self.store / next(iter(EXCLUDED))).write_bytes(b"not even opened")
        self.assertEqual(loader.load_documents(self.store, "law"), [])

    def test_only_two_versions_are_kept(self):
        for h in ("h1", "h2", "h3", "h4"):
            self.open(["a", h], h)
        self.assertEqual(len(list((self.store / "versions").iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
