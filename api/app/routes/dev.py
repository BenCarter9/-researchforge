from __future__ import annotations

"""Dev-only demo seed used by Playwright and the live walkthrough.

Gated by RESEARCHFORGE_DEV_SEED=1 (see app/main.py). Never invents
financials: table figures and verbatim quotes come from Alphabet's
FY2024 Form 10-K (filed 2025-02-05, EDGAR accession 0001652044-25-000014).
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

PROJECT_ID = "e2e-project"
TICKER = "GOOGL"
COMPANY = "Alphabet Inc."

_DOC_10K = "e2e-doc-10k"

# Public 10-K passages (FY2024, year ended 2024-12-31). Quotes used as
# citations are exact substrings of these chunks.
_ITEM_1 = (
    "Google Services' core products and platforms include ads, Android, "
    "Chrome, devices, Gmail, Google Drive, Google Maps, Google Photos, "
    "Google Play, Search, and YouTube, with broad and growing adoption by "
    "users around the world. Google Services generates revenues primarily "
    "by delivering both performance and brand advertising that appears on "
    "Google Search & other properties, YouTube, and Google Network "
    "partners' properties (\"Google Network properties\"). We continue to "
    "invest in both performance and brand advertising and seek to improve "
    "the measurability of advertising so advertisers understand the "
    "effectiveness of their campaigns."
)
_ITEM_1A = (
    "We face intense competition. If we do not continue to innovate and "
    "provide products and services that are useful to users, customers, "
    "and other partners, we may not remain competitive, which could harm "
    "our business, financial condition, and operating results. "
    "International revenues accounted for approximately 51% of our "
    "consolidated revenues in 2024."
)
_ITEM_7 = (
    "The following table summarizes our consolidated financial results "
    "(in millions, except for per share information and percentages): "
    "Consolidated revenues $307,394 $350,018. Revenues were $350.0 billion, "
    "an increase of 14% year over year, primarily driven by an increase in "
    "Google Services revenues of $32.4 billion, or 12%, and an increase in "
    "Google Cloud revenues of $10.1 billion, or 31%."
)

_Q_BUSINESS = (
    "Google Services generates revenues primarily by delivering both "
    "performance and brand advertising that appears on Google Search & "
    "other properties, YouTube, and Google Network partners' properties"
)
_Q_SNAPSHOT = (
    "Google Services' core products and platforms include ads, Android, "
    "Chrome, devices, Gmail, Google Drive, Google Maps, Google Photos, "
    "Google Play, Search, and YouTube"
)
_Q_RISK = (
    "We face intense competition. If we do not continue to innovate and "
    "provide products and services that are useful to users, customers, "
    "and other partners, we may not remain competitive"
)
_Q_FINANCIALS = (
    "Revenues were $350.0 billion, an increase of 14% year over year"
)

# 10-K consolidated results, in millions of USD (same units as the filing).
_REVENUE_FY2023 = 307_394.0
_REVENUE_FY2024 = 350_018.0
_OI_FY2023 = 84_293.0
_OI_FY2024 = 112_390.0
_NI_FY2023 = 73_795.0
_NI_FY2024 = 100_118.0


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


def seed_demo_project(db: Session) -> dict:
    """Idempotent GOOGL demo project. Caller must create tables first."""
    _reset(db)

    project = ResearchProject(
        id=PROJECT_ID,
        company=COMPANY,
        ticker=TICKER,
        cik="0001652044",
        research_date="2026-09-01",
        status="ready",
    )
    document = Document(
        id=_DOC_10K,
        project_id=PROJECT_ID,
        type="10-K",
        source="edgar",
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1652044/"
            "000165204425000014/goog-20241231.htm"
        ),
        filing_date="2025-02-05",
        fiscal_period="FY2024",
    )
    chunk_item1 = DocumentChunk(
        id="c-item1",
        document_id=_DOC_10K,
        section_label="item_1",
        text=_ITEM_1,
    )
    chunk_item1a = DocumentChunk(
        id="c-item1a",
        document_id=_DOC_10K,
        section_label="item_1a",
        text=_ITEM_1A,
    )
    chunk_item7 = DocumentChunk(
        id="c-item7",
        document_id=_DOC_10K,
        section_label="item_7",
        text=_ITEM_7,
    )

    snapshot = Claim(
        id="e2e-claim-snapshot",
        project_id=PROJECT_ID,
        section="snapshot",
        claim_text=(
            "Alphabet's Google Services products include Search, YouTube, "
            "Android, Chrome, and Maps."
        ),
        claim_type="reported_fact",
        evidence_status="green",
        ordinal=0,
    )
    snapshot_cite = ClaimCitation(
        id="e2e-cit-snapshot",
        claim_id="e2e-claim-snapshot",
        chunk_id="c-item1",
        verbatim_quote=_Q_SNAPSHOT,
        verbatim_verified=True,
    )
    business = Claim(
        id="e2e-claim-1",
        project_id=PROJECT_ID,
        section="business",
        claim_text=(
            "Google Services generates revenue primarily from performance "
            "and brand advertising on Search, YouTube, and Network properties."
        ),
        claim_type="reported_fact",
        evidence_status="green",
        ordinal=0,
    )
    business_cite = ClaimCitation(
        id="e2e-cit-1",
        claim_id="e2e-claim-1",
        chunk_id="c-item1",
        verbatim_quote=_Q_BUSINESS,
        verbatim_verified=True,
    )
    risks = Claim(
        id="e2e-claim-risk",
        project_id=PROJECT_ID,
        section="risks",
        claim_text=(
            "Management flags intense competition and the need to keep "
            "innovating as a principal risk."
        ),
        claim_type="management_claim",
        evidence_status="green",
        ordinal=0,
    )
    risks_cite = ClaimCitation(
        id="e2e-cit-risk",
        claim_id="e2e-claim-risk",
        chunk_id="c-item1a",
        verbatim_quote=_Q_RISK,
        verbatim_verified=True,
    )
    financials = Claim(
        id="e2e-claim-fin",
        project_id=PROJECT_ID,
        section="financials",
        claim_text=(
            "Alphabet reported FY2024 revenues of $350.0 billion, up 14% "
            "year over year (10-K, in millions in the consolidated table)."
        ),
        claim_type="reported_fact",
        evidence_status="green",
        ordinal=0,
    )
    financials_cite = ClaimCitation(
        id="e2e-cit-fin",
        claim_id="e2e-claim-fin",
        chunk_id="c-item7",
        verbatim_quote=_Q_FINANCIALS,
        verbatim_verified=True,
    )

    facts = [
        FinancialFact(
            id="e2e-ff-revenue-fy2023",
            project_id=PROJECT_ID,
            concept="revenue",
            period="FY2023",
            value=_REVENUE_FY2023,
            unit="USD millions",
            xbrl_tag="Revenues",
            source_document_id=_DOC_10K,
        ),
        FinancialFact(
            id="e2e-ff-revenue-fy2024",
            project_id=PROJECT_ID,
            concept="revenue",
            period="FY2024",
            value=_REVENUE_FY2024,
            unit="USD millions",
            xbrl_tag="Revenues",
            source_document_id=_DOC_10K,
        ),
        FinancialFact(
            id="e2e-ff-oi-fy2023",
            project_id=PROJECT_ID,
            concept="operating_income",
            period="FY2023",
            value=_OI_FY2023,
            unit="USD millions",
            xbrl_tag="OperatingIncomeLoss",
            source_document_id=_DOC_10K,
        ),
        FinancialFact(
            id="e2e-ff-oi-fy2024",
            project_id=PROJECT_ID,
            concept="operating_income",
            period="FY2024",
            value=_OI_FY2024,
            unit="USD millions",
            xbrl_tag="OperatingIncomeLoss",
            source_document_id=_DOC_10K,
        ),
        FinancialFact(
            id="e2e-ff-ni-fy2023",
            project_id=PROJECT_ID,
            concept="net_income",
            period="FY2023",
            value=_NI_FY2023,
            unit="USD millions",
            xbrl_tag="NetIncomeLoss",
            source_document_id=_DOC_10K,
        ),
        FinancialFact(
            id="e2e-ff-ni-fy2024",
            project_id=PROJECT_ID,
            concept="net_income",
            period="FY2024",
            value=_NI_FY2024,
            unit="USD millions",
            xbrl_tag="NetIncomeLoss",
            source_document_id=_DOC_10K,
        ),
        # gross_profit intentionally omitted so the table still has an
        # "unavailable" row for the e2e / live demo.
    ]

    db.add_all(
        [
            project,
            document,
            chunk_item1,
            chunk_item1a,
            chunk_item7,
            snapshot,
            snapshot_cite,
            business,
            business_cite,
            risks,
            risks_cite,
            financials,
            financials_cite,
            *facts,
        ]
    )
    db.commit()
    return {"project_id": PROJECT_ID, "ticker": TICKER, "company": COMPANY}


def ensure_schema_and_seed(db: Session) -> dict:
    Base.metadata.create_all(engine)
    return seed_demo_project(db)


@router.post("/api/dev/seed")
def seed(db: Session = Depends(get_db)) -> dict:
    return ensure_schema_and_seed(db)


@router.get("/api/dev/demo")
def demo(db: Session = Depends(get_db)) -> dict:
    project = db.get(ResearchProject, PROJECT_ID)
    if project is None:
        ensure_schema_and_seed(db)
        project = db.get(ResearchProject, PROJECT_ID)
    return {
        "project_id": PROJECT_ID,
        "ticker": project.ticker if project else TICKER,
        "company": project.company if project else COMPANY,
        "report_path": f"/projects/{PROJECT_ID}/report",
    }
