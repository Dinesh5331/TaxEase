_reranker = None
MAX_PAIRS = 80


def get_reranker():
    global _reranker

    if _reranker is None:
        from sentence_transformers import CrossEncoder
        print("Loading reranker (only once)...")
        _reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512
        )

    return _reranker


def rerank(query, docs, top_k=5):
    reranker = get_reranker()
    docs = docs[:MAX_PAIRS]

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
