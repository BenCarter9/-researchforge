"""Thin CLI that runs the two automatic eval metrics against a *running*
ResearchForge API + a hand-checked gold file.

This module is safe to import (e.g. from tests) without doing any I/O -
everything network/filesystem-touching lives behind `if __name__ ==
"__main__":` or inside functions that are only called from there.

Usage:

    RESEARCHFORGE_API_BASE=http://localhost:8000 \\
        python -m eval.run_eval <project_id> <ticker> <gold.jsonl>

Requires a running API (`uvicorn app.main:app`) with the pilot project's
pipeline already run, plus network access to fetch fresh SEC XBRL facts
for the financial-accuracy comparison. Not exercised by the test suite -
see api/tests/test_eval_harness.py for the unit-tested metric functions.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

from app.finance.xbrl import extract_facts
from app.sec.client import SecClient
from eval.metrics import financial_accuracy, report_verified_rate

_DEFAULT_API_BASE = "http://localhost:8000"


def load_gold(path: str | Path) -> tuple[dict[str, dict[str, float]], list[dict]]:
    """Reads a gold `.jsonl` file and splits it into:
    - a financial-facts dict shaped like `extract_facts`'s output, built
      from `{"type": "financial_fact", "concept", "period", "value"}` lines
    - a list of the remaining (e.g. `{"type": "qa", ...}`) entries, which
      have no automatic metric yet and are surfaced for manual review
    """
    gold: dict[str, dict[str, float]] = {}
    other: list[dict] = []

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("type") == "financial_fact":
                gold.setdefault(entry["concept"], {})[entry["period"]] = entry["value"]
            else:
                other.append(entry)

    return gold, other


async def fetch_report(client: httpx.AsyncClient, base_url: str, project_id: str) -> dict:
    resp = await client.get(f"{base_url}/api/projects/{project_id}/report")
    resp.raise_for_status()
    return resp.json()


async def fetch_extracted_facts(ticker: str) -> dict[str, dict[str, float]]:
    sec = SecClient(user_agent=os.environ.get("SEC_USER_AGENT", "ResearchForge you@example.com"))
    cik = await sec.resolve_cik(ticker)
    company_facts = await sec.company_facts(cik)
    return extract_facts(company_facts)


def _print_report(verified_rate: float | None, fin: dict, qa_entries: list[dict]) -> None:
    print("=== ResearchForge eval run ===")
    if verified_rate is None:
        print("Verbatim-citation-verified rate: n/a (no material claims)")
    else:
        print(f"Verbatim-citation-verified rate: {verified_rate * 100:.1f}%")

    if fin["accuracy"] is None:
        print("Financial-figure accuracy:       n/a (empty gold set)")
    else:
        print(
            f"Financial-figure accuracy:       {fin['accuracy'] * 100:.1f}% "
            f"({fin['matched']}/{fin['total']})"
        )

    if fin["mismatches"]:
        print("\nFinancial mismatches:")
        for m in fin["mismatches"]:
            print(f"  - {m['concept']} {m['period']}: expected {m['expected']}, got {m['actual']}")

    if qa_entries:
        print(f"\n{len(qa_entries)} qa gold entries need manual review (no automatic metric yet).")


async def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "usage: python -m eval.run_eval <project_id> <ticker> <gold.jsonl>",
            file=sys.stderr,
        )
        return 2

    project_id, ticker, gold_path = argv
    base_url = os.environ.get("RESEARCHFORGE_API_BASE", _DEFAULT_API_BASE)

    gold_facts, qa_entries = load_gold(gold_path)

    async with httpx.AsyncClient(timeout=30) as client:
        report = await fetch_report(client, base_url, project_id)

    extracted = await fetch_extracted_facts(ticker)

    verified_rate = report_verified_rate(report)
    fin = financial_accuracy(extracted, gold_facts)

    _print_report(verified_rate, fin, qa_entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
