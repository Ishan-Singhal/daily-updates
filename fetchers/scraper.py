"""Scrape full article content from news URLs."""

import requests
from newspaper import Article


def scrape_article(url, timeout=10):
    """Extract title, text, and summary from a news article URL."""
    try:
        article = Article(url)
        article.download()
        article.parse()

        # Try NLP summary if enough text
        try:
            article.nlp()
            summary = article.summary
        except Exception:
            summary = article.text[:500] if article.text else ""

        return {
            "title": article.title or "",
            "text": article.text[:2000] if article.text else "",
            "summary": summary[:500] if summary else "",
            "authors": article.authors,
            "url": url,
        }
    except Exception:
        return {"title": "", "text": "", "summary": "", "authors": [], "url": url}


def scrape_articles_batch(urls, max_articles=10):
    """Scrape multiple articles, skipping failures."""
    results = []
    for url in urls[:max_articles]:
        article = scrape_article(url)
        if article["text"]:
            results.append(article)
    return results
