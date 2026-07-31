from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

ClaimType = Literal[
    "reported_fact",
    "management_claim",
    "analyst_inference",
    "assumption",
    "unsupported",
]


class GeneratedClaim(BaseModel):
    claim_text: str
    claim_type: ClaimType
    verbatim_quote: str
    chunk_id: str
    contradictory_evidence: Optional[str] = None


class SectionResult(BaseModel):
    claims: list[GeneratedClaim]
