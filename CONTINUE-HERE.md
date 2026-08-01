# ResearchForge — Continue Here (handoff for Claude Code / Cursor)

Read this first. It orients a fresh Claude Code session on what this project is, its
current state, how to run it, and what to do next. (The detailed build ledger under
`.superpowers/sdd/` is gitignored and does **not** travel with the repo — this file is the
portable handoff.)

---

## What ResearchForge is

An **evidence-grounded equity-research tool**: enter a public-company ticker and upload an
earnings-call transcript → get a **source-backed research skeleton** (Snapshot · Business ·
Financials · Risks) where **every material claim links to its exact source passage** and
**every number traces to a formula**. It is a research *copilot*, not an autonomous investment
manager — it does **not** issue buy/sell recommendations.

This repo is the **first slice** ("evidence-grounded skeleton"). Design decisions and the full
requirements are in:
- **Spec:** `docs/superpowers/specs/2026-07-31-researchforge-evidence-skeleton-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-31-researchforge-evidence-skeleton.md`

The differentiators (all enforced in code + tests): claim-level **verbatim citation
verification** (a claim's cited quote must be an exact—whitespace-normalized—substring of its
source chunk); a **green/yellow/red/gray evidence traffic light** with **no numeric confidence
score**; a **deterministic finance engine** (the LLM does *zero* arithmetic; every metric
carries its inputs + formula); missing financial data renders **"unavailable", never 0**.

---

## Current status

- **Branch:** `build/evidence-skeleton` (31 commits ahead of `main`, at `f9207f3`). Not merged, not pushed (no git remote configured yet).
- **All 23 plan tasks complete.** Built via a subagent-driven TDD workflow (fresh implementer + independent reviewer per task); a final whole-branch review passed **"ready to merge with fixes"** and the fixes were applied.
- **Tests green:** backend **84** pytest, frontend **30** vitest, **1** Playwright e2e (drives the real demo path).
- Everything is tested against **fakes** — no live SEC calls and no Anthropic API key have been exercised yet.

---

## Stack & architecture

- **`web/`** — Next.js 15 (App Router) + TypeScript + Tailwind. Proxies `/api/*` → FastAPI via `next.config.mjs` rewrite.
- **`api/`** — FastAPI + SQLAlchemy 2 + Pydantic v2. Python **3.10** (repo is pinned to 3.10; there is no 3.11 here). venv at `api/.venv`.
- **PostgreSQL** (via `docker-compose.yml`). **Claude** (`claude-opus-5`) for the analysis passes. **SEC EDGAR** (10-K HTML + XBRL company-facts) as the primary source. Structural chunking (no vector DB in this slice).

### Backend map (`api/app/`)
- `sec/client.py` — SEC EDGAR: ticker→CIK, latest 10-K HTML, XBRL company-facts.
- `ingest/chunk_10k.py` — splits a 10-K by real Item boundaries (keeps only Item 1/1A/7/8).
- `ingest/chunk_transcript.py` — splits a transcript into CEO/CFO prepared remarks + Q&A.
- `finance/xbrl.py` — `extract_facts(company_facts)` → `{concept: {period: value}}` (missing = absent, never 0).
- `finance/engine.py` — deterministic `growth/margin/free_cash_flow/net_debt/cagr` + `build_table` (each result carries inputs + formula).
- `llm/schema.py` — Pydantic `GeneratedClaim` / `SectionResult`. `llm/prompts.py` — cached `SYSTEM_PROMPT` (role + source policy + finance rules + adversarial instruction) + per-section `OBJECTIVES`.
- `llm/client.py` — `ClaudeClient.generate_section` (`messages.parse`, structured output, prompt-cached system). `llm/verify.py` — `verbatim_verify` + `evidence_status` (the traffic light). `llm/persist.py` — turns a `SectionResult` into `Claim` + `ClaimCitation` rows with verification.
- `pipeline/runner.py` — 8-stage staged runner with per-stage `AnalysisRun` status rows. `pipeline/stages.py` — wires SEC→chunk→finance→Claude→persist.
- `routes/projects.py` — create project / upload transcript / start analysis (BackgroundTasks) / status. `routes/report.py` — report / chunk / mark-citation. `routes/dev.py` — dev-only seed route (gated by `RESEARCHFORGE_DEV_SEED=1`; used by the e2e).
- `models.py`, `db.py`, `deps.py`, `ids.py`. Eval harness in `api/eval/` (citation-verified-rate + financial-accuracy metrics; `api/eval/README.md`).

### Frontend map (`web/`)
- Pages: `app/projects/new`, `app/projects/[id]/sources`, `app/projects/[id]/processing`, `app/projects/[id]/report`.
- Components: `CreateProjectForm`, `AddTranscript`, `StageList`, `SectionView`, `ClaimLine`, `EvidenceChip`, `FinancialsTable`, `SourceViewer` (passage highlighting), `ui/*`.
- `lib/api.ts` (+ `lib/types.ts` mirroring the server shapes), `lib/pipeline.ts`. e2e: `e2e/report_flow.spec.ts`.

---

## Run it locally

Prereqs: Docker (Postgres), Python 3.10, Node 20+, and Google Chrome (only for the Playwright e2e).

```bash
docker compose up -d
```

```bash
python3 -m venv api/.venv && api/.venv/bin/pip install -e "api[dev]"
```

```bash
cd api && .venv/bin/python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)"
```
(The app has **no migrations and does not create tables on startup** — run the line above once against a fresh DB. See "Deferred" below.)

```bash
cd api && .venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

```bash
npm --prefix web install && npm --prefix web run dev
```

Then open http://localhost:3000/projects/new . Env vars: `DATABASE_URL` (default local Postgres), `SEC_USER_AGENT` (set your own contact — SEC requires it), `ANTHROPIC_API_KEY` (only for a real Claude pass), `RESEARCHFORGE_DEV_SEED` (keep unset outside the e2e), `RESEARCHFORGE_API_BASE` (eval CLI). Full details in `README.md`.

### Tests
```bash
cd api && .venv/bin/python -m pytest -q
```
```bash
npm --prefix web test
```
```bash
npm --prefix web run e2e
```

---

## What's built vs. deferred

**Built & tested (this slice):** SEC ingestion, structural chunking, deterministic finance engine + table, Claude passes with structured output + prompt caching, claim-level verbatim citation verification + traffic light, the 8-stage background pipeline (runs end-to-end against fakes), all read/write API routes, the full frontend flow (create → sources → processing → report → source viewer), and the eval-metric harness.

**Deferred (tracked — for later specs or before real deploy):**
1. **Production blocker:** no DB migrations / no startup `create_all`. Fine for a demo (README documents the manual step); add Alembic or a startup hook before deploying for real.
2. The **LLM path is only tested against a fake.** Before the first live run, exercise `llm/client.py` against the installed Anthropic SDK + a real `ANTHROPIC_API_KEY`, and confirm `claude-opus-5` resolves.
3. **Financials-tab narrative is empty** and derived metrics (`margin`/`net_debt`/`cagr` — computed & unit-tested in `engine.py`) are **not wired into the report** yet; `item_7`/`item_8` chunks are stored but unrouted (no `generate_financials` stage). Scope cut for the skeleton.
4. Snapshot prose grounds on Item 1 only (the financial numbers live in the Financials table).
5. **Later specs (not started):** thesis pillars, bull/base/bear scenarios, valuation, management questions, comparables, cross-document contradiction detection, section editing/regeneration, arbitrary PDF upload, real auth, vector search.
6. Assorted accepted Minors (SEC-UA-header test, client singletons, a `/report` 404-on-unknown-project, N+1 citation load, dropping the unused `label` field, an npm dev-audit pass, etc.).

**Pick a pilot company** for the first live run: a clean consumer/software name (USD, calendar-ish fiscal year; avoid banks/insurers/biotech/conglomerates).

---

## Suggested first move in Claude Code (Cursor)

Good next steps, roughly in order of value:
- **See it live end-to-end against fakes:** run the stack (above) and click through, or run the e2e.
- **Do the first *real* run:** set `ANTHROPIC_API_KEY` + `SEC_USER_AGENT`, pick a pilot ticker, and wire a real analyze pass — this is item #2 above and the highest-signal validation.
- **Then** either harden for deploy (migrations, item #1) or start the next feature spec (thesis pillars) using the same brainstorm → plan → build flow the `docs/superpowers/` files came from.

A useful opening prompt for a fresh session: *"Read CONTINUE-HERE.md, then let's do the first real Claude analysis pass against a live SEC filing — help me pick a pilot company and wire it up."*
