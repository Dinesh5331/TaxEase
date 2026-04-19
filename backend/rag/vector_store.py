import faiss
import json
import numpy as np
import pickle
import os

from rag.embedder import get_embedding_model
from rag.config import VECTOR_DB_MANIFEST_PATH, VECTOR_DB_PATH


def create_vectorstore(docs, manifest=None):
    model = get_embedding_model()

    texts = [doc.page_content for doc in docs]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )

    dim = len(embeddings[0])

    index = faiss.IndexFlatIP(dim)

    index.add(np.array(embeddings).astype("float32"))

    os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)

    faiss.write_index(index, str(VECTOR_DB_PATH) + ".index")

    with open(str(VECTOR_DB_PATH) + ".pkl", "wb") as f:
        pickle.dump(docs, f)

    if manifest is not None:
        with open(VECTOR_DB_MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)


def load_vectorstore():
    index = faiss.read_index(str(VECTOR_DB_PATH) + ".index")

    with open(str(VECTOR_DB_PATH) + ".pkl", "rb") as f:
        docs = pickle.load(f)

    return index, docs


def vectorstore_exists():
    return (
        os.path.exists(str(VECTOR_DB_PATH) + ".index")
        and os.path.exists(str(VECTOR_DB_PATH) + ".pkl")
    )


def load_vectorstore_manifest():
    if not os.path.exists(VECTOR_DB_MANIFEST_PATH):
        return None

    with open(VECTOR_DB_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)




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
