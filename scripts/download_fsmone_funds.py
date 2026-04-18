#!/usr/bin/env python3
"""
Download FSMOne fund daily prices into CSV files compatible with app.py.

Examples:
  python scripts/download_fsmone_funds.py
  python scripts/download_fsmone_funds.py FI3095 JPM048
  python scripts/download_fsmone_funds.py --identifier "Fidelity America A-SGD (hedged)"
  python scripts/download_fsmone_funds.py --start-date 2021-01-01 --end-date 2025-12-31
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


BASE_URL = "https://secure.fundsupermart.com"
FSMONE_URL = f"{BASE_URL}/fsmone"
FUND_API_URL = f"{FSMONE_URL}/rest/fund"
FUND_SELECTOR_URL = f"{FSMONE_URL}/tools/fund-selector"

ACTIVE_FUNDS_URL = f"{FUND_API_URL}/get-all-active-fund-list-with-id"
PRICE_HISTORY_URL = f"{FUND_API_URL}/find-daily-price-history-by-period"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data"

DEFAULT_START_DATE = "2021-01-01"
DEFAULT_END_DATE = "2025-12-31"
FSMONE_TIMEZONE = timezone(timedelta(hours=8), "Asia/Singapore")

PRICE_FIELDS = ("navPrice", "bidPrice", "bidPriceSgd")
HISTORY_PERIODS = ("1w", "1m", "3m", "6m", "1y", "2y", "3y", "5y", "10y")


@dataclass(frozen=True)
class DefaultFund:
    code: str
    requested_name: str


DEFAULT_FUNDS = (
    DefaultFund("FI3095", "Fidelity Global Dividend A-MINCOME(G)-SGD-H"),
    DefaultFund("FI3044", "Fidelity America A-SGD (hedged)"),
    DefaultFund("FI3014", "Fidelity Emerging Markets A-SGD"),
    DefaultFund("JPM048", "JPMorgan Funds - ASEAN Equity A (acc) SGD"),
    DefaultFund("370007", "Amova Singapore Equity SGD (formerly Nikko AM)"),
    DefaultFund("PAM089", "Eastspring Investments - Japan Dynamic AS SGD-H"),
    DefaultFund("ALZ276", "Allianz Global Artificial Intelligence AT Acc H2-SGD"),
    DefaultFund("FI3107", "Fidelity Global Technology A-ACC SGD"),
    DefaultFund("BGF006", "Blackrock World Gold Fund A2 SGD-H"),
    DefaultFund("BGF008", "Blackrock World Energy Fund A2 SGD-H"),
)

DEFAULT_ALIASES = {
    "FI3095": (
        "Fidelity Funds - Global Dividend Fund A-MINCOME(G)-SGD (SGD/USD Hedged)",
        "Fidelity Global Dividend A-MINCOME(G)-SGD-H",
    ),
    "FI3044": (
        "Fidelity Funds - America Fund A-SGD (SGD Hedged)",
        "Fidelity America A-SGD (hedged)",
    ),
    "FI3014": (
        "Fidelity Funds - Emerging Markets Fund A-SGD",
        "Fidelity Emerging Markets A-SGD",
    ),
    "JPM048": (
        "JPMorgan Funds - ASEAN Equity Fund A (acc) - SGD",
        "JPMorgan Funds - ASEAN Equity A (acc) SGD",
    ),
    "370007": (
        "Amova Singapore Equity Fund SGD (formerly Nikko AM Singapore Equity)",
        "Amova Singapore Equity SGD (formerly Nikko AM)",
    ),
    "PAM089": (
        "Eastspring Investments - Japan Dynamic Fund Class AS SGD-H",
        "Eastspring Investments - Japan Dynamic AS SGD-H",
    ),
    "ALZ276": (
        "Allianz Global Artificial Intelligence AT Acc H2-SGD",
    ),
    "FI3107": (
        "Fidelity Global Technology A-ACC SGD",
        "Fidelity Global Technology A-ACC SGD Fidelity International - S$ Share Class",
    ),
    "BGF006": (
        "BlackRock Global Funds - World Gold Fund A2 SGD-H",
        "Blackrock World Gold Fund A2 SGD-H",
    ),
    "BGF008": (
        "BlackRock Global Funds - World Energy Fund A2 SGD-H",
        "Blackrock World Energy Fund A2 SGD-H",
    ),
}


class DownloadError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download FSMOne fund daily price CSVs into the repository data folder."
    )
    parser.add_argument(
        "identifiers",
        nargs="*",
        help="Fund codes or quoted fund names. Defaults to the project fund basket.",
    )
    parser.add_argument(
        "-i",
        "--identifier",
        action="append",
        default=[],
        help="Fund code or product name. Can be supplied multiple times.",
    )
    parser.add_argument(
        "--identifiers-file",
        type=Path,
        help="Text file containing one fund code or product name per line.",
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help=f"Inclusive start date in YYYY-MM-DD format. Default: {DEFAULT_START_DATE}.",
    )
    parser.add_argument(
        "--end-date",
        default=DEFAULT_END_DATE,
        help=f"Inclusive end date in YYYY-MM-DD format. Default: {DEFAULT_END_DATE}.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for CSV output. Default: {DEFAULT_OUTPUT_DIR}.",
    )
    parser.add_argument(
        "--price-field",
        choices=PRICE_FIELDS,
        default="navPrice",
        help="FSMOne price field to write as the app-compatible Price column.",
    )
    parser.add_argument(
        "--history-period",
        choices=HISTORY_PERIODS,
        default="10y",
        help="FSMOne history window to request before local date filtering. Default: 10y.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve identifiers and print planned downloads without writing CSVs.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification. Use only if local CA certificates are broken.",
    )
    return parser.parse_args()


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise DownloadError(f"Invalid date '{value}'. Use YYYY-MM-DD.") from exc


def read_identifiers(args: argparse.Namespace) -> list[str]:
    identifiers = [*args.identifiers, *args.identifier]

    if args.identifiers_file:
        with args.identifiers_file.open(encoding="utf-8") as handle:
            identifiers.extend(
                line.strip()
                for line in handle
                if line.strip() and not line.lstrip().startswith("#")
            )

    if identifiers:
        return identifiers

    return [fund.code for fund in DEFAULT_FUNDS]


def request_json(
    url: str,
    *,
    method: str = "GET",
    form: dict[str, str] | None = None,
    insecure: bool = False,
) -> dict[str, Any]:
    body = None
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": FUND_SELECTOR_URL,
    }

    if form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    context = ssl._create_unverified_context() if insecure else ssl_context()

    try:
        with urllib.request.urlopen(request, timeout=45, context=context) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise DownloadError(f"Request failed for {url}: {exc}") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DownloadError(f"Expected JSON from {url}, received: {payload[:200]!r}") from exc


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def fetch_active_funds(*, insecure: bool = False) -> list[dict[str, Any]]:
    payload = request_json(ACTIVE_FUNDS_URL, insecure=insecure)
    funds = payload.get("data")
    if not isinstance(funds, list):
        raise DownloadError("FSMOne active fund response did not contain a data list.")
    return funds


def normalize(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9]+", " ", ascii_value)).strip().lower()


def match_score(identifier: str, fund: dict[str, Any]) -> float:
    wanted = normalize(identifier)
    name = normalize(str(fund.get("name", "")))
    code = normalize(str(fund.get("code", "")))

    if wanted == code:
        return 2.0
    if wanted == name:
        return 1.8
    if wanted and wanted in name:
        return 1.2 + min(len(wanted) / max(len(name), 1), 0.5)

    ratio = SequenceMatcher(None, wanted, name).ratio()
    wanted_tokens = set(wanted.split())
    name_tokens = set(name.split())
    overlap = len(wanted_tokens & name_tokens) / max(len(wanted_tokens), 1)
    return ratio + 0.25 * overlap


def alias_match_score(identifier: str, alias: str) -> float:
    wanted = normalize(identifier)
    candidate = normalize(alias)
    if wanted == candidate:
        return 2.0
    if wanted and (wanted in candidate or candidate in wanted):
        return 1.4
    return SequenceMatcher(None, wanted, candidate).ratio()


def resolve_default_alias(
    identifier: str,
    funds_by_code: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    best_score = 0.0
    best_code = None

    for code, aliases in DEFAULT_ALIASES.items():
        for alias in aliases:
            score = alias_match_score(identifier, alias)
            if score > best_score:
                best_score = score
                best_code = code

    if best_code and best_score >= 0.92:
        return funds_by_code.get(best_code)

    return None


def resolve_fund(identifier: str, funds: list[dict[str, Any]]) -> dict[str, Any]:
    funds_by_code = {str(fund.get("code", "")).upper(): fund for fund in funds}
    exact_code = funds_by_code.get(str(identifier).upper())
    if exact_code:
        return exact_code

    default_alias = resolve_default_alias(identifier, funds_by_code)
    if default_alias:
        return default_alias

    ranked = sorted(
        ((match_score(identifier, fund), fund) for fund in funds),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score, best = ranked[0]

    if best_score < 0.65:
        suggestions = ", ".join(
            f"{fund.get('code')}:{fund.get('name')}" for _, fund in ranked[:5]
        )
        raise DownloadError(f"No confident match for '{identifier}'. Closest: {suggestions}")

    if len(ranked) > 1:
        second_score, _ = ranked[1]
        exact_code_match = normalize(identifier) == normalize(str(best.get("code", "")))
        exact_name_match = normalize(identifier) == normalize(str(best.get("name", "")))
        if not exact_code_match and not exact_name_match and second_score >= best_score - 0.03:
            choices = ", ".join(
                f"{fund.get('code')}:{fund.get('name')}" for _, fund in ranked[:5]
            )
            raise DownloadError(f"Ambiguous identifier '{identifier}'. Use a fund code. Matches: {choices}")

    return best


def fetch_price_history(
    code: str,
    *,
    period: str,
    insecure: bool = False,
) -> list[dict[str, Any]]:
    payload = request_json(
        PRICE_HISTORY_URL,
        method="POST",
        form={"paramSedolnumber": code, "paramPeriod": period},
        insecure=insecure,
    )
    history = payload.get("dailyPriceHistory")
    if not isinstance(history, list):
        raise DownloadError(f"Price history response for {code} did not contain dailyPriceHistory.")
    return history


def timestamp_ms_to_date(value: int | float) -> date:
    return datetime.fromtimestamp(value / 1000, tz=FSMONE_TIMEZONE).date()


def price_from_record(record: dict[str, Any], preferred_field: str) -> float | None:
    for field in (preferred_field, "navPrice", "bidPrice", "bidPriceSgd"):
        value = record.get(field)
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
    return None


def filter_price_rows(
    history: list[dict[str, Any]],
    *,
    start_date: date,
    end_date: date,
    price_field: str,
) -> list[tuple[date, float]]:
    rows_by_date: dict[date, tuple[float, float]] = {}

    for record in history:
        daily_price_pk = record.get("dailyPricePk") or {}
        show_date = daily_price_pk.get("showDate") or record.get("showDate")
        if not isinstance(show_date, (int, float)):
            continue

        row_date = timestamp_ms_to_date(show_date)
        if row_date < start_date or row_date > end_date:
            continue

        price = price_from_record(record, price_field)
        if price is not None:
            current = rows_by_date.get(row_date)
            if current is None or show_date > current[0]:
                rows_by_date[row_date] = (float(show_date), price)

    rows = [(row_date, value[1]) for row_date, value in rows_by_date.items()]
    rows.sort(key=lambda row: row[0])
    return rows


def safe_filename(code: str, name: str) -> str:
    cleaned = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("_")
    cleaned = re.sub(r"_+", "_", cleaned)
    return f"{code}_{cleaned[:100]}.csv"


def write_csv(path: Path, rows: list[tuple[date, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Date", "Price"])
        for row_date, price in rows:
            writer.writerow([row_date.strftime("%d/%m/%Y"), f"{price:.10g}"])


def main() -> int:
    args = parse_args()
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    if start_date > end_date:
        raise DownloadError("--start-date must be on or before --end-date.")

    identifiers = read_identifiers(args)
    output_dir = args.output_dir.resolve()

    print(f"Fetching FSMOne active fund list from {ACTIVE_FUNDS_URL}")
    funds = fetch_active_funds(insecure=args.insecure)

    resolved = [resolve_fund(identifier, funds) for identifier in identifiers]
    seen_codes: set[str] = set()
    unique_funds: list[dict[str, Any]] = []
    for fund in resolved:
        code = str(fund["code"])
        if code not in seen_codes:
            seen_codes.add(code)
            unique_funds.append(fund)

    print(f"Resolved {len(unique_funds)} fund(s):")
    for fund in unique_funds:
        print(f"  {fund['code']} - {fund['name']}")

    if args.dry_run:
        print("Dry run only. No CSV files were written.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for fund in unique_funds:
        code = str(fund["code"])
        name = str(fund["name"])
        try:
            history = fetch_price_history(
                code,
                period=args.history_period,
                insecure=args.insecure,
            )
            rows = filter_price_rows(
                history,
                start_date=start_date,
                end_date=end_date,
                price_field=args.price_field,
            )
            if not rows:
                failures += 1
                print(f"WARNING: {code} - {name}: no rows in {start_date} to {end_date}")
                continue

            path = output_dir / safe_filename(code, name)
            write_csv(path, rows)
            print(f"Wrote {len(rows):4d} rows -> {path}")
        except DownloadError as exc:
            failures += 1
            print(f"ERROR: {code} - {name}: {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DownloadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
