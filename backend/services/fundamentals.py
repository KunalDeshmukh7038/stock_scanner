import logging
import os
import re
import threading
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FUNDAMENTAL_API_KEY = (os.getenv("FUNDAMENTAL_API_KEY") or "").strip()
SCREENER_URL = "https://www.screener.in/company/{symbol}/"
CACHE_TTL_SECONDS = 600
REQUEST_DELAY_SECONDS = 1.0
MAX_RETRIES = 3
MAX_BULK_UNCACHED_FETCHES = 8

USER_AGENT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
}

SYMBOL_MAP: dict[str, str] = {
    "M&M": "M&M",
    "BAJAJ-AUTO": "BAJAJ-AUTO",
    "MCDOWELL-N": "MCDOWELL-N",
    "MOTHERSON": "MOTHERSON",
}

_cache: dict[str, dict[str, Any]] = {}
_cache_lock = threading.RLock()
_request_lock = threading.RLock()
_last_request_time = 0.0
_session = requests.Session()


def _empty_result(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "roe": None,
        "roce": None,
        "dividendYield": None,
        "faceValue": None,
        "source": "Screener.in",
    }


def _normalize_symbol(symbol: str) -> str:
    clean_symbol = str(symbol or "").replace(".NS", "").strip().upper()
    return SYMBOL_MAP.get(clean_symbol, clean_symbol)


def _to_number(value: str | None) -> float | None:
    if value is None:
        return None

    cleaned = (
        str(value)
        .replace(",", "")
        .replace("%", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )

    if not cleaned or cleaned.upper() in {"N/A", "NA", "--", "-"}:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def _read_cache(symbol: str) -> dict[str, Any] | None:
    now = time.time()
    with _cache_lock:
        cached = _cache.get(symbol)
        if cached and now - cached["time"] < CACHE_TTL_SECONDS:
            return cached["value"]
    return None


def _write_cache(symbol: str, value: dict[str, Any]):
    with _cache_lock:
        _cache[symbol] = {"time": time.time(), "value": value}


def _rate_limited_get(url: str):
    global _last_request_time

    with _request_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)

        response = _session.get(url, headers=USER_AGENT_HEADERS, timeout=20)
        _last_request_time = time.time()
        return response


def _extract_from_top_ratios(soup: BeautifulSoup) -> dict[str, float | None]:
    top_ratio_items = soup.select("ul#top-ratios li") or soup.select("#top-ratios li")
    ratios: dict[str, float | None] = {}

    for item in top_ratio_items:
        label_element = item.select_one(".name")
        value_element = item.select_one(".value") or item.select_one(".number")

        label = " ".join(label_element.stripped_strings) if label_element else ""
        value = " ".join(value_element.stripped_strings) if value_element else " ".join(item.stripped_strings)

        if not label:
            continue

        ratios[label.strip()] = _to_number(value)

    return {
        "roe": ratios.get("ROE"),
        "roce": ratios.get("ROCE"),
        "dividendYield": ratios.get("Dividend Yield"),
        "faceValue": ratios.get("Face Value"),
    }


def _extract_from_text(soup: BeautifulSoup) -> dict[str, float | None]:
    page_text = soup.get_text(" ", strip=True)
    patterns = {
        "roe": r"\bROE\s+([₹]?\s*[\d.,]+(?:\.\d+)?\s*%?)",
        "roce": r"\bROCE\s+([₹]?\s*[\d.,]+(?:\.\d+)?\s*%?)",
        "dividendYield": r"\bDividend Yield\s+([₹]?\s*[\d.,]+(?:\.\d+)?\s*%?)",
        "faceValue": r"\bFace Value\s+([₹]?\s*[\d.,]+(?:\.\d+)?)",
    }

    extracted: dict[str, float | None] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, page_text, flags=re.IGNORECASE)
        extracted[key] = _to_number(match.group(1)) if match else None

    return extracted


def get_fundamentals(symbol: str) -> dict[str, Any]:
    normalized_symbol = _normalize_symbol(symbol)
    cached = _read_cache(normalized_symbol)
    if cached is not None:
        return cached

    result = _empty_result(normalized_symbol)
    url = SCREENER_URL.format(symbol=normalized_symbol)

    last_error = ""
    for attempt in range(MAX_RETRIES):
        try:
            response = _rate_limited_get(url)

            if response.status_code == 404:
                _write_cache(normalized_symbol, result)
                return result

            if response.status_code == 429:
                last_error = "429 Too Many Requests"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(REQUEST_DELAY_SECONDS * (attempt + 1))
                    continue
                break

            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            parsed = _extract_from_top_ratios(soup)

            if not any(parsed.values()):
                parsed = _extract_from_text(soup)

            enriched = {**result, **parsed}
            _write_cache(normalized_symbol, enriched)
            return enriched
        except Exception as exc:
            last_error = str(exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_DELAY_SECONDS * (attempt + 1))
                continue
            logger.exception("Fundamentals scrape failed for %s", normalized_symbol)

    fallback = {**result, "error": last_error or "Unable to fetch fundamentals"}
    _write_cache(normalized_symbol, fallback)
    return fallback


def get_bulk_fundamentals(symbols: list[str]) -> dict[str, dict[str, Any]]:
    unique_symbols = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = _normalize_symbol(symbol)
        if normalized and normalized not in seen:
            unique_symbols.append(normalized)
            seen.add(normalized)

    results: dict[str, dict[str, Any]] = {}
    missing: list[str] = []

    for symbol in unique_symbols:
        cached = _read_cache(symbol)
        if cached is not None:
            results[symbol] = cached
        else:
            missing.append(symbol)

    if not missing:
        return results

    limited_missing = missing[:MAX_BULK_UNCACHED_FETCHES]
    for symbol in limited_missing:
        try:
            results[symbol] = get_fundamentals(symbol)
        except Exception as exc:
            logger.exception("Bulk fundamentals fetch failed for %s", symbol)
            results[symbol] = {**_empty_result(symbol), "error": str(exc)}

    for symbol in missing[MAX_BULK_UNCACHED_FETCHES:]:
        results[symbol] = _empty_result(symbol)

    return results
