"""Fetch high-impact business deals, M&A, IPOs, and major tech moves that affect markets."""

import requests
import feedparser
from config import NEWSAPI_KEY
from fetchers.scraper import scrape_article


# Google News RSS queries for high-impact business events
BUSINESS_QUERIES = {
    "M&A / Deals": "merger+OR+acquisition+OR+buyout+OR+%22billion+deal%22+OR+IPO+OR+SPAC",
    "Big Tech Moves": "apple+OR+google+OR+microsoft+OR+nvidia+OR+amazon+stock+OR+earnings+OR+guidance",
    "AI Industry": "artificial+intelligence+deal+OR+AI+investment+OR+AI+partnership+OR+AI+regulation",
}


def get_newsapi_business():
    """Get market-moving business/tech headlines from NewsAPI."""
    if not NEWSAPI_KEY:
        return []

    articles = []
    try:
        # Business headlines
        resp = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "category": "business",
                "country": "us",
                "pageSize": 8,
                "apiKey": NEWSAPI_KEY,
            },
            timeout=10,
        )
        data = resp.json()
        for a in data.get("articles", [])[:8]:
            articles.append({
                "title": a.get("title", ""),
                "summary": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
            })
    except Exception:
        pass
    return articles


def get_google_business_rss():
    """Scrape high-impact business news from Google News RSS by category."""
    all_articles = []
    seen_titles = set()

    for category, query in BUSINESS_QUERIES.items():
        try:
            url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                clean_title = entry.title.split(" - ")[0]
                if clean_title not in seen_titles:
                    seen_titles.add(clean_title)
                    all_articles.append({
                        "title": entry.title,
                        "summary": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "category": category,
                    })
        except Exception:
            continue

    return all_articles


def get_all_market_news():
    """Combine all sources into a single list of market-moving articles with content."""
    # Get headlines from both sources
    articles = get_newsapi_business()
    if len(articles) < 5:
        articles.extend(get_google_business_rss())

    # Scrape full content for top articles (for AI analysis)
    for article in articles[:10]:
        if article.get("url"):
            scraped = scrape_article(article["url"])
            if scraped["text"]:
                article["text"] = scraped["text"]
                if scraped["summary"]:
                    article["summary"] = scraped["summary"]

    return articles


def format_tech_section():
    """Return formatted high-impact business news section (without AI analysis - that's added by orchestrator)."""
    articles = get_google_business_rss()

    parts = ["\U0001F4BC BIG MOVES & DEALS"]
    if articles:
        for a in articles[:6]:
            parts.append(f"  - {a['title']}")
    else:
        parts.append("  No major deals/moves detected")

    return "\n".join(parts)
