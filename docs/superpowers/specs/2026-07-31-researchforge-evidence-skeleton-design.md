# ResearchForge — First Slice Design: "Evidence-Grounded Skeleton"

**Date:** 2026-07-31
**Status:** Approved design, pre-implementation
**Author:** Ben Carter (with Claude)

---

## 1. Purpose & positioning

ResearchForge converts primary-source company documents into an **evidence-grounded, editable equity
research product** — every material claim traceable to a source. It is a research *copilot*, not an
autonomous investment manager, and it does **not** issue buy/sell recommendations.

This spec covers only the **first slice**: an "evidence-grounded skeleton" that proves the single most
important differentiator — **claim-level citations** — end to end, while being a compelling demo on its own.

**One-line promise for the slice:**
> Enter a ticker and add an earnings transcript → get a source-backed research skeleton where every
> material claim links to its exact supporting passage, and every number is traceable to a formula and
> a source.

### Project context
- **Primary goal:** Portfolio-first, but must genuinely work on a real filing. Optimize for a clean,
  demoable engineering story with a credible accuracy bar (not bulletproof on every edge case).
- Greenfield: `/Users/bencarter/ResearchForge` is empty, not yet a git repo.

---

## 2. Scope

### In scope (this slice)
1. Create a research project (company, ticker, research date).
2. Fetch the latest **10-K** (HTML) and **XBRL company-facts** from SEC EDGAR by ticker.
3. Add an earnings-call **transcript** by upload/paste (user-labeled, authorized use).
4. Structural chunking of both documents with stable chunk IDs + metadata.
5. Deterministic **financial summary** from SEC XBRL (all math in code).
6. Generate four report sections: **Snapshot, Business overview, Financial summary, Risks (ranked).**
7. **Claim-level citations** with two-layer validation (deterministic verbatim check + optional LLM
   entailment), rendered as a traffic-light evidence status.
8. **Report reader** UI and **source viewer** with passage highlighting.

### Explicit non-goals (deferred to later specs)
Thesis pillars · bull/base/bear scenarios · valuation · management questions · comparables ·
cross-document contradiction detection · section editing/regeneration · arbitrary PDF upload
(investor decks) · news ingestion · multi-company workspaces · real authentication · vector search /
embeddings · numeric AI "confidence scores" · quantified risk probability/impact scoring.

---

## 3. Architecture

Monorepo, two deployables, one datastore.

```
ResearchForge/
├─ web/          # Next.js + TypeScript + Tailwind + shadcn/ui
├─ api/          # FastAPI (Python) — ingestion, SEC, Claude passes, validation
├─ docker-compose.yml   # web + api + postgres
└─ docs/
```

- **`web/`** — UI, project/document CRUD proxied to the API, report reader, source viewer with
  passage highlighting. Uses **Next.js rewrites** to proxy `/api/*` → FastAPI, so the browser sees a
  **single origin** (no CORS) in dev and prod.
- **`api/`** — all heavy lifting: SEC fetch, document parsing/chunking, deterministic finance engine,
  Claude analysis passes, citation validation. This is the primary Python/AI showcase.
- **PostgreSQL** — single source of truth (JSONB used for structured claim/citation payloads).
- **Local object storage** — the transcript original (checksum recorded); swappable for S3 later.
- **Claude** — AI passes, with **prompt caching** on the shared system prompt.
- **No embeddings / vector DB** in this slice (Approach B: structural routing + long context). A vector
  column can be added later without reshaping the schema.

### Key architectural decisions
| Decision | Choice | Why |
|---|---|---|
| Document→cited-claim | **Structural routing + long context (Approach B)** | Fewest moving parts to a *correct* cited demo on two docs; drops in a retrieval layer later. |
| 10-K source | **SEC EDGAR HTML fetch by ticker** | Removes the largest extraction risk (PDF parsing); strengthens the primary-source story. |
| Financial figures | **SEC XBRL company-facts API** | Higher accuracy + less work than LLM extraction; cleanly separates reported facts from AI narrative. |
| Citation validation | **Deterministic verbatim check, then optional LLM entailment** | Kills fabricated citations for free; yields a measurable metric; cheaper than a full second LLM pass. |
| Confidence signal | **Traffic-light evidence status, no numeric score** | Avoids the "fake precision" the blueprint itself warns against. |
| Processing | **FastAPI background task + status polling** | Avoids HTTP timeouts and gives staged progress without Celery/Redis (premature). |

---

## 4. Data model (slice-scoped)

The **claim — not the paragraph — is the atomic unit** of the report. Sentence-level claims render *as*
the section prose.

- `research_projects` — id, company, ticker, cik, research_date, status.
- `documents` — id, project_id, type (`10-K` | `transcript`), source (`edgar` | `upload`),
  source_url, filing_date, fiscal_period, checksum, storage_ref.
- `document_chunks` — id (stable), document_id, section_label (e.g. `item_1`, `item_1a`, `item_7`,
  `item_8`, `prepared_remarks_ceo`, `qa`), page_span, speaker (nullable), text.
- `financial_facts` — id, project_id, concept, period, value, unit, source_document_id, xbrl_tag.
- `claims` — id, project_id, section (`snapshot` | `business` | `financials` | `risks`), claim_text,
  claim_type (`reported_fact` | `management_claim` | `analyst_inference` | `assumption` |
  `unsupported`), evidence_status (`green` | `yellow` | `red` | `gray`), ordinal, status
  (`needs_review` | `accepted` | `rejected`).
- `claim_citations` — id, claim_id, chunk_id, verbatim_quote, verbatim_verified (bool),
  entailment (nullable: `supports` | `partial` | `inference` | `contradicts`).
- `analysis_runs` — id, project_id, stage, status, started_at, finished_at, error (for staged
  progress + polling).

Example claim + citation record:
```json
{
  "claim_id": "claim_123",
  "section": "risks",
  "claim_text": "Management flags customer concentration as a principal risk.",
  "claim_type": "management_claim",
  "evidence_status": "green",
  "citations": [
    {
      "chunk_id": "chunk_item1a_014",
      "verbatim_quote": "A limited number of customers account for a substantial portion of our revenue.",
      "verbatim_verified": true,
      "entailment": "supports"
    }
  ]
}
```

---

## 5. Ingestion pipeline (`api/`)

Runs as a FastAPI background task; the frontend polls `analysis_runs` for staged progress
(meaningful stages, never fake percentages).

1. **Resolve ticker → CIK** via SEC's ticker→CIK mapping file.
2. **Fetch 10-K (HTML)** — latest annual filing primary document from EDGAR. Preserve section/page anchors.
3. **Fetch XBRL company-facts** — standardized concepts across recent filings.
4. **Structural chunk the 10-K** — split on real Item headers: `item_1` Business, `item_1a` Risk
   Factors, `item_7` MD&A, `item_8` Financial Statements. Fallback: if an Item header is not cleanly
   detected, record the gap and continue (do not silently mis-assign). Each chunk gets a stable ID +
   section/page metadata.
5. **Ingest transcript** — user upload/paste + label; chunk into `prepared_remarks_ceo`,
   `prepared_remarks_cfo`, and `qa` (individual Q/A pairs where detectable). Store original + checksum.
6. **No LLM document classifier** — 10-K type is known (fetched); transcript type is user-labeled.

**Data-absence handling:** wrong/unknown ticker → clear error; a missing XBRL concept renders as
**"unavailable," never 0**; unknown business facts render as **"unknown."**

---

## 6. Financial engine (100% deterministic)

Standardized figures come from SEC XBRL. Python functions compute derived metrics — never the LLM.

- Reported (from XBRL): revenue, gross/operating/net income, diluted EPS, operating cash flow,
  capex, cash, total debt, shares outstanding.
- Derived (code): revenue growth, gross/operating/EBITDA margin, free cash flow, net debt, CAGR.
- Every derived result stores **inputs + formula + units + period + source** for full auditability:

```json
{
  "metric": "free_cash_flow",
  "formula": "operating_cash_flow - capital_expenditures",
  "inputs": { "operating_cash_flow": 820000000, "capital_expenditures": 240000000 },
  "result": 580000000, "currency": "USD", "period": "FY2025"
}
```

Financial summary table: Revenue, Gross profit, Operating income, Net income, Diluted EPS, Operating
cash flow, Capex, Free cash flow, Cash, Total debt, Shares outstanding — across the available fiscal
years with YoY change. Rows with missing inputs show **"unavailable."**

---

## 7. Report generation

Per section, **structural routing** feeds only the relevant chunks to Claude (also controls token
cost):

| Section | Chunk sources |
|---|---|
| Snapshot | XBRL facts + `item_1` |
| Business overview | `item_1` (products, customers, geography, segments, cost structure, suppliers, regulation, cyclicality, capital intensity — each cited or **"unknown"**) |
| Financial summary | Deterministic engine (§6); narrative cites `item_7` MD&A |
| Risks (ranked) | `item_1a` + transcript `qa`, ordered by **management emphasis** (e.g. echoed in the call) — **no AI-invented probability/impact** |

**Shared system prompt (prompt-cached across passes):** role ("assist an equity research analyst;
organize and analyze supplied evidence, do not make unsupported claims"), source policy (use only
supplied sources; treat management statements as management claims; return "insufficient evidence"
when unsupported), finance rules (don't equate adjusted EBITDA with cash flow; don't call a target a
forecast; don't treat risk-factor boilerplate as a realized risk; don't infer market expectations
without consensus; don't calc without inputs), and an **adversarial instruction** ("before
finalizing, identify the strongest evidence against your conclusion").

**Structured JSON output** per claim: `claim_text`, `claim_type`, `verbatim_quote`, `chunk_ids`,
`contradictory_evidence`. Sentence-level claims render in `ordinal` order as the section prose.

### Citation validation (two layers)
1. **Deterministic (required):** `verbatim_quote` must be a substring of the cited chunk's text →
   sets `verbatim_verified`. Fabricated citations are rejected here for free, and the pass rate is a
   real metric.
2. **LLM entailment (optional nuance):** classify supports / partial / inference / contradicts.

**Traffic-light evidence status (UI):** green = directly supported; yellow = inference/partial;
red = unsupported/contradicted; gray = assumption. **No numeric confidence score.**

---

## 8. Frontend screens (`web/`)

1. **Create project** — company, ticker, research date.
2. **Add sources** — ticker triggers SEC fetch; user uploads/pastes + labels the transcript.
3. **Processing** — staged progress from `analysis_runs` polling.
4. **Report reader** — nav: Snapshot / Business / Financials / Risks. Each material claim shows its
   evidence-status chip and citation marker.
5. **Source viewer** — click a citation → open the document, **highlight the passage**, show page +
   the claim it supports, and let the user mark the citation valid/invalid (feedback captured for the
   later eval phase).

Read-and-trace only in this slice — no editing/regeneration.

---

## 9. Success criteria

- Financial-table figures **≥95% accurate** (SEC-sourced makes this very achievable).
- Backend calculations **100% traceable** to inputs + formula.
- **≥90% of material claims verbatim-citation-verified** (now an automatic, measurable metric).
- **Zero unlabeled invented forecasts.**
- Any conclusion traceable to a source in the UI.
- Report generated in **under ~5 minutes.**

---

## 10. Testing

- **Unit tests** on deterministic finance functions (exact expected values).
- **Fixture tests** on 10-K Item chunking (sample filing → expected section/chunk boundaries).
- **Gold-set harness** — a small set of hand-checked Q&A on one pilot company measuring
  citation-verification rate; the seed of the fuller eval suite in a later phase.
- **Pilot company:** a clean, single-ish-segment **consumer or software** name (USD, calendar-ish
  fiscal year; avoid banks/insurers/biotech/conglomerates per the blueprint) — chosen during setup.

---

## 11. Legal / product boundaries

Displayed disclaimer: *"This product assists with research organization and analysis. It does not
provide personalized investment advice or guarantee the accuracy or completeness of generated
content. Users should verify all information against original sources."* SEC filings are used as
primary sources; the user is responsible for using only transcripts they are authorized to use; all
research is clearly dated; nothing implies live market information.

---

## 12. Roadmap context (this slice is Phase 1–3 of a larger plan)

Later slices, each with its own spec → plan → build cycle: investment reasoning (thesis pillars,
counterarguments, scenarios, management questions) · financial/valuation engine expansion ·
validation & evaluation suite · polish & demo (export, sharing, onboarding, cost tracking).
