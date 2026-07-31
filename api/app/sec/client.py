from dataclasses import dataclass

import httpx

class TickerNotFound(Exception): ...
class FilingNotFound(Exception): ...

@dataclass
class Filing:
    html: str
    source_url: str
    filing_date: str
    fiscal_period: str

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

    async def latest_10k(self, cik: str) -> Filing:
        r = await self._get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        recent = r.json()["filings"]["recent"]
        forms = recent["form"]
        for i, form in enumerate(forms):
            if form == "10-K":
                break
        else:
            raise FilingNotFound(cik)

        accession_nodash = recent["accessionNumber"][i].replace("-", "")
        primary_document = recent["primaryDocument"][i]
        url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession_nodash}/{primary_document}"
        )
        doc = await self._get(url)

        return Filing(
            html=doc.text,
            source_url=url,
            filing_date=recent["filingDate"][i],
            fiscal_period="FY" + recent["reportDate"][i][:4],
        )

    async def company_facts(self, cik: str) -> dict:
        r = await self._get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        return r.json()
