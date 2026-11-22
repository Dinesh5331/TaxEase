# TaxAssist (TaxNexus) - project context

Recommends which ITR form to file from a taxpayer's Form 16, AIS and TIS, and answers questions about
income tax law with citations. Target: production-grade, demo-able without real user data.

## Core design decision
- **ITR selection = deterministic rules engine** (`backend/rules/itr_rules.yaml`), not RAG. The inputs are
  structured facts (income heads, residency, caps); an LLM must not decide this.
- **RAG is only for**: (a) Q&A on the Act / forms with section citations, (b) explaining the rules-engine result.
- Form 16 proves only salary + TDS. Capital gains, property sales, VDA, dividends, foreign remittance come from
  **AIS/TIS**. Director / unlisted shares / residency / foreign assets / carry-forward losses are NOT in any
  document: ask the user (questionnaire step).

## Domain facts to keep straight
- Current filing = **AY 2026-27 (FY 2025-26) under Income-tax Act 1961**. The Income-tax Act 2025 applies from
  tax year 2026-27 (returns filed in 2027). Every corpus chunk needs `act_version` + `tax_year` metadata or
  1961 and 2025 section numbers will be mixed in answers.
- The Income-tax Act 2025 (Act 30 of 2025) is in force from 1 Apr 2026, after a Select Committee review. `backend/docs/laws/Income-tax_Bill(2025).pdf`
  is the Bill *as introduced* (Bill No. 24) and is superseded: replace it with the enacted Act before any 2025-Act Q&A.
  AY 2026-27 returns, revised returns and penalties stay under the 1961 Act; section map is in `rules/itr_rules.yaml` `compliance.act_2025_mapping`.
- ITR-1 (AY 26-27): resident (ROR) individual, income <= 50L, <= 2 house properties, LTCG 112A <= 1.25L,
  agri <= 5k, no director / unlisted shares / foreign assets / 194N / ESOP deferral / loss carry-forward.
- 44ADA limit is 50L (75L if cash receipts <= 5%); 44AD 2Cr (3Cr if cash <= 5%).
- Open point: ITR-4 and RNOR (form header says only "resident"). Treated as not eligible until confirmed.

## Layout
- `backend/api/` FastAPI app (routers: auth, chat, upload, health; JWT; SQLAlchemy/Postgres)
- `backend/rag/` loader -> FAISS + BM25 hybrid -> cross-encoder rerank -> Groq (llama-3.3-70b)
- `backend/ocr/` PyMuPDF text, Tesseract fallback, LLM JSON extraction of Form 16
- `backend/rules/` `itr_rules.yaml` (rules for ITR-1..7, U, V, B, late-filing routes, regime facts; source of truth),
  `regime.py` (old vs new tax comparison), `compliance.py` (belated / revised / ITR-U route + 234A/234F/140B/270A costs),
  `source/*.txt` (text of AY 26-27 ITR-1/2/3/4/U/V; ITR-5/6/7/B text was NOT extracted before the PDFs were deleted, those rules come from web sources)
- `backend/rules/engine.py` deterministic ITR selection (predicates keyed by the yaml rule ids); `backend/extractors/` Form 16 / AIS / TIS parsers + questionnaire + facts builder;
  `backend/services/analyze.py` single entry point (documents + answers -> result, PAN masked); `backend/api/routers/itr.py` HTTP routes;
  `backend/rag/{fusion,sections,citations}.py` RRF, section chunking + Act metadata, citations; `backend/eval/` golden Q&A + harness;
- `backend/demo_data/` 21 synthetic personas + `golden_itr.json` ground truth; built by `scripts/generate_demo_data.py`
- `backend/docs/{eligibility,laws,forms,Guidelines}` RAG corpus. Blank ITR PDFs were deleted on purpose.
- `taxeaseui/` Next.js 16 UI; server routes proxy to the backend via `NEXT_PUBLIC_API_URL`

## Commands (from `backend/`)
- Run API: `python -m uvicorn api.app:app --reload --port 8000`  (needs `.env`: DATABASE_URL, GROQ_API_KEY, SECRET_KEY)
- Regenerate demo data: `python scripts/generate_demo_data.py`
- Tests: `python -m unittest discover -s tests`  (87 tests; 6 API-contract tests skip without FastAPI). Rules gate: `python -m eval.run_eval engine` must stay 100%
- UI: `cd taxeaseui && npm run dev`

## Rules for working here
- Demo/test data is synthetic only. Never commit real PAN/Form 16. Mask PAN before any LLM call.
- `.env` holds a real Groq key: never print or commit it.
- Rules file tags each rule `verified: form` (read in the AY 26-27 form), `web` (secondary sources: taxguru, cleartax, news; confirm
  at incometax.gov.in) or `know` (statute/prior-year instructions; confirm). Do not promote a tag without checking the source.
- Regime facts that matter: a belated filer without business income cannot opt for the old regime; new regime disallows
  professional tax, HP-loss set-off and self-occupied-home interest. The Form 16 generator must not deduct professional tax.
- ITR-7 is for 139(4A)-(4D) only. Business trusts 139(4E) and investment funds 139(4F) file ITR-5.
- ITR-U window is 48 months for AY 2026-27 and earlier (extra tax 25/50/60/70%); the window under the 2025 Act is reported inconsistently (48 vs 60 months).
- Golden labels in `demo_data/golden_itr.json` are hand-written, not engine output. Keep them independent.
- Many files show as modified in git because of CRLF/LF and tracked `__pycache__`; do not "fix" that in feature work.
- Vector index auto-rebuilds when the manifest changes; first start after a corpus change is slow (embeds + OCR).
- Engine never fills an unknown questionnaire fact silently: status stays `provisional` and open questions are returned. AIS gives sale value, not gain: capital gains come from the user.
- Keep the engine/extractor/service layers free of FastAPI imports so they stay testable without the web stack.
- The remote file bridge cannot write `.github/`; `ci.example.yml` must be moved there by hand.
