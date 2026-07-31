from __future__ import annotations

import os
import tempfile

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.deps import get_claude_client, get_db, get_sec_client
from app.llm.schema import GeneratedClaim, SectionResult
from app.main import app
from app.pipeline.runner import STAGES
from app.sec.client import Filing, TickerNotFound

# Route the transcript-upload storage writes to a throwaway temp dir instead
# of the repo's real api/storage directory.
os.environ["STORAGE_DIR"] = tempfile.mkdtemp(prefix="researchforge-test-storage-")

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


# --- fakes ---------------------------------------------------------------


class _FakeSecClient:
    _KNOWN = {"AAPL": "0000320193"}

    async def resolve_cik(self, ticker: str) -> str:
        cik = self._KNOWN.get(ticker.strip().upper())
        if cik is None:
            raise TickerNotFound(ticker)
        return cik

    async def latest_10k(self, cik: str) -> Filing:
        html = (
            "<html><body>"
            "<p>Item 1. Business. Acme Corp designs and sells widgets globally, "
            "serving enterprise and consumer customers across many regions.</p>"
            "<p>Item 1A. Risk Factors. The company faces significant competition "
            "and supply chain risk that could harm its business.</p>"
            "</body></html>"
        )
        return Filing(
            html=html,
            source_url="https://example.com/10k",
            filing_date="2026-01-01",
            fiscal_period="FY2025",
        )

    async def company_facts(self, cik: str) -> dict:
        return {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {
                                    "fy": 2025,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "end": "2025-12-31",
                                    "val": 1000.0,
                                },
                                {
                                    "fy": 2024,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "end": "2024-12-31",
                                    "val": 900.0,
                                },
                            ]
                        }
                    }
                }
            }
        }


class _FakeClaudeClient:
    def generate_section(self, objective: str, chunks: list[dict]) -> SectionResult:
        if not chunks:
            return SectionResult(claims=[])
        chunk = chunks[0]
        return SectionResult(
            claims=[
                GeneratedClaim(
                    claim_text="Fake generated claim for testing.",
                    claim_type="reported_fact",
                    verbatim_quote=chunk["text"],
                    chunk_id=chunk["id"],
                )
            ]
        )


def _override_get_sec_client() -> _FakeSecClient:
    return _FakeSecClient()


def _override_get_claude_client() -> _FakeClaudeClient:
    return _FakeClaudeClient()


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_sec_client] = _override_get_sec_client
app.dependency_overrides[get_claude_client] = _override_get_claude_client

client = TestClient(app)


# --- tests -----------------------------------------------------------------


def test_create_project_returns_uuid_project_id():
    resp = client.post("/api/projects", json={"company": "Acme", "ticker": "AAPL"})
    assert resp.status_code == 200
    body = resp.json()
    assert "project_id" in body
    project_id = body["project_id"]
    assert isinstance(project_id, str)
    assert len(project_id) >= 32
    assert project_id.count("-") == 4  # uuid4-ish


def test_create_project_unknown_ticker_returns_422():
    resp = client.post("/api/projects", json={"company": "Nope", "ticker": "ZZZZ"})
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body


def test_upload_transcript_json_returns_positive_chunk_count():
    create_resp = client.post("/api/projects", json={"company": "Acme", "ticker": "AAPL"})
    project_id = create_resp.json()["project_id"]

    transcript_text = (
        "Jane Doe — Chief Executive Officer\n"
        "Thank you all for joining. Revenue grew nicely this quarter.\n"
        "John Smith — Chief Financial Officer\n"
        "Our margins improved as well.\n"
        "Question-and-Answer Session\n"
        "Operator: We will now begin the Q&A session.\n"
        "Analyst: Can you comment on guidance?\n"
    )

    resp = client.post(
        f"/api/projects/{project_id}/transcript",
        json={"text": transcript_text, "label": "Q3 earnings call"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "document_id" in body
    assert isinstance(body["chunk_count"], int)
    assert body["chunk_count"] >= 1


def test_status_empty_before_analyze_then_populated_after():
    create_resp = client.post("/api/projects", json={"company": "Acme", "ticker": "AAPL"})
    project_id = create_resp.json()["project_id"]

    status_resp = client.get(f"/api/projects/{project_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json() == []

    analyze_resp = client.post(f"/api/projects/{project_id}/analyze")
    assert analyze_resp.status_code == 200
    assert analyze_resp.json() == {"status": "started"}

    # TestClient runs BackgroundTasks synchronously before returning the
    # response, so by now the pipeline has already run to completion (or
    # to its first error) against the fakes.
    status_resp = client.get(f"/api/projects/{project_id}/status")
    assert status_resp.status_code == 200
    rows = status_resp.json()
    assert isinstance(rows, list)
    assert len(rows) > 0
    for row in rows:
        assert "stage" in row
        assert "status" in row
        assert "error" in row

    by_stage = {row["stage"]: row for row in rows}

    # At minimum, the deterministic early stages must not have errored.
    for stage in ("fetch_filing", "fetch_xbrl", "chunk", "financials"):
        assert by_stage[stage]["status"] == "done", f"{stage}: {by_stage[stage]}"

    # With well-formed fakes for every dependency, the whole pipeline
    # should complete end to end.
    assert set(by_stage.keys()) == set(STAGES)
    for stage in STAGES:
        assert by_stage[stage]["status"] == "done", f"{stage}: {by_stage[stage]}"
