# Project Directory Structure & Paths

## Root Directory
```
d:\TaxAssist\
```

---

## Project Structure with Paths

```
d:\TaxAssist\
├── README.md                          # Project documentation and setup guide
├── .gitignore                         # Git ignore rules for both frontend and backend
├── render.yaml                        # Render deployment configuration (both services)
├── Procfile                           # Process file for production deployment
├── vercel.json                        # Vercel configuration (for Next.js frontend)
│
├── backend\                           # FastAPI backend application
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Example environment variables for backend
│   ├── __pycache__\                   # Python cache (ignored by git)
│   │
│   ├── fastapi\                       # Main FastAPI application
│   │   ├── app.py                     # FastAPI app entry point
│   │   ├── database.py                # SQLAlchemy database configuration
│   │   ├── models.py                  # Database models (User)
│   │   ├── schemas.py                 # Pydantic request/response schemas
│   │   ├── auth_utils.py              # Authentication utilities
│   │   ├── state.py                   # Application state management
│   │   └── routers\                   # API route handlers
│   │       ├── __init__.py
│   │       ├── auth.py                # Authentication endpoints
│   │       ├── upload.py              # Form 16 upload endpoint
│   │       ├── chat.py                # Chat/RAG endpoint
│   │       └── health.py              # Health check endpoint
│   │
│   ├── ocr\                           # OCR extraction module
│   │   ├── ocr_loader.py              # OCR text extraction
│   │   ├── extractor.py               # Form 16 data extraction
│   │   └── parser.py                  # JSON parsing of extracted data
│   │
│   ├── rag\                           # RAG pipeline for ITR recommendations
│   │   ├── config.py                  # RAG configuration
│   │   ├── main.py                    # RAG pipeline entry point
│   │   ├── llm.py                     # LLM interface (Groq)
│   │   ├── loader.py                  # Document loader
│   │   ├── embedder.py                # Text embeddings
│   │   ├── vector_store.py            # FAISS vector store
│   │   ├── hybrid_retriever.py        # Hybrid search retriever
│   │   ├── query_classifier.py        # Query classification
│   │   ├── reranker.py                # Search result reranking
│   │   ├── rag_pipeline.py            # Main RAG pipeline
│   │   ├── data_ingestion.py          # Data ingestion
│   │   └── docs\                      # Reference documents for RAG
│   │       ├── laws\                  # Tax law documents
│   │       │   ├── Finance_Bill-2026.pdf
│   │       │   └── Income-tax_Bill(2025).pdf
│   │       └── returns\               # ITR form documents
│   │           ├── ITR-1.pdf
│   │           ├── ITR-2.pdf
│   │           ├── ITR-3.pdf
│   │           ├── ITR-4.pdf
│   │           ├── ITR-5.pdf
│   │           ├── ITR-6.pdf
│   │           ├── ITR-7.pdf
│   │           ├── ITR-B.pdf
│   │           ├── ITR-U.pdf
│   │           └── ITR-V.pdf
│   │
│   ├── docs\                          # Backend documentation
│   │   ├── eligibility\
│   │   ├── empty returns\
│   │   ├── forms\
│   │   ├── Guidelines\
│   │   └── laws\
│   │
│   ├── scripts\                       # Utility scripts
│   │   └── fill_form16_sample.py      # Sample Form 16 filling script
│   │
│   ├── vectorstore\                   # FAISS vector store (generated at runtime)
│   │   ├── faiss_index.index          # FAISS index file
│   │   └── faiss_index_manifest.json  # Index metadata
│   │
│   └── myenv\                         # Python virtual environment (ignored by git)
│       ├── Scripts\                   # Executable scripts
│       │   ├── activate.bat
│       │   ├── python.exe
│       │   └── pip.exe
│       ├── Lib\                       # Python packages
│       │   └── site-packages\
│       └── pyvenv.cfg
│
├── taxeaseui\                         # Next.js frontend application
│   ├── package.json                   # Node.js dependencies
│   ├── package-lock.json              # Dependency lock file
│   ├── .env.example                   # Example environment variables for frontend
│   ├── next.config.ts                 # Next.js configuration
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── eslint.config.mjs              # ESLint configuration
│   ├── postcss.config.mjs             # PostCSS configuration
│   ├── README.md                      # Next.js README
│   │
│   ├── src\                           # Source code
│   │   ├── middleware.ts              # Request middleware
│   │   │
│   │   ├── app\                       # Next.js app directory (pages/layouts)
│   │   │   ├── globals.css            # Global styles
│   │   │   ├── layout.tsx             # Root layout
│   │   │   ├── page.tsx               # Home page
│   │   │   │
│   │   │   ├── api\                   # API routes (backend proxy)
│   │   │   │   ├── upload\
│   │   │   │   │   └── route.ts       # Upload endpoint
│   │   │   │   ├── chat\
│   │   │   │   │   └── route.ts       # Chat endpoint
│   │   │   │   ├── health\
│   │   │   │   │   └── route.ts       # Health check
│   │   │   │   └── auth\
│   │   │   │       ├── signup\
│   │   │   │       │   └── route.ts
│   │   │   │       └── login\
│   │   │   │           └── route.ts
│   │   │   │
│   │   │   ├── login\                 # Login page
│   │   │   │   └── page.tsx
│   │   │   │
│   │   │   ├── signup\                # Signup page
│   │   │   │   └── page.tsx
│   │   │   │
│   │   │   ├── upload\                # Form 16 upload page
│   │   │   │   └── page.tsx
│   │   │   │
│   │   │   ├── mapping\               # ITR mapping/review page
│   │   │   │   └── page.tsx
│   │   │   │
│   │   │   └── assistant\             # Chat assistant page
│   │   │       └── page.tsx
│   │   │
│   │   └── components\                # Reusable React components
│   │       ├── ClientLayout.tsx       # Client-side layout wrapper
│   │       ├── Sidebar.tsx            # Navigation sidebar
│   │       └── TopBar.tsx             # Top navigation bar
│   │
│   ├── public\                        # Static assets
│   │   └── (favicon, images, etc.)
│   │
│   ├── node_modules\                  # Node packages (ignored by git)
│   │
│   └── .next\                         # Next.js build output (ignored by git)
│
└── tmp_form16_*\                      # Temporary directories for form processing
    └── (generated at runtime)
```

---

## Key Paths to Remember

### Environment Configuration
```
Backend:    d:\TaxAssist\backend\.env
            d:\TaxAssist\backend\.env.example

Frontend:   d:\TaxAssist\taxeaseui\.env.local
            d:\TaxAssist\taxeaseui\.env.example
```

### Python Virtual Environment
```
Activate (Windows):    d:\TaxAssist\backend\myenv\Scripts\activate.bat
Python Packages:       d:\TaxAssist\backend\myenv\Lib\site-packages\
```

### Main Application Files
```
Backend Entry:         d:\TaxAssist\backend\fastapi\app.py
Frontend Entry:        d:\TaxAssist\taxeaseui\src\app\page.tsx
Database Config:       d:\TaxAssist\backend\fastapi\database.py
Models:                d:\TaxAssist\backend\fastapi\models.py
```

### API Endpoints
```
Upload:                d:\TaxAssist\backend\fastapi\routers\upload.py
Authentication:        d:\TaxAssist\backend\fastapi\routers\auth.py
Chat/RAG:              d:\TaxAssist\backend\fastapi\routers\chat.py
Health:                d:\TaxAssist\backend\fastapi\routers\health.py
```

### Frontend Pages
```
Home:                  d:\TaxAssist\taxeaseui\src\app\page.tsx
Login:                 d:\TaxAssist\taxeaseui\src\app\login\page.tsx
Signup:                d:\TaxAssist\taxeaseui\src\app\signup\page.tsx
Upload Form 16:        d:\TaxAssist\taxeaseui\src\app\upload\page.tsx
Mapping Review:        d:\TaxAssist\taxeaseui\src\app\mapping\page.tsx
Assistant Chat:        d:\TaxAssist\taxeaseui\src\app\assistant\page.tsx
```

### RAG Pipeline
```
Main:                  d:\TaxAssist\backend\rag\main.py
Pipeline:              d:\TaxAssist\backend\rag\rag_pipeline.py
Vector Store:          d:\TaxAssist\backend\rag\vector_store.py
Reference Docs:        d:\TaxAssist\backend\rag\docs\
```

### Deployment Config
```
Render:                d:\TaxAssist\render.yaml
Vercel:                d:\TaxAssist\vercel.json
Procfile:              d:\TaxAssist\Procfile
Git:                   d:\TaxAssist\.gitignore
Documentation:         d:\TaxAssist\README.md
```

---

## Starting Commands

### Start Backend
```bash
cd d:\TaxAssist\backend
myenv\Scripts\activate.bat
python -m uvicorn fastapi.app:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd d:\TaxAssist\taxeaseui
npm run dev
```

---

## File Size Reference (Important for Render)

```
Large directories to note:
- backend/myenv/               → ~1.2GB (virtual environment - don't push to git)
- backend/rag/docs/            → ~500MB (reference documents)
- taxeaseui/node_modules/      → ~800MB (node packages - don't push to git)
- backend/__pycache__/         → Variable (Python cache - don't push)
- backend/vectorstore/         → ~200MB (FAISS indices - generated at runtime)
```

All these are in `.gitignore`, so Git won't track them when you push to GitHub.

---

## Quick Navigation

| What | Path |
|------|------|
| Backend Code | `d:\TaxAssist\backend\fastapi\` |
| Frontend Code | `d:\TaxAssist\taxeaseui\src\` |
| API Routes | `d:\TaxAssist\backend\fastapi\routers\` |
| Pages | `d:\TaxAssist\taxeaseui\src\app\` |
| RAG System | `d:\TaxAssist\backend\rag\` |
| Components | `d:\TaxAssist\taxeaseui\src\components\` |
| Deployment | `d:\TaxAssist\*.yaml, *.json, Procfile` |
| Docs | `d:\TaxAssist\README.md` |
