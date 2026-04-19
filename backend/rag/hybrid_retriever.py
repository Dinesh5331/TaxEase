import re

from rank_bm25 import BM25Okapi

from rag.vector_store import faiss_search


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

    @staticmethod
    def _normalize_scores(score_map):
        if not score_map:
            return {}

        values = list(score_map.values())
        min_score = min(values)
        max_score = max(values)

        if max_score == min_score:
            return {key: 1.0 for key in score_map}

        return {
            key: (score - min_score) / (max_score - min_score)
            for key, score in score_map.items()
        }

    def search(self, query, k=8):
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        query_tokens = self._expand_query_tokens(query_tokens)

        candidate_pool_size = max(k * 2, 10)

        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_top_idx = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:candidate_pool_size]

        bm25_score_map = {
            idx: float(bm25_scores[idx])
            for idx in bm25_top_idx
        }

        faiss_results = faiss_search(
            query,
            self.index,
            self.docs,
            candidate_pool_size
        )
        faiss_score_map = {
            self.doc_id_map[id(result["doc"])]: result["faiss_score"]
            for result in faiss_results
        }

        normalized_bm25 = self._normalize_scores(bm25_score_map)
        normalized_faiss = self._normalize_scores(faiss_score_map)

        candidate_indices = set(bm25_score_map) | set(faiss_score_map)
        combined = []

        for idx in candidate_indices:
            combined.append({
                "doc": self.docs[idx],
                "bm25_score": bm25_score_map.get(idx, 0.0),
                "faiss_score": faiss_score_map.get(idx, 0.0),
                "hybrid_score": (
                    0.45 * normalized_bm25.get(idx, 0.0) +
                    0.55 * normalized_faiss.get(idx, 0.0)
                )
            })

        combined.sort(key=lambda item: item["hybrid_score"], reverse=True)
        return combined[:k]
