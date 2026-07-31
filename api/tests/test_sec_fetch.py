import httpx, respx, pytest
from app.sec.client import SecClient, FilingNotFound

CIK = "0000320193"

SUBMISSIONS_WITH_10K = {
    "filings": {
        "recent": {
            "form": ["10-Q", "10-K"],
            "accessionNumber": ["0000320193-26-000004", "0000320193-26-000005"],
            "primaryDocument": ["aapl-10q.htm", "aapl-10k.htm"],
            "filingDate": ["2026-05-01", "2026-02-15"],
            "reportDate": ["2026-03-28", "2025-09-28"],
        }
    }
}

SUBMISSIONS_NO_10K = {
    "filings": {
        "recent": {
            "form": ["10-Q"],
            "accessionNumber": ["0000320193-26-000004"],
            "primaryDocument": ["aapl-10q.htm"],
            "filingDate": ["2026-05-01"],
            "reportDate": ["2026-03-28"],
        }
    }
}


@respx.mock
async def test_latest_10k_picks_10k_not_10q():
    respx.get(f"https://data.sec.gov/submissions/CIK{CIK}.json").mock(
        return_value=httpx.Response(200, json=SUBMISSIONS_WITH_10K))
    respx.get(
        "https://www.sec.gov/Archives/edgar/data/320193/000032019326000005/aapl-10k.htm"
    ).mock(return_value=httpx.Response(200, text="<html>...</html>"))

    filing = await SecClient("ResearchForge test@example.com").latest_10k(CIK)

    assert filing.source_url.endswith("/aapl-10k.htm")
    assert "/edgar/data/320193/000032019326000005/" in filing.source_url
    assert filing.filing_date == "2026-02-15"
    assert filing.fiscal_period == "FY2025"
    assert filing.html == "<html>...</html>"


@respx.mock
async def test_latest_10k_raises_when_no_10k():
    respx.get(f"https://data.sec.gov/submissions/CIK{CIK}.json").mock(
        return_value=httpx.Response(200, json=SUBMISSIONS_NO_10K))

    with pytest.raises(FilingNotFound):
        await SecClient("ResearchForge test@example.com").latest_10k(CIK)


@respx.mock
async def test_company_facts_returns_raw_json():
    respx.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json").mock(
        return_value=httpx.Response(200, json={"cik": 320193}))

    facts = await SecClient("ResearchForge test@example.com").company_facts(CIK)

    assert facts == {"cik": 320193}
