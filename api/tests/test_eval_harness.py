from __future__ import annotations

from eval.metrics import citation_verified_rate, financial_accuracy, report_verified_rate


def _claim(claim_type: str, citation: dict | None) -> dict:
    return {
        "id": f"cl-{claim_type}-{id(citation)}",
        "claim_text": "irrelevant text",
        "claim_type": claim_type,
        "evidence_status": "green",
        "citation": citation,
    }


def _verified_citation() -> dict:
    return {
        "id": "cit-1",
        "chunk_id": "c1",
        "verbatim_quote": "quote",
        "verbatim_verified": True,
    }


def _unverified_citation() -> dict:
    return {
        "id": "cit-2",
        "chunk_id": "c2",
        "verbatim_quote": "quote",
        "verbatim_verified": False,
    }


# --- citation_verified_rate ---------------------------------------------


def test_citation_verified_rate_over_material_claims_only():
    claims = [
        _claim("reported_fact", _verified_citation()),
        _claim("management_claim", _verified_citation()),
        _claim("analyst_inference", _unverified_citation()),
        # assumption claim has no citation at all and must be excluded
        # from both numerator and denominator.
        _claim("assumption", None),
    ]

    rate = citation_verified_rate(claims)

    assert rate == 2 / 3


def test_citation_verified_rate_absent_citation_counts_as_unverified():
    claims = [
        _claim("reported_fact", _verified_citation()),
        _claim("reported_fact", None),
    ]

    rate = citation_verified_rate(claims)

    assert rate == 0.5


def test_citation_verified_rate_no_material_claims_returns_none():
    claims = [
        _claim("assumption", None),
        _claim("assumption", _verified_citation()),
    ]

    rate = citation_verified_rate(claims)

    assert rate is None


def test_citation_verified_rate_empty_list_returns_none():
    assert citation_verified_rate([]) is None


# --- report_verified_rate -------------------------------------------------


def test_report_verified_rate_pools_claims_across_sections():
    report = {
        "snapshot": {"claims": []},
        "business": {
            "claims": [
                _claim("reported_fact", _verified_citation()),
                _claim("management_claim", _unverified_citation()),
            ]
        },
        "financials": {"claims": [], "table": []},
        "risks": {
            "claims": [
                _claim("reported_fact", _verified_citation()),
                _claim("assumption", None),
            ]
        },
    }

    rate = report_verified_rate(report)

    # 3 material claims total (assumption excluded), 2 verified.
    assert rate == 2 / 3


def test_report_verified_rate_no_material_claims_returns_none():
    report = {
        "snapshot": {"claims": [_claim("assumption", None)]},
        "business": {"claims": []},
        "financials": {"claims": [], "table": []},
        "risks": {"claims": []},
    }

    assert report_verified_rate(report) is None


# --- financial_accuracy ---------------------------------------------------


def test_financial_accuracy_exact_match():
    extracted = {"revenue": {"FY2025": 1200.0}}
    gold = {"revenue": {"FY2025": 1200.0}}

    result = financial_accuracy(extracted, gold)

    assert result == {
        "matched": 1,
        "total": 1,
        "accuracy": 1.0,
        "mismatches": [],
    }


def test_financial_accuracy_value_mismatch_recorded():
    extracted = {"revenue": {"FY2025": 1100.0}}
    gold = {"revenue": {"FY2025": 1200.0}}

    result = financial_accuracy(extracted, gold)

    assert result["matched"] == 0
    assert result["total"] == 1
    assert result["accuracy"] == 0.0
    assert result["mismatches"] == [
        {
            "concept": "revenue",
            "period": "FY2025",
            "expected": 1200.0,
            "actual": 1100.0,
        }
    ]


def test_financial_accuracy_missing_concept_counts_as_miss_with_none_actual():
    extracted = {}
    gold = {"revenue": {"FY2025": 1200.0}}

    result = financial_accuracy(extracted, gold)

    assert result["matched"] == 0
    assert result["total"] == 1
    assert result["accuracy"] == 0.0
    assert result["mismatches"] == [
        {
            "concept": "revenue",
            "period": "FY2025",
            "expected": 1200.0,
            "actual": None,
        }
    ]


def test_financial_accuracy_mixed_match_mismatch_and_missing():
    extracted = {
        "revenue": {"FY2025": 1200.0, "FY2024": 999.0},
        "net_income": {"FY2025": 50.0},
    }
    gold = {
        "revenue": {"FY2025": 1200.0, "FY2024": 900.0},
        "net_income": {"FY2025": 50.0},
        "eps_diluted": {"FY2025": 2.5},
    }

    result = financial_accuracy(extracted, gold)

    assert result["total"] == 4
    assert result["matched"] == 2
    assert result["accuracy"] == 0.5
    assert {
        "concept": "revenue",
        "period": "FY2024",
        "expected": 900.0,
        "actual": 999.0,
    } in result["mismatches"]
    assert {
        "concept": "eps_diluted",
        "period": "FY2025",
        "expected": 2.5,
        "actual": None,
    } in result["mismatches"]
    assert len(result["mismatches"]) == 2


def test_financial_accuracy_empty_gold_returns_none_accuracy():
    result = financial_accuracy({}, {})

    assert result == {
        "matched": 0,
        "total": 0,
        "accuracy": None,
        "mismatches": [],
    }


def test_financial_accuracy_respects_rel_tol():
    extracted = {"revenue": {"FY2025": 1200.0000001}}
    gold = {"revenue": {"FY2025": 1200.0}}

    result = financial_accuracy(extracted, gold, rel_tol=1e-6)

    assert result["matched"] == 1
    assert result["mismatches"] == []
