from dataclasses import dataclass

import httpx
import re


class TickerNotFound(Exception): ...
class CompanyNotFound(Exception): ...
class AmbiguousCompany(Exception):
    def __init__(self, query: str, matches: list[str]):
        self.query = query
        self.matches = matches
        super().__init__(query)


class FilingNotFound(Exception): ...


@dataclass
class Filing:
    html: str
    source_url: str
    filing_date: str
    fiscal_period: str


@dataclass
class CompanyIdentity:
    """Resolved SEC identity: CIK + ticker + official title."""

    cik: str
    ticker: str
    title: str


_SUFFIX_RE = re.compile(
    r"\b(incorporated|inc\.?|corporation|corp\.?|company|co\.?|ltd\.?|limited|plc)\b\.?",
    re.IGNORECASE,
)


def _normalize_name(name: str) -> str:
    text = re.sub(r"\s+", " ", name.strip().lower())
    text = _SUFFIX_RE.sub("", text)
    return re.sub(r"[^\w\s]", "", text).strip()


class SecClient:
    def __init__(self, user_agent: str):
        self._headers = {"User-Agent": user_agent}

    async def _get(self, url: str) -> httpx.Response:
        async with httpx.AsyncClient(headers=self._headers, timeout=30) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r

    async def _ticker_map(self) -> list[dict]:
        r = await self._get("https://www.sec.gov/files/company_tickers.json")
        return list(r.json().values())

    async def resolve_cik(self, ticker: str) -> str:
        return (await self.resolve_by_ticker(ticker)).cik

    async def resolve_by_ticker(self, ticker: str) -> CompanyIdentity:
        want = ticker.strip().upper()
        if not want:
            raise TickerNotFound(ticker)
        for row in await self._ticker_map():
            if row["ticker"].upper() == want:
                return CompanyIdentity(
                    cik=f'{int(row["cik_str"]):010d}',
                    ticker=row["ticker"].upper(),
                    title=row["title"],
                )
        raise TickerNotFound(ticker)

    async def resolve_by_company(self, company: str) -> CompanyIdentity:
        query = company.strip()
        if not query:
            raise CompanyNotFound(company)

        rows = await self._ticker_map()
        want_exact = query.casefold()
        want_norm = _normalize_name(query)

        exact = [
            row
            for row in rows
            if str(row.get("title", "")).casefold() == want_exact
        ]
        if len(exact) == 1:
            row = exact[0]
            return CompanyIdentity(
                cik=f'{int(row["cik_str"]):010d}',
                ticker=row["ticker"].upper(),
                title=row["title"],
            )
        if len(exact) > 1:
            raise AmbiguousCompany(
                query, [f"{r['ticker']}: {r['title']}" for r in exact[:8]]
            )

        fuzzy = [
            row
            for row in rows
            if want_norm
            and (
                _normalize_name(str(row.get("title", ""))) == want_norm
                or want_norm in _normalize_name(str(row.get("title", "")))
                or _normalize_name(str(row.get("title", ""))) in want_norm
            )
        ]
        # Prefer shorter titles when the query is a substring (more specific).
        if len(fuzzy) > 1:
            fuzzy_sorted = sorted(
                fuzzy, key=lambda r: len(str(r.get("title", "")))
            )
            best_len = len(str(fuzzy_sorted[0].get("title", "")))
            top = [r for r in fuzzy_sorted if len(str(r.get("title", ""))) == best_len]
            if len(top) == 1:
                fuzzy = top
            else:
                raise AmbiguousCompany(
                    query, [f"{r['ticker']}: {r['title']}" for r in top[:8]]
                )

        if len(fuzzy) == 1:
            row = fuzzy[0]
            return CompanyIdentity(
                cik=f'{int(row["cik_str"]):010d}',
                ticker=row["ticker"].upper(),
                title=row["title"],
            )
        if not fuzzy:
            raise CompanyNotFound(company)
        raise AmbiguousCompany(
            query, [f"{r['ticker']}: {r['title']}" for r in fuzzy[:8]]
        )

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
