"""Dense search over the FAISS index. Building, versioning and loading live in rag/index_store.py."""
import numpy as np

from rag.embedder import get_embedding_model


def faiss_search(query, index, docs, k=5):
    model = get_embedding_model()

    query_vec = model.encode(
        [query],
        normalize_embeddings=True
    )

    scores, indices = index.search(
        np.array(query_vec).astype("float32"),
        k
    )

    results = []

    for idx, score in zip(indices[0], scores[0]):
        if idx < 0 or idx >= len(docs):
            continue

        results.append({
            "doc": docs[idx],
            "faiss_score": float(score)
        })

    return results
