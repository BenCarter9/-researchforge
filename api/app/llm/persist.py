from __future__ import annotations

from typing import Callable

from app.llm.schema import SectionResult
from app.llm.verify import evidence_status, verbatim_verify
from app.models import Claim, ClaimCitation, DocumentChunk


def persist_section(
    session,
    project_id: str,
    section: str,
    result: SectionResult,
    chunks_by_id: dict[str, DocumentChunk],
    id_factory: Callable[[], str],
) -> list[Claim]:
    """
    Turn a SectionResult's GeneratedClaims into persisted Claim + ClaimCitation
    rows.

    Layer-2 LLM entailment is a later task: entailment is always None here, so
    evidence_status is derived purely from claim_type and verbatim verification.

    A GeneratedClaim referencing an unknown chunk_id is treated as unverified
    (verified=False) and gets no ClaimCitation row, since a citation row would
    violate the chunk_id foreign key.
    """
    claims: list[Claim] = []

    for ordinal, gc in enumerate(result.claims):
        chunk = chunks_by_id.get(gc.chunk_id)

        if chunk is not None:
            verified = verbatim_verify(gc.verbatim_quote, chunk.text)
        else:
            verified = False

        entailment = None
        status = evidence_status(gc.claim_type, verified, entailment)

        claim = Claim(
            id=id_factory(),
            project_id=project_id,
            section=section,
            claim_text=gc.claim_text,
            claim_type=gc.claim_type,
            evidence_status=status,
            ordinal=ordinal,
            status="needs_review",
        )
        session.add(claim)
        claims.append(claim)

        if chunk is not None:
            citation = ClaimCitation(
                id=id_factory(),
                claim_id=claim.id,
                chunk_id=gc.chunk_id,
                verbatim_quote=gc.verbatim_quote,
                verbatim_verified=verified,
                entailment=None,
            )
            session.add(citation)

    session.commit()
    return claims
