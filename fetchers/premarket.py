"""Fetch pre-market movers, futures, and sector performance."""

import yfinance as yf
import feedparser
import requests


# Futures tickers
FUTURES = {
    "ES=F": "S&P Futures",
    "NQ=F": "Nasdaq Futures",
    "YM=F": "Dow Futures",
    "CL=F": "Crude Oil",
    "GC=F": "Gold",
    "BTC-USD": "Bitcoin",
    "^TNX": "10Y Treasury",
}

# Sector ETFs for rotation analysis
SECTORS = {
    "XLK": "Tech",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLY": "Consumer Disc",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
}


def get_futures_snapshot():
    """Get futures/commodities/crypto prices and overnight moves."""
    lines = []
    for ticker, name in FUTURES.items():
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price
            prev = info.previous_close
            change = price - prev
            pct = (change / prev) * 100
            arrow = "+" if change >= 0 else ""
            # Compact formatting
            if name == "10Y Treasury":
                lines.append(f"  {name}: {price:.3f}% ({arrow}{change:.3f})")
            elif price > 1000:
                lines.append(f"  {name}: {price:,.0f} ({arrow}{pct:.2f}%)")
            else:
                lines.append(f"  {name}: {price:,.2f} ({arrow}{pct:.2f}%)")
        except Exception:
            lines.append(f"  {name}: unavailable")
    return lines


def get_sector_performance():
    """Get sector ETF performance to identify rotation."""
    results = []
    for ticker, name in SECTORS.items():
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.last_price
            prev = info.previous_close
            pct = ((price - prev) / prev) * 100
            results.append((name, pct))
        except Exception:
            continue

    if not results:
        return []

    results.sort(key=lambda x: x[1], reverse=True)
    lines = []
    # Show top 3 and bottom 3
    for name, pct in results[:3]:
        lines.append(f"  \u2b06 {name}: {pct:+.2f}%")
    for name, pct in results[-3:]:
        lines.append(f"  \u2b07 {name}: {pct:+.2f}%")
    return lines


def get_premarket_movers():
    """Scrape pre-market most active / biggest movers from Yahoo Finance RSS."""
    movers = []
    try:
        # Yahoo Finance trending tickers
        trending = yf.Tickers(
            "AAPL MSFT GOOGL AMZN NVDA TSLA META AMD SMCI PLTR"
        )
        results = []
        for symbol, t in trending.tickers.items():
            try:
                info = t.fast_info
                price = info.last_price
                prev = info.previous_close
                pct = ((price - prev) / prev) * 100
                results.append((symbol, price, pct))
            except Exception:
                continue
        # Sort by absolute % change to find biggest movers
        results.sort(key=lambda x: abs(x[2]), reverse=True)
        for symbol, price, pct in results[:5]:
            arrow = "\u2b06" if pct >= 0 else "\u2b07"
            movers.append(f"  {arrow} {symbol}: ${price:,.2f} ({pct:+.2f}%)")
    except Exception:
        pass
    return movers


def format_premarket_section():
    """Return formatted pre-market intelligence section."""
    parts = ["\U0001F30D FUTURES & OVERNIGHT"]
    parts.extend(get_futures_snapshot())

    parts.append("\n\U0001F504 SECTOR ROTATION")
    sectors = get_sector_performance()
    if sectors:
        parts.extend(sectors)
    else:
        parts.append("  Unavailable")

    parts.append("\n\U0001F525 BIGGEST MOVERS")
    movers = get_premarket_movers()
    if movers:
        parts.extend(movers)
    else:
        parts.append("  Unavailable")

    return "\n".join(parts)
