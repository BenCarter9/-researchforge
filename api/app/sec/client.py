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
