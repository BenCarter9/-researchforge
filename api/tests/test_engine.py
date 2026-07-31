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
    ]


def test_build_table_computes_fcf_when_both_present():
    facts = {
        "operating_cash_flow": {"FY2025": 820_000_000.0},
        "capex": {"FY2025": 240_000_000.0},
    }
    table = build_table(facts)
    fcf_row = next(row for row in table if row["key"] == "free_cash_flow")
    assert fcf_row["values"]["FY2025"] == 580_000_000.0
