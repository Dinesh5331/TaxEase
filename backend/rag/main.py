from rag.config import DOCUMENT_SOURCES, INDEX_SCHEMA_VERSION
from rag.loader import load_all_documents, split_documents
from rag.vector_store import (
    create_vectorstore,
    load_vectorstore,
    load_vectorstore_manifest,
    vectorstore_exists,
)
from rag.rag_pipeline import run_rag
from rag.llm import get_model
from rag.embedder import get_embedding_model
from rag.reranker import get_reranker


def _build_manifest():
    files = [
        {
            "schema_version": INDEX_SCHEMA_VERSION,
        }
    ]

    for source in DOCUMENT_SOURCES:
        base_path = source["path"]
        if not base_path.exists():
            continue

        # Track both PDF and TXT files so changes to either trigger a rebuild
        for file_path in sorted(
            list(base_path.rglob("*.pdf")) + list(base_path.rglob("*.txt"))
        ):
            stat = file_path.stat()
            files.append(
                {
                    "path": str(file_path),
                    "source": source["source"],
                    "size": stat.st_size,
                    "modified_ns": stat.st_mtime_ns,
                }
            )

    return files


def _vectorstore_is_current():
    if not vectorstore_exists():
        return False

    return load_vectorstore_manifest() == _build_manifest()


def setup():
    if _vectorstore_is_current():
        return load_vectorstore()

    print("\n📥 Loading and processing PDFs...")
    all_docs = load_all_documents(DOCUMENT_SOURCES)

    # --- Diagnostic: warn on unknown form_name ---
    unknown_chunks = [d for d in all_docs if d.metadata.get("form_name") == "unknown"]
    if unknown_chunks:
        unknown_files = sorted(set(d.metadata["file"] for d in unknown_chunks))
        print(f"\n⚠️  WARNING: {len(unknown_chunks)} chunks have form_name=unknown from:")
        for f in unknown_files:
            print(f"     - {f}")

    # --- Diagnostic: form coverage ---
    from collections import Counter
    form_counts = Counter(d.metadata.get("form_name", "unknown") for d in all_docs)
    print("\n📊 Form coverage (pages before splitting):")
    for form, count in sorted(form_counts.items()):
        print(f"   {form:15s}: {count} pages")

    split_docs = split_documents(all_docs)
    print(f"\n🔧 Splitting complete: {len(split_docs)} chunks from {len(all_docs)} pages")

    create_vectorstore(split_docs, manifest=_build_manifest())
    print("✅ Vector store saved.")

    return load_vectorstore()


def main():
    # Pre-warm models at startup (each loads only once via module-level singletons)
    print("\n🔧 Loading models...")
    get_embedding_model()   # BertModel — used for FAISS search
    get_reranker()          # CrossEncoder — used for reranking
    print("✅ Models ready.\n")

    index, docs = setup()
    model = get_model()

    query = "Which ITR form should a taxpayer file, and what conditions decide that?"

    result = run_rag(model, index, docs, query)

    print("\n===== RESULT =====\n")
    print(result)


if __name__ == "__main__":
    main()
