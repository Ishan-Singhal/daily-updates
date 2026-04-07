"""Fetch market data using yfinance and scrape top market-moving headlines."""

import yfinance as yf
from config import MARKET_TICKERS, TICKER_NAMES


def get_market_snapshot():
    """Get current/previous-close data for major indices."""
    lines = []
    for ticker in MARKET_TICKERS:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price
            prev = info.previous_close
            change = price - prev
            pct = (change / prev) * 100
            arrow = "+" if change >= 0 else ""
            name = TICKER_NAMES.get(ticker, ticker)
            lines.append(f"  {name}: {price:,.2f} ({arrow}{pct:.2f}%)")
        except Exception:
            lines.append(f"  {TICKER_NAMES.get(ticker, ticker)}: unavailable")
    return lines


def get_market_movers():
    """Scrape top market-moving headlines from Yahoo Finance RSS."""
    import feedparser

    feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")
    headlines = []
    for entry in feed.entries[:3]:
        headlines.append(f"  - {entry.title}")
    if not headlines:
        # Fallback: try Google News business feed
        feed = feedparser.parse(
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB"
        )
        for entry in feed.entries[:3]:
            headlines.append(f"  - {entry.title}")
    return headlines


def format_market_section():
    """Return formatted market section string."""
    parts = ["\U0001F4C8 MARKETS"]
    parts.extend(get_market_snapshot())

    movers = get_market_movers()
    if movers:
        parts.append("\nMarket Headlines:")
        parts.extend(movers)

    return "\n".join(parts)
