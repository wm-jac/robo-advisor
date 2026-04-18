"""
Fetch the Singapore 1-year T-bill yield used as the risk-free rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
import ssl
import subprocess
from urllib.request import Request, urlopen

import certifi


MAS_ONE_YEAR_TBILL_URL = (
    "https://eservices.mas.gov.sg/Statistics/fdanet/"
    "TreasuryBillOriginalMaturities.aspx?type=BY"
)


@dataclass(frozen=True)
class RiskFreeRate:
    rate: float
    yield_percent: float
    as_of: date
    issue_code: str
    source_url: str = MAS_ONE_YEAR_TBILL_URL


class _OriginalMaturityTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_target_table = False
        self._in_thead = False
        self._in_tbody = False
        self._in_cell = False
        self._current_row: list[str] | None = None
        self._cell_parts: list[str] = []
        self.header_rows: list[list[str]] = []
        self.body_rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table" and attrs_dict.get("id") == "ContentPlaceHolder1_OriginalMaturitiesTable":
            self._in_target_table = True
        if not self._in_target_table:
            return
        if tag == "thead":
            self._in_thead = True
        elif tag == "tbody":
            self._in_tbody = True
        elif tag == "tr":
            self._current_row = []
        elif tag in {"th", "td"}:
            self._in_cell = True
            self._cell_parts = []
        elif tag == "br" and self._in_cell:
            self._cell_parts.append(" ")

    def handle_data(self, data):
        if self._in_target_table and self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag):
        if not self._in_target_table:
            return
        if tag in {"th", "td"} and self._in_cell:
            cell = " ".join("".join(self._cell_parts).split())
            if self._current_row is not None:
                self._current_row.append(cell)
            self._in_cell = False
        elif tag == "tr" and self._current_row is not None:
            if self._in_thead:
                self.header_rows.append(self._current_row)
            elif self._in_tbody:
                self.body_rows.append(self._current_row)
            self._current_row = None
        elif tag == "thead":
            self._in_thead = False
        elif tag == "tbody":
            self._in_tbody = False
        elif tag == "table":
            self._in_target_table = False


def fetch_latest_one_year_tbill_rate(timeout: int = 10) -> RiskFreeRate:
    request = Request(
        MAS_ONE_YEAR_TBILL_URL,
        headers={"User-Agent": "BMD5302-RoboAdvisor/1.0"},
    )
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=timeout, context=context) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as urllib_error:
        html = _fetch_with_curl(timeout, urllib_error)
    return parse_one_year_tbill_rate(html)


def parse_one_year_tbill_rate(html: str) -> RiskFreeRate:
    parser = _OriginalMaturityTableParser()
    parser.feed(html)

    if not parser.header_rows or not parser.body_rows:
        raise ValueError("MAS 1-year T-bill table was not found.")

    header = parser.header_rows[0]
    issue_headers = header[1:]
    benchmark_idx = next(
        (idx for idx, cell in enumerate(issue_headers) if "(B1Y)" in cell),
        None,
    )

    if benchmark_idx is not None:
        result = _latest_numeric_for_column(parser.body_rows, benchmark_idx)
        if result is not None:
            as_of, yield_percent = result
            return RiskFreeRate(
                rate=yield_percent / 100,
                yield_percent=yield_percent,
                as_of=as_of,
                issue_code=_issue_code(issue_headers[benchmark_idx]),
            )

    result = _latest_numeric_any_column(parser.body_rows, issue_headers)
    if result is None:
        raise ValueError("MAS 1-year T-bill table did not contain a numeric yield.")

    as_of, column_idx, yield_percent = result
    return RiskFreeRate(
        rate=yield_percent / 100,
        yield_percent=yield_percent,
        as_of=as_of,
        issue_code=_issue_code(issue_headers[column_idx]),
    )


def _fetch_with_curl(timeout: int, urllib_error: Exception) -> str:
    try:
        result = subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout), MAS_ONE_YEAR_TBILL_URL],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception as curl_error:
        raise RuntimeError(
            f"urllib fetch failed: {urllib_error}; curl fallback failed: {curl_error}"
        ) from curl_error


def _latest_numeric_for_column(
    rows: list[list[str]], column_idx: int
) -> tuple[date, float] | None:
    for row in reversed(rows):
        if len(row) <= column_idx + 1:
            continue
        as_of = _parse_date(row[0])
        yield_percent = _parse_yield(row[column_idx + 1])
        if as_of is not None and yield_percent is not None:
            return as_of, yield_percent
    return None


def _latest_numeric_any_column(
    rows: list[list[str]], issue_headers: list[str]
) -> tuple[date, int, float] | None:
    for row in reversed(rows):
        as_of = _parse_date(row[0]) if row else None
        if as_of is None:
            continue
        max_columns = min(len(issue_headers), len(row) - 1)
        for column_idx in range(max_columns - 1, -1, -1):
            yield_percent = _parse_yield(row[column_idx + 1])
            if yield_percent is not None:
                return as_of, column_idx, yield_percent
    return None


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%d %b %Y").date()
    except ValueError:
        return None


def _parse_yield(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _issue_code(header_cell: str) -> str:
    return header_cell.split()[0]
