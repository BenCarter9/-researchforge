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

    Rules:
    - assumption → gray (regardless of verified/entailment)
    - not verified → red
    - verified + entailment in (None, "supports") → green
    - verified + entailment in ("partial", "inference") → yellow
    - verified + entailment == "contradicts" → red
    - verified + any other/unrecognized entailment → yellow (conservative;
      never default unknown/malformed entailment values to green)
    """
    if claim_type == "assumption":
        return "gray"

    if not verified:
        return "red"

    # verified is True
    if entailment in (None, "supports"):
        return "green"
    elif entailment == "contradicts":
        return "red"

    # entailment in ("partial", "inference"), or any unrecognized/malformed
    # value: conservative fallback. A trust signal must never default an
    # unknown entailment to the most-trusting color.
    return "yellow"
