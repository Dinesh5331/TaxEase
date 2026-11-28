"""Load (or rebuild) the search index. `python -m rag.main "question"` runs one query from the command line."""
import sys

from rag.config import DOCUMENT_SOURCES, EMBEDDING_MODEL, INDEX_SCHEMA_VERSION, PROJECT_ROOT, VECTOR_STORE_DIR
from rag.index_store import corpus_manifest, open_index


def _make_docs():
    from rag.loader import load_all_documents, split_documents
    docs = split_documents(load_all_documents(DOCUMENT_SOURCES))
    for d in docs:
        d.metadata["rel_path"] = _relative(d.metadata.get("path", ""))
    return docs


def _relative(path):
    from pathlib import Path
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path


def _embed(texts):
    from rag.embedder import get_embedding_model
    return get_embedding_model().encode(texts, normalize_embeddings=True)


def setup():
    """-> (index, docs, index_meta)."""
    return open_index(VECTOR_STORE_DIR, corpus_manifest(DOCUMENT_SOURCES, PROJECT_ROOT), INDEX_SCHEMA_VERSION,
                      EMBEDDING_MODEL, _make_docs, _embed)


def main():
    from rag.llm import get_model
    from rag.rag_pipeline import run_rag_result

    index, docs, meta = setup()
    print(f"index {meta['version']}: {meta['chunks']} chunks")
    query = " ".join(sys.argv[1:]) or "Which ITR form should a taxpayer file, and what conditions decide that?"
    result = run_rag_result(get_model(), index, docs, query, index_meta=meta)
    print(f"\n[{result.status}]\n{result.answer}")


if __name__ == "__main__":
    main()
