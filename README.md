# ResearchForge

Enter a ticker and upload an earnings transcript to get a source-backed
equity research skeleton — Snapshot, Business, Financials, and Risks —
where every material claim links to its exact source passage and every
number traces to a formula. This is the **evidence-grounded skeleton**:
the first slice of the product, focused on making claims and numbers
verifiably traceable to their sources rather than on breadth of analysis
(see [Scope / non-goals](#scope--non-goals)).

## Architecture

- **`web/`** — Next.js 15 (App Router) / TypeScript frontend. Proxies
  `/api/*` to the FastAPI service (`next.config.mjs` rewrites), so the
  browser only ever talks to one origin and there's no CORS setup.
- **`api/`** — FastAPI service (Python 3.10). Owns:
  - Fetching primary sources from **SEC EDGAR** — the 10-K HTML filing and
    its XBRL company facts — as the source of record for filed financials
    and disclosures.
  - **Structural chunking** of the 10-K and the uploaded transcript by
    document structure (sections/items, speaker turns), not embeddings —
    there's no vector database in this slice.
  - A **deterministic finance engine**: every number in the Financials
    section comes from plain Python arithmetic over extracted XBRL facts.
    The LLM (**Claude**, `claude-opus-5`) never does arithmetic — it only
    writes prose and points at evidence.
  - **Claim-level citation verification**: each generated claim is checked
    against a verbatim quote from its source chunk and gets one of four
    evidence statuses — green (verified), yellow (inference / partial
    support), red (not verbatim-verified — no exact, whitespace-normalized
    match for the quote in its source chunk), gray (not applicable, e.g.
    a data point marked unavailable). Yellow is produced by Layer-2 LLM
    entailment checking (partial/inference support for an otherwise
    verified quote), which is deferred in this slice, so yellow is not yet
    emitted. There is no numeric confidence score — only these four states.
- **PostgreSQL 16** (via `docker-compose.yml`) — the single datastore for
  projects, documents, chunks, financial facts, claims, and citations.

## Prerequisites

- **Docker** (for Postgres via `docker-compose.yml`)
- **Python 3.10** — the repo is pinned to 3.10, *not* 3.11 (see
  `api/pyproject.toml`'s `requires-python`)
- **Node 20+** and **npm**
- **Google Chrome** — only needed to run the Playwright e2e test, which
  drives the system Chrome channel rather than downloading its own
  Chromium build

## Environment variables

| Variable | Required | Default / example | Notes |
|---|---|---|---|
| `DATABASE_URL` | No | `postgresql+psycopg://forge:forge@localhost:5432/researchforge` | Matches the `docker-compose.yml` defaults. |
| `SEC_USER_AGENT` | Yes, for any real SEC EDGAR fetch | `"ResearchForge you@example.com"` | SEC requires a descriptive User-Agent **with a contact email** on every request. Set this to your own contact info, not a placeholder — SEC will rate-limit or block generic/missing UAs. |
| `ANTHROPIC_API_KEY` | Only for a real Claude analysis pass | — | All automated tests (pytest, vitest, Playwright) run against fakes and need no key. |
| `GLM_API_KEY` / `OPENROUTER_API_KEY` / `ZAI_API_KEY` | Only for a live GLM-5.2 desk memo | — | Optional. First key found wins. No key → labeled **cached GLM-5.2 draft** on `/desk` (same prompt and model id). |
| `RESEARCHFORGE_DEV_SEED` | No | unset | Set to `1` to auto-seed a GOOGL (Alphabet FY2024 10-K excerpts) report on API startup and register `POST /api/dev/seed`. Used by Playwright and the walkthrough. **Must stay unset in production.** |
| `RESEARCHFORGE_API_BASE` | No | `http://localhost:8000` | Used by the [evaluation harness](#evaluation-harness) CLI to find a running API. |

Copy `.env.example` to `.env` and fill in your own values as a starting
point.

## Run it locally

Start Postgres:

```bash
docker compose up -d
```

Create the Python virtualenv and install the API package (editable, with
dev/test dependencies):

```bash
python3 -m venv api/.venv
api/.venv/bin/pip install -e "api[dev]"
```

Create the database tables. There are no migrations yet, and the app does
not create tables on startup, so this is a one-time step against a fresh
database:

```bash
cd api && .venv/bin/python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)"
```

Start the API (from `api/`, with the venv active or referenced directly):

```bash
cd api && .venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Install and start the web app (in a separate terminal; `.claude/launch.json`
also has this wired up to run on port 3000):

```bash
npm install --prefix web
npm --prefix web run dev
```

Open **http://localhost:3000/projects/new** and start a project with a
ticker and a transcript file.

For the 60-second workflow-tools **and** seeded-report demo, start the API
with the seed flag (SQLite is enough; Postgres is not required):

```bash
cd api && RESEARCHFORGE_DEV_SEED=1 DATABASE_URL=sqlite:///./demo.db \
  .venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:3000**. Click **Open GOOGL report** (Alphabet
FY2024 10-K excerpts, not invented financials) → click a claim to see the
verbatim passage → **Open the desk**. See [Desk (GLM-5.2)](#desk-glm-52).

## Running the tests

Backend (pytest, 101 tests, all against fakes — no network or API key
needed):

```bash
cd api && .venv/bin/python -m pytest -q
```

Frontend (vitest, 41 tests):

```bash
npm --prefix web test
```

End-to-end (Playwright, 1 smoke test of the demo path). This needs Google
Chrome installed and boots its own throwaway API (SQLite database,
`RESEARCHFORGE_DEV_SEED=1`) and web dev server automatically — you don't
need `docker compose` or a manually-started API/web server running first:

```bash
npm --prefix web run e2e
```

## Evaluation harness

`api/eval/` measures the spec's success criterion (verbatim-citation-verified
rate) plus a secondary financial-figure accuracy check against a
hand-checked gold set. See `api/eval/README.md` for the gold file format
and how to run it — real gold data is still pending a chosen pilot company
(see below); `api/eval/gold/EXAMPLE.jsonl` only illustrates the schema.

## Pilot company

The first live end-to-end run (real SEC filing + real transcript + real
Claude pass) needs a chosen pilot company. Pick a clean consumer or
software name: USD reporting, a roughly calendar fiscal year. Avoid banks,
insurers, biotechs, and conglomerates — their filings and financial
concepts don't fit the deterministic finance engine's assumptions well.

## Scope / non-goals

This slice deliberately does **not** include:

- Investment thesis pillars, or bull/base/bear scenarios
- Valuation (comps, DCF, multiples)
- A running list of management questions
- Comparable-company analysis
- Cross-document contradiction detection
- Section editing or regeneration
- Arbitrary PDF upload (only the earnings transcript upload + SEC EDGAR
  fetch are supported)
- Real authentication (no user accounts / auth in this slice)
- Vector search or embeddings (chunking is structural, not semantic)

## Desk (GLM-5.2)

`/desk` is a tiny sourced screen of two **AI-in-finance workflow tools**. It
does not replace the evidence-grounded 10-K / transcript skeleton above.

- **Model:** [GLM-5.2](https://huggingface.co/zai-org/GLM-5.2) open weights
  (`zai-org/GLM-5.2`), MIT license, via an optional OpenAI-compatible API.
- **Facts are cited.** Every dollar figure and named customer on the desk is
  copied from a linked company or wire source. Unverified items stay labeled
  (including any Rogo valuation rumor). The model does not invent financials.
- **Human owns TAKE/PASS.** GLM-5.2 drafts a memo (live if a key is set;
  otherwise a **cached GLM-5.2 draft** with the same prompt and model id
  `zai-org/GLM-5.2`). The analyst confirms or rejects the call.

## Disclaimer

> This product assists with research organization and analysis. It does
> not provide personalized investment advice or guarantee the accuracy or
> completeness of generated content. Users should verify all information
> against original sources.

SEC filings are used as primary sources for financial data and
disclosures. Users are responsible for only uploading transcripts they are
authorized to use. All research output is clearly dated, and nothing in
this product implies live or real-time market data.
