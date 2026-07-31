from __future__ import annotations

"""Dev-only route used exclusively by the Playwright e2e smoke test
(web/e2e/report_flow.spec.ts). Seeds a fixed, deterministic project so the
e2e can drive the demo path without running the real Claude pipeline.

This module is only wired into the app (see app/main.py) when
RESEARCHFORGE_DEV_SEED=1 is set in the environment - it must never be
reachable in a normal deployment.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, engine
from app.deps import get_db
from app.models import (
    Claim,
    ClaimCitation,
    Document,
    DocumentChunk,
    FinancialFact,
    ResearchProject,
)

router = APIRouter()

# Fixed, deterministic ids so re-running the seed against a fresh (or
# stale) e2e database is idempotent and the Playwright spec can hardcode
# them.
PROJECT_ID = "e2e-project"
_DOCUMENT_ID = "e2e-doc-1"
_CHUNK_ID = "c1"
_CLAIM_ID = "e2e-claim-1"
_CITATION_ID = "e2e-cit-1"

_CHUNK_TEXT = (
    "North American revenue increased 18% in FY2025, driven by new store "
    "openings."
)
_VERBATIM_QUOTE = "North American revenue increased 18% in FY2025"


def _reset(db: Session) -> None:
    """Deletes any rows left over from a previous seed call so the route is
    idempotent across re-runs (e.g. `playwright test` run twice locally
    against the same e2e.db file)."""
    claims = db.scalars(select(Claim).where(Claim.project_id == PROJECT_ID)).all()
    for claim in claims:
        for citation in list(claim.citations):
            db.delete(citation)
        db.delete(claim)

    documents = db.scalars(
        select(Document).where(Document.project_id == PROJECT_ID)
    ).all()
    for document in documents:
        for chunk in list(document.chunks):
            db.delete(chunk)
        db.delete(document)

    facts = db.scalars(
        select(FinancialFact).where(FinancialFact.project_id == PROJECT_ID)
    ).all()
    for fact in facts:
        db.delete(fact)

    project = db.get(ResearchProject, PROJECT_ID)
    if project is not None:
        db.delete(project)

    db.commit()


@router.post("/api/dev/seed")
def seed(db: Session = Depends(get_db)) -> dict:
    # The e2e runs against a throwaway sqlite file with no migrations
    # applied, so make sure the schema exists before writing to it.
    Base.metadata.create_all(engine)

    _reset(db)

    project = ResearchProject(
        id=PROJECT_ID, company="Demo Corp", ticker="DEMO", status="created"
    )
    document = Document(
        id=_DOCUMENT_ID,
        project_id=PROJECT_ID,
        type="10-K",
        source="edgar",
    )
    chunk = DocumentChunk(
        id=_CHUNK_ID,
        document_id=_DOCUMENT_ID,
        section_label="item_7",
        text=_CHUNK_TEXT,
    )
    claim = Claim(
        id=_CLAIM_ID,
        project_id=PROJECT_ID,
        section="business",
        claim_text="North American revenue increased 18% in FY2025.",
        claim_type="reported_fact",
        evidence_status="green",
        ordinal=0,
    )
    citation = ClaimCitation(
        id=_CITATION_ID,
        claim_id=_CLAIM_ID,
        chunk_id=_CHUNK_ID,
        verbatim_quote=_VERBATIM_QUOTE,
        verbatim_verified=True,
    )
    # "revenue" has both years so the Financials table renders real
    # numbers; "gross_profit" is intentionally never seeded so its row
    # renders "unavailable" cells for the e2e to assert on.
    revenue_fy2024 = FinancialFact(
        id="e2e-ff-revenue-fy2024",
        project_id=PROJECT_ID,
        concept="revenue",
        period="FY2024",
        value=900.0,
    )
    revenue_fy2025 = FinancialFact(
        id="e2e-ff-revenue-fy2025",
        project_id=PROJECT_ID,
        concept="revenue",
        period="FY2025",
        value=1200.0,
    )

    db.add_all(
        [
            project,
            document,
            chunk,
            claim,
            citation,
            revenue_fy2024,
            revenue_fy2025,
        ]
    )
    db.commit()

    return {"project_id": PROJECT_ID}
