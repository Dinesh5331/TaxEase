# TaxEase — AI-Powered Tax Assistance

TaxEase is a full-stack tax assistance platform that helps users explore Indian Income Tax Return (ITR) filing requirements, get context-aware answers to tax questions, and analyze Form 16 information. It combines document extraction with a Retrieval-Augmented Generation (RAG) pipeline to ground responses in relevant tax reference material.

## Overview

Tax-related information can be difficult to navigate across forms, rules, and eligibility requirements. TaxEase brings document processing and conversational tax guidance into one application.

### Key capabilities

- **ITR guidance:** Ask questions about tax filing, ITR forms, eligibility, and related requirements.
- **Hybrid information retrieval:** Combines BM25 keyword search with FAISS vector similarity to retrieve relevant tax content.
- **Context reranking:** Uses a cross-encoder to rerank candidate passages before they are passed to the language model.
- **Form 16 processing:** Extracts text from supported documents and images, then uses an LLM to structure relevant information.
- **OCR support:** Uses Tesseract OCR and image-processing tools to handle scanned content.
- **Full-stack application:** A Next.js and TypeScript frontend communicates with a FastAPI backend.
- **User accounts:** Supports signup, login, and user information endpoints.

## Architecture

```text
┌──────────────────────────────┐
│      Next.js / TypeScript     │
│       Frontend (UI)           │
└──────────────┬───────────────┘
               │ REST API
┌──────────────▼───────────────┐
│         FastAPI Backend       │
│  Authentication · Uploads     │
│  Chat · Document Processing   │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼───────┐  ┌─────▼────────────┐
│ Document &   │  │ Retrieval-Augmented│
│ OCR Pipeline │  │ Generation (RAG)   │
└──────────────┘  └─────┬────────────┘
                        │
              ┌─────────▼─────────┐
              │ BM25 + FAISS      │
              │ Hybrid Retrieval  │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │ Cross-Encoder     │
              │ Reranking         │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │ Groq-hosted LLM   │
              │ Response Creation │
              └───────────────────┘
```

## How the RAG pipeline works

1. **Load and extract:** Tax reference material is loaded, with text extraction and OCR used where needed.
2. **Chunk the content:** Extracted text is split into overlapping chunks so retrieval can target relevant passages.
3. **Create embeddings:** Sentence Transformers converts chunks into dense vector representations.
4. **Retrieve candidates:** BM25 finds keyword matches while FAISS searches by vector similarity. The pipeline combines the retrieval scores.
5. **Rerank results:** A cross-encoder reranks candidate passages to prioritize the most relevant context.
6. **Generate a response:** The selected context is sent to the language model to produce a response to the user's query.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| Database and ORM | PostgreSQL, SQLAlchemy |
| Authentication | JWT, bcrypt |
| Retrieval | BM25, FAISS |
| Embeddings | Sentence Transformers, `all-MiniLM-L6-v2` |
| Reranking | Cross-Encoder, `ms-marco-MiniLM-L-6-v2` |
| Document processing | PyMuPDF, Tesseract OCR, pytesseract, Pillow |
| Language model | Groq API, Llama 3.3 70B Versatile |

## Repository structure

```text
TaxEase/
├── backend/
│   ├──  api/     # API application and route handlers
│   ├── rag/              # Retrieval and response-generation pipeline
│   ├── ocr/              # OCR and document extraction utilities
│   └── requirements.txt  # Python dependencies
├── taxeaseui/            # Next.js frontend
│   ├── src/              # Application source
│   └── package.json      # Node.js dependencies and scripts
└── README.md
```

## Getting started

### Prerequisites

Install the following before running the application:

- Python and pip
- Node.js and npm
- PostgreSQL
- Tesseract OCR
- A Groq API key

Use a Python version compatible with the dependencies in `backend/requirements.txt`.

### 1. Clone the repository

```bash
git clone https://github.com/Dinesh5331/TaxEase.git
cd TaxEase
```

### 2. Configure the backend

```bash
cd backend
python -m venv myenv
```

Activate the environment:

**Windows (PowerShell):**
```powershell
.\myenv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source myenv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Configure the backend environment variables in `backend/.env`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/taxease
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=replace_with_a_strong_secret
```

Create the PostgreSQL database and make sure the connection string matches your local setup.

### 3. Configure the frontend

Open a second terminal:

```bash
cd taxeaseui
npm install
```

Create `taxeaseui/.env.local`:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 4. Run the application

Start the backend from the `backend` directory with the virtual environment activated:

```bash
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend from the `taxeaseui` directory in another terminal:

```bash
npm run dev
```

Open **http://localhost:3000** in your browser. The backend API is available at **http://localhost:8000**; when enabled, FastAPI's interactive API documentation is available at **http://localhost:8000/docs**.

## API overview

The application exposes endpoints for these workflows (exact request schemas are defined in the backend):

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/signup` | Register a user |
| `POST` | `/auth/login` | Authenticate a user |
| `GET` | `/auth/me` | Retrieve current-user information |
| `POST` | `/upload` | Upload a document for extraction and ITR guidance |
| `PUT` | `/upload/save` | Save edited mapping values for the upload workflow |
| `POST` | `/chat` | Submit a tax question to the RAG-powered assistant |
| `GET` | `/health` | Check backend health |

## Example questions

Try asking questions such as:

- Which ITR form may be applicable to my tax situation?
- What conditions determine eligibility for a particular ITR form?
- What information should I review before filing my return?
- Can you explain a tax rule in the context of the available reference material?

TaxEase is an assistance tool, not a substitute for professional tax advice. Verify important filing decisions against current official Income Tax Department guidance or consult a qualified tax professional.

## Configuration and security

- Keep API keys, database credentials, and secret keys in environment variables; never commit real secrets.
- Use a strong, unique `SECRET_KEY` outside local development.
- Configure HTTPS and appropriate access controls before exposing the application publicly.
- Handle uploaded financial documents carefully and review data-retention behavior before using real personal information.

## Contributing

Contributions and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-change`.
3. Make and test your changes.
4. Commit your work: `git commit -m "Describe your change"`.
5. Push the branch and open a pull request.

## License

See the repository's license file for applicable terms.
