from pathlib import Path


EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
INDEX_SCHEMA_VERSION = 8  # bumped: law corpus is chunked by section and every chunk carries act_version/text_status

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"

DOCUMENT_SOURCES = [
    {
        "path": DOCS_ROOT / "eligibility",
        "source": "eligibility",
        "label": "itr eligibility reference",
    },
    {
        "path": DOCS_ROOT / "laws",
        "source": "law",
        "label": "tax law",
    },
    {
        "path": DOCS_ROOT / "Guidelines",
        "source": "guideline",
        "label": "itr filing guideline",
    },
]

VECTOR_DB_PATH = PROJECT_ROOT / "vectorstore" / "faiss_index"
VECTOR_DB_MANIFEST_PATH = PROJECT_ROOT / "vectorstore" / "faiss_index_manifest.json"
