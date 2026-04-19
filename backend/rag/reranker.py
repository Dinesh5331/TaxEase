from sentence_transformers import CrossEncoder

_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        print("Loading reranker (only once)...")
        _reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=256
        )

    return _reranker


def rerank(query, docs, top_k=5):
    reranker = get_reranker()
    docs = docs[:20]

    if not docs:
        return []

    pairs = [[query, item["doc"].page_content] for item in docs]
    scores = reranker.predict(pairs)

    ranked = []
    for item, score in zip(docs, scores):
        enriched = dict(item)
        enriched["rerank_score"] = float(score)
        ranked.append(enriched)

    ranked.sort(key=lambda item: item["rerank_score"], reverse=True)
    return ranked[:top_k]
