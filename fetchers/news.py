"""Fetch comprehensive market-moving news with full article content for AI analysis."""

import requests
import feedparser
from config import NEWSAPI_KEY
from fetchers.scraper import scrape_article


# Google News RSS queries for market-moving categories
MARKET_NEWS_QUERIES = {
    "Fed & Policy": "federal+reserve+OR+interest+rate+OR+fomc+OR+treasury+OR+tariff+OR+trade+war",
    "Geopolitical": "geopolitical+OR+sanctions+OR+war+OR+conflict+OR+OPEC+OR+trade+deal",
    "Commodities": "oil+price+OR+gold+price+OR+commodity+OR+natural+gas+OR+copper",
    "Crypto News": "bitcoin+OR+ethereum+OR+crypto+regulation+OR+SEC+crypto",
}


def get_newsapi_top(category="business", count=8):
    """Get top headlines from NewsAPI with article content."""
    if not NEWSAPI_KEY:
        return []
    articles = []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "category": category,
                "country": "us",
                "pageSize": count,
                "apiKey": NEWSAPI_KEY,
            },
            timeout=10,
        )
        data = resp.json()
        for a in data.get("articles", [])[:count]:
            articles.append({
                "title": a.get("title", ""),
                "summary": a.get("description", ""),
                "text": a.get("content", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
            })
    except Exception:
        pass
    return articles


def get_google_news_by_query(query, count=3):
    """Get articles from Google News RSS for a specific query."""
    articles = []
    try:
        url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        seen = set()
        for entry in feed.entries[:count * 2]:
            clean = entry.title.split(" - ")[0]
            if clean not in seen:
                seen.add(clean)
                articles.append({
                    "title": entry.title,
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                })
            if len(articles) >= count:
                break
    except Exception:
        pass
    return articles


def get_google_news_top(count=8):
    """Get top general headlines from Google News RSS."""
    articles = []
    try:
        feed = feedparser.parse("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
        for entry in feed.entries[:count]:
            articles.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "url": entry.get("link", ""),
            })
    except Exception:
        pass
    return articles


def collect_all_news():
    """Collect all news from all sources, enriched with scraped content.

    Returns:
        dict with keys: 'top_news', 'fed_policy', 'geopolitical', 'commodities', 'crypto'
        Each value is a list of article dicts with 'title', 'text', 'summary', 'url'
    """
    result = {}

    # Top business headlines
    top = get_newsapi_top("business", 8)
    if len(top) < 4:
        top.extend(get_google_news_top(8))
    result["top_news"] = top

    # Category-specific news
    for category, query in MARKET_NEWS_QUERIES.items():
        key = category.lower().replace(" & ", "_").replace(" ", "_")
        result[key] = get_google_news_by_query(query, 4)

    # Scrape full content for the most important articles
    all_articles = []
    for key, articles in result.items():
        for a in articles[:4]:  # Top 4 per category
            all_articles.append(a)

    for article in all_articles:
        if article.get("url") and not article.get("text"):
            scraped = scrape_article(article["url"])
            if scraped["text"]:
                article["text"] = scraped["text"]
            if scraped["summary"] and not article.get("summary"):
                article["summary"] = scraped["summary"]

    return result


def format_news_section():
    """Return formatted news headlines (basic version without AI analysis)."""
    top = get_newsapi_top("business", 5)
    if not top:
        top = get_google_news_top(5)

    parts = ["\U0001F4F0 TOP NEWS"]
    for a in top[:5]:
        parts.append(f"  - {a['title']}")

    for category, query in MARKET_NEWS_QUERIES.items():
        items = get_google_news_by_query(query, 3)
        if items:
            parts.append(f"\n{category}:")
            for a in items:
                clean = a["title"].split(" - ")[0]
                parts.append(f"  - {clean}")

    return "\n".join(parts)
