"""
STEP 1: Data collection module for stock + text sources.

This module downloads:
1) Historical OHLCV stock prices from Yahoo Finance
2) News headlines from NewsAPI
3) Tweets from Twitter API v2 (via Tweepy)
4) Reddit posts from PRAW

Outputs are saved under data/raw/ as CSV files.
"""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yfinance as yf

try:
    import praw
except ImportError:  # pragma: no cover - handled at runtime
    praw = None

try:
    import tweepy
except ImportError:  # pragma: no cover - handled at runtime
    tweepy = None

try:
    from newsapi import NewsApiClient
except ImportError:  # pragma: no cover - handled at runtime
    NewsApiClient = None


LOGGER = logging.getLogger("sentiment_stock_prediction.data_collection")

DEFAULT_TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
DEFAULT_QUERIES = {
    "RELIANCE.NS": "Reliance Industries stock OR Reliance share",
    "TCS.NS": "TCS stock OR Tata Consultancy Services share",
    "INFY.NS": "Infosys stock OR Infosys share",
}


@dataclass(frozen=True)
class DataCollectionConfig:
    tickers: List[str] = field(default_factory=lambda: DEFAULT_TICKERS.copy())
    start_date: str = "2021-01-01"
    end_date: str = field(default_factory=lambda: date.today().isoformat())
    raw_data_dir: Path = field(default_factory=lambda: Path("data/raw"))


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging for consistent module output."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def download_stock_data(tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
    """Download daily OHLCV stock data from Yahoo Finance for each ticker."""
    records: List[pd.DataFrame] = []

    for ticker in tickers:
        LOGGER.info("Downloading stock data for %s", ticker)
        try:
            stock_df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
        except Exception as exc:
            LOGGER.exception("Failed to download stock data for %s: %s", ticker, exc)
            continue

        if stock_df.empty:
            LOGGER.warning("No stock rows returned for %s", ticker)
            continue

        stock_df = stock_df.reset_index()
        stock_df.columns = [str(col).lower().replace(" ", "_") for col in stock_df.columns]
        stock_df["ticker"] = ticker
        records.append(stock_df)

    if not records:
        return pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "adj_close", "volume", "ticker"]
        )

    combined = pd.concat(records, ignore_index=True)
    combined = combined.sort_values(["ticker", "date"]).reset_index(drop=True)
    return combined


def fetch_news_data(
    query_map: Dict[str, str], start_date: str, end_date: str, max_pages_per_ticker: int = 2
) -> pd.DataFrame:
    """
    Fetch news headlines from NewsAPI.

    Required env var:
    - NEWSAPI_KEY
    """
    columns = [
        "ticker",
        "source",
        "published_at",
        "title",
        "description",
        "content",
        "author",
        "url",
    ]
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        LOGGER.warning("NEWSAPI_KEY is not set. Skipping NewsAPI collection.")
        return pd.DataFrame(columns=columns)
    if NewsApiClient is None:
        LOGGER.warning("newsapi-python is not installed. Skipping NewsAPI collection.")
        return pd.DataFrame(columns=columns)

    client = NewsApiClient(api_key=api_key)
    items = []

    for ticker, query in query_map.items():
        LOGGER.info("Fetching news for %s", ticker)
        for page in range(1, max_pages_per_ticker + 1):
            try:
                response = client.get_everything(
                    q=query,
                    language="en",
                    from_param=start_date,
                    to=end_date,
                    sort_by="publishedAt",
                    page_size=100,
                    page=page,
                )
            except Exception as exc:
                LOGGER.exception("NewsAPI fetch failed for %s page %s: %s", ticker, page, exc)
                break

            articles = response.get("articles", [])
            if not articles:
                break

            for article in articles:
                items.append(
                    {
                        "ticker": ticker,
                        "source": (article.get("source") or {}).get("name"),
                        "published_at": article.get("publishedAt"),
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "content": article.get("content"),
                        "author": article.get("author"),
                        "url": article.get("url"),
                    }
                )

    if not items:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(items)
    df = df.drop_duplicates(subset=["ticker", "title", "published_at", "url"])
    return df.reset_index(drop=True)


def fetch_twitter_data(query_map: Dict[str, str], max_results_per_ticker: int = 200) -> pd.DataFrame:
    """
    Fetch tweets using Twitter API v2 via Tweepy.

    Required env var:
    - TWITTER_BEARER_TOKEN
    """
    columns = [
        "ticker",
        "tweet_id",
        "created_at",
        "text",
        "lang",
        "like_count",
        "reply_count",
        "retweet_count",
        "quote_count",
    ]
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        LOGGER.warning("TWITTER_BEARER_TOKEN is not set. Skipping Twitter collection.")
        return pd.DataFrame(columns=columns)
    if tweepy is None:
        LOGGER.warning("tweepy is not installed. Skipping Twitter collection.")
        return pd.DataFrame(columns=columns)

    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
    items = []

    for ticker, query in query_map.items():
        LOGGER.info("Fetching tweets for %s", ticker)
        # Keep query simple and language-filtered for sentiment analysis.
        full_query = f"({query}) lang:en -is:retweet"
        fetched = 0

        try:
            paginator = tweepy.Paginator(
                client.search_recent_tweets,
                query=full_query,
                max_results=100,
                tweet_fields=["created_at", "lang", "public_metrics"],
                expansions=None,
                limit=10,
            )

            for response in paginator:
                tweets = response.data or []
                for tweet in tweets:
                    metrics = tweet.public_metrics or {}
                    items.append(
                        {
                            "ticker": ticker,
                            "tweet_id": tweet.id,
                            "created_at": tweet.created_at,
                            "text": tweet.text,
                            "lang": tweet.lang,
                            "like_count": metrics.get("like_count"),
                            "reply_count": metrics.get("reply_count"),
                            "retweet_count": metrics.get("retweet_count"),
                            "quote_count": metrics.get("quote_count"),
                        }
                    )
                    fetched += 1
                    if fetched >= max_results_per_ticker:
                        break
                if fetched >= max_results_per_ticker:
                    break
        except Exception as exc:
            LOGGER.exception("Twitter fetch failed for %s: %s", ticker, exc)
            continue

    if not items:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(items)
    df = df.drop_duplicates(subset=["ticker", "tweet_id"])
    return df.reset_index(drop=True)


def fetch_reddit_data(query_map: Dict[str, str], limit_per_ticker: int = 200) -> pd.DataFrame:
    """
    Fetch Reddit submissions via PRAW.

    Required env vars:
    - REDDIT_CLIENT_ID
    - REDDIT_CLIENT_SECRET
    - REDDIT_USER_AGENT
    """
    columns = [
        "ticker",
        "post_id",
        "created_utc",
        "subreddit",
        "title",
        "selftext",
        "score",
        "num_comments",
        "url",
        "author",
    ]
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not (client_id and client_secret and user_agent):
        LOGGER.warning(
            "Reddit credentials are incomplete. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT."
        )
        return pd.DataFrame(columns=columns)
    if praw is None:
        LOGGER.warning("praw is not installed. Skipping Reddit collection.")
        return pd.DataFrame(columns=columns)

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    items = []

    for ticker, query in query_map.items():
        LOGGER.info("Fetching Reddit posts for %s", ticker)
        try:
            subreddit = reddit.subreddit("all")
            for submission in subreddit.search(query, sort="new", time_filter="all", limit=limit_per_ticker):
                items.append(
                    {
                        "ticker": ticker,
                        "post_id": submission.id,
                        "created_utc": submission.created_utc,
                        "subreddit": str(submission.subreddit),
                        "title": submission.title,
                        "selftext": submission.selftext,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "url": submission.url,
                        "author": str(submission.author) if submission.author else None,
                    }
                )
        except Exception as exc:
            LOGGER.exception("Reddit fetch failed for %s: %s", ticker, exc)
            continue

    if not items:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(items)
    df = df.drop_duplicates(subset=["ticker", "post_id"])
    return df.reset_index(drop=True)


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    """Persist dataset as CSV with consistent encoding and no index."""
    df.to_csv(path, index=False, encoding="utf-8")
    LOGGER.info("Saved %s rows to %s", len(df), path)


def run_data_collection(config: DataCollectionConfig) -> Dict[str, Path]:
    """Orchestrate full raw data ingestion for all configured sources."""
    _ensure_dir(config.raw_data_dir)

    query_map = {ticker: DEFAULT_QUERIES.get(ticker, ticker.replace(".NS", "")) for ticker in config.tickers}

    stock_df = download_stock_data(config.tickers, config.start_date, config.end_date)
    news_df = fetch_news_data(query_map, config.start_date, config.end_date)
    twitter_df = fetch_twitter_data(query_map)
    reddit_df = fetch_reddit_data(query_map)

    output_paths = {
        "stocks": config.raw_data_dir / "stocks_raw.csv",
        "news": config.raw_data_dir / "news_raw.csv",
        "twitter": config.raw_data_dir / "twitter_raw.csv",
        "reddit": config.raw_data_dir / "reddit_raw.csv",
    }

    save_dataframe(stock_df, output_paths["stocks"])
    save_dataframe(news_df, output_paths["news"])
    save_dataframe(twitter_df, output_paths["twitter"])
    save_dataframe(reddit_df, output_paths["reddit"])

    return output_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect raw stock/news/social data.")
    parser.add_argument(
        "--tickers",
        type=str,
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated Yahoo tickers (default: RELIANCE.NS,TCS.NS,INFY.NS)",
    )
    parser.add_argument("--start-date", type=str, default="2021-01-01", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, default=date.today().isoformat(), help="End date in YYYY-MM-DD format")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Output directory for raw CSV files")
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
    config = DataCollectionConfig(
        tickers=tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        raw_data_dir=Path(args.raw_dir),
    )

    LOGGER.info(
        "Starting data collection | tickers=%s | range=%s to %s",
        config.tickers,
        config.start_date,
        config.end_date,
    )
    paths = run_data_collection(config)
    LOGGER.info("Data collection complete. Files: %s", paths)


if __name__ == "__main__":
    main()
