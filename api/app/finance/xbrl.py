from __future__ import annotations

_ANNUAL_FORMS = ("10-K", "10-K/A")

# target_key -> (candidate concept names in priority order, unit)
_CONCEPT_MAP: dict[str, tuple[list[str], str]] = {
    "revenue": (
        ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
        "USD",
    ),
    "gross_profit": (["GrossProfit"], "USD"),
    "operating_income": (["OperatingIncomeLoss"], "USD"),
    "net_income": (["NetIncomeLoss"], "USD"),
    "eps_diluted": (["EarningsPerShareDiluted"], "USD/shares"),
    "operating_cash_flow": (["NetCashProvidedByUsedInOperatingActivities"], "USD"),
    "capex": (["PaymentsToAcquirePropertyPlantAndEquipment"], "USD"),
    "cash": (["CashAndCashEquivalentsAtCarryingValue"], "USD"),
    "shares_outstanding": (["CommonStockSharesOutstanding"], "shares"),
}

_DEBT_CONCEPTS = ["LongTermDebtNoncurrent", "LongTermDebtCurrent"]


def _raw_concept_series(company_facts: dict, concept: str, unit: str) -> list[dict] | None:
    """Return the raw list of period entries for a concept/unit, checking
    us-gaap first then dei. None if the concept/unit isn't present at all."""
    facts = company_facts.get("facts", {})
    for taxonomy in ("us-gaap", "dei"):
        node = facts.get(taxonomy, {}).get(concept)
        if node is None:
            continue
        entries = node.get("units", {}).get(unit)
        if entries is not None:
            return entries
    return None


def _annual_series(company_facts: dict, concept: str, unit: str = "USD") -> dict[str, float]:
    """Build a fy-keyed {"FY2025": value, ...} series for a single concept,
    keeping only annual (fp == "FY", form in 10-K/10-K/A) entries and, for
    duplicate fiscal years, the entry with the greatest `end` date."""
    entries = _raw_concept_series(company_facts, concept, unit)
    if not entries:
        return {}

    best_by_fy: dict[int, dict] = {}
    for entry in entries:
        if entry.get("fp") != "FY" or entry.get("form") not in _ANNUAL_FORMS:
            continue
        fy = entry.get("fy")
        if fy is None:
            continue
        current_best = best_by_fy.get(fy)
        if current_best is None or entry.get("end", "") > current_best.get("end", ""):
            best_by_fy[fy] = entry

    return {f"FY{fy}": entry["val"] for fy, entry in best_by_fy.items()}


def _limit_to_recent_years(series: dict[str, float], years: int) -> dict[str, float]:
    if len(series) <= years:
        return series
    # Sort by fiscal year descending (parsed from the "FY{fy}" key) and keep
    # only the most recent `years` entries.
    ordered = sorted(series.items(), key=lambda kv: int(kv[0][2:]), reverse=True)
    return dict(ordered[:years])


def extract_facts(company_facts: dict, years: int = 3) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}

    for target_key, (candidates, unit) in _CONCEPT_MAP.items():
        series: dict[str, float] = {}
        for concept in candidates:
            series = _annual_series(company_facts, concept, unit)
            if series:
                break
        if series:
            result[target_key] = _limit_to_recent_years(series, years)

    # total_debt: sum LongTermDebtNoncurrent + LongTermDebtCurrent per fy.
    # Include a year if at least one component has a value for it (missing
    # component treated as 0); omit total_debt entirely if neither concept
    # has any data at all.
    component_series = [_annual_series(company_facts, concept, "USD") for concept in _DEBT_CONCEPTS]
    if any(component_series):
        all_fys = set()
        for series in component_series:
            all_fys.update(series.keys())
        debt_series = {
            fy: sum(series.get(fy, 0) for series in component_series) for fy in all_fys
        }
        result["total_debt"] = _limit_to_recent_years(debt_series, years)

    return result
