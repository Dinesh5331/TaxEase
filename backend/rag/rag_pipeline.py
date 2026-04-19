import re

from rag.hybrid_retriever import HybridRetriever
from rag.query_classifier import classify_query
from rag.reranker import rerank
from rag.llm import generate
from rag.loader import normalize_document_key


MIN_HYBRID_SCORE = 0.2
MIN_RERANK_SCORE = -2.0


# ---------------------------------------------------------------------------
# Form extraction from query
# ---------------------------------------------------------------------------

def _extract_requested_forms(query):
    """
    Detect any ITR form references and return them normalised.
    e.g. "itr 1" / "ITR-2" / "itr_3" -> ["ITR-1"] / ["ITR-2"] / ["ITR-3"]
    """
    matches = re.findall(r"itr[\s\-_]*[a-z0-9]+", query, re.IGNORECASE)
    forms, seen = [], set()
    for m in matches:
        suffix = re.sub(r"^itr[\s\-_]*", "", m, flags=re.IGNORECASE).upper()
        key = f"ITR-{suffix}"
        if key not in seen:
            forms.append(key)
            seen.add(key)
    return forms


def _detect_sub_focus(query):
    """
    Detect if the user is asking a specific sub-question rather than full eligibility.
    Returns a focus hint string, or None for full coverage.
    """
    q = query.lower()
    if any(p in q for p in ("who can use", "who can file", "who is eligible",
                             "can i use", "can i file", "am i eligible")):
        return "who_can"
    if any(p in q for p in ("who cannot", "who can't", "who cannot use",
                             "not eligible", "ineligible", "who should not")):
        return "who_cannot"
    if any(p in q for p in ("income limit", "income threshold", "how much income",
                             "maximum income", "50 lakh", "50 lakhs")):
        return "income_limit"
    return None  # full coverage


# ---------------------------------------------------------------------------
# Metadata-based form matching
# ---------------------------------------------------------------------------

def _matches_form(metadata, requested_forms):
    """Return True if the chunk belongs to any of the requested forms."""
    if not requested_forms:
        return False
    form_name    = metadata.get("form_name", "")
    document_key = metadata.get("document_key", "")
    file_name    = metadata.get("file", "")
    for form in requested_forms:
        norm = normalize_document_key(form)
        if (form_name == form
                or document_key.startswith(norm)
                or norm in normalize_document_key(file_name)):
            return True
    return False


# ---------------------------------------------------------------------------
# Guaranteed eligibility injection (bypasses hybrid search scoring entirely)
# ---------------------------------------------------------------------------

def _get_eligibility_items(docs, requested_forms):
    """
    Directly pull ALL eligibility-source chunks from the doc store.
    These bypass BM25/FAISS scoring — included regardless of hybrid score.
    The general reference (form_name='unknown') covers all forms so is always included.
    """
    items = []
    for doc in docs:
        if doc.metadata.get("source") != "eligibility":
            continue
        # Include if: no form filter, or doc matches the form, or it's the general reference
        if (not requested_forms
                or _matches_form(doc.metadata, requested_forms)
                or doc.metadata.get("form_name") == "unknown"):
            items.append({
                "doc": doc,
                "bm25_score": 1.0,
                "faiss_score": 1.0,
                "hybrid_score": 1.0,   # guaranteed to pass MIN_HYBRID_SCORE
                "rerank_score": 1.0,   # guaranteed to pass MIN_RERANK_SCORE
            })
    return items


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _deduplicate(items):
    seen, out = set(), []
    for item in items:
        doc = item["doc"]
        key = (doc.metadata.get("path"), doc.metadata.get("page"), doc.page_content[:120])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def _build_context(items):
    """
    Build context string for the LLM.
    Headers are kept minimal so the LLM does not echo page numbers or file names.
    """
    parts, files = [], []
    for item in items:
        doc    = item["doc"]
        fname  = doc.metadata.get("file", "unknown")
        page   = doc.metadata.get("page", "?")
        source = doc.metadata.get("source", "unknown")
        form   = doc.metadata.get("form_name", "unknown")
        files.append(f"{fname} (page {page})")
        parts.append(f"[{form} | {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts), files


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(query, context, requested_forms, matched_files, query_type, sub_focus=None):
    if requested_forms:
        forms_str = ", ".join(requested_forms)
        scope = (
            f"The question is specifically about: {forms_str}. "
            f"Use ONLY context from that form's eligibility reference and documents."
        )
        not_found = (
            f'If the context does not contain a clear answer, say: '
            f'"The answer was not found in the available {forms_str} documents. '
            f'Please consult a tax professional."'
        )
    else:
        scope = "Answer using whichever documents are most relevant."
        not_found = 'If the answer is not in the context, say: "Not found in documents."'

    if query_type == "tax_regime":
        focus = (
            "The user is asking about the old tax regime vs new tax regime, or the "
            "Income Tax Act 2025 / Budget 2025 changes. "
            "Give a clear, specific answer directly addressing what was asked. "
            "If asked for a comparison, cover: tax slabs, standard deduction, "
            "exemptions allowed, rebate under 87A, and when to choose each. "
            "Use exact rupee amounts from the context. Be specific, not generic."
        )
    elif query_type == "itr_selection":
        if sub_focus == "who_can":
            focus = (
                "The user is asking specifically WHO CAN use this form. "
                "Answer ONLY that: taxpayer type, residency requirement, "
                "allowed income sources, income limit, special allowed cases. "
                "Be concise and use exact amounts from the context."
            )
        elif sub_focus == "who_cannot":
            focus = (
                "The user is asking specifically WHO CANNOT use this form. "
                "List all disqualifications: excluded taxpayer types, "
                "disqualifying income types, residency bars, income limit exceeded, "
                "and any other explicit exclusions from the context."
            )
        elif sub_focus == "income_limit":
            focus = (
                "The user is asking about income limits. "
                "State the exact total income ceiling, per-source limits, and conditions "
                "with the exact amounts from the context."
            )
        else:
            focus = (
                "Give a COMPREHENSIVE, structured answer covering:\n"
                "  1. Who CAN use this form (taxpayer type, residency, allowed income sources)\n"
                "  2. Who CANNOT use this form (explicit bars and disqualifications)\n"
                "  3. Income limits / monetary thresholds (exact amounts)\n"
                "  4. Allowed income sources\n"
                "  5. Disallowed income sources\n"
                "  6. Special cases (senior citizens, NRIs, agricultural income, etc.)\n"
                "Use exact amounts and conditions from the eligibility reference. "
                "Do NOT include TDS section codes or field-level validation rules — "
                "those are technical checks, NOT eligibility criteria."
            )
    elif query_type == "form_filling":
        focus = (
            "Focus on how to fill specific fields, schedules, or sections. "
            "Use exact field names and instructions from the guidelines."
        )
    else:
        focus = (
            "Give a comprehensive answer covering all key rules, conditions, "
            "income types, limits, and special cases from the context."
        )

    return (
        "You are TaxAssist, an expert Indian income tax assistant.\n\n"
        "CRITICAL FORMATTING RULES — YOU MUST FOLLOW THESE EXACTLY:\n"
        "- Do NOT use markdown formatting in your answer.\n"
        "- Do NOT use ** for bold, * for italic, or # for headers.\n"
        "- Do NOT use any markdown symbols whatsoever.\n"
        "- Use plain numbered lists: 1. 2. 3. and plain bullets: - item\n"
        "- Write as clean, readable plain text only.\n\n"
        "ANSWER INSTRUCTIONS:\n"
        f"1. Answer ONLY from the CONTEXT below. Do not use outside knowledge.\n"
        f"2. {scope}\n"
        f"3. {focus}\n"
        f"4. {not_found}\n"
        "5. Do NOT mention page numbers, file names, TDS section codes "
        "(like 194B, 195, 196A etc.), or field-level validation rules in your answer.\n"
        "6. Present your answer in clear, readable plain text sections.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{query}\n\n"
        "ANSWER:"
    )


# ---------------------------------------------------------------------------
# Main RAG entry point
# ---------------------------------------------------------------------------

def run_rag(model, index, docs, query, debug=False):
    """
    Unified RAG pipeline:
      1. Classify query and detect sub-focus.
      2. GUARANTEE-INJECT eligibility chunks directly (bypasses hybrid search scoring).
      3. Run hybrid retrieval for additional supporting context.
      4. Merge, deduplicate, rerank, generate.
    """
    query_type      = classify_query(query)
    requested_forms = _extract_requested_forms(query)
    sub_focus       = _detect_sub_focus(query)

    # --- Step 1: Guarantee-inject eligibility chunks ---
    # Pulled directly from the doc store, NOT via hybrid search.
    # They can NEVER be filtered out by score thresholds.
    eligibility_items = []
    if query_type in ("itr_selection", "tax_regime") or requested_forms:
        eligibility_items = _get_eligibility_items(docs, requested_forms)

    # --- Step 2: Hybrid retrieval for supporting context ---
    retriever       = HybridRetriever(docs, index)
    retrieved_items = retriever.search(query, k=40)

    # --- Step 3: Form filter on hybrid results ---
    if requested_forms:
        form_items = [
            item for item in retrieved_items
            if _matches_form(item["doc"].metadata, requested_forms)
        ]
        retrieved_items = form_items or retrieved_items

    # --- Step 4: For eligibility queries, prefer blank form over validation-rules guidelines ---
    # The guidelines are "Validation Rules" PDFs full of TDS codes — not useful for eligibility.
    if query_type == "itr_selection":
        form_only = [i for i in retrieved_items
                     if i["doc"].metadata.get("source") == "itr_form"]
        retrieved_items = form_only or retrieved_items

    # --- Step 5: Merge (eligibility guaranteed first) + deduplicate ---
    merged = _deduplicate(eligibility_items + retrieved_items)

    # --- Step 6: Score filter — eligibility chunks always pass ---
    candidates = [
        item for item in merged
        if item.get("hybrid_score", 0) >= MIN_HYBRID_SCORE
        or item["doc"].metadata.get("source") == "eligibility"
    ]

    # --- Step 7: Rerank ---
    rerank_top_k = 10 if query_type == "itr_selection" else 8
    top_items = rerank(query, candidates[:20], top_k=rerank_top_k)

    # Eligibility chunks bypass rerank score threshold too
    strong = [
        item for item in top_items
        if item.get("rerank_score", 0) >= MIN_RERANK_SCORE
        or item["doc"].metadata.get("source") == "eligibility"
    ] or top_items

    if debug:
        print(f"\n[DEBUG] forms={requested_forms}, type={query_type}, "
              f"sub_focus={sub_focus}, final_chunks={len(strong)}")
        for item in strong:
            m = item["doc"].metadata
            print(f"  -> src={m.get('source'):12s} | form={m.get('form_name')} | "
                  f"p{m.get('page')} | rerank={item.get('rerank_score', 1.0):.3f}")

    if not strong:
        return "Not found in documents. Please consult a tax professional."

    context, matched_files = _build_context(strong)
    prompt = _build_prompt(
        query, context, requested_forms, matched_files, query_type, sub_focus=sub_focus
    )
    return generate(model, prompt)
