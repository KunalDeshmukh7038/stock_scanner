import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import Any

import requests

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "backend" / ".cache"
SCRIP_MASTER_CACHE = CACHE_DIR / "angel_scrip_master.json"
SCRIP_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

_SESSION_CACHE: dict[str, Any] = {
    "time": 0.0,
    "client": None,
    "auth_token": "",
    "feed_token": "",
    "refresh_token": "",
    "api_key": "",
    "client_code": "",
}
_SCRIP_CACHE: dict[str, Any] = {"time": 0.0, "data": None}
_TOKEN_CACHE: dict[str, dict[str, Any] | None] = {}

INDEX_INSTRUMENTS = [
    {
        "name": "NIFTY 50",
        "exchange": "NSE",
        "symbol": "^NSEI",
        "search_terms": ["NIFTY 50", "NIFTY", "NIFTY50"],
        "token_candidates": ["99926000", "26000"],
    },
    {
        "name": "NIFTY 100",
        "exchange": "NSE",
        "symbol": "^CNX100",
        "search_terms": ["NIFTY 100", "NIFTY100"],
        "token_candidates": [],
    },
    {
        "name": "BANKNIFTY",
        "exchange": "NSE",
        "symbol": "^NSEBANK",
        "search_terms": ["NIFTY BANK", "BANKNIFTY", "NIFTYBANK"],
        "token_candidates": ["99926009", "26009"],
    },
    {
        "name": "SENSEX",
        "exchange": "BSE",
        "symbol": "^BSESN",
        "search_terms": ["SENSEX", "BSE SENSEX"],
        "token_candidates": ["99919000"],
    },
]


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _client_timeout() -> int:
    return max(7, _env_int("ANGEL_TIMEOUT_SECONDS", 20))


def _request_attempts() -> int:
    return max(2, _env_int("ANGEL_RETRY_ATTEMPTS", 3))


def _normalize_totp_secret(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    if raw.lower().startswith("otpauth://"):
        try:
            parsed = urlparse(raw)
            query = parse_qs(parsed.query)
            raw = (query.get("secret") or [""])[0]
        except Exception:
            raw = value

    return raw.replace(" ", "").replace("-", "").strip().upper()


def _resolve_totp_code(raw_value: str, pyotp_module) -> str:
    cleaned = _normalize_totp_secret(raw_value)
    if not cleaned:
        raise RuntimeError("Angel One TOTP secret is missing.")

    if cleaned.isdigit() and len(cleaned) == 6:
        return cleaned

    try:
        return pyotp_module.TOTP(cleaned).now()
    except Exception as exc:
        raise RuntimeError(
            "Angel One TOTP value is invalid. Use either the Base32 setup key from Enable TOTP or a current 6-digit OTP."
        ) from exc


def angel_one_ready() -> bool:
    return all(
        [
            _env("ANGEL_API_KEY"),
            _env("ANGEL_CLIENT_CODE"),
            _env("ANGEL_PIN"),
            _env("ANGEL_TOTP_SECRET"),
        ]
    )


def _load_sdk():
    from SmartApi import SmartConnect  # type: ignore
    import pyotp  # type: ignore

    return SmartConnect, pyotp


def _load_ws_sdk():
    from SmartApi.smartWebSocketV2 import SmartWebSocketV2  # type: ignore

    return SmartWebSocketV2


def _normalize_exchange(exchange: str) -> str:
    value = (exchange or "").upper()
    return "NSE" if value not in {"NSE", "BSE", "MCX"} else value


def _normalize_name(value: str) -> str:
    return "".join(character for character in (value or "").upper() if character.isalnum())


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _iso_timestamp(value: Any = None) -> str:
    if value in (None, "", 0):
        return datetime.now(timezone.utc).isoformat()

    numeric = _safe_float(value, 0.0)
    if numeric <= 0:
        return datetime.now(timezone.utc).isoformat()

    if numeric > 10_000_000_000:
        numeric = numeric / 1000.0

    return datetime.fromtimestamp(numeric, tz=timezone.utc).isoformat()


def _scaled_price(value: Any) -> float:
    numeric = _safe_float(value, 0.0)
    if numeric == 0:
        return 0.0

    if float(int(numeric)) == numeric:
        return round(numeric / 100.0, 2)

    return round(numeric, 2)


def _ensure_session():
    if not angel_one_ready():
        raise RuntimeError("Angel One credentials are missing.")

    now = time.time()
    if _SESSION_CACHE["client"] is not None and now - _SESSION_CACHE["time"] < 6 * 60 * 60:
        return _SESSION_CACHE["client"]

    SmartConnect, pyotp = _load_sdk()
    timeout = _client_timeout()
    attempts = _request_attempts()
    session = None
    client = None
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            client = SmartConnect(api_key=_env("ANGEL_API_KEY"), timeout=timeout)
            totp = _resolve_totp_code(_env("ANGEL_TOTP_SECRET"), pyotp)
            session = client.generateSession(_env("ANGEL_CLIENT_CODE"), _env("ANGEL_PIN"), totp)
            if session and session.get("status"):
                break

            message = "Unable to log in to Angel One SmartAPI."
            if isinstance(session, dict) and session.get("message"):
                message = str(session["message"])
            raise RuntimeError(message)
        except Exception as exc:
            last_error = exc
            session = None
            client = None
            _SESSION_CACHE["client"] = None
            _SESSION_CACHE["time"] = 0.0
            if attempt < attempts - 1:
                time.sleep(min(1.2 * (attempt + 1), 4))
                continue
            raise RuntimeError(f"Angel One login timed out or failed after {attempts} attempts: {exc}") from exc

    if client is None or session is None:
        raise RuntimeError(f"Angel One login timed out or failed: {last_error or 'unknown error'}")

    session_data = session.get("data") or {}
    auth_token = str(session_data.get("jwtToken") or "").strip()
    refresh_token = ((session.get("data") or {}).get("refreshToken")) or None
    feed_token = ""
    try:
        feed_token = str(client.getfeedToken() or "").strip()
    except Exception:
        pass

    if refresh_token:
        try:
            client.generateToken(refresh_token)
        except Exception:
            pass

    _SESSION_CACHE["time"] = now
    _SESSION_CACHE["client"] = client
    _SESSION_CACHE["auth_token"] = auth_token
    _SESSION_CACHE["feed_token"] = feed_token
    _SESSION_CACHE["refresh_token"] = str(refresh_token or "")
    _SESSION_CACHE["api_key"] = _env("ANGEL_API_KEY")
    _SESSION_CACHE["client_code"] = _env("ANGEL_CLIENT_CODE")
    return client


def get_session_credentials() -> dict[str, str]:
    _ensure_session()
    return {
        "auth_token": str(_SESSION_CACHE.get("auth_token") or ""),
        "feed_token": str(_SESSION_CACHE.get("feed_token") or ""),
        "client_code": str(_SESSION_CACHE.get("client_code") or ""),
        "api_key": str(_SESSION_CACHE.get("api_key") or ""),
    }


def angel_login():
    try:
        return _ensure_session()
    except Exception as exc:
        logger.exception("Angel One login failed")
        raise RuntimeError(f"Angel One login failed: {exc}") from exc


def get_ltp_data(exchange: str, symbol: str, token: str) -> dict[str, Any]:
    normalized_exchange = _normalize_exchange(exchange)
    clean_symbol = str(symbol or "").strip()
    clean_token = str(token or "").strip()

    if not clean_symbol or not clean_token:
        raise RuntimeError("Angel One ltpData requires exchange, symbol, and token.")

    response = None
    last_error: Exception | None = None

    for attempt in range(_request_attempts()):
        try:
            client = _ensure_session()
            response = client.ltpData(normalized_exchange, clean_symbol, clean_token)
            break
        except Exception as exc:
            last_error = exc
            _SESSION_CACHE["client"] = None
            _SESSION_CACHE["time"] = 0.0
            if attempt == _request_attempts() - 1:
                logger.exception("Angel One ltpData failed for %s %s", normalized_exchange, clean_symbol)
            else:
                time.sleep(min(0.8 * (attempt + 1), 3))

    if response is None:
        raise RuntimeError(f"Angel One ltpData failed for {clean_symbol}: {last_error or 'unknown error'}")

    if not response.get("status"):
        message = str(response.get("message") or f"Angel One ltpData failed for {clean_symbol}.")
        raise RuntimeError(message)

    payload = response.get("data") or {}
    ltp_value = _safe_float(payload.get("ltp") or payload.get("last_traded_price"))

    return {
        "exchange": normalized_exchange,
        "symbol": clean_symbol,
        "symbol_token": clean_token,
        "ltp": round(ltp_value, 2),
        "open": round(_safe_float(payload.get("open") or payload.get("open_price_of_the_day")), 2),
        "high": round(_safe_float(payload.get("high") or payload.get("high_price_of_the_day")), 2),
        "low": round(_safe_float(payload.get("low") or payload.get("low_price_of_the_day")), 2),
        "prev_close": round(_safe_float(payload.get("close") or payload.get("closed_price")), 2),
        "timestamp": _iso_timestamp(
            payload.get("exchangeTime")
            or payload.get("exchange_timestamp")
            or payload.get("last_traded_timestamp")
            or time.time()
        ),
        "raw": payload,
    }


def _download_scrip_master() -> list[dict[str, Any]]:
    response = requests.get(SCRIP_MASTER_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("Angel One scrip master format is invalid.")
    return payload


def load_scrip_master() -> list[dict[str, Any]]:
    now = time.time()
    if _SCRIP_CACHE["data"] is not None and now - _SCRIP_CACHE["time"] < 12 * 60 * 60:
        return _SCRIP_CACHE["data"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if SCRIP_MASTER_CACHE.exists():
        age = now - SCRIP_MASTER_CACHE.stat().st_mtime
        if age < 12 * 60 * 60:
            with open(SCRIP_MASTER_CACHE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            _SCRIP_CACHE["time"] = now
            _SCRIP_CACHE["data"] = data
            return data

    data = _download_scrip_master()
    with open(SCRIP_MASTER_CACHE, "w", encoding="utf-8") as handle:
        json.dump(data, handle)

    _SCRIP_CACHE["time"] = now
    _SCRIP_CACHE["data"] = data
    return data


def _find_instrument(exchange: str, search_terms: list[str], preferred_symbol: str | None = None) -> dict[str, Any] | None:
    exchange = _normalize_exchange(exchange)
    cache_key = f"{exchange}:{preferred_symbol or ''}:{'|'.join(search_terms)}"
    if cache_key in _TOKEN_CACHE:
        return _TOKEN_CACHE[cache_key]

    normalized_terms = {_normalize_name(term) for term in search_terms if term}
    preferred_symbol_value = (preferred_symbol or "").upper()

    instrument = None
    for row in load_scrip_master():
        row_exchange = _normalize_exchange(str(row.get("exch_seg") or row.get("exchange") or ""))
        if row_exchange != exchange:
            continue

        token = str(row.get("token") or row.get("symboltoken") or "").strip()
        if not token:
            continue

        trading_symbol = str(row.get("symbol") or row.get("tradingsymbol") or "").strip()
        name = str(row.get("name") or "").strip()
        normalized_values = {
            _normalize_name(trading_symbol),
            _normalize_name(name),
        }

        if preferred_symbol_value:
            equity_candidates = {
                preferred_symbol_value,
                f"{preferred_symbol_value}EQ",
                f"{preferred_symbol_value}BE",
            }
            if normalized_values & {_normalize_name(value) for value in equity_candidates}:
                instrument = {
                    "exchange": exchange,
                    "symbol_token": token,
                    "tradingsymbol": trading_symbol or preferred_symbol_value,
                    "name": name or preferred_symbol_value,
                }
                break

        if normalized_values & normalized_terms:
            instrument = {
                "exchange": exchange,
                "symbol_token": token,
                "tradingsymbol": trading_symbol or name,
                "name": name or trading_symbol,
            }
            if preferred_symbol_value and trading_symbol.upper().endswith("-EQ"):
                break

    _TOKEN_CACHE[cache_key] = instrument
    return instrument


def resolve_equity_instrument(symbol: str) -> dict[str, Any] | None:
    clean_symbol = symbol.replace(".NS", "").upper()
    return _find_instrument("NSE", [clean_symbol, f"{clean_symbol}-EQ"], preferred_symbol=clean_symbol)


def resolve_index_instrument(name: str) -> dict[str, Any] | None:
    config = next((item for item in INDEX_INSTRUMENTS if item["name"] == name), None)
    if not config:
        return None

    for token in config["token_candidates"]:
        if token:
            return {
                "exchange": config["exchange"],
                "symbol_token": token,
                "tradingsymbol": name,
                "name": name,
                "symbol": config["symbol"],
            }

    instrument = _find_instrument(config["exchange"], config["search_terms"])
    if instrument:
        instrument["symbol"] = config["symbol"]
    return instrument


def _chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def fetch_quotes(instruments: list[dict[str, Any]], mode: str = "FULL") -> list[dict[str, Any]]:
    if not instruments:
        return []

    grouped: dict[str, list[str]] = {}
    instrument_map: dict[str, dict[str, Any]] = {}

    for instrument in instruments:
        exchange = _normalize_exchange(str(instrument.get("exchange") or "NSE"))
        token = str(instrument.get("symbol_token") or instrument.get("token") or "").strip()
        if not token:
            continue
        grouped.setdefault(exchange, []).append(token)
        instrument_map[f"{exchange}:{token}"] = instrument

    results: list[dict[str, Any]] = []
    attempts = _request_attempts()
    for exchange, tokens in grouped.items():
        for chunk in _chunked(tokens, 50):
            response = None
            for attempt in range(attempts):
                try:
                    client = _ensure_session()
                    response = client.getMarketData(mode, {exchange: chunk})
                    break
                except Exception:
                    _SESSION_CACHE["client"] = None
                    _SESSION_CACHE["time"] = 0.0
                    if attempt < attempts - 1:
                        time.sleep(min(0.8 * (attempt + 1), 3))
                        continue
                    raise

            payload = (response or {}).get("data") or {}
            fetched = payload.get("fetched") or payload.get("quotes") or []

            for item in fetched:
                token = str(item.get("symbolToken") or item.get("symboltoken") or "").strip()
                key = f"{exchange}:{token}"
                instrument = instrument_map.get(key, {})
                close_value = _safe_float(item.get("close"))
                ltp_value = _safe_float(item.get("ltp"))
                change_value = _safe_float(item.get("netChange"), ltp_value - close_value)
                change_pct = _safe_float(item.get("percentChange"))
                if not change_pct and close_value:
                    change_pct = (change_value / close_value) * 100

                results.append(
                    {
                        "name": instrument.get("name") or item.get("tradingSymbol") or item.get("tradingsymbol"),
                        "symbol": instrument.get("symbol") or instrument.get("name") or item.get("tradingSymbol"),
                        "exchange": exchange,
                        "symbol_token": token,
                        "tradingsymbol": instrument.get("tradingsymbol") or item.get("tradingSymbol") or item.get("tradingsymbol"),
                        "value": round(ltp_value, 2),
                        "change": round(change_value, 2),
                        "change_pct": round(change_pct, 2),
                        "open": round(_safe_float(item.get("open")), 2),
                        "high": round(_safe_float(item.get("high")), 2),
                        "low": round(_safe_float(item.get("low")), 2),
                        "prev_close": round(close_value, 2),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                )

            if len(tokens) > 50:
                time.sleep(1.05)

    return results


def get_live_market_indices() -> list[dict[str, Any]]:
    instruments = [instrument for item in INDEX_INSTRUMENTS if (instrument := resolve_index_instrument(item["name"]))]
    return fetch_quotes(instruments, mode="FULL")


def get_live_equity_quotes(symbols: list[str]) -> dict[str, dict[str, Any]]:
    instruments = []
    symbol_map: dict[str, str] = {}

    for symbol in symbols:
        instrument = resolve_equity_instrument(symbol)
        if not instrument:
            continue
        clean_symbol = symbol.replace(".NS", "").upper()
        instrument = {**instrument, "symbol": clean_symbol, "name": clean_symbol}
        instruments.append(instrument)
        symbol_map[instrument["symbol_token"]] = clean_symbol

    quotes = fetch_quotes(instruments, mode="FULL")
    return {
        symbol_map[quote["symbol_token"]]: quote
        for quote in quotes
        if quote.get("symbol_token") in symbol_map
    }


def get_live_equity_quote(symbol: str) -> dict[str, Any] | None:
    quotes = get_live_equity_quotes([symbol])
    return quotes.get(symbol.replace(".NS", "").upper())


class AngelOneMarketStream:
    ORDERED_NAMES = ["NIFTY 50", "NIFTY 100", "BANKNIFTY", "SENSEX"]
    EXCHANGE_TYPE_MAP = {"NSE": 1, "BSE": 3, "MCX": 5}

    def __init__(self):
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._ws: Any | None = None
        self._stop_event = threading.Event()
        self._items: dict[str, dict[str, Any]] = {}
        self._status = "idle"
        self._message = "Market stream has not started."
        self._last_updated: str | None = None
        self._revision = 0

    def start(self):
        if not angel_one_ready():
            self._set_status("fallback", "Angel One credentials are missing. Using fallback market source.")
            return

        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="angel-market-stream", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        with self._lock:
            ws = self._ws
            self._ws = None
        if ws is not None:
            try:
                ws.close_connection()
            except Exception:
                pass

    def _set_status(self, status: str, message: str, last_updated: str | None = None):
        with self._lock:
            self._status = status
            self._message = message
            if last_updated:
                self._last_updated = last_updated
            self._revision += 1

    def _merge_item(self, item: dict[str, Any]):
        with self._lock:
            self._items[item["name"]] = item
            self._last_updated = item.get("last_updated") or item.get("timestamp") or _iso_timestamp()
            self._status = "live"
            self._message = "Angel One WebSocket stream is live."
            self._revision += 1

    def _build_subscription(self):
        token_groups: dict[int, list[str]] = {}
        instrument_map: dict[str, dict[str, Any]] = {}

        for name in self.ORDERED_NAMES:
            instrument = resolve_index_instrument(name)
            if not instrument:
                continue

            exchange = str(instrument.get("exchange") or "NSE").upper()
            exchange_type = self.EXCHANGE_TYPE_MAP.get(exchange)
            token = str(instrument.get("symbol_token") or "").strip()
            if not exchange_type or not token:
                continue

            token_groups.setdefault(exchange_type, []).append(token)
            instrument_map[token] = {
                "name": name,
                "symbol": instrument.get("symbol") or name,
                "exchange": exchange,
                "symbol_token": token,
            }

        token_list = [{"exchangeType": exchange_type, "tokens": tokens} for exchange_type, tokens in token_groups.items()]
        return token_list, instrument_map

    def _connect_once(self):
        try:
            SmartWebSocketV2 = _load_ws_sdk()
        except Exception as exc:
            self._set_status("fallback", f"Angel One WebSocket SDK is unavailable: {exc}")
            return False

        try:
            credentials = get_session_credentials()
        except Exception as exc:
            self._set_status("fallback", f"Angel One login failed: {exc}")
            return False

        token_list, instrument_map = self._build_subscription()
        if not token_list:
            self._set_status("fallback", "Unable to resolve Angel One index tokens for live market stream.")
            return False

        sws = SmartWebSocketV2(
            credentials["auth_token"],
            credentials["api_key"],
            credentials["client_code"],
            credentials["feed_token"],
            max_retry_attempt=5,
            retry_strategy=1,
            retry_delay=3,
            retry_multiplier=2,
            retry_duration=30,
        )
        with self._lock:
            self._ws = sws

        correlation_id = "sentdrive"

        def on_data(wsapp, message):
            token = str(message.get("token") or message.get("symbolToken") or "").strip()
            instrument = instrument_map.get(token)
            if not instrument:
                return

            ltp = _scaled_price(message.get("last_traded_price") or message.get("ltp"))
            prev_close = _scaled_price(message.get("closed_price") or message.get("close"))
            open_price = _scaled_price(message.get("open_price_of_the_day") or message.get("open"))
            high_price = _scaled_price(message.get("high_price_of_the_day") or message.get("high"))
            low_price = _scaled_price(message.get("low_price_of_the_day") or message.get("low"))
            change_value = round(ltp - prev_close, 2) if prev_close else 0.0
            change_pct = round((change_value / prev_close) * 100, 2) if prev_close else 0.0
            timestamp = _iso_timestamp(message.get("exchange_timestamp") or message.get("last_traded_timestamp"))

            self._merge_item(
                {
                    **instrument,
                    "value": round(ltp, 2),
                    "change": change_value,
                    "change_pct": change_pct,
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "prev_close": round(prev_close, 2),
                    "timestamp": timestamp,
                    "last_updated": timestamp,
                    "source": "Angel One",
                    "is_live": True,
                }
            )

        def on_open(wsapp):
            self._set_status("connecting", "Connected to Angel One WebSocket. Subscribing to live market data.", _iso_timestamp())
            try:
                sws.subscribe(correlation_id, sws.SNAP_QUOTE, token_list)
            except Exception as exc:
                self._set_status("fallback", f"Angel One subscribe failed: {exc}", _iso_timestamp())
                raise

        def on_error(wsapp, error):
            self._set_status("fallback", f"Angel One WebSocket error: {error}", _iso_timestamp())

        def on_close(wsapp):
            self._set_status("fallback", "Angel One WebSocket connection closed. Using fallback until it reconnects.", _iso_timestamp())

        sws.on_open = on_open
        sws.on_data = on_data
        sws.on_error = on_error
        sws.on_close = on_close

        try:
            sws.connect()
            return True
        except Exception as exc:
            self._set_status("fallback", f"Angel One WebSocket connection failed: {exc}", _iso_timestamp())
            return False
        finally:
            with self._lock:
                if self._ws is sws:
                    self._ws = None

    def _run(self):
        reconnect_delay = 5
        while not self._stop_event.is_set():
            self._set_status("connecting", "Starting Angel One live market stream.", _iso_timestamp())
            self._connect_once()
            if self._stop_event.wait(reconnect_delay):
                break

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            items = [self._items[name] for name in self.ORDERED_NAMES if name in self._items]
            return {
                "items": items,
                "meta": {
                    "source": "Angel One" if self._status == "live" else "fallback",
                    "is_live": self._status == "live",
                    "status": self._status,
                    "message": self._message,
                    "last_updated": self._last_updated,
                    "revision": self._revision,
                },
            }


market_stream = AngelOneMarketStream()
