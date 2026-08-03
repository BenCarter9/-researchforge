from __future__ import annotations

import re


def verbatim_verify(quote: str, chunk_text: str) -> bool:
    """
    Normalize whitespace on both sides and check if the normalized quote
    is a substring of the normalized chunk text.

    Normalization: collapse all runs of whitespace (spaces, tabs, newlines)
    to a single space, and strip ends.
    """
    # Normalize whitespace: replace all runs of whitespace with single space
    normalized_quote = re.sub(r'\s+', ' ', quote).strip()
    normalized_chunk = re.sub(r'\s+', ' ', chunk_text).strip()

    return normalized_quote in normalized_chunk


def evidence_status(claim_type: str, verified: bool, entailment: str | None) -> str:
    """
    Map claim type, verification status, and entailment type to a status color.

    When entailment is None (Layer-2 deferred), claim_type supplies provisional
    semantics so verified management/inference quotes are not painted green.

    Rules:
    - assumption → gray (regardless of verified/entailment)
    - unsupported → red (regardless of verified/entailment)
    - not verified → red
    - verified + entailment == "contradicts" → red
    - verified + entailment in ("partial", "inference") → yellow
    - verified + entailment in ("supports",) → green (Layer-2 override)
    - verified + entailment is None → claim_type provisional:
        reported_fact → green; management_claim / analyst_inference → yellow
    - verified + any other/unrecognized entailment → yellow (conservative;
      never default unknown/malformed entailment values to green)
    """
    if claim_type == "assumption":
        return "gray"

    if claim_type == "unsupported":
        return "red"

    if not verified:
        return "red"

    # verified is True
    if entailment == "contradicts":
        return "red"
    if entailment in ("partial", "inference"):
        return "yellow"
    if entailment == "supports":
        return "green"

    if entailment is None:
        if claim_type == "reported_fact":
            return "green"
        if claim_type in ("management_claim", "analyst_inference"):
            return "yellow"
        # Unknown claim_type with a verified quote: never default to green.
        return "yellow"

    # Unrecognized/malformed entailment: conservative fallback.
    return "yellow"
