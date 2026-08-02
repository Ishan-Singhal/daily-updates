"""Fetch high-impact business deals, M&A, IPOs, and major tech moves that affect markets.

Sourced from direct-publisher RSS feeds (CNBC, TechCrunch) rather than NewsAPI or
Google News search RSS, so every story's full article text can be scraped for the
AI analysis instead of a truncated headline/snippet.
"""

import feedparser
from fetchers.scraper import scrape_article


# Direct-publisher RSS feeds per business category (no API key required)
BUSINESS_FEEDS = {
    "M&A / Deals": ["https://www.cnbc.com/id/10001147/device/rss/rss.html"],       # CNBC Business
    "Big Tech Moves": ["https://www.cnbc.com/id/19854910/device/rss/rss.html"],    # CNBC Technology
    "AI Industry": ["https://techcrunch.com/category/artificial-intelligence/feed/"],
}


def get_business_feed_articles():
    """Get high-impact business news from direct-publisher RSS feeds by category."""
    all_articles = []
    seen_titles = set()

    for category, feeds in BUSINESS_FEEDS.items():
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
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
    """Get business/deal news with full scraped article content (for AI analysis)."""
    articles = get_business_feed_articles()

    # Scrape full content for top articles so the AI works from complete articles
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
    articles = get_business_feed_articles()

    parts = ["\U0001F4BC BIG MOVES & DEALS"]
    if articles:
        for a in articles[:6]:
            parts.append(f"  - {a['title']}")
    else:
        parts.append("  No major deals/moves detected")

    return "\n".join(parts)
