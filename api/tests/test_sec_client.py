import httpx
import pytest
import respx

from app.sec.client import (
    AmbiguousCompany,
    CompanyNotFound,
    SecClient,
    TickerNotFound,
)

MAP = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    "2": {"cik_str": 909832, "ticker": "COST", "title": "COSTCO WHOLESALE CORP /NEW"},
}


@respx.mock
async def test_resolve_cik_pads_to_ten_digits():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP)
    )
    cik = await SecClient("ResearchForge test@example.com").resolve_cik("aapl")
    assert cik == "0000320193"


@respx.mock
async def test_resolve_cik_unknown_raises():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP)
    )
    with pytest.raises(TickerNotFound):
        await SecClient("ResearchForge test@example.com").resolve_cik("ZZZZ")


@respx.mock
async def test_resolve_by_ticker_returns_identity():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP)
    )
    ident = await SecClient("ResearchForge test@example.com").resolve_by_ticker("cost")
    assert ident.cik == "0000909832"
    assert ident.ticker == "COST"
    assert "COSTCO" in ident.title.upper()


@respx.mock
async def test_resolve_by_company_exact_and_fuzzy():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP)
    )
    sec = SecClient("ResearchForge test@example.com")
    exact = await sec.resolve_by_company("Apple Inc.")
    assert exact.ticker == "AAPL"
    fuzzy = await sec.resolve_by_company("costco wholesale")
    assert fuzzy.ticker == "COST"


@respx.mock
async def test_resolve_by_company_unknown_raises():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MAP)
    )
    with pytest.raises(CompanyNotFound):
        await SecClient("ResearchForge test@example.com").resolve_by_company(
            "Not A Real Company LLC"
        )
