from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import ResearchProject, Document, DocumentChunk, Claim, ClaimCitation
from app.llm.schema import GeneratedClaim, SectionResult
from app.llm.persist import persist_section


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def _make_id_factory(prefix: str = "id"):
    counter = {"n": 0}

    def factory():
        counter["n"] += 1
        return f"{prefix}{counter['n']}"

    return factory


def test_persist_section_creates_claims_and_citations():
    s = _session()
    proj = ResearchProject(id="p1", company="Acme", ticker="ACME")
    doc = Document(id="d1", project_id="p1", type="10-K", source="edgar")
    c1 = DocumentChunk(
        id="c1",
        document_id="d1",
        section_label="item_1a",
        text="A limited number of customers account for a substantial portion of revenue.",
    )
    c2 = DocumentChunk(
        id="c2",
        document_id="d1",
        section_label="item_7",
        text="Revenue grew 12%.",
    )
    s.add_all([proj, doc, c1, c2])
    s.commit()

    result = SectionResult(
        claims=[
            GeneratedClaim(
                claim_text="Customer concentration is a principal risk.",
                claim_type="management_claim",
                verbatim_quote="customers account for a substantial portion",
                chunk_id="c1",
            ),
            GeneratedClaim(
                claim_text="Revenue tripled overnight.",
                claim_type="reported_fact",
                verbatim_quote="revenue tripled overnight",
                chunk_id="c2",
            ),
            GeneratedClaim(
                claim_text="Some fabricated claim citing a nonexistent chunk.",
                claim_type="reported_fact",
                verbatim_quote="anything",
                chunk_id="does_not_exist",
            ),
        ]
    )

    chunks_by_id = {"c1": c1, "c2": c2}
    id_factory = _make_id_factory("claim")

    claims = persist_section(s, "p1", "risks", result, chunks_by_id, id_factory)

    assert len(claims) == 3
    assert [c.ordinal for c in claims] == [0, 1, 2]

    # Re-query from DB to ensure commit actually happened.
    db_claims = (
        s.query(Claim)
        .filter(Claim.project_id == "p1", Claim.section == "risks")
        .order_by(Claim.ordinal)
        .all()
    )
    assert len(db_claims) == 3

    claim_a, claim_b, claim_c = db_claims

    # Verified management_claim is yellow without Layer-2 entailment.
    assert claim_a.evidence_status == "yellow"
    assert claim_a.ordinal == 0
    assert len(claim_a.citations) == 1
    assert claim_a.citations[0].verbatim_verified is True
    assert claim_a.citations[0].chunk_id == "c1"

    assert claim_b.evidence_status == "red"
    assert claim_b.ordinal == 1
    assert len(claim_b.citations) == 1
    assert claim_b.citations[0].verbatim_verified is False
    assert claim_b.citations[0].chunk_id == "c2"

    assert claim_c.evidence_status == "red"
    assert claim_c.ordinal == 2
    assert len(claim_c.citations) == 0

    # All claims default to needs_review status per spec.
    for c in db_claims:
        assert c.status == "needs_review"

    # No orphan citations exist for the missing-chunk claim.
    all_citations = s.query(ClaimCitation).all()
    assert len(all_citations) == 2
