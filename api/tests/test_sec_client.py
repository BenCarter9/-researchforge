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
