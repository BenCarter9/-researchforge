from __future__ import annotations

import dataclasses

from app.finance.engine import (
    build_table,
    cagr,
    free_cash_flow,
    growth,
    margin,
    net_debt,
)


def test_growth_exact():
    c = growth(1180.0, 1000.0)
    assert c.result == 0.18
    assert c.formula == "(curr - prev) / prev"
    assert c.inputs == {"curr": 1180.0, "prev": 1000.0}


def test_fcf_exact():
    assert free_cash_flow(820_000_000, 240_000_000).result == 580_000_000


def test_net_debt_exact():
    assert net_debt(300.0, 100.0).result == 200.0


def test_margin_missing_input_is_none():
    assert margin(None, 1000.0).result is None


def test_margin_exact():
    c = margin(250.0, 1000.0)
    assert c.result == 0.25
    assert c.formula == "numerator / revenue"
    assert c.inputs == {"numerator": 250.0, "revenue": 1000.0}


def test_growth_missing_input_is_none():
    assert growth(None, 1000.0).result is None
    assert growth(1000.0, None).result is None


def test_free_cash_flow_missing_input_is_none():
    assert free_cash_flow(None, 240_000_000).result is None
    assert free_cash_flow(820_000_000, None).result is None


def test_net_debt_missing_input_is_none():
    assert net_debt(None, 100.0).result is None
    assert net_debt(300.0, None).result is None


def test_cagr_exact():
    c = cagr(1000.0, 1210.0, 2)
    assert c.result == 0.1
    assert c.inputs == {"first": 1000.0, "last": 1210.0, "years": 2}


def test_cagr_missing_or_zero_first_or_zero_years_is_none():
    assert cagr(None, 1210.0, 2).result is None
    assert cagr(0, 1210.0, 2).result is None
    assert cagr(1000.0, 1210.0, 0).result is None


def test_cagr_negative_first_is_none_not_raising():
    # (last / first) ** (1 / years) with a negative first yields a complex
    # number in Python; this must be guarded rather than raising.
    assert cagr(-100.0, 200.0, 3).result is None


# --- Calc shape / auditability -------------------------------------------------


def test_calc_shape_snapshot():
    c = growth(1180.0, 1000.0)
    d = dataclasses.asdict(c)
    assert set(d.keys()) == {"metric", "formula", "inputs", "result", "unit", "period"}
    assert d["metric"] == "growth"
    assert d["formula"] == "(curr - prev) / prev"
    assert d["inputs"] == {"curr": 1180.0, "prev": 1000.0}
    assert d["result"] == 0.18


# --- build_table -----------------------------------------------------------


def _facts():
    return {
        "revenue": {"FY2024": 1000.0, "FY2025": 1180.0},
        "gross_profit": {"FY2025": 500.0},
    }


def test_build_table_revenue_row_values_and_yoy():
    table = build_table(_facts())
    revenue_row = next(row for row in table if row["key"] == "revenue")
    assert revenue_row["metric"] == "Revenue"
    assert revenue_row["values"]["FY2025"] == 1180.0
    assert revenue_row["values"]["FY2024"] == 1000.0
    assert revenue_row["yoy"] == 0.18
    assert revenue_row["yoy_calc"]["formula"] == "(curr - prev) / prev"
    assert revenue_row["yoy_calc"]["inputs"] == {"curr": 1180.0, "prev": 1000.0}


def test_build_table_gross_profit_missing_year_is_unavailable():
    table = build_table(_facts())
    gp_row = next(row for row in table if row["key"] == "gross_profit")
    assert gp_row["values"]["FY2024"] == "unavailable"
    assert gp_row["values"]["FY2025"] == 500.0
    # only one year present -> yoy cannot be computed
    assert gp_row["yoy"] == "unavailable"


def test_build_table_free_cash_flow_unavailable_when_inputs_missing():
    table = build_table(_facts())
    fcf_row = next(row for row in table if row["key"] == "free_cash_flow")
    assert fcf_row["metric"] == "Free cash flow"
    assert fcf_row["values"]["FY2024"] == "unavailable"
    assert fcf_row["values"]["FY2025"] == "unavailable"
    assert fcf_row["yoy"] == "unavailable"


def test_build_table_row_order_and_columns():
    table = build_table(_facts())
    labels = [row["metric"] for row in table]
    assert labels == [
        "Revenue",
        "Gross profit",
        "Operating income",
        "Net income",
        "Diluted EPS",
        "Operating cash flow",
        "Capital expenditures",
        "Free cash flow",
        "Cash",
        "Total debt",
        "Shares outstanding",
        "Gross margin",
        "Operating margin",
        "Net margin",
        "Net debt",
        "Revenue CAGR",
    ]


def test_build_table_derived_margins_and_cagr():
    facts = {
        "revenue": {"FY2023": 1000.0, "FY2024": 1100.0, "FY2025": 1210.0},
        "gross_profit": {"FY2025": 605.0},
        "operating_income": {"FY2025": 242.0},
        "net_income": {"FY2025": 121.0},
        "total_debt": {"FY2025": 400.0},
        "cash": {"FY2025": 150.0},
    }
    table = build_table(facts)
    by_key = {row["key"]: row for row in table}

    assert by_key["gross_margin"]["values"]["FY2025"] == 0.5
    assert by_key["operating_margin"]["values"]["FY2025"] == 0.2
    assert by_key["net_margin"]["values"]["FY2025"] == 0.1
    assert by_key["net_debt"]["values"]["FY2025"] == 250.0
    assert by_key["revenue_cagr"]["values"]["FY2025"] == 0.1
    assert by_key["revenue_cagr"]["values"]["FY2023"] == "unavailable"
    assert by_key["revenue_cagr"]["yoy"] == "unavailable"


def test_build_table_yoy_ties_to_newest_two_columns_not_rows_own_latest_data():
    # revenue has all three years; capex is missing the newest column
    # (FY2025). capex's yoy must be "unavailable" -- it must NOT fall back
    # to an older FY2023-vs-FY2024 delta just because that data exists.
    facts = {
        "revenue": {"FY2023": 800.0, "FY2024": 1000.0, "FY2025": 1180.0},
        "capex": {"FY2023": 100.0, "FY2024": 150.0},
    }
    table = build_table(facts)

    revenue_row = next(row for row in table if row["key"] == "revenue")
    assert revenue_row["yoy"] == growth(1180.0, 1000.0).result

    capex_row = next(row for row in table if row["key"] == "capex")
    assert capex_row["yoy"] == "unavailable"


def test_build_table_computes_fcf_when_both_present():
    facts = {
        "operating_cash_flow": {"FY2025": 820_000_000.0},
        "capex": {"FY2025": 240_000_000.0},
    }
    table = build_table(facts)
    fcf_row = next(row for row in table if row["key"] == "free_cash_flow")
    assert fcf_row["values"]["FY2025"] == 580_000_000.0
