"""Questions for the facts no document can prove. Ids are the Facts / answers keys."""

QUESTIONS = [
    {"id": "residential_status", "type": "choice", "options": ["ROR", "RNOR", "NR"], "rule": "i1_resident",
     "text": "What was your residential status in FY 2025-26? (Resident and ordinarily resident, resident but not ordinarily resident, or non-resident.)",
     "help": "Staying in India 182+ days, or 60+ days plus 365+ days in the previous 4 years, makes you resident. NRIs and RNORs cannot file ITR-1."},
    {"id": "hp_count", "type": "int", "rule": "i1_sources",
     "text": "How many house properties did you own on 31 March 2026 (self-occupied, let-out or deemed let-out)?",
     "help": "AIS shows only rent that was reported to the department, not the number of properties."},
    {"id": "director", "type": "bool", "rule": "i1_director",
     "text": "Were you a director of any company at any time in FY 2025-26?"},
    {"id": "unlisted_equity", "type": "bool", "rule": "i1_unlisted",
     "text": "Did you hold unlisted equity shares (including startup ESOPs) at any time in the year?"},
    {"id": "foreign_asset_or_income", "type": "bool", "rule": "i1_foreign",
     "text": "Did you hold any asset outside India, have signing authority on a foreign account, or earn income from outside India?"},
    {"id": "loss_carry_forward", "type": "bool", "rule": "i1_losses",
     "text": "Do you have any loss from earlier years to carry forward, or a capital loss to set off this year?"},
    {"id": "esop_deferral", "type": "bool", "rule": "i1_esop",
     "text": "Is tax on ESOPs of an eligible start-up deferred in your case?"},
    {"id": "tds_194N", "type": "bool", "rule": "i1_194N",
     "text": "Was TDS deducted on cash withdrawals from your bank (section 194N)?"},
    {"id": "partner_in_firm", "type": "bool", "rule": "business",
     "text": "Are you a partner in a firm or LLP that pays you remuneration or interest?"},
    {"id": "agri_income", "type": "amount", "rule": "i1_sources",
     "text": "How much agricultural income did you earn in the year (Rs)? Enter 0 if none."},
    {"id": "lottery_or_gambling", "type": "amount", "rule": "i1_special",
     "text": "Did you win any lottery, game show, horse race or online-game prize (Rs)? Enter 0 if none."},
]

CONDITIONAL = {
    "capital_gains": [
        {"id": "ltcg_112a", "type": "amount", "rule": "i1_cg",
         "text": "Long-term gain on listed shares / equity mutual funds (Rs), from your broker's capital-gains statement.",
         "when": "AIS shows a sale of securities or mutual-fund units. AIS gives only the sale value, not your gain."},
        {"id": "stcg_111a", "type": "amount", "rule": "i1_cg",
         "text": "Short-term gain on listed shares / equity mutual funds (Rs). Enter 0 if none.", "when": "same"},
        {"id": "ltcg_other", "type": "amount", "rule": "i1_cg",
         "text": "Any other capital gain, such as property, unlisted shares, debt funds or gold (Rs). Enter 0 if none.", "when": "same"},
    ],
    "property_sale": [
        {"id": "ltcg_other", "type": "amount", "rule": "i1_cg",
         "text": "Capital gain or loss on the property you sold (Rs).",
         "when": "AIS shows a TDS 194-IA entry. A sale needs ITR-2 or higher even if the gain is nil."},
    ],
    "vda": [
        {"id": "vda_gain", "type": "amount", "rule": "i1_special",
         "text": "Gain on crypto / virtual digital assets (Rs).", "when": "AIS shows a TDS 194S entry."},
    ],
    "business": [
        {"id": "business_kind", "type": "choice",
         "options": ["44AD", "44ADA", "44AE", "NON_PRESUMPTIVE", "SPECULATIVE"], "rule": "business",
         "text": "How do you report your business or professional income? 44AD (business, presumptive), 44ADA (profession, presumptive), "
                 "44AE (goods carriage), regular books, or speculative / F&O trading.",
         "when": "AIS shows GST turnover, professional-fee TDS or firm income."},
        {"id": "business_receipts", "type": "amount", "rule": "i4_income",
         "text": "Gross receipts or turnover for the year (Rs).", "when": "same"},
        {"id": "cash_receipt_pct", "type": "percent", "rule": "i4_income",
         "text": "What share of receipts came in cash (not by bank or digital means)? Enter a percentage.", "when": "same"},
    ],
}


def questions_for(missing: list, bucket_flags: dict) -> list:
    """Questions still to ask, in a stable order. `bucket_flags` says which AIS signals are present."""
    asked, seen = [], set()
    by_id = {q["id"]: q for q in QUESTIONS}
    for m in missing:
        if m in by_id and m not in seen:
            asked.append(by_id[m])
            seen.add(m)
    if "capital_gain_amounts" in missing:
        asked += [q for q in CONDITIONAL["capital_gains"] if q["id"] not in seen]
        seen.update(q["id"] for q in CONDITIONAL["capital_gains"])
    if "property_gain" in missing and "ltcg_other" not in seen:
        asked += CONDITIONAL["property_sale"]
        seen.add("ltcg_other")
    if "vda_gain" in missing:
        asked += CONDITIONAL["vda"]
    if "business_kind" in missing:
        asked += CONDITIONAL["business"]
    return asked
