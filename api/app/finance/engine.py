from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Calc:
    """A single deterministic financial calculation.

    Every result carries the formula and the exact inputs that produced it,
    so the calculation is fully auditable. `result` is `None` when a
    required input was missing — never fabricated as 0.
    """

    metric: str
    formula: str
    inputs: dict[str, float | int | None]
    result: float | None
    unit: str
    period: str | None = None

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "formula": self.formula,
            "inputs": self.inputs,
            "result": self.result,
            "unit": self.unit,
            "period": self.period,
        }


def growth(curr: float | None, prev: float | None, period: str | None = None) -> Calc:
    inputs = {"curr": curr, "prev": prev}
    formula = "(curr - prev) / prev"
    result = None
    if curr is not None and prev is not None and prev != 0:
        result = round((curr - prev) / prev, 4)
    return Calc(metric="growth", formula=formula, inputs=inputs, result=result, unit="ratio", period=period)


def margin(numerator: float | None, revenue: float | None, period: str | None = None) -> Calc:
    inputs = {"numerator": numerator, "revenue": revenue}
    formula = "numerator / revenue"
    result = None
    if numerator is not None and revenue is not None and revenue != 0:
        result = round(numerator / revenue, 4)
    return Calc(metric="margin", formula=formula, inputs=inputs, result=result, unit="ratio", period=period)


def free_cash_flow(ocf: float | None, capex: float | None, period: str | None = None) -> Calc:
    inputs = {"ocf": ocf, "capex": capex}
    formula = "ocf - capex"
    result = None
    if ocf is not None and capex is not None:
        result = ocf - capex
    return Calc(metric="free_cash_flow", formula=formula, inputs=inputs, result=result, unit="USD", period=period)


def net_debt(total_debt: float | None, cash: float | None, period: str | None = None) -> Calc:
    inputs = {"total_debt": total_debt, "cash": cash}
    formula = "total_debt - cash"
    result = None
    if total_debt is not None and cash is not None:
        result = total_debt - cash
    return Calc(metric="net_debt", formula=formula, inputs=inputs, result=result, unit="USD", period=period)


def cagr(first: float | None, last: float | None, years: float | None, period: str | None = None) -> Calc:
    inputs = {"first": first, "last": last, "years": years}
    formula = "(last / first) ** (1 / years) - 1"
    result = None
    if first is not None and first > 0 and last is not None and years is not None and years != 0:
        result = round((last / first) ** (1 / years) - 1, 4)
    return Calc(metric="cagr", formula=formula, inputs=inputs, result=result, unit="ratio", period=period)


# --- financial-summary table -------------------------------------------------

_ROWS: list[tuple[str, str]] = [
    ("Revenue", "revenue"),
    ("Gross profit", "gross_profit"),
    ("Operating income", "operating_income"),
    ("Net income", "net_income"),
    ("Diluted EPS", "eps_diluted"),
    ("Operating cash flow", "operating_cash_flow"),
    ("Capital expenditures", "capex"),
    ("Free cash flow", "free_cash_flow"),
    ("Cash", "cash"),
    ("Total debt", "total_debt"),
    ("Shares outstanding", "shares_outstanding"),
]

# Derived rows appended after the reported/fact rows. Keys are synthetic —
# they are computed in `_row_series`, not looked up as XBRL concepts.
_DERIVED_ROWS: list[tuple[str, str]] = [
    ("Gross margin", "gross_margin"),
    ("Operating margin", "operating_margin"),
    ("Net margin", "net_margin"),
    ("Net debt", "net_debt"),
    ("Revenue CAGR", "revenue_cagr"),
]

_UNAVAILABLE = "unavailable"


def _all_years(facts: dict[str, dict[str, float]]) -> list[str]:
    years: set[str] = set()
    for series in facts.values():
        years.update(series.keys())
    return sorted(years, key=lambda fy: int(fy[2:]))


def _margin_series(
    numerator_key: str, facts: dict[str, dict[str, float]]
) -> dict[str, float]:
    numerators = facts.get(numerator_key, {})
    revenue = facts.get("revenue", {})
    series: dict[str, float] = {}
    for year in set(numerators) & set(revenue):
        calc = margin(numerators[year], revenue[year], period=year)
        if calc.result is not None:
            series[year] = calc.result
    return series


def _row_series(key: str, facts: dict[str, dict[str, float]]) -> dict[str, float]:
    if key == "free_cash_flow":
        ocf = facts.get("operating_cash_flow", {})
        capex = facts.get("capex", {})
        series: dict[str, float] = {}
        for year in set(ocf) & set(capex):
            series[year] = ocf[year] - capex[year]
        return series
    if key == "gross_margin":
        return _margin_series("gross_profit", facts)
    if key == "operating_margin":
        return _margin_series("operating_income", facts)
    if key == "net_margin":
        return _margin_series("net_income", facts)
    if key == "net_debt":
        debt = facts.get("total_debt", {})
        cash = facts.get("cash", {})
        series = {}
        for year in set(debt) & set(cash):
            calc = net_debt(debt[year], cash[year], period=year)
            if calc.result is not None:
                series[year] = calc.result
        return series
    if key == "revenue_cagr":
        revenue = facts.get("revenue", {})
        if len(revenue) < 2:
            return {}
        years_sorted = sorted(revenue.keys(), key=lambda fy: int(fy[2:]))
        first_year, last_year = years_sorted[0], years_sorted[-1]
        span = int(last_year[2:]) - int(first_year[2:])
        calc = cagr(revenue[first_year], revenue[last_year], float(span), period=last_year)
        if calc.result is None:
            return {}
        # Single value on the latest FY column only.
        return {last_year: calc.result}
    return facts.get(key, {})


def _row_yoy(series: dict[str, float], years_sorted: list[str], key: str) -> tuple[float | str, dict | None]:
    # CAGR is a multi-year metric — YoY is not meaningful.
    if key == "revenue_cagr":
        return _UNAVAILABLE, None
    # YoY always ties to the table's two most-recent COLUMNS (the last two
    # entries of the ascending fiscal-year column list), using this row's
    # values for those two columns specifically. A row missing either of
    # those two columns reports "unavailable" rather than falling back to
    # an older, stale delta.
    if len(years_sorted) < 2:
        return _UNAVAILABLE, None
    latest, prior = years_sorted[-1], years_sorted[-2]
    if latest not in series or prior not in series:
        return _UNAVAILABLE, None
    calc = growth(series[latest], series[prior])
    if calc.result is None:
        return _UNAVAILABLE, None
    return calc.result, calc.to_dict()


def build_table(facts: dict[str, dict[str, float]]) -> list[dict]:
    years_sorted = _all_years(facts)
    table: list[dict] = []
    for label, key in _ROWS + _DERIVED_ROWS:
        series = _row_series(key, facts)
        values = {year: series.get(year, _UNAVAILABLE) for year in years_sorted}
        yoy, yoy_calc = _row_yoy(series, years_sorted, key)
        table.append(
            {
                "metric": label,
                "key": key,
                "values": values,
                "yoy": yoy,
                "yoy_calc": yoy_calc,
            }
        )
    return table


def render_table_text(table: list[dict]) -> str:
    """Plain-text rendering of the financial table for citation grounding.

    Stored as a DocumentChunk so Snapshot/Financials claims can cite
    supplied XBRL figures verbatim without inventing arithmetic.
    """
    if not table:
        return "Financial summary table: no facts available."

    years: list[str] = []
    seen: set[str] = set()
    for row in table:
        for year in row["values"]:
            if year not in seen:
                seen.add(year)
                years.append(year)
    years = sorted(years, key=lambda fy: int(fy[2:]))

    lines = ["Financial summary table (deterministic XBRL-derived figures):"]
    header = "Metric | " + " | ".join(years) + " | YoY"
    lines.append(header)
    for row in table:
        cells = []
        for year in years:
            val = row["values"].get(year, _UNAVAILABLE)
            cells.append(str(val))
        yoy = row["yoy"]
        lines.append(f"{row['metric']} | " + " | ".join(cells) + f" | {yoy}")
    return "\n".join(lines)
