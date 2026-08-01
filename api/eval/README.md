# ResearchForge eval harness

Measures the spec's success criterion automatically: **≥90% of material
claims verbatim-citation-verified**, plus a secondary financial-figure
accuracy check against a hand-checked gold set.

`eval/metrics.py` holds the pure metric functions (no network, no
filesystem) — see `api/tests/test_eval_harness.py` for their unit tests.
`eval/run_eval.py` is a thin CLI that wires those metrics up to a running
API and live SEC data; it is not unit-tested (needs a live filing + a
running server) and is exercised manually.

## Gold file format

A gold file is a `.jsonl` file — one JSON object per line — with two entry
types:

```json
{"type": "financial_fact", "concept": "revenue", "period": "FY2025", "value": 1200.0}
{"type": "qa", "question": "What drove the FY2025 revenue growth?", "expected": "..."}
```

- `financial_fact` entries are compared against `app/finance/xbrl.py`'s
  `extract_facts(company_facts)` output (same `concept` keys: `revenue`,
  `gross_profit`, `operating_income`, `net_income`, `eps_diluted`,
  `operating_cash_flow`, `capex`, `cash`, `shares_outstanding`,
  `total_debt`) via `financial_accuracy()`. This is the only entry type
  with an automatic metric today.
- `qa` entries document the kind of factual question a reviewer should
  hand-check against the generated report (there is no LLM-judge or
  automatic scoring for these yet — `run_eval.py` just counts them as a
  manual-review reminder).

`api/eval/gold/EXAMPLE.jsonl` is a **template illustrating the schema, not
real gold data** — its values are made up.

## Filling in real gold data

Once a pilot company is chosen (a clean consumer/software name, USD
reporting, a roughly calendar fiscal year — avoid banks, insurers, and
biotechs per the build notes), hand-check 10–15 entries against that
company's actual 10-K/transcript and save them as
`eval/gold/<TICKER>.jsonl`:

- Pull 4–8 `financial_fact` entries straight from the filing's XBRL
  facts (or the filing itself) for 1–2 fiscal years.
- Pull 5–10 `qa` entries covering claims a careful analyst would want
  verbatim-cited: reported figures, management statements, and risk
  factors.

## Running against a live API

Requires a running API with the pilot project's pipeline already executed
(so `GET /api/projects/{id}/report` returns real claims/citations), and
network access for the SEC XBRL fetch used in the financial-accuracy
check.

```bash
# from api/, with the venv active and the API running (e.g. `uvicorn app.main:app`)
RESEARCHFORGE_API_BASE=http://localhost:8000 \
    python -m eval.run_eval <project_id> <ticker> eval/gold/<TICKER>.jsonl
```

This prints the verbatim-citation-verified rate, the financial-figure
accuracy (with any mismatches), and a count of `qa` entries left for
manual review.
