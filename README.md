# ResearchForge

Enter a ticker + upload an earnings transcript to produce a source-backed
equity research skeleton (Snapshot, Business, Financials, Risks), where every
material claim links to its exact source passage and every number traces to
a formula.

## Layout

- `api/` — FastAPI service (Python 3.10). Owns SEC fetching, structural
  chunking, deterministic financial math, Claude analysis passes, and
  citation validation.
- `web/` — Next.js 15 / TypeScript frontend. Proxies `/api/*` to the FastAPI
  service (single origin, no CORS).
- `docker-compose.yml` — PostgreSQL 16, the single datastore.

## Getting started

### Database

```bash
docker compose up -d db
```

### API

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
uvicorn app.main:app --reload --port 8000
```

### Web

```bash
cd web
npm install
npm run dev
```

Copy `.env.example` to `.env` and fill in secrets (e.g. `ANTHROPIC_API_KEY`)
before running the API against real data.
