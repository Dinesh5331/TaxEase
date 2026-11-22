# Implementation plan

Status: done = built and checked here; **unverified** = written but not run (this environment had no network,
so Python deps, the Groq call and Postgres were never exercised). Run the app once locally before trusting Phase 1.

| Phase | Goal | Status |
|---|---|---|
| 0 | Audit | done |
| 1 | Repo / deploy hygiene | done, **unverified at runtime** |
| 2 | Synthetic Form 16 / AIS / TIS + golden set | done, tests pass (`tests/test_demo_data.py`) |
| 2b | Real AIS/TIS/Form 16 structure, regime comparator, late-filing calculator | done, 26 tests pass |
| 3 | Rules engine + Form 16/AIS/TIS extractors + questionnaire + API routes | done; 87 tests pass, engine reproduces all 21 labels. API routes written but **not run** (no FastAPI in the build sandbox) |
| 4 | Backend re-architecture | **not started** (needs Postgres/Redis/object storage to verify); only `services/` split done |
| 5 | RAG upgrade | code written (RRF, section chunking, Act metadata/filter, citations); pure parts tested, **pipeline unverified at runtime** |
| 6 | Evaluation | golden Q&A (21, draft) + harness; engine gate runs now; answers/RAGAS modes need the index and a key |
| 7 | Claude plugin / MCP connector | **dropped** (code removed 2026-11-22; revisit only if the product should live inside Claude) |

## Phase 1 - what changed and why
- `requirements.txt`: added missing bcrypt, email-validator, pyyaml, langchain-text-splitters; dropped unused passlib,
  langchain meta-package; loosened sentence-transformers (2.2.2 breaks on current huggingface_hub). **Not install-tested.**
- Entry point: Procfile/README pointed at `fastapi.app` (module is `api.app`); Procfile now one uvicorn worker
  (each worker loads its own embedding + rerank models).
- `chat.py`: removed Dropbox corpus download (wrote to the wrong dir, ran at request time); load guarded by a lock;
  `/chat` and `/upload` are sync `def` so blocking work uses the threadpool instead of freezing the event loop.
- Index manifest uses relative paths (was absolute `D:\...`, which forced a rebuild on every other machine).
  `INDEX_SCHEMA_VERSION` 7; the existing `vectorstore/` is stale (still contains the deleted ITR form chunks) and will rebuild.
- `HybridRetriever` (BM25 over all chunks) was rebuilt per request; now cached per loaded corpus.
- `SECRET_KEY` no longer falls back to a hardcoded string; CORS from `ALLOWED_ORIGINS`.
- `.gitignore` no longer hides `backend/docs` (the text corpus must be tracked); PDFs stay ignored.
- `itr_eligibility_reference.txt` corrected to AY 2026-27 (ITR-1: two properties, LTCG 112A <= 1.25L; 44ADA 50L/75L).
- Deleted: `backend/rag/data_ingestion.py` (dead stub), both blank-ITR PDF folders.
- Left for your call: `backend/api/rag/` and `api/docs.zip` (leftovers of the old download, now gitignored),
  stale `PROJECT_STRUCTURE.md` (describes `backend/fastapi/`).

## Phase 2 - synthetic data
- 21 personas covering ITR-1..4, with edge cases on each threshold (112A 90k vs 1.8L, 44ADA 62L at cash 3% vs 8%,
  2 vs 3 properties, 50L cap, NRI, director, VDA, property sale, foreign remittance, partner, carry-forward loss).
- AIS/TIS are **simplified models** of the portal documents (same categories and codes, not the exact JSON/PDF layout).
  Real AIS parsing needs real samples before launch.
- Form 16 TDS is computed with new-regime FY 2025-26 slabs (87A rebate, marginal relief, 10% surcharge band). Demo-grade only.
- Known limit: `form16.pdf` has a text layer, so it does not exercise OCR. Add an image-only variant for OCR tests.
- Aligned to the real documents (from the e-filing portal help and Form 16 format notes, not from a real sample):
  AIS Part A (PAN, masked Aadhaar, name, DOB, contacts) and Part B tabs TDS/TCS, SFT, Payment of Taxes, Demand and Refund,
  Other Information, each row with a reported and a modified value; TIS per category with processed and derived value;
  Form 16 Part B items 1-19 and the 115BAC(1A) opt-out line. Real AIS PDFs are password protected and the portal also gives
  JSON/CSV: obtain at least one real sample from a consenting tester to harden the parsers.
- Bug fixed: demo Form 16 deducted professional tax; not allowed under the new regime (115BAC(1A)).

## Phase 2b - regime and late-filing logic (exposed via /api/regime/compare and /api/compliance/route in Phase 3)
- `rules/regime.py`: old vs new comparison with HRA, 80C/80CCD/80D/80E/80G/80TTA-B, 24(b), HP loss rule, special-rate gains,
  basic-exemption shortfall adjustment, 87A and marginal relief, surcharge, cess, break-even extra deduction, belated-filer lock to new regime.
  Cross-checked against ClearTax worked examples (97,500; 3,19,800 vs 3,90,000). Not modelled: surcharge marginal relief, loss carry-forward, clubbing, agricultural income.
- `rules/compliance.py`: belated / revised / ITR-U / wrong-form routing for a given date, plus 234F, 234A, ITR-U additional tax, 270A. Dates and fees come from secondary sources; verify at incometax.gov.in.
- Rules for ITR-5/6/7/U/V/B were written from web sources because the blank PDFs were deleted before extraction (Phase 0 ordering mistake). Re-extract from the official forms when convenient.

## Phase 3 - extraction + rules engine (done)
- `rules/engine.py`: predicates keyed by the rule ids in `itr_rules.yaml`; a test fails if the two lists diverge. Output: form, failed rule ids with
  plain reasons, schedules, `missing` questions, status `final` | `provisional`. Unknown questionnaire answers never default silently:
  the form is still computed, but status is provisional and the open questions are listed.
- `extractors/form16.py`: regex over layout text (poppler, then PyMuPDF words, then pypdf), each field keeps its source line; arithmetic
  cross-checks (item 3-5=6, 6+8=9, 9-11=12, 17-18=19, TDS total) lower confidence; missing fields are reported, never guessed.
  `extractors/ais.py`: exact information-code map (prefix matching would file 194C under dividend), skips non-Active rows, uses the
  modified value, lists unknown codes; AIS-vs-TIS cross-check. `extractors/facts.py`: merges documents + answers, flags conflicts, estimates total income
  (only for the 50-lakh test). `extractors/questionnaire.py`: the facts no document proves.
- AIS never contains the capital gain, only sale value (SFT-017), so the gain comes from the user's broker statement; until given, status is provisional.
  A property sale or any VDA transfer forces ITR-2 or higher even at nil gain (`property_sold`, `vda_transferred`).
- `services/analyze.py` is the single entry point (documents + answers -> result, PAN masked). `api/routers/itr.py`: `GET /api/itr/questionnaire`,
  `POST /api/itr/select`, `POST /api/itr/analyze` (multipart, 10 MB cap, temp file removed), `POST /api/regime/compare`, `POST /api/compliance/route`.
- Bug found by test: PAN leaked through the Form 16 field dump; masked now.
- Limits: the gate proves consistency with hand-written labels, not correctness against the real form. 11 rules are tagged `know`/`web` in the YAML.
  Extractors were built only against synthetic documents.

## Phase 4 - backend architecture (not started)
- Modular monolith: routers -> services -> repositories; `services/analyze.py` and `rules/` are the first framework-free pieces.
- OCR/extraction as background jobs (Redis + arq) with status polling; upload to object storage, encrypted at rest.
- Auth on every route (today `/chat`, `/upload` and the new `/itr/*`, `/regime/*`, `/compliance/*` routes are open); JWT in `Authorization` header (not `/auth/me?token=`, which also needs the UI changed).
- FAISS + pickle -> pgvector (default) or Qdrant. Pickle load is also an unsafe-deserialisation risk.
- Mask PAN/name before LLM calls (the ITR path already masks); no PII in logs. Replace the `app_state` dict with a dependency.

## Phase 5 - RAG upgrade (code written, unverified)
- `rag/fusion.py` reciprocal rank fusion replaces the 0.45/0.55 min-max blend in `HybridRetriever` (score scaled to (0,1] so thresholds keep meaning).
- `rag/sections.py`: law PDFs are chunked by statutory section (heading regex, monotonic section numbers, margin line numbers dropped); each chunk carries
  `section`, `act_version`, `text_status`, `tax_year` from an explicit filename map (`Income-tax_Bill(1962).pdf` is the 1961 Act; the 2025 PDF is the superseded Bill).
  `choose_act` routes a query to 1961 or 2025 and `filter_by_act` never returns an empty set. `INDEX_SCHEMA_VERSION` 8: the index rebuilds on first start.
- `rag/citations.py`: `/chat` returns `citations` (document, section, Act, page, snippet). `run_rag` kept as a wrapper.
- Not done: removing the "inject all eligibility chunks" hack (kept until the UI uses the engine), stronger reranker, pgvector, conversation memory, replacing the 2025 Bill PDF with the enacted Act.
- Unverified: the loader change was never run (needs PyMuPDF + models); section detection was checked on pages 56-75 of the 2025 Bill only; 1961 Act headings may differ.

## Phase 6 - evaluation (partly runnable)
- `eval/golden_qa.json`: 21 questions, reference answers from `itr_rules.yaml`, `must_include` / `must_not_include` strings. Status: **draft, not reviewed by a tax professional**; entries tagged web/know need checking.
- `python -m eval.run_eval engine` (runs anywhere, gate 100%), `answers` (needs index + GROQ key; checks substrings, citation rate, Act routing), `ragas` (needs `ragas datasets` and a judge LLM key).
- Thresholds in `run_eval.THRESHOLDS` are initial guesses; set them from a first real run. Tracing (Langfuse/OpenTelemetry) not started.
- CI: `ci.example.yml` at the repo root (the bridge cannot write `.github/`; move it to `.github/workflows/ci.yml`). Demo PDFs are gitignored, so CI regenerates them.

## Phase 7 - Claude plugin / MCP connector (dropped)
- Built and then removed on request. `services/analyze.py` and `rules/` are framework-free, so an MCP wrapper can be added later without touching them.

## Open decisions
- Keep Groq + Llama 3.3? (assumed yes)
- pgvector vs Qdrant (assumed pgvector)
- Verify at incometax.gov.in: AY 2026-27 due dates (ITR-3/4 non-audit 31 Aug), revised-return fee after 31 Dec, ITR-U limits, ITR-4 and RNOR, 87A treatment with capital gains.
- Frontend `mapping/page.tsx` no longer shows invented DEMO_DATA: it shows empty fields and a notice when nothing was uploaded (typechecks; not viewed in a browser). The UI still uses the old Form-16 LLM path, not the new `/api/itr/analyze`.

## Manual verification checklist (could not be done from the build sandbox)
1. `pip install -r requirements.txt`, set `.env` (DATABASE_URL, GROQ_API_KEY, SECRET_KEY), start the API, call `/api/health`, `/chat`, `/upload`. First start rebuilds the index (schema 8) and is slow.
2. Run `python -m unittest discover -s tests` with FastAPI installed: the 6 skipped API-contract tests then run.
3. `/chat` returns `citations`; ask one AY 2026-27 question and one 2025-Act question and check the cited Act. Spot-check `section` values on 1961 Act chunks (heading regex was only tried on the 2025 Bill).
4. Official-source checks listed under Open decisions, then promote tags in `itr_rules.yaml` only after reading the source.
5. Review `eval/golden_qa.json` with someone who knows Indian tax; run `eval.run_eval answers` and `ragas`, then set thresholds.
6. Get at least one real AIS JSON, TIS and Form 16 from a consenting tester and run the extractors on them.
7. Move `ci.example.yml` to `.github/workflows/ci.yml` (the file bridge cannot write `.github/`).
8. Look at the Next.js mapping page in a browser; wire the UI to `/api/itr/analyze` and the questionnaire.
9. Leftovers still awaiting your call: `backend/api/rag/`, `api/docs.zip`, `PROJECT_STRUCTURE.md`, `final.pdf`, `opencode.json`, empty `.github/workflows/` folder.
