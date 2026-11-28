import re

from rank_bm25 import BM25Okapi

from rag.fusion import rrf_fuse


def faiss_search(query, index, docs, k):
    from rag.vector_store import faiss_search as search     # imported late: loads the embedding library
    return search(query, index, docs, k)


class HybridRetriever:
    def __init__(self, docs, index):
        self.docs = docs
        self.index = index
        self.doc_id_map = {id(doc): idx for idx, doc in enumerate(docs)}
        self.corpus = [self._tokenize(doc.page_content) for doc in docs]
        self.bm25 = BM25Okapi(self.corpus)

    @staticmethod
    def _tokenize(text):
        return re.findall(r"\b\w+\b", text.lower())

    def _expand_query_tokens(self, query_tokens):
        expanded = list(query_tokens)
        token_set = set(query_tokens)

        if "eligibility" in token_set or "eligibilty" in token_set or "eligible" in token_set:
            expanded.extend(["applicable", "qualify", "qualified"])

        if "rules" in token_set or "conditions" in token_set:
            expanded.extend(["criteria", "applicable", "requirements"])

        if "return" in token_set and any(token.startswith("itr") for token in token_set):
            expanded.extend(["file", "filing", "form"])

        return expanded

    def _bm25_ranking(self, query_tokens, allowed, size):
        scores = self.bm25.get_scores(query_tokens)
        top = sorted((i for i in allowed if scores[i] > 0), key=lambda i: scores[i], reverse=True)[:size]
        return {i: float(scores[i]) for i in top}

    def _dense_ranking(self, query, allowed, size):
        # IndexFlatIP scores every vector anyway, so ask for all and filter before cutting to size.
        results = faiss_search(query, self.index, self.docs, len(self.docs))
        out = {}
        for r in results:
            idx = self.doc_id_map[id(r["doc"])]
            if idx in allowed:
                out[idx] = r["faiss_score"]
                if len(out) == size:
                    break
        return out

    def search(self, query, k=8, predicate=None, on_error=None):
        """-> (items, failed). `failed` names the retrievers that raised; the other one still answers.
        `predicate(metadata)` restricts the search before ranking, so a filter cannot empty the result."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [], []
        query_tokens = self._expand_query_tokens(query_tokens)
        allowed = {i for i, d in enumerate(self.docs) if predicate is None or predicate(d.metadata)}
        size = max(k * 2, 10)

        failed, rankings = [], {}
        for name, run in (("bm25", lambda: self._bm25_ranking(query_tokens, allowed, size)),
                          ("dense", lambda: self._dense_ranking(query, allowed, size))):
            try:
                rankings[name] = run()
            except Exception as e:
                failed.append(name)
                rankings[name] = {}
                if on_error:
                    on_error(name, e)

        # Reciprocal rank fusion: ranks, not raw scores, so BM25 and cosine need no common scale.
        fused = rrf_fuse([list(rankings["bm25"]), list(rankings["dense"])])
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return [{"doc": self.docs[i], "bm25_score": rankings["bm25"].get(i, 0.0),
                 "faiss_score": rankings["dense"].get(i, 0.0), "hybrid_score": fused[i]} for i in best], failed
