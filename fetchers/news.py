"""Fetch comprehensive market-moving news with full article content for AI analysis.

Sourced from direct-publisher RSS feeds (CNBC, CoinDesk, OilPrice, etc.) rather than
NewsAPI or Google News search RSS: NewsAPI truncates article content to ~200 chars,
and Google News search RSS links are Google redirect pages that can't be scraped for
full text. Direct-publisher feeds link straight to the article, so every story gets
its full text scraped for the AI analysis instead of a truncated snippet.
"""

import feedparser
from fetchers.scraper import scrape_article


# Direct-publisher RSS feeds per market-moving category (no API key required)
MARKET_NEWS_FEEDS = {
    "top_news": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Top News
        "https://www.cnbc.com/id/10000664/device/rss/rss.html",   # CNBC Finance
    ],
    "fed_policy": [
        "https://www.cnbc.com/id/20910258/device/rss/rss.html",   # CNBC Economy
    ],
    "geopolitical": [
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",  # CNBC World
    ],
    "commodities": [
        "https://oilprice.com/rss/main",
        "https://www.investing.com/rss/commodities.rss",
    ],
    "crypto": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
    ],
}


def get_feed_articles(url, count=4):
    """Get articles from a direct-publisher RSS feed."""
    articles = []
    try:
        feed = feedparser.parse(url)
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
    """Collect all news from all sources, enriched with scraped full-article content.

    Returns:
        dict with keys: 'top_news', 'fed_policy', 'geopolitical', 'commodities', 'crypto'
        Each value is a list of article dicts with 'title', 'text', 'summary', 'url'
    """
    result = {}
    for key, feeds in MARKET_NEWS_FEEDS.items():
        articles = []
        seen = set()
        for feed_url in feeds:
            for a in get_feed_articles(feed_url, 4):
                clean = a["title"].split(" - ")[0].strip()
                if clean and clean not in seen:
                    seen.add(clean)
                    articles.append(a)
        result[key] = articles

    # Scrape full content for the most important articles so the AI analyzes
    # complete articles, not just headline/snippet fragments.
    all_articles = []
    for key, articles in result.items():
        for a in articles[:4]:  # Top 4 per category
            all_articles.append(a)

    for article in all_articles:
        if article.get("url"):
            scraped = scrape_article(article["url"])
            if scraped["text"]:
                article["text"] = scraped["text"]
            if scraped["summary"]:
                article["summary"] = scraped["summary"]

    return result


def format_news_section():
    """Return formatted news headlines (basic version without AI analysis)."""
    parts = ["\U0001F4F0 TOP NEWS"]
    for a in get_feed_articles(MARKET_NEWS_FEEDS["top_news"][0], 5):
        parts.append(f"  - {a['title']}")

    labels = {
        "fed_policy": "Fed & Policy",
        "geopolitical": "Geopolitical",
        "commodities": "Commodities",
        "crypto": "Crypto News",
    }
    for key, label in labels.items():
        items = []
        for feed_url in MARKET_NEWS_FEEDS[key]:
            items.extend(get_feed_articles(feed_url, 3))
        if items:
            parts.append(f"\n{label}:")
            for a in items[:3]:
                clean = a["title"].split(" - ")[0]
                parts.append(f"  - {clean}")

    return "\n".join(parts)
