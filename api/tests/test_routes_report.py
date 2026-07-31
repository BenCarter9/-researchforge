from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.deps import get_db
from app.finance.engine import growth
from app.main import app
from app.models import (
    Claim,
    ClaimCitation,
    Document,
    DocumentChunk,
    FinancialFact,
    ResearchProject,
)

# --- shared in-memory sqlite DB, single connection for the whole test module ---

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_engine)
_TestingSessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _dependency_overrides():
    """Install this module's fake dependency overrides on the shared `app`
    singleton before any test in this module runs, and remove them again
    once the module's tests finish - so they never leak into other test
    modules (route-test modules for other resources share the same `app`).
    """
    prev = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(prev)


# --- seed helper -------------------------------------------------------------


def _seed():
    db = _TestingSessionLocal()
    try:
        project = ResearchProject(id="p1", company="Acme", ticker="ACME")
        document = Document(id="d1", project_id="p1", type="transcript", source="upload")
        chunk = DocumentChunk(
            id="c1",
            document_id="d1",
            section_label="prepared_remarks_cfo",
            page_start=3,
            page_end=4,
            speaker="John Smith",
            text="Revenue grew 12% year over year to $1.2 billion in the quarter.",
        )
        business_claim = Claim(
            id="cl-business",
            project_id="p1",
            section="business",
            claim_text="Revenue grew 12% year over year.",
            claim_type="reported_fact",
            evidence_status="green",
            ordinal=0,
        )
        citation = ClaimCitation(
            id="cit-1",
            claim_id="cl-business",
            chunk_id="c1",
            verbatim_quote="Revenue grew 12% year over year to $1.2 billion in the quarter.",
            verbatim_verified=True,
        )
        risks_claim = Claim(
            id="cl-risks",
            project_id="p1",
            section="risks",
            claim_text="The company faces significant competitive pressure.",
            claim_type="management_claim",
            evidence_status="gray",
            ordinal=0,
        )
        fact_2024 = FinancialFact(
            id="ff-2024", project_id="p1", concept="revenue", period="FY2024", value=900.0
        )
        fact_2025 = FinancialFact(
            id="ff-2025", project_id="p1", concept="revenue", period="FY2025", value=1200.0
        )
        db.add_all(
            [
                project,
                document,
                chunk,
                business_claim,
                citation,
                risks_claim,
                fact_2024,
                fact_2025,
            ]
        )
        db.commit()
    finally:
        db.close()

    return db


@pytest.fixture(autouse=True, scope="module")
def _seed_data(_dependency_overrides):
    """Seed the shared DB once for the whole module - the seeded rows use
    fixed ids ("p1", "cl-business", ...) so re-seeding per test would hit
    primary-key conflicts against the shared in-memory sqlite connection."""
    _seed()


# --- tests -------------------------------------------------------------------


def test_report_has_four_sections_with_ordered_claims_and_citations():
    resp = client.get("/api/projects/p1/report")
    assert resp.status_code == 200
    body = resp.json()

    assert set(body.keys()) == {"snapshot", "business", "financials", "risks"}

    business_claims = body["business"]["claims"]
    assert len(business_claims) == 1
    business_claim = business_claims[0]
    assert business_claim["id"] == "cl-business"
    assert business_claim["claim_text"] == "Revenue grew 12% year over year."
    assert business_claim["claim_type"] == "reported_fact"
    assert business_claim["evidence_status"] == "green"
    assert business_claim["citation"] is not None
    assert business_claim["citation"]["chunk_id"] == "c1"
    assert business_claim["citation"]["verbatim_verified"] is True
    assert (
        business_claim["citation"]["verbatim_quote"]
        == "Revenue grew 12% year over year to $1.2 billion in the quarter."
    )

    risks_claims = body["risks"]["claims"]
    assert len(risks_claims) == 1
    risks_claim = risks_claims[0]
    assert risks_claim["id"] == "cl-risks"
    assert risks_claim["citation"] is None

    # snapshot section has no seeded claims - still present, empty.
    assert body["snapshot"]["claims"] == []


def test_report_claims_ordered_by_ordinal():
    db = _TestingSessionLocal()
    try:
        project = ResearchProject(id="p-order", company="Ordo", ticker="ORD")
        second = Claim(
            id="cl-second",
            project_id="p-order",
            section="business",
            claim_text="Second claim.",
            claim_type="reported_fact",
            evidence_status="gray",
            ordinal=1,
        )
        first = Claim(
            id="cl-first",
            project_id="p-order",
            section="business",
            claim_text="First claim.",
            claim_type="reported_fact",
            evidence_status="gray",
            ordinal=0,
        )
        db.add_all([project, second, first])
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/projects/p-order/report")
    assert resp.status_code == 200
    claims = resp.json()["business"]["claims"]
    assert [c["id"] for c in claims] == ["cl-first", "cl-second"]


def test_report_financials_table_uses_seeded_facts_and_marks_missing_as_unavailable():
    resp = client.get("/api/projects/p1/report")
    assert resp.status_code == 200
    table = resp.json()["financials"]["table"]
    assert isinstance(table, list)
    assert len(table) > 0

    revenue_row = next(row for row in table if row["metric"] == "Revenue")
    assert revenue_row["values"]["FY2025"] == 1200.0
    assert revenue_row["values"]["FY2024"] == 900.0
    expected_yoy = growth(1200.0, 900.0).result
    assert revenue_row["yoy"] == expected_yoy

    gross_profit_row = next(row for row in table if row["metric"] == "Gross profit")
    assert gross_profit_row["values"]["FY2025"] == "unavailable"
    assert gross_profit_row["values"]["FY2024"] == "unavailable"


def test_report_financials_table_empty_when_no_facts():
    db = _TestingSessionLocal()
    try:
        db.add(ResearchProject(id="p-nofacts", company="NoFacts", ticker="NF"))
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/projects/p-nofacts/report")
    assert resp.status_code == 200
    table = resp.json()["financials"]["table"]
    assert isinstance(table, list)
    assert len(table) > 0
    for row in table:
        assert row["values"] == {}
        assert row["yoy"] == "unavailable"


def test_get_chunk_returns_full_chunk_for_source_viewer():
    resp = client.get("/api/chunks/c1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["document_id"] == "d1"
    assert body["section_label"] == "prepared_remarks_cfo"
    assert body["page_start"] == 3
    assert body["page_end"] == 4
    assert body["speaker"] == "John Smith"
    assert "Revenue grew 12%" in body["text"]


def test_get_chunk_unknown_returns_404():
    resp = client.get("/api/chunks/does-not-exist")
    assert resp.status_code == 404


def test_mark_citation_valid_persists_and_returns_ok():
    resp = client.post("/api/citations/cit-1/mark", json={"valid": True})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    db = _TestingSessionLocal()
    try:
        cit = db.get(ClaimCitation, "cit-1")
        assert cit.user_marked_valid is True
    finally:
        db.close()

    resp2 = client.post("/api/citations/cit-1/mark", json={"valid": False})
    assert resp2.status_code == 200
    db2 = _TestingSessionLocal()
    try:
        cit2 = db2.get(ClaimCitation, "cit-1")
        assert cit2.user_marked_valid is False
    finally:
        db2.close()


def test_mark_citation_unknown_returns_404():
    resp = client.post("/api/citations/does-not-exist/mark", json={"valid": True})
    assert resp.status_code == 404
