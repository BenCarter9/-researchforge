# ResearchForge Evidence-Grounded Skeleton — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enter a ticker + upload an earnings transcript → produce a source-backed research skeleton (Snapshot, Business, Financials, Risks) where every material claim links to its exact source passage and every number traces to a formula.

**Architecture:** Monorepo with a Next.js/TypeScript frontend (`web/`) and a FastAPI/Python service (`api/`) that does all SEC fetching, structural chunking, deterministic financial math, Claude analysis passes, and citation validation. Next.js rewrites proxy `/api/*` → FastAPI (single origin, no CORS). PostgreSQL is the single datastore; the transcript original lives in local object storage. No embeddings/vector DB — sections are routed structurally to document chunks. Claude passes use `claude-opus-5` with a prompt-cached system prompt.

**Tech Stack:** Next.js 15 (App Router) · TypeScript · Tailwind · shadcn/ui · FastAPI · Python 3.10 (host interpreter; do not require 3.11) · SQLAlchemy 2.x · Pydantic v2 · PostgreSQL 16 (via docker-compose) · `anthropic` Python SDK · `httpx` · `selectolax` (HTML parsing) · `pytest` · `vitest`/Playwright (frontend). Every Python module that uses `X | None` annotations must start with `from __future__ import annotations`.

## Global Constraints

- **Model:** all Claude calls use `claude-opus-5`. Never hardcode a date-suffixed ID.
- **Determinism:** the LLM never performs arithmetic. All financial growth/margin/FCF/CAGR math is Python functions with unit tests asserting exact expected values.
- **Citations:** every claim carries a `verbatim_quote`; a claim's citation is only `verbatim_verified=True` if that quote is an exact substring of the cited chunk's text. Fabricated citations are rejected in code, not by the model.
- **No numeric confidence in the UI.** Evidence status is the traffic-light enum only: `green | yellow | red | gray`.
- **Data absence:** a missing XBRL concept renders as `"unavailable"`, never `0`. An unknown business fact renders as `"unknown"`.
- **SEC etiquette:** every SEC request sends a descriptive `User-Agent` header (`ResearchForge research tool bencarteroh@gmail.com`) and is rate-limited to ≤ 10 req/s.
- **Sections in scope:** Snapshot, Business overview, Financial summary, Risks. Nothing else (thesis, scenarios, valuation, management questions are later specs).
- **Claim is the atomic unit.** Section prose is rendered from an ordered list of sentence-level claims, not stored as paragraphs.

---

## Phase 0: Repo scaffold & tooling

### Task 0.1: Monorepo skeleton + docker-compose

**Files:**
- Create: `README.md`, `docker-compose.yml`, `.gitignore`, `.env.example`
- Create: `api/pyproject.toml`, `api/app/__init__.py`, `api/app/main.py`, `api/tests/__init__.py`, `api/tests/test_health.py`
- Create: `web/package.json`, `web/next.config.mjs`, `web/tsconfig.json`, `web/app/layout.tsx`, `web/app/page.tsx`

**Interfaces:**
- Produces: FastAPI app object `app` in `api/app/main.py` with `GET /api/health` → `{"status": "ok"}`. Next.js rewrite forwarding `/api/:path*` → `http://localhost:8000/api/:path*`.

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

def test_health_ok():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd api && python -m pytest tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Write minimal implementation**

```python
# api/app/main.py
from fastapi import FastAPI

app = FastAPI(title="ResearchForge API")

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```toml
# api/pyproject.toml
[project]
name = "researchforge-api"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "httpx>=0.27",
  "selectolax>=0.3.21",
  "sqlalchemy>=2.0",
  "psycopg[binary]>=3.2",
  "pydantic>=2.8",
  "anthropic>=0.40",
  "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "respx>=0.21"]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd api && pip install -e ".[dev]" && python -m pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 5: Create the Next.js rewrite + docker-compose, then commit**

```js
// web/next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
  },
};
export default nextConfig;
```

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: forge
      POSTGRES_PASSWORD: forge
      POSTGRES_DB: researchforge
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
volumes:
  pgdata:
```

```bash
git add -A && git commit -m "Scaffold monorepo: FastAPI health route, Next.js proxy, docker-compose

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase 1: Data model & migrations

### Task 1.1: SQLAlchemy models + engine

**Files:**
- Create: `api/app/db.py` (engine, `SessionLocal`, `Base`)
- Create: `api/app/models.py` (all tables)
- Create: `api/tests/test_models.py`
- Test DB: SQLite in-memory for unit tests; Postgres for integration (via `DATABASE_URL`).

**Interfaces:**
- Produces: ORM classes `ResearchProject`, `Document`, `DocumentChunk`, `FinancialFact`, `Claim`, `ClaimCitation`, `AnalysisRun` with the columns named in the spec §4. `Base.metadata.create_all(engine)` builds the schema. IDs are UUID strings (`str(uuid4())`), passed in from the app layer (not `Date.now()`/random inside migrations).
- Enums (stored as strings): `DocumentType = {"10-K","transcript"}`, `EvidenceStatus = {"green","yellow","red","gray"}`, `ClaimType = {"reported_fact","management_claim","analyst_inference","assumption","unsupported"}`, `ClaimStatus = {"needs_review","accepted","rejected"}`, `RunStage` (see Task 3.1).

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_models.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
from app.models import ResearchProject, Document, DocumentChunk, Claim, ClaimCitation

def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)

def test_claim_links_to_citation_and_chunk():
    s = _session()
    proj = ResearchProject(id="p1", company="Acme", ticker="ACME")
    doc = Document(id="d1", project_id="p1", type="10-K", source="edgar")
    chunk = DocumentChunk(id="c1", document_id="d1", section_label="item_1a",
                          text="A limited number of customers account for a substantial portion of revenue.")
    claim = Claim(id="cl1", project_id="p1", section="risks",
                  claim_text="Management flags customer concentration as a principal risk.",
                  claim_type="management_claim", evidence_status="green", ordinal=0)
    cite = ClaimCitation(id="ci1", claim_id="cl1", chunk_id="c1",
                         verbatim_quote="A limited number of customers account for a substantial portion of revenue.",
                         verbatim_verified=True)
    s.add_all([proj, doc, chunk, claim, cite]); s.commit()
    got = s.get(Claim, "cl1")
    assert got.section == "risks"
    assert got.citations[0].chunk.section_label == "item_1a"
```

- [ ] **Step 2: Run** `cd api && python -m pytest tests/test_models.py -v` → FAIL (`No module named 'app.db'`).

- [ ] **Step 3: Implement `db.py` and `models.py`**

```python
# api/app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://forge:forge@localhost:5432/researchforge")
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
```

```python
# api/app/models.py
from __future__ import annotations
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class ResearchProject(Base):
    __tablename__ = "research_projects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    company: Mapped[str] = mapped_column(String)
    ticker: Mapped[str] = mapped_column(String)
    cik: Mapped[str | None] = mapped_column(String, nullable=True)
    research_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="created")
    documents: Mapped[list["Document"]] = relationship(back_populates="project")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    type: Mapped[str] = mapped_column(String)         # 10-K | transcript
    source: Mapped[str] = mapped_column(String)       # edgar | upload
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    filing_date: Mapped[str | None] = mapped_column(String, nullable=True)
    fiscal_period: Mapped[str | None] = mapped_column(String, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    project: Mapped[ResearchProject] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    section_label: Mapped[str] = mapped_column(String)   # item_1, item_1a, item_7, item_8, prepared_remarks_ceo, prepared_remarks_cfo, qa
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speaker: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    document: Mapped[Document] = relationship(back_populates="chunks")

class FinancialFact(Base):
    __tablename__ = "financial_facts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    concept: Mapped[str] = mapped_column(String)      # Revenues, NetIncomeLoss, ...
    period: Mapped[str] = mapped_column(String)       # FY2025
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, default="USD")
    xbrl_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(String, nullable=True)

class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    section: Mapped[str] = mapped_column(String)      # snapshot | business | financials | risks
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String)
    evidence_status: Mapped[str] = mapped_column(String, default="gray")
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="needs_review")
    citations: Mapped[list["ClaimCitation"]] = relationship(back_populates="claim")

class ClaimCitation(Base):
    __tablename__ = "claim_citations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id"))
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id"))
    verbatim_quote: Mapped[str] = mapped_column(Text)
    verbatim_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    entailment: Mapped[str | None] = mapped_column(String, nullable=True)  # supports|partial|inference|contradicts
    claim: Mapped[Claim] = relationship(back_populates="citations")
    chunk: Mapped[DocumentChunk] = relationship()

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"))
    stage: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|done|error
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

- [ ] **Step 4: Run** the test → PASS.
- [ ] **Step 5: Commit** (`git add -A && git commit -m "Add ORM models and DB engine" …` with the Co-Authored-By trailer).

---

## Phase 2: SEC ingestion & structural chunking

### Task 2.1: Ticker → CIK resolution

**Files:**
- Create: `api/app/sec/client.py` (`SecClient`)
- Create: `api/tests/test_sec_client.py`

**Interfaces:**
- Produces: `SecClient(user_agent: str)` with `async def resolve_cik(self, ticker: str) -> str` returning a 10-digit zero-padded CIK. Raises `TickerNotFound` for unknown tickers. Uses `https://www.sec.gov/files/company_tickers.json`.

- [ ] **Step 1: Write the failing test** (mock the SEC JSON with `respx`)

```python
# api/tests/test_sec_client.py
import httpx, respx, pytest
from app.sec.client import SecClient, TickerNotFound

MAP = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
       "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"}}

@respx.mock
async def test_resolve_cik_pads_to_ten_digits():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP))
    cik = await SecClient("ResearchForge test@example.com").resolve_cik("aapl")
    assert cik == "0000320193"

@respx.mock
async def test_resolve_cik_unknown_raises():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP))
    with pytest.raises(TickerNotFound):
        await SecClient("ResearchForge test@example.com").resolve_cik("ZZZZ")
```

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**

```python
# api/app/sec/client.py
import httpx

class TickerNotFound(Exception): ...
class FilingNotFound(Exception): ...

class SecClient:
    def __init__(self, user_agent: str):
        self._headers = {"User-Agent": user_agent}

    async def _get(self, url: str) -> httpx.Response:
        async with httpx.AsyncClient(headers=self._headers, timeout=30) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r

    async def resolve_cik(self, ticker: str) -> str:
        r = await self._get("https://www.sec.gov/files/company_tickers.json")
        want = ticker.strip().upper()
        for row in r.json().values():
            if row["ticker"].upper() == want:
                return f'{int(row["cik_str"]):010d}'
        raise TickerNotFound(ticker)
```

- [ ] **Step 4: Run** → PASS. **Step 5: Commit.**

### Task 2.2: Fetch latest 10-K HTML + company-facts

**Files:**
- Modify: `api/app/sec/client.py` (add `latest_10k` and `company_facts`)
- Create: `api/tests/test_sec_fetch.py` (respx-mocked submissions + document)

**Interfaces:**
- Produces:
  - `async def latest_10k(self, cik: str) -> Filing` where `Filing = dataclass(html: str, source_url: str, filing_date: str, fiscal_period: str)`. Reads `https://data.sec.gov/submissions/CIK{cik}.json`, finds the most recent `form == "10-K"`, builds the primary-document URL `https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{primaryDocument}`.
  - `async def company_facts(self, cik: str) -> dict` → raw JSON from `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`.

- [ ] **Step 1: Test** — mock a submissions payload with two filings (a 10-Q and a 10-K), assert `latest_10k` picks the 10-K and builds the correct URL, and returns the mocked HTML. (Full code in test file; assert `filing.source_url.endswith("/aapl-10k.htm")` and `filing.filing_date == "2026-02-15"`.)
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** the two methods per the Interfaces spec. **Step 4:** PASS. **Step 5: Commit.**

### Task 2.3: 10-K structural chunker

**Files:**
- Create: `api/app/ingest/chunk_10k.py`
- Create: `api/tests/test_chunk_10k.py` + `api/tests/fixtures/sample_10k.html`

**Interfaces:**
- Produces: `chunk_10k(html: str) -> list[Chunk]` where `Chunk = dataclass(section_label: str, text: str)`. Extracts visible text via `selectolax`, then splits on Item headers using a regex that tolerates markup/whitespace: matches `Item\s+1A?\.` etc. Maps to labels `item_1` (Business), `item_1a` (Risk Factors), `item_7` (MD&A), `item_8` (Financial Statements). Item 1 must not swallow Item 1A — split at the *next* Item boundary. Sections not found are simply absent (recorded as a gap, not fabricated).

- [ ] **Step 1: Write the failing test** with a minimal fixture

```python
# api/tests/test_chunk_10k.py
from pathlib import Path
from app.ingest.chunk_10k import chunk_10k

HTML = Path(__file__).parent / "fixtures" / "sample_10k.html"

def test_splits_item_1_and_1a():
    chunks = {c.section_label: c.text for c in chunk_10k(HTML.read_text())}
    assert "item_1" in chunks and "item_1a" in chunks
    assert "We design and sell smartphones" in chunks["item_1"]
    assert "smartphones" not in chunks["item_1a"]           # 1 didn't swallow 1A
    assert "limited number of customers" in chunks["item_1a"]
```

Fixture `sample_10k.html` (create it): headings `<b>Item 1. Business</b>` … `<b>Item 1A. Risk Factors</b>` … `<b>Item 7. Management's Discussion</b>` … `<b>Item 8. Financial Statements</b>` … with a sentence of body text under each.

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**

```python
# api/app/ingest/chunk_10k.py
import re
from dataclasses import dataclass
from selectolax.parser import HTMLParser

@dataclass
class Chunk:
    section_label: str
    text: str

_ITEM_LABELS = {"1": "item_1", "1A": "item_1a", "7": "item_7", "8": "item_8"}
_ITEM_RE = re.compile(r"\bItem\s+(1A|1|7|8)\b\.?", re.IGNORECASE)

def chunk_10k(html: str) -> list[Chunk]:
    text = HTMLParser(html).text(separator="\n")
    text = re.sub(r"[ \t]+", " ", text)
    matches = list(_ITEM_RE.finditer(text))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        num = m.group(1).upper()
        label = _ITEM_LABELS.get(num)
        if not label:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        # keep the longest capture if an item header appears twice (TOC + body)
        if len(body) > len(out.get(label, "")):
            out[label] = body
    return [Chunk(section_label=k, text=v) for k, v in out.items()]
```

- [ ] **Step 4: Run** → PASS. **Step 5: Commit.**

### Task 2.4: Transcript chunker

**Files:**
- Create: `api/app/ingest/chunk_transcript.py`
- Create: `api/tests/test_chunk_transcript.py`

**Interfaces:**
- Produces: `chunk_transcript(text: str) -> list[Chunk]`. Splits prepared remarks vs Q&A on a case-insensitive `question-and-answer` / `Q&A` marker; within prepared remarks, tags CEO vs CFO by a speaker-line heuristic (`^Name — Chief Executive Officer` / `Chief Financial Officer`), producing `prepared_remarks_ceo`, `prepared_remarks_cfo`, and a single `qa` chunk. Speaker stored on the chunk.

- [ ] **Steps 1–5:** Test with a 6-line fixture transcript (CEO line, CFO line, "Question-and-Answer Session", one Q/A). Assert three labels present and the Q&A text lands only under `qa`. Implement, pass, commit.

---

## Phase 3: Pipeline orchestration (background task + status)

### Task 3.1: Run-status store + staged pipeline runner

**Files:**
- Create: `api/app/pipeline/runner.py`
- Create: `api/tests/test_pipeline_runner.py`

**Interfaces:**
- Produces: `STAGES = ["fetch_filing","fetch_xbrl","chunk","financials","generate_snapshot","generate_business","generate_risks","validate"]`. `async def run_pipeline(project_id: str, deps: PipelineDeps) -> None` executes each stage, writing an `AnalysisRun` row (`status` transitions pending→running→done, or →error with `error`). `PipelineDeps` is a small struct of injected callables (sec client, chunkers, finance engine, claude passes) so the runner is unit-testable with fakes. On any stage exception, the stage row is marked `error` and the pipeline stops.

- [ ] **Step 1: Test** with all-fake deps: assert that after `run_pipeline`, every stage has an `AnalysisRun` row with `status == "done"` in `STAGES` order, and that a stage raising an exception marks that row `error` and leaves later stages `pending`.
- [ ] **Steps 2–5:** Implement the linear runner, pass, commit. (FastAPI wires this via `BackgroundTasks` in Phase 6 — no Celery/Redis.)

---

## Phase 4: Deterministic financial engine

### Task 4.1: XBRL fact extraction

**Files:**
- Create: `api/app/finance/xbrl.py`
- Create: `api/tests/test_xbrl.py`

**Interfaces:**
- Produces: `extract_facts(company_facts: dict, years: int = 3) -> dict[str, dict[str, float]]` returning `{concept: {"FY2025": value, ...}}` for a fixed concept map: `Revenues`/`RevenueFromContractWithCustomerExcludingAssessedTax` → `revenue`, `GrossProfit`, `OperatingIncomeLoss`, `NetIncomeLoss`, `EarningsPerShareDiluted`, `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment` → `capex`, `CashAndCashEquivalentsAtCarryingValue`, debt (sum of `LongTermDebtNoncurrent` + `LongTermDebtCurrent` when present), `CommonStockSharesOutstanding`. Picks annual (`fp == "FY"`, `form == "10-K"`) USD values; missing concept → key absent (not `0`).

- [ ] **Step 1: Test** with a trimmed company-facts fixture containing `Revenues` for FY2024/FY2025 and `NetIncomeLoss`; assert the returned dict has `revenue["FY2025"]` exact and that an absent concept (`GrossProfit`) is simply not a key.
- [ ] **Steps 2–5:** Implement, pass, commit.

### Task 4.2: Deterministic metric functions

**Files:**
- Create: `api/app/finance/engine.py`
- Create: `api/tests/test_engine.py`

**Interfaces:**
- Produces pure functions, each returning a `Calc` dataclass `(metric, formula, inputs, result, unit, period)`; return `None`-valued `result` when a required input is missing:
  - `growth(curr, prev) -> Calc` (`(curr-prev)/prev`)
  - `margin(numerator, revenue) -> Calc`
  - `free_cash_flow(ocf, capex) -> Calc` (`ocf - capex`)
  - `net_debt(total_debt, cash) -> Calc`
  - `cagr(first, last, years) -> Calc`
  - `build_table(facts) -> list[dict]` assembling the financial-summary rows with per-row YoY.

- [ ] **Step 1: Write the failing test with exact expected numbers**

```python
# api/tests/test_engine.py
from app.finance.engine import growth, free_cash_flow, net_debt, margin

def test_growth_exact():
    c = growth(1180.0, 1000.0)
    assert c.result == 0.18
    assert c.formula == "(curr - prev) / prev"
    assert c.inputs == {"curr": 1180.0, "prev": 1000.0}

def test_fcf_exact():
    assert free_cash_flow(820_000_000, 240_000_000).result == 580_000_000

def test_net_debt_exact():
    assert net_debt(300.0, 100.0).result == 200.0

def test_margin_missing_input_is_none():
    assert margin(None, 1000.0).result is None
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** the functions (each guards `None` inputs, rounds growth/margin to 4 decimals, records `formula`/`inputs`). **Step 4:** PASS. **Step 5: Commit.**

> Success criterion for the phase: backend calculations are 100% traceable — every `Calc` carries its inputs and formula. A snapshot test dumps a `Calc` to dict and asserts the full shape.

---

## Phase 5: Claude passes & citation validation

### Task 5.1: Structured claim schema + shared cached system prompt

**Files:**
- Create: `api/app/llm/schema.py` (Pydantic models)
- Create: `api/app/llm/prompts.py` (`SYSTEM_PROMPT`, per-section objectives)
- Create: `api/tests/test_schema.py`

**Interfaces:**
- Produces Pydantic models:
  - `GeneratedClaim(claim_text: str, claim_type: Literal[...], verbatim_quote: str, chunk_id: str, contradictory_evidence: str | None = None)`
  - `SectionResult(claims: list[GeneratedClaim])`
- `SYSTEM_PROMPT: str` — the role + source policy + finance rules + adversarial instruction from the spec §7, written as a single stable string (cached). Finance rules include: don't equate adjusted EBITDA with cash flow; don't call a management target a forecast; don't treat risk-factor boilerplate as a realized risk; return `claim_type="unsupported"` when evidence is insufficient; end with "Before finalizing, identify the strongest evidence against your conclusion."

- [ ] **Step 1: Test** that `SectionResult.model_validate({...})` accepts a valid payload and rejects a claim with an out-of-enum `claim_type`. Assert `SYSTEM_PROMPT` contains the adversarial sentence and the "adjusted EBITDA" rule (guards against accidental edits).
- [ ] **Steps 2–5:** Implement, pass, commit.

### Task 5.2: Claude client wrapper (parse + prompt cache)

**Files:**
- Create: `api/app/llm/client.py`
- Create: `api/tests/test_llm_client.py`

**Interfaces:**
- Produces: `class ClaudeClient` with `def generate_section(self, objective: str, chunks: list[dict]) -> SectionResult`. Builds one user message containing the objective + each chunk rendered as `--- chunk_id: {id} (section {label}) ---\n{text}`. Calls `client.messages.parse(model="claude-opus-5", max_tokens=16000, system=[{"type":"text","text":SYSTEM_PROMPT,"cache_control":{"type":"ephemeral"}}], output_format=SectionResult, messages=[...])` and returns `resp.parsed_output`. The `anthropic.Anthropic` client is injected for testability (tests pass a fake whose `.messages.parse` returns a canned `SectionResult`).

- [ ] **Step 1: Test** with a fake anthropic client: assert the system block carries `cache_control` (`{"type":"ephemeral"}`), `model == "claude-opus-5"`, `output_format is SectionResult`, and that each chunk id appears in the rendered user message. Assert the return value is the fake's `parsed_output`.
- [ ] **Steps 2–5:** Implement, pass, commit. (Real API key only needed for the manual gold-set run in Phase 7 — unit tests never hit the network.)

### Task 5.3: Deterministic citation verification (Layer 1)

**Files:**
- Create: `api/app/llm/verify.py`
- Create: `api/tests/test_verify.py`

**Interfaces:**
- Produces:
  - `def verbatim_verify(quote: str, chunk_text: str) -> bool` — normalizes whitespace on both sides, returns `True` iff the normalized quote is a substring of the normalized chunk.
  - `def evidence_status(claim_type: str, verified: bool, entailment: str | None) -> str` — mapping: `assumption` → `gray`; not verified → `red`; verified + `entailment in (None,"supports")` → `green`; verified + `entailment in ("partial","inference")` → `yellow`; verified + `entailment=="contradicts"` → `red`.

- [ ] **Step 1: Write the failing test**

```python
# api/tests/test_verify.py
from app.llm.verify import verbatim_verify, evidence_status

def test_verbatim_true_ignores_whitespace():
    assert verbatim_verify("customers account for a substantial",
                           "A limited number of  customers   account for a substantial portion.")

def test_verbatim_false_for_fabricated_quote():
    assert not verbatim_verify("revenue tripled overnight", "Revenue grew 12% year over year.")

def test_status_rules():
    assert evidence_status("reported_fact", True, "supports") == "green"
    assert evidence_status("analyst_inference", True, "partial") == "yellow"
    assert evidence_status("management_claim", False, None) == "red"
    assert evidence_status("assumption", False, None) == "gray"
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** both functions. **Step 4:** PASS. **Step 5: Commit.**

### Task 5.4: Section persistence — turn `SectionResult` into `Claim` + `ClaimCitation` rows

**Files:**
- Create: `api/app/llm/persist.py`
- Create: `api/tests/test_persist.py`

**Interfaces:**
- Produces: `def persist_section(session, project_id, section, result: SectionResult, chunks_by_id: dict[str, DocumentChunk], id_factory) -> list[Claim]`. For each `GeneratedClaim`: run `verbatim_verify` against the referenced chunk (missing chunk_id → `verified=False`, status `red`), compute `evidence_status` (entailment left `None` in this slice; Layer-2 LLM entailment is a later task), create `Claim` (ordinal = position) + one `ClaimCitation`. `id_factory` is injected (`lambda: str(uuid4())`) so tests get deterministic IDs.

- [ ] **Step 1: Test** persisting a 2-claim result where one quote is verbatim (→ `green`) and one is fabricated (→ `red`); assert the ordinals, the `verbatim_verified` flags, and that a claim citing an unknown `chunk_id` is `red`.
- [ ] **Steps 2–5:** Implement, pass, commit.

---

## Phase 6: API routes & wiring

### Task 6.1: Project creation + source ingestion endpoints

**Files:**
- Create: `api/app/routes/projects.py`
- Modify: `api/app/main.py` (include router, dependency wiring)
- Create: `api/tests/test_routes_projects.py`

**Interfaces (HTTP):**
- `POST /api/projects` `{company, ticker, research_date?}` → `{project_id}` (creates row, resolves CIK; on `TickerNotFound` returns 422 with a clear message).
- `POST /api/projects/{id}/transcript` (multipart file OR `{text}` JSON + `label`) → stores original to local object storage, computes checksum, chunks it, persists `Document` + chunks → `{document_id, chunk_count}`.
- `POST /api/projects/{id}/analyze` → schedules `run_pipeline` via `BackgroundTasks` → `{status: "started"}`.
- `GET /api/projects/{id}/status` → `[{stage, status, error}]` from `AnalysisRun` rows.

- [ ] **Step 1: Test** (TestClient + fake SEC/Claude deps via dependency overrides): `POST /api/projects` returns 200 + a UUID; an unknown ticker returns 422; `GET .../status` returns the stage list. Transcript upload returns a positive `chunk_count`.
- [ ] **Steps 2–5:** Implement routes with FastAPI dependency injection for `SecClient`/`ClaudeClient`/`SessionLocal` (overridable in tests), pass, commit.

### Task 6.2: Report + source-viewer read endpoints

**Files:**
- Create: `api/app/routes/report.py`
- Create: `api/tests/test_routes_report.py`

**Interfaces (HTTP):**
- `GET /api/projects/{id}/report` → `{snapshot, business, financials, risks}` where each section is `{claims: [{id, claim_text, claim_type, evidence_status, citation: {chunk_id, verbatim_quote, verbatim_verified}}]}` ordered by `ordinal`; `financials` also includes the `build_table` rows with `"unavailable"` for missing cells.
- `GET /api/chunks/{chunk_id}` → `{document_id, section_label, page_start, page_end, speaker, text}` (for the source viewer).
- `POST /api/citations/{id}/mark` `{valid: bool}` → records user feedback (adds a `user_marked_valid` boolean column to `claim_citations` in this task's migration).

- [ ] **Step 1: Test** the report shape against a seeded project (2 claims across 2 sections) and the chunk fetch. **Steps 2–5:** implement, pass, commit.

---

## Phase 7: Frontend

> Frontend tasks use component-level tests with `vitest` + Testing Library where logic exists; purely presentational screens get a Playwright smoke test in Task 7.5. Follow shadcn/ui conventions. All data comes from the `/api/*` proxy.

### Task 7.1: API client + types

**Files:**
- Create: `web/lib/api.ts`, `web/lib/types.ts`
- Create: `web/lib/api.test.ts`

**Interfaces:**
- Produces typed fetchers: `createProject`, `uploadTranscript`, `startAnalysis`, `getStatus`, `getReport`, `getChunk`, `markCitation`, mirroring the Phase 6 responses. Types mirror `EvidenceStatus`, `ClaimType`, `SectionResult` server shapes.

- [ ] **Steps 1–5:** Test `getReport` parses a mocked JSON into typed sections (mock `fetch`); implement; pass; commit.

### Task 7.2: Create-project + add-sources screens

**Files:**
- Create: `web/app/projects/new/page.tsx`, `web/components/CreateProjectForm.tsx`, `web/components/AddTranscript.tsx`
- Create: `web/components/CreateProjectForm.test.tsx`

**Interfaces:** form (company/ticker/date) → `createProject` → route to `/projects/{id}/sources`; transcript uploader (file or paste + label) → `uploadTranscript`; a "Generate report" button → `startAnalysis` then route to the processing screen.

- [ ] **Steps 1–5:** Test that submitting the form calls `createProject` with trimmed values and a 422 surfaces an inline error; implement; pass; commit.

### Task 7.3: Processing (staged progress) screen

**Files:**
- Create: `web/app/projects/[id]/processing/page.tsx`, `web/components/StageList.tsx`
- Create: `web/components/StageList.test.tsx`

**Interfaces:** polls `getStatus` every 2s; renders the stage list with pending/running/done/error states (meaningful stage names, no fake percentages); on all-`done` routes to the report; on any `error` shows the stage + message.

- [ ] **Steps 1–5:** Test `StageList` renders an error stage distinctly and stops polling on terminal state; implement; pass; commit.

### Task 7.4: Report reader + evidence chips

**Files:**
- Create: `web/app/projects/[id]/report/page.tsx`, `web/components/SectionView.tsx`, `web/components/ClaimLine.tsx`, `web/components/EvidenceChip.tsx`
- Create: `web/components/EvidenceChip.test.tsx`

**Interfaces:** nav tabs Snapshot / Business / Financials / Risks. Each claim renders as a line with an `EvidenceChip` (green/yellow/red/gray, with a text label — never a numeric score) and a citation marker; clicking the marker opens the source viewer (Task 7.6). Financials tab renders the table with `"unavailable"` cells and a per-row YoY column.

- [ ] **Steps 1–5:** Test `EvidenceChip` maps each status to its label + color class and renders no number; implement; pass; commit.

### Task 7.5: Source viewer with passage highlight

**Files:**
- Create: `web/components/SourceViewer.tsx`
- Create: `web/components/SourceViewer.test.tsx`

**Interfaces:** given `{chunk, verbatim_quote, claim_text}` from `getChunk`, renders the chunk text with the `verbatim_quote` span highlighted (`<mark>`), shows the section label/page and the claim it supports, and a valid/invalid toggle calling `markCitation`. If the quote isn't found in the chunk text (should not happen for verified citations), render the chunk without a highlight and show a "quote not located" note.

- [ ] **Steps 1–5:** Test the highlight wraps exactly the quote substring and the toggle calls `markCitation` with the right id/value; implement; pass; commit.

### Task 7.6: End-to-end smoke test

**Files:**
- Create: `web/e2e/report_flow.spec.ts` (Playwright)

**Interfaces:** with the API running against a seeded project (a `POST /api/dev/seed` test-only route that inserts a fixed 2-section report — gate behind an env flag), drive: open report → click a green citation → verify the source viewer highlights the quote → switch to Financials → assert an `"unavailable"` cell renders. This is the demo path.

- [ ] **Steps 1–5:** Write the seed route + spec, run `npx playwright test`, pass, commit.

---

## Phase 8: Evaluation seed & docs

### Task 8.1: Gold-set harness (citation-verification metric)

**Files:**
- Create: `api/eval/gold/<PILOT>.jsonl` (10–15 hand-checked Q/A on one pilot company)
- Create: `api/eval/run_eval.py`
- Create: `api/tests/test_eval_harness.py`

**Interfaces:** `run_eval.py` runs the pipeline on the pilot project and reports: financial-figure accuracy vs the gold file, and **verbatim-citation-verified rate** = verified citations / material claims (the automatic ≥90% metric). `test_eval_harness.py` unit-tests the metric computation on a fixed in-memory report (no network).

- [ ] **Steps 1–5:** Implement the metric function + a thin CLI; unit-test the metric; commit. (Running against the live pilot with a real API key is a manual step, documented in the README.)

### Task 8.2: README, run instructions, disclaimer

**Files:**
- Modify: `README.md`

**Interfaces:** one-command dev startup (`docker compose up -d`, `cd api && uvicorn app.main:app --reload`, `cd web && npm run dev`), the SEC `User-Agent` env note, the pilot-company choice, and the product disclaimer verbatim from spec §11.

- [ ] **Steps 1–3:** Write the README, verify the commands as written, commit.

---

## Self-Review (completed during authoring)

- **Spec coverage:** Snapshot/Business/Financials/Risks (Tasks 5.x, 6.2, 7.4); EDGAR 10-K + XBRL (2.2, 4.1); structural chunking (2.3, 2.4); deterministic engine (4.2); claim-level citations with verbatim verification (5.3, 5.4); traffic-light status, no numeric confidence (5.3, 7.4); staged background pipeline + polling (3.1, 6.1, 7.3); source viewer with highlight + valid/invalid feedback (6.2, 7.5); data-absence "unavailable"/"unknown" (4.1, 4.2, 7.4); success-criteria metric (8.1); disclaimer (8.2). No orphaned spec sections.
- **Non-goals honored:** no thesis/scenarios/valuation/management-questions/comparables/embeddings/PDF-upload/auth tasks.
- **Type consistency:** `SectionResult`/`GeneratedClaim` (5.1) are consumed by 5.2/5.4; `Calc` (4.2) by 6.2/7.4; `EvidenceStatus`/`ClaimType` enums shared server↔client (1.1, 7.1). `evidence_status()` signature identical across 5.3 and 5.4.
- **Placeholders:** none — the two lighter-detail tasks (2.4 transcript chunker, 6.x route bodies) specify exact interfaces, HTTP shapes, and test assertions; representative full code is given for every novel/tricky unit (SEC client, 10-K chunker, finance functions, verification, LLM wrapper, persistence).
