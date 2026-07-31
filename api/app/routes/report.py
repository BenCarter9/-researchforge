from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.finance.engine import build_table
from app.models import Claim, ClaimCitation, DocumentChunk, FinancialFact

router = APIRouter()

_SECTIONS = ("snapshot", "business", "financials", "risks")


def _citation_dict(citation: ClaimCitation | None) -> dict | None:
    if citation is None:
        return None
    return {
        "chunk_id": citation.chunk_id,
        "verbatim_quote": citation.verbatim_quote,
        "verbatim_verified": citation.verbatim_verified,
    }


def _claim_dict(claim: Claim) -> dict:
    first_citation = claim.citations[0] if claim.citations else None
    return {
        "id": claim.id,
        "claim_text": claim.claim_text,
        "claim_type": claim.claim_type,
        "evidence_status": claim.evidence_status,
        "citation": _citation_dict(first_citation),
    }


def _section(db: Session, project_id: str, section: str) -> dict:
    claims = db.scalars(
        select(Claim)
        .where(Claim.project_id == project_id, Claim.section == section)
        .order_by(Claim.ordinal.asc())
    ).all()
    return {"claims": [_claim_dict(c) for c in claims]}


@router.get("/api/projects/{project_id}/report")
def get_report(project_id: str, db: Session = Depends(get_db)) -> dict:
    facts: dict[str, dict[str, float]] = {}
    fact_rows = db.scalars(
        select(FinancialFact).where(FinancialFact.project_id == project_id)
    ).all()
    for fact in fact_rows:
        facts.setdefault(fact.concept, {})[fact.period] = fact.value

    financials = _section(db, project_id, "financials")
    financials["table"] = build_table(facts)

    return {
        "snapshot": _section(db, project_id, "snapshot"),
        "business": _section(db, project_id, "business"),
        "financials": financials,
        "risks": _section(db, project_id, "risks"),
    }


@router.get("/api/chunks/{chunk_id}")
def get_chunk(chunk_id: str, db: Session = Depends(get_db)) -> dict:
    chunk = db.get(DocumentChunk, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="chunk not found")
    return {
        "document_id": chunk.document_id,
        "section_label": chunk.section_label,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "speaker": chunk.speaker,
        "text": chunk.text,
    }


class CitationMark(BaseModel):
    valid: bool


@router.post("/api/citations/{citation_id}/mark")
def mark_citation(
    citation_id: str, payload: CitationMark, db: Session = Depends(get_db)
) -> dict:
    citation = db.get(ClaimCitation, citation_id)
    if citation is None:
        raise HTTPException(status_code=404, detail="citation not found")
    citation.user_marked_valid = payload.valid
    db.commit()
    return {"ok": True}
