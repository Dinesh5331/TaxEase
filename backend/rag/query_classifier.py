def classify_query(query: str) -> str:
    """
    Classify a user query into one of four categories:
    - tax_regime    : old vs new regime, Income Tax Act 2025, 87A, 115BAC
    - form_filling  : how to fill specific fields/schedules
    - itr_selection : which ITR form, eligibility, who can file
    - general_tax   : everything else
    """
    normalized = query.lower()

    # ── Tax regime keywords (highest priority — checked first) ──────────────
    tax_regime_keywords = [
        "old regime",
        "new regime",
        "tax regime",
        "old tax regime",
        "new tax regime",
        "115bac",
        "old vs new",
        "new vs old",
        "difference between old and new",
        "which regime",
        "which regime is better",
        "switch regime",
        "switch to new",
        "switch to old",
        "choose regime",
        "income tax act 2025",
        "income tax bill 2025",
        "budget 2025",
        "new tax code",
        "rebate 87a",
        "section 87a",
        "12 lakh zero tax",
        "12 lakh no tax",
        "nil tax",
        "zero tax",
        "standard deduction 75000",
        "standard deduction 50000",
        "default regime",
        "opt for old",
        "opt out of new",
        "breakeven",
        "break even",
        "tax saving comparison",
    ]

    # ── Form filling keywords ───────────────────────────────────────────────
    form_filling_keywords = [
        "how to fill",
        "how do i fill",
        "fill itr",
        "schedule",
        "column",
        "field",
        "where to mention",
        "where should i enter",
        "what to enter",
        "instruction",
        "guideline",
    ]

    # ── ITR selection / eligibility keywords ────────────────────────────────
    itr_selection_keywords = [
        "which itr",
        "itr form",
        "which return",
        "eligible",
        "eligibility",
        "condition",
        "criteria",
        "who can file",
        "who should file",
        "applicable",
        "who is eligible",
        "can i file",
        "am i eligible",
        "requirements",
        "rules for",
        "rules",
        "qualify",
        "qualification",
        "who cannot file",
        "not applicable",
        "ineligible",
        "explain",
        "about itr",
        "tell me about",
        "what is itr",
        "overview",
    ]

    if any(kw in normalized for kw in tax_regime_keywords):
        return "tax_regime"

    if any(kw in normalized for kw in form_filling_keywords):
        return "form_filling"

    if any(kw in normalized for kw in itr_selection_keywords):
        return "itr_selection"

    return "general_tax"
