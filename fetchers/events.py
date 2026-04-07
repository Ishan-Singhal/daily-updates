"""Fetch earnings calendar, economic events, and Fed activity."""

import yfinance as yf
import requests
import feedparser
from datetime import datetime, timedelta


def get_earnings_today():
    """Get stocks reporting earnings today using Yahoo Finance calendar."""
    lines = []
    try:
        from datetime import date

        today = date.today()
        # Use yfinance to get earnings calendar
        # Check major tickers for upcoming earnings
        major_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX",
            "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "SQ", "SHOP",
            "COIN", "SNOW", "PLTR", "UBER", "ABNB", "DIS", "NKE", "BA",
            "JPM", "GS", "MS", "BAC", "WFC", "C", "V", "MA",
            "UNH", "JNJ", "PFE", "MRK", "LLY", "ABBV",
            "XOM", "CVX", "COP", "WMT", "COST", "HD", "TGT",
        ]
        earnings_today = []
        for symbol in major_tickers:
            try:
                t = yf.Ticker(symbol)
                cal = t.calendar
                if cal is not None and not cal.empty:
                    # calendar can be a DataFrame or dict
                    if hasattr(cal, "to_dict"):
                        cal_dict = cal.to_dict()
                        earnings_date = cal_dict.get("Earnings Date", {})
                        if earnings_date:
                            for key, val in earnings_date.items():
                                if hasattr(val, "date") and val.date() == today:
                                    earnings_today.append(symbol)
                                    break
                    elif isinstance(cal, dict):
                        ed = cal.get("Earnings Date")
                        if ed and hasattr(ed, "date") and ed.date() == today:
                            earnings_today.append(symbol)
            except Exception:
                continue

            if len(earnings_today) >= 5:
                break

        if earnings_today:
            lines.append(f"  Reporting today: {', '.join(earnings_today)}")
        else:
            lines.append("  No major earnings today")

    except Exception as e:
        lines.append(f"  Earnings data unavailable: {e}")

    return lines


def get_economic_events():
    """Scrape economic calendar events from RSS feeds."""
    events = []
    try:
        # Forex Factory / Investing.com economic calendar via Google News
        feed = feedparser.parse(
            "https://news.google.com/rss/search?q=economic+calendar+today+fed+jobs+inflation&hl=en-US&gl=US&ceid=US:en"
        )
        seen = set()
        keywords = [
            "fed", "fomc", "cpi", "ppi", "jobs", "payroll", "gdp", "inflation",
            "interest rate", "unemployment", "retail sales", "housing",
            "consumer confidence", "ism", "manufacturing", "powell", "treasury",
        ]
        for entry in feed.entries[:20]:
            title = entry.title.lower()
            if any(kw in title for kw in keywords):
                clean = entry.title.split(" - ")[0]  # Remove source suffix
                if clean not in seen:
                    seen.add(clean)
                    events.append(f"  - {clean}")
            if len(events) >= 4:
                break
    except Exception:
        pass
    return events


def format_events_section():
    """Return formatted earnings & economic events section."""
    parts = ["\U0001F4C5 EARNINGS & EVENTS"]

    earnings = get_earnings_today()
    parts.extend(earnings)

    econ = get_economic_events()
    if econ:
        parts.append("\nEconomic Calendar:")
        parts.extend(econ)

    return "\n".join(parts)
