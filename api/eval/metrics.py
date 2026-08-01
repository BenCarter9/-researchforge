"""Pure, network-free metric functions for the evaluation harness.

These compute the two automatic metrics named in the spec's success
criterion:

- citation_verified_rate / report_verified_rate: the "≥90% of material
  claims verbatim-citation-verified" metric.
- financial_accuracy: extracted XBRL facts vs a hand-checked gold set.

Nothing in this module performs I/O (no network, no filesystem) so tests
can import it freely.
"""

from __future__ import annotations

import math

_SECTIONS = ("snapshot", "business", "financials", "risks")


def _is_material(claim: dict) -> bool:
    return claim.get("claim_type") != "assumption"


def _is_verified(claim: dict) -> bool:
    citation = claim.get("citation")
    return citation is not None and citation.get("verbatim_verified") is True


def citation_verified_rate(claims: list[dict]) -> float | None:
    """Verified-citation rate over MATERIAL claims (claim_type != "assumption").

    Returns verified_material / total_material, or None if there are zero
    material claims (avoids a fabricated 1.0 from a 0/0 division).
    """
    material = [c for c in claims if _is_material(c)]
    if not material:
        return None
    verified = sum(1 for c in material if _is_verified(c))
    return verified / len(material)


def report_verified_rate(report: dict) -> float | None:
    """Flattens claims across the report's four sections and computes the
    pooled citation_verified_rate over all of them."""
    claims: list[dict] = []
    for section in _SECTIONS:
        claims.extend(report.get(section, {}).get("claims", []))
    return citation_verified_rate(claims)


def financial_accuracy(
    extracted: dict[str, dict[str, float]],
    gold: dict[str, dict[str, float]],
    rel_tol: float = 1e-9,
) -> dict:
    """Compares extracted vs gold financial facts per (concept, period).

    `total` is the number of (concept, period) entries in `gold`. A match
    requires the concept+period to be present in `extracted` and
    numerically close to the gold value (math.isclose, rel_tol). Every
    miss (mismatched value or missing entirely) is recorded in
    `mismatches`.
    """
    matched = 0
    total = 0
    mismatches: list[dict] = []

    for concept, periods in gold.items():
        for period, expected in periods.items():
            total += 1
            actual = extracted.get(concept, {}).get(period)
            if actual is not None and math.isclose(actual, expected, rel_tol=rel_tol):
                matched += 1
            else:
                mismatches.append(
                    {
                        "concept": concept,
                        "period": period,
                        "expected": expected,
                        "actual": actual,
                    }
                )

    accuracy = matched / total if total > 0 else None

    return {
        "matched": matched,
        "total": total,
        "accuracy": accuracy,
        "mismatches": mismatches,
    }
