import json
import logging
import os
import time
import warnings
import asyncio
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import requests
import ta
import yfinance as yf
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from backend.angel_one import angel_login, angel_one_ready, get_live_equity_quote, get_live_equity_quotes, get_live_market_indices, get_ltp_data, market_stream
from backend.services.fundamentals import FUNDAMENTAL_API_KEY, get_bulk_fundamentals, get_fundamentals

try:
    from pygooglenews import GoogleNews
except Exception:
    GoogleNews = None


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env")
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
RAW_DATA_DIR = DATA_DIR / "nifty100_raw"
MASTER_FILE = DATA_DIR / "ind_nifty100list.csv"
COMBINED_DATASET_FILE = DATA_DIR / "final_dataset" / "nifty100_combined.csv"

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
USE_TRAINED_MODEL = os.getenv("USE_TRAINED_MODEL", "0").lower() in {"1", "true", "yes"}

app = FastAPI(title="Sentimental Drive API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

analyzer = SentimentIntensityAnalyzer()
_cache: dict[str, dict[str, Any]] = {}
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

ANGEL_MARKET_LTP_CONFIG = [
    {
        "name": "NIFTY 50",
        "exchange": "NSE",
        "token": "99926000",
        "symbol_candidates": ["NIFTY", "NIFTY 50"],
    },
    {
        "name": "BANKNIFTY",
        "exchange": "NSE",
        "token": "99926009",
        "symbol_candidates": ["BANKNIFTY", "NIFTY BANK"],
    },
    {
        "name": "SENSEX",
        "exchange": "BSE",
        "token": "99919000",
        "symbol_candidates": ["SENSEX", "BSE SENSEX"],
    },
]
COINGECKO_BTC_URL = "https://api.coingecko.com/api/v3/simple/price"


def cached(key: str, ttl: int, factory):
    now = time.time()
    existing = _cache.get(key)
    if existing and now - existing["time"] < ttl:
        return existing["value"]
    value = factory()
    _cache[key] = {"time": now, "value": value}
    return value


@app.on_event("startup")
def warm_startup_cache():
    load_company_master()
    available_symbols()
    load_combined_latest_rows()
    market_stream.start()

    try:
        stocks = {"stocks": load_combined_latest_rows()}
        _cache["stocks"] = {"time": time.time(), "value": stocks}
    except Exception:
        pass


@app.on_event("shutdown")
def stop_market_stream():
    market_stream.stop()


@lru_cache(maxsize=1)
def load_company_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_FILE)
    df["Ticker"] = df["Symbol"].astype(str).str.strip() + ".NS"
    return df


@lru_cache(maxsize=1)
def available_symbols() -> list[str]:
    symbols = []
    for path in RAW_DATA_DIR.glob("*.csv"):
        symbols.append(path.stem.upper())
    return sorted(set(symbols))


@lru_cache(maxsize=1)
def load_combined_latest_rows() -> list[dict[str, Any]]:
    if not COMBINED_DATASET_FILE.exists():
        return []

    frame = pd.read_csv(COMBINED_DATASET_FILE)
    if frame.empty or "Symbol" not in frame.columns:
        return []

    date_column = next((column for column in ["Date", "date", "Datetime", "datetime"] if column in frame.columns), None)
    if date_column:
        frame["_sort_key"] = pd.to_datetime(frame[date_column], errors="coerce")
    else:
        frame["_sort_key"] = np.arange(len(frame))

    frame = frame.dropna(subset=["_sort_key"]).sort_values(["Symbol", "_sort_key"]).reset_index(drop=True)
    latest_rows: list[dict[str, Any]] = []

    for symbol, group in frame.groupby("Symbol", sort=False):
        latest = group.iloc[-1]
        previous = group.iloc[-2] if len(group) > 1 else latest
        close = float(latest.get("Close", 0) or 0)
        prev_close = float(previous.get("Close", close) or close)
        change_pct = ((close - prev_close) / prev_close) * 100 if prev_close else 0.0
        rsi = float(latest.get("RSI", 50) or 50)
        macd = float(latest.get("MACD", 0) or 0)
        macd_signal = float(latest.get("MACD_signal", 0) or 0)
        sma20 = float(latest.get("SMA_20", close) or close)
        target = int(latest.get("Target", 1) or 1)

        if target == 1 and rsi < 70 and close > sma20 and macd > macd_signal:
            signal = "BUY"
        elif target == 0 and rsi > 30 and close < sma20 and macd < macd_signal:
            signal = "SELL"
        else:
            signal = "HOLD"

        info = company_row(symbol) if symbol else None
        latest_rows.append(
            {
                "symbol": str(symbol).upper(),
                "company_name": info["Company Name"] if info is not None else symbol,
                "sector": info["Industry"] if info is not None else "Unknown",
                "current_price": round(close, 2),
                "change_pct": round(change_pct, 2),
                "rsi": round(rsi, 2),
                "macd": round(macd, 3),
                "sentiment_score": 0.0,
                "signal": signal,
                "prediction": "UP" if target == 1 else "DOWN",
                "confidence": 58.0,
                "market_cap": 0,
                "pe": 0,
                "book_value": 0,
                "roe": 0,
                "roce": 0,
                "dividend_yield": 0,
                "face_value": 0,
                "history": [],
                "news": [],
                "feature_importance": [],
                "model_used": "Fast cached summary",
            }
        )

    return latest_rows


def apply_live_quote(snapshot: dict[str, Any], quote: dict[str, Any] | None) -> dict[str, Any]:
    if not quote:
        return snapshot

    enriched = {**snapshot}
    enriched["current_price"] = round(float(quote.get("value", enriched.get("current_price", 0)) or 0), 2)
    enriched["change_pct"] = round(float(quote.get("change_pct", enriched.get("change_pct", 0)) or 0), 2)
    enriched["high"] = round(float(quote.get("high", enriched.get("high", 0)) or 0), 2)
    enriched["low"] = round(float(quote.get("low", enriched.get("low", 0)) or 0), 2)
    enriched["open"] = round(float(quote.get("open", enriched.get("open", 0)) or 0), 2)
    enriched["prev_close"] = round(float(quote.get("prev_close", enriched.get("prev_close", 0)) or 0), 2)
    enriched["price_source"] = "Angel One"
    enriched["price_timestamp"] = quote.get("timestamp")
    return enriched


def apply_fundamentals(snapshot: dict[str, Any], fundamentals: dict[str, Any] | None) -> dict[str, Any]:
    resolved = fundamentals or {}
    merged = {**snapshot}
    merged["fundamentals"] = {
        "roe": resolved.get("roe"),
        "roce": resolved.get("roce"),
        "dividendYield": resolved.get("dividendYield"),
        "faceValue": resolved.get("faceValue"),
        "source": resolved.get("source", "Screener.in"),
    }
    merged["roe"] = resolved.get("roe")
    merged["roce"] = resolved.get("roce")
    merged["dividend_yield"] = resolved.get("dividendYield")
    merged["face_value"] = resolved.get("faceValue")
    return merged


def apply_bulk_fundamentals(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return records

    fundamentals_map = get_bulk_fundamentals([record.get("symbol", "") for record in records])
    enriched_records = []
    for record in records:
        symbol = str(record.get("symbol") or "").replace(".NS", "").upper()
        enriched_records.append(apply_fundamentals(record, fundamentals_map.get(symbol)))
    return enriched_records


def get_yfinance_market_items(selected_names: list[str] | None = None) -> list[dict[str, Any]]:
    symbols = {
        "NIFTY 50": "^NSEI",
        "NIFTY 100": "^CNX100",
        "BANKNIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "BTC-USD": "BTC-USD",
        "GOLD": "GC=F",
        "SILVER": "SI=F",
    }

    items = []
    requested = set(selected_names or symbols.keys())
    for name, ticker in symbols.items():
        if name not in requested:
            continue
        try:
            history = yf.Ticker(ticker).history(period="5d", interval="1d")
            if history.empty or len(history) < 2:
                continue
            latest_row = history.iloc[-1]
            previous_row = history.iloc[-2]
            current = float(latest_row["Close"])
            previous = float(previous_row["Close"])
            change = current - previous
            pct = (change / previous) * 100 if previous else 0.0
            items.append(
                {
                    "name": name,
                    "symbol": ticker,
                    "value": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(pct, 2),
                    "high": round(float(latest_row["High"]), 2),
                    "low": round(float(latest_row["Low"]), 2),
                    "open": round(float(latest_row["Open"]), 2),
                    "prev_close": round(previous, 2),
                    "timestamp": history.index[-1].isoformat() if len(history.index) else None,
                    "last_updated": history.index[-1].isoformat() if len(history.index) else None,
                    "source": "Fallback",
                    "is_live": False,
                }
            )
        except Exception:
            continue
    return items


def get_cached_fallback_market_items(selected_names: list[str]) -> list[dict[str, Any]]:
    cache_key = f"market:fallback:{'|'.join(sorted(selected_names))}"
    return cached(cache_key, 300, lambda: get_yfinance_market_items(selected_names))


def get_last_successful_market_items() -> list[dict[str, Any]]:
    cached_value = _cache.get("market:last_success")
    if cached_value:
        return cached_value["value"]
    return []


def remember_market_items(items: list[dict[str, Any]]):
    if items:
        _cache["market:last_success"] = {"time": time.time(), "value": items}


def fetch_btc_market_data() -> dict[str, Any] | None:
    try:
        response = requests.get(
            COINGECKO_BTC_URL,
            params={
                "ids": "bitcoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json().get("bitcoin") or {}
        ltp = float(payload.get("usd") or 0)
        change_pct = float(payload.get("usd_24h_change") or 0)
        prev_close = ltp / (1 + (change_pct / 100)) if ltp and change_pct > -100 else ltp
        change = ltp - prev_close if prev_close else 0.0
        last_updated = pd.Timestamp.utcnow().isoformat()
        return {
            "name": "BTC-USD",
            "ltp": round(ltp, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "high": round(ltp, 2),
            "low": round(ltp, 2),
            "open": round(prev_close, 2),
            "prev_close": round(prev_close, 2),
            "source": "CoinGecko",
            "last_updated": last_updated,
        }
    except Exception as exc:
        logger.exception("BTC market fetch failed")
        raise RuntimeError(f"CoinGecko BTC fetch failed: {exc}") from exc


def _fetch_angel_market_row(config: dict[str, Any]) -> dict[str, Any]:
    last_error: Exception | None = None

    for symbol in config["symbol_candidates"]:
        try:
            quote = get_ltp_data(config["exchange"], symbol, config["token"])
            ltp = float(quote.get("ltp") or 0)
            prev_close = float(quote.get("prev_close") or 0)
            change = ltp - prev_close if prev_close else 0.0
            change_pct = (change / prev_close) * 100 if prev_close else 0.0
            return {
                "name": config["name"],
                "ltp": round(ltp, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "high": round(float(quote.get("high") or 0), 2),
                "low": round(float(quote.get("low") or 0), 2),
                "open": round(float(quote.get("open") or 0), 2),
                "prev_close": round(prev_close, 2),
                "source": "Angel One",
                "last_updated": quote.get("timestamp"),
            }
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"{config['name']} fetch failed: {last_error or 'unknown error'}")


def get_market_data() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    issues: list[str] = []

    if angel_one_ready():
        try:
            angel_login()
            for config in ANGEL_MARKET_LTP_CONFIG:
                try:
                    rows.append(_fetch_angel_market_row(config))
                except Exception as exc:
                    logger.exception("Angel One market fetch failed for %s", config["name"])
                    issues.append(str(exc))
        except Exception as exc:
            issues.append(str(exc))
    else:
        issues.append("Angel One credentials are missing or incomplete.")

    try:
        btc_row = fetch_btc_market_data()
        if btc_row:
            rows.append(btc_row)
    except Exception as exc:
        issues.append(str(exc))

    missing_names = [
        name
        for name in ["NIFTY 50", "BANKNIFTY", "SENSEX", "BTC-USD"]
        if name not in {row["name"] for row in rows}
    ]
    if missing_names:
        fallback_items = get_cached_fallback_market_items(missing_names)
        for item in fallback_items:
            rows.append(
                {
                    "name": item["name"],
                    "ltp": round(float(item.get("value") or 0), 2),
                    "change": round(float(item.get("change") or 0), 2),
                    "change_pct": round(float(item.get("change_pct") or 0), 2),
                    "high": round(float(item.get("high") or 0), 2),
                    "low": round(float(item.get("low") or 0), 2),
                    "open": round(float(item.get("open") or 0), 2),
                    "prev_close": round(float(item.get("prev_close") or 0), 2),
                    "source": item.get("source") or "Fallback",
                    "last_updated": item.get("last_updated") or item.get("timestamp"),
                }
            )

    deduped_rows: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for name in ["NIFTY 50", "BANKNIFTY", "SENSEX", "BTC-USD"]:
        row = next((item for item in rows if item["name"] == name), None)
        if row and name not in seen_names:
            deduped_rows.append(row)
            seen_names.add(name)

    if not deduped_rows:
        message = " | ".join(issues) if issues else "No market data available right now."
        return {"data": [], "message": message}

    message = "Live market data loaded."
    if issues:
        message = " | ".join(issues)
    return {"data": deduped_rows, "message": message}


def build_market_payload() -> dict[str, Any]:
    ordered_names = ["NIFTY 50", "NIFTY 100", "BANKNIFTY", "SENSEX", "BTC-USD", "GOLD", "SILVER"]
    stream_snapshot = market_stream.snapshot()
    live_items = stream_snapshot["items"] if angel_one_ready() else []
    issues: list[str] = []

    if angel_one_ready() and not live_items:
        try:
            rest_live_items = get_live_market_indices()
            live_items = [
                {
                    **item,
                    "source": "Angel One",
                    "is_live": False,
                    "last_updated": item.get("timestamp"),
                }
                for item in rest_live_items
            ]
        except Exception as exc:
            issues.append(f"Angel One REST market fetch failed: {exc}")
            live_items = []
    elif not angel_one_ready():
        issues.append("Angel One credentials are missing or incomplete.")

    live_names = {item["name"] for item in live_items}
    missing_names = [name for name in ordered_names if name not in live_names]
    fallback_items = []
    if missing_names:
        try:
            fallback_items = get_cached_fallback_market_items(missing_names)
        except Exception as exc:
            issues.append(f"Fallback market source failed: {exc}")
            fallback_items = []
    combined = live_items + fallback_items
    combined = sorted(combined, key=lambda item: ordered_names.index(item["name"]) if item["name"] in ordered_names else 999)

    if not combined:
        try:
            simple_payload = get_market_data()
            combined = [
                {
                    "name": row["name"],
                    "symbol": row["name"],
                    "value": round(float(row.get("ltp") or 0), 2),
                    "change": round(float(row.get("change") or 0), 2),
                    "change_pct": round(float(row.get("change_pct") or 0), 2),
                    "high": round(float(row.get("high") or 0), 2),
                    "low": round(float(row.get("low") or 0), 2),
                    "open": round(float(row.get("open") or 0), 2),
                    "prev_close": round(float(row.get("prev_close") or 0), 2),
                    "timestamp": row.get("last_updated"),
                    "last_updated": row.get("last_updated"),
                    "source": row.get("source") or "Fallback",
                    "is_live": row.get("source") == "Angel One",
                }
                for row in simple_payload.get("data", [])
            ]
            if simple_payload.get("message"):
                issues.append(str(simple_payload["message"]))
        except Exception as exc:
            issues.append(f"Simple market data fallback failed: {exc}")

    if not combined:
        combined = get_last_successful_market_items()
        if combined:
            combined = [
                {
                    **item,
                    "source": item.get("source") or "Cached fallback",
                    "is_live": False,
                }
                for item in combined
            ]
            issues.append("Showing the last successful cached market snapshot.")
    else:
        remember_market_items(combined)

    latest_market_time = next(
        (item.get("last_updated") or item.get("timestamp") for item in combined if item.get("last_updated") or item.get("timestamp")),
        None,
    )

    meta = {
        "source": "Angel One" if any(item.get("source") == "Angel One" for item in combined) else "Fallback",
        "is_live": bool(stream_snapshot["meta"].get("is_live")),
        "status": stream_snapshot["meta"].get("status") or ("ready" if combined else "empty"),
        "message": stream_snapshot["meta"].get("message") or (" | ".join(issues) if issues else ("Market data loaded." if combined else "No market data is currently available from the active sources.")),
        "last_updated": stream_snapshot["meta"].get("last_updated") or latest_market_time,
        "revision": stream_snapshot["meta"].get("revision", 0),
    }

    return {"items": combined, "meta": meta}


@lru_cache(maxsize=1)
def load_model_bundle():
    model_path = MODELS_DIR / "xgb_upgraded_small.pkl"
    feature_path = MODELS_DIR / "feature_cols_upgraded.json"

    if not model_path.exists():
        model_path = MODELS_DIR / "xgb_small_model.pkl"
        feature_path = MODELS_DIR / "feature_cols_best.json"

    model = joblib.load(model_path)
    with open(feature_path, "r", encoding="utf-8") as file:
        feature_cols = json.load(file)
    return model, feature_cols


def company_row(symbol: str) -> pd.Series | None:
    master = load_company_master()
    clean_symbol = symbol.replace(".NS", "").upper()
    matches = master.loc[master["Symbol"].astype(str).str.upper() == clean_symbol]
    if matches.empty:
        return None
    return matches.iloc[0]


def normalize_history_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()

    if "Date" not in frame.columns:
        frame.rename(columns={frame.columns[0]: "Date"}, inplace=True)

    keep = [column for column in ["Date", "Open", "High", "Low", "Close", "Volume"] if column in frame.columns]
    frame = frame[keep]
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")

    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)
    return frame


def load_local_history(symbol: str) -> pd.DataFrame:
    path = RAW_DATA_DIR / f"{symbol.replace('.NS', '').upper()}.csv"
    if not path.exists():
        return pd.DataFrame()

    try:
        frame = pd.read_csv(path, skiprows=[1, 2])
        return normalize_history_frame(frame)
    except Exception:
        return pd.DataFrame()


def download_history(symbol: str, period: str = "5y") -> pd.DataFrame:
    ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"

    local = load_local_history(ticker)
    if not local.empty:
        return local

    frame = yf.download(ticker, period=period, auto_adjust=False, progress=False)
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.reset_index()
    return normalize_history_frame(frame)


@lru_cache(maxsize=256)
def load_feature_history(symbol: str, allow_network: bool = False) -> pd.DataFrame:
    ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
    history = load_local_history(ticker)

    if history.empty and allow_network:
      history = download_history(ticker)

    if history.empty:
        return pd.DataFrame()

    return add_features(history)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["Return"] = frame["Close"].pct_change()
    frame["SMA_10"] = frame["Close"].rolling(10).mean()
    frame["SMA_20"] = frame["Close"].rolling(20).mean()
    frame["SMA_50"] = frame["Close"].rolling(50).mean()
    frame["SMA_200"] = frame["Close"].rolling(200).mean()
    frame["RSI"] = ta.momentum.RSIIndicator(frame["Close"], window=14).rsi()
    macd = ta.trend.MACD(frame["Close"])
    frame["MACD"] = macd.macd()
    frame["MACD_signal"] = macd.macd_signal()
    bb = ta.volatility.BollingerBands(frame["Close"], window=20, window_dev=2)
    frame["BB_upper"] = bb.bollinger_hband()
    frame["BB_lower"] = bb.bollinger_lband()
    frame["BB_width"] = frame["BB_upper"] - frame["BB_lower"]
    frame["BB_pct"] = (frame["Close"] - frame["BB_lower"]) / (frame["BB_width"] + 1e-9)
    frame["ATR"] = ta.volatility.AverageTrueRange(frame["High"], frame["Low"], frame["Close"], window=14).average_true_range()
    frame["Momentum"] = frame["Close"] - frame["Close"].shift(10)
    frame["Volatility"] = frame["Close"].rolling(10).std()
    frame["Price_chg_5d"] = frame["Close"].pct_change(5)
    frame["Vol_MA_10"] = frame["Volume"].rolling(10).mean()
    frame["Volume_change"] = frame["Volume"].pct_change() * 100
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    return frame


def fetch_sentiment(company_name: str) -> tuple[float, list[dict[str, Any]]]:
    scores: list[float] = []
    articles: list[dict[str, Any]] = []

    if NEWSAPI_KEY:
        try:
            newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
            payload = newsapi.get_everything(q=company_name, language="en", sort_by="publishedAt", page_size=8)
            for article in payload.get("articles", []):
                title = (article.get("title") or "").strip()
                if not title:
                    continue
                score = analyzer.polarity_scores(title)["compound"]
                scores.append(score)
                articles.append(
                    {
                        "title": title,
                        "source": (article.get("source") or {}).get("name", "NewsAPI"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "sentiment_score": score,
                    }
                )
        except Exception:
            pass

    if GoogleNews is not None:
        try:
            google_news = GoogleNews(country="IN", lang="en")
            payload = google_news.search(f"{company_name} stock", when="3d")
            for item in payload.get("entries", [])[:6]:
                title = (item.get("title") or "").strip()
                if not title:
                    continue
                score = analyzer.polarity_scores(title)["compound"]
                scores.append(score)
                articles.append(
                    {
                        "title": title,
                        "source": "Google News",
                        "url": item.get("link"),
                        "published_at": item.get("published"),
                        "sentiment_score": score,
                    }
                )
        except Exception:
            pass

    avg = float(np.mean(scores)) if scores else 0.0
    return avg, articles[:12]


def heuristic_prediction(feature_frame: pd.DataFrame, sentiment_score: float) -> dict[str, Any]:
    frame = feature_frame.copy()
    latest = frame.iloc[-1]
    bullish_score = sum(
        [
            latest["Close"] > latest["SMA_20"],
            latest["RSI"] < 70,
            latest["MACD"] > latest["MACD_signal"],
            sentiment_score >= 0,
        ]
    )
    bearish_score = sum(
        [
            latest["Close"] < latest["SMA_20"],
            latest["RSI"] > 30,
            latest["MACD"] < latest["MACD_signal"],
            sentiment_score < 0,
        ]
    )

    if bullish_score >= bearish_score:
        prediction_label = "UP"
        confidence = 50 + bullish_score * 8
    else:
        prediction_label = "DOWN"
        confidence = 50 + bearish_score * 8

    if prediction_label == "UP" and latest["RSI"] < 70 and latest["Close"] > latest["SMA_20"] and latest["MACD"] > latest["MACD_signal"]:
        signal = "BUY"
    elif prediction_label == "DOWN" and latest["RSI"] > 30 and latest["Close"] < latest["SMA_20"] and latest["MACD"] < latest["MACD_signal"]:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "prediction": prediction_label,
        "signal": signal,
        "confidence": round(float(min(confidence, 92)), 2),
        "feature_importance": [
            {"feature": "RSI", "value": 0.24},
            {"feature": "MACD", "value": 0.22},
            {"feature": "SMA_20", "value": 0.19},
            {"feature": "Volume_change", "value": 0.13},
            {"feature": "Sentiment_score", "value": 0.22},
        ],
        "model_used": "Rule-based fallback",
    }


def make_prediction(feature_frame: pd.DataFrame, sentiment_score: float) -> dict[str, Any]:
    if not USE_TRAINED_MODEL:
        return heuristic_prediction(feature_frame, sentiment_score)

    frame = feature_frame.copy()
    frame["Sentiment_score"] = sentiment_score

    try:
        model, feature_cols = load_model_bundle()
        latest = frame.iloc[-1]
        x = frame[feature_cols].tail(1).replace([np.inf, -np.inf], np.nan)
        x = x.fillna(x.median(numeric_only=True)).fillna(0)

        prediction = int(model.predict(x)[0])
        probability = float(model.predict_proba(x)[0][prediction]) * 100

        if prediction == 1 and latest["RSI"] < 70 and latest["Close"] > latest["SMA_20"] and latest["MACD"] > latest["MACD_signal"]:
            signal = "BUY"
        elif prediction == 0 and latest["RSI"] > 30 and latest["Close"] < latest["SMA_20"] and latest["MACD"] < latest["MACD_signal"]:
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "prediction": "UP" if prediction == 1 else "DOWN",
            "signal": signal,
            "confidence": round(probability, 2),
            "feature_importance": [
                {"feature": feature, "value": float(value)}
                for feature, value in zip(feature_cols, getattr(model, "feature_importances_", np.zeros(len(feature_cols))))
            ],
            "model_used": "XGBoost",
        }
    except Exception:
        return heuristic_prediction(feature_frame, sentiment_score)


def build_stock_snapshot(symbol: str, include_news: bool = False, allow_network: bool = False) -> dict[str, Any]:
    info = company_row(symbol)
    company_name = info["Company Name"] if info is not None else symbol
    sector = info["Industry"] if info is not None else "Unknown"
    ticker = f"{symbol.replace('.NS', '').upper()}.NS"

    features = load_feature_history(ticker, allow_network=allow_network)
    if features.empty:
        raise ValueError(f"No history available for {symbol}")

    sentiment_score = 0.0
    news_items: list[dict[str, Any]] = []
    if include_news:
        sentiment_score, news_items = fetch_sentiment(company_name)

    prediction = make_prediction(features, sentiment_score)
    latest = features.iloc[-1]
    previous_close = features.iloc[-2]["Close"] if len(features) > 1 else latest["Close"]
    change_pct = ((latest["Close"] - previous_close) / previous_close) * 100 if previous_close else 0.0

    snapshot = {
        "symbol": symbol.replace(".NS", "").upper(),
        "company_name": company_name,
        "sector": sector,
        "current_price": round(float(latest["Close"]), 2),
        "change_pct": round(float(change_pct), 2),
        "rsi": round(float(latest["RSI"]), 2),
        "macd": round(float(latest["MACD"]), 3),
        "sentiment_score": round(float(sentiment_score), 3),
        "signal": prediction["signal"],
        "prediction": prediction["prediction"],
        "confidence": prediction["confidence"],
        "market_cap": 0,
        "pe": 0,
        "book_value": 0,
        "roe": 0,
        "roce": 0,
        "dividend_yield": 0,
        "face_value": 0,
        "history": features.to_dict(orient="records"),
        "news": news_items,
        "feature_importance": prediction["feature_importance"],
        "model_used": prediction.get("model_used", "XGBoost"),
    }

    return apply_fundamentals(snapshot, get_fundamentals(snapshot["symbol"]))


def summary_rows(financial_frame: pd.DataFrame, key_name: str) -> list[dict[str, Any]]:
    if financial_frame is None or financial_frame.empty:
        return []

    frame = financial_frame.T.reset_index().rename(columns={"index": key_name})
    frame[key_name] = frame[key_name].astype(str)
    return frame.replace({np.nan: None}).to_dict(orient="records")


def enrich_detail(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "market_cap": snapshot.get("market_cap", 0),
        "pe": snapshot.get("pe", 0),
        "book_value": snapshot.get("book_value", 0),
        "roe": snapshot.get("roe", 0),
        "roce": snapshot.get("roce", 0),
        "dividend_yield": snapshot.get("dividend_yield", 0),
        "face_value": snapshot.get("face_value", 0),
        "about": f"{snapshot['company_name']} is part of the {snapshot['sector']} sector and is covered by the Sentimental Drive technical and sentiment engine.",
        "key_points": [
            f"Sector: {snapshot['sector']}",
            f"Signal: {snapshot['signal']}",
            f"Prediction: {snapshot['prediction']} ({snapshot['confidence']}%)",
            "Exchange: NSE",
        ],
    }

    source_counts = Counter(item.get("source", "Unknown") for item in snapshot["news"])
    source_breakdown = [{"source": source, "count": count} for source, count in source_counts.items()]

    detail = {
        **snapshot,
        **summary,
        "source_breakdown": source_breakdown,
        "quarters": [],
        "profit_and_loss": [],
        "balance_sheet": [],
    }
    return detail


@app.get("/")
def root():
    return {"message": "Sentimental Drive API is running"}


@app.get("/api/market")
def get_market():
    if angel_one_ready():
        return build_market_payload()

    return cached("market:fallback", 300, build_market_payload)


@app.get("/api/market-data")
def market_data_endpoint():
    return get_market_data()


@app.get("/api/bootstrap")
def get_bootstrap():
    def build():
        return {
            "market": get_market(),
            "stocks": get_stocks()["stocks"],
        }

    if angel_one_ready():
        return build()

    return cached("bootstrap:fallback", 120, build)


@app.websocket("/ws/market")
async def market_socket(websocket: WebSocket):
    await websocket.accept()
    last_revision = None

    try:
        while True:
            payload = build_market_payload()
            revision = payload.get("meta", {}).get("revision")

            if revision != last_revision:
                await websocket.send_json(payload)
                last_revision = revision

            await asyncio.sleep(1 if payload.get("meta", {}).get("is_live") else 5)
    except WebSocketDisconnect:
        return


@app.get("/api/stocks")
def get_stocks():
    def build():
        records = load_combined_latest_rows()
        if not records:
            records = []
            for symbol in available_symbols():
                try:
                    records.append(build_stock_snapshot(symbol, include_news=False, allow_network=False))
                except Exception:
                    continue
        else:
            records = apply_bulk_fundamentals(records)

        if angel_one_ready() and records:
            try:
                live_quotes = get_live_equity_quotes([record["symbol"] for record in records])
                records = [apply_live_quote(record, live_quotes.get(record["symbol"])) for record in records]
            except Exception:
                pass
        return {"stocks": records}

    ttl = 30 if angel_one_ready() else 900
    return cached(f"stocks:{'angel' if angel_one_ready() else 'fallback'}", ttl, build)


@app.get("/api/top-picks")
def get_top_picks():
    stocks = get_stocks()["stocks"]
    buy = sorted([stock for stock in stocks if stock["signal"] == "BUY"], key=lambda item: item["confidence"], reverse=True)[:6]
    sell = sorted([stock for stock in stocks if stock["signal"] == "SELL"], key=lambda item: item["confidence"], reverse=True)[:6]
    return {"buy": buy, "sell": sell}


@app.get("/api/stocks/{symbol}")
def get_stock_detail(symbol: str):
    clean_symbol = symbol.replace(".NS", "").upper()

    def build():
        snapshot = build_stock_snapshot(clean_symbol, include_news=True, allow_network=False)
        if angel_one_ready():
            try:
                snapshot = apply_live_quote(snapshot, get_live_equity_quote(clean_symbol))
            except Exception:
                pass
        detail = enrich_detail(snapshot)

        stocks = get_stocks()["stocks"]
        peers = [
            stock
            for stock in stocks
            if stock["symbol"] != clean_symbol and stock["sector"] == detail["sector"]
        ][:8]
        detail["peers"] = peers
        detail["stock"] = {
            key: value
            for key, value in detail.items()
            if key
            not in {
                "history",
                "news",
                "feature_importance",
                "quarters",
                "profit_and_loss",
                "balance_sheet",
                "peers",
                "source_breakdown",
                "stock",
            }
        }
        return detail

    try:
        ttl = 60 if angel_one_ready() else 1800
        mode = "angel" if angel_one_ready() else "fallback"
        return cached(f"detail:{clean_symbol}:{mode}", ttl, build)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
