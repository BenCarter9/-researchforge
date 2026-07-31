from __future__ import annotations

from app.finance.xbrl import extract_facts


def _entry(end, val, fy, fp="FY", form="10-K"):
    return {"end": end, "val": val, "fy": fy, "fp": fp, "form": form}


FIXTURE = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "units": {
                    "USD": [
                        _entry("2024-09-28", 383285000000, 2024),
                        _entry("2025-09-27", 410000000000, 2025),
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        _entry("2025-09-27", 99000000000, 2025),
                    ]
                }
            },
        },
        "dei": {},
    },
}


def test_revenue_exact_value_for_fy2025():
    facts = extract_facts(FIXTURE)
    assert facts["revenue"]["FY2025"] == 410000000000


def test_net_income_exact_value_for_fy2025():
    facts = extract_facts(FIXTURE)
    assert facts["net_income"]["FY2025"] == 99000000000


def test_missing_concept_is_absent_key_not_zero():
    facts = extract_facts(FIXTURE)
    assert "gross_profit" not in facts


def test_quarterly_entry_excluded():
    fixture = {
        "cik": 1,
        "entityName": "Test Co",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            _entry("2025-06-28", 111, 2025, fp="Q3", form="10-Q"),
                            _entry("2025-09-27", 410000000000, 2025, fp="FY", form="10-K"),
                        ]
                    }
                }
            },
            "dei": {},
        },
    }
    facts = extract_facts(fixture)
    # Only the FY/10-K entry should be reflected; the quarterly one must not
    # sneak in as a duplicate/overwritten value.
    assert facts["revenue"]["FY2025"] == 410000000000
    assert len(facts["revenue"]) == 1


def test_total_debt_sums_current_and_noncurrent_components():
    fixture = {
        "cik": 1,
        "entityName": "Test Co",
        "facts": {
            "us-gaap": {
                "LongTermDebtNoncurrent": {
                    "units": {
                        "USD": [
                            _entry("2025-09-27", 90000000000, 2025),
                        ]
                    }
                },
                "LongTermDebtCurrent": {
                    "units": {
                        "USD": [
                            _entry("2025-09-27", 10000000000, 2025),
                        ]
                    }
                },
            },
            "dei": {},
        },
    }
    facts = extract_facts(fixture)
    assert facts["total_debt"]["FY2025"] == 100000000000


def test_total_debt_treats_missing_component_as_zero_but_present_if_one_exists():
    fixture = {
        "cik": 1,
        "entityName": "Test Co",
        "facts": {
            "us-gaap": {
                "LongTermDebtNoncurrent": {
                    "units": {
                        "USD": [
                            _entry("2025-09-27", 90000000000, 2025),
                        ]
                    }
                },
            },
            "dei": {},
        },
    }
    facts = extract_facts(fixture)
    assert facts["total_debt"]["FY2025"] == 90000000000


def test_total_debt_absent_when_neither_component_exists():
    facts = extract_facts(FIXTURE)
    assert "total_debt" not in facts


def test_same_fy_duplicates_keep_latest_end_value():
    fixture = {
        "cik": 1,
        "entityName": "Test Co",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            # Earlier-filed restatement for FY2025 with a stale end date
                            _entry("2025-06-30", 400000000000, 2025),
                            # Later restatement, greater end date, should win
                            _entry("2025-09-27", 410000000000, 2025),
                        ]
                    }
                }
            },
            "dei": {},
        },
    }
    facts = extract_facts(fixture)
    assert facts["revenue"]["FY2025"] == 410000000000
    assert len(facts["revenue"]) == 1
