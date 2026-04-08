"""
Daily Updates Agent (v2 - Learning Edition)
Powered by Claude Opus 4.6 via Puter.com

Features:
- AI-analyzed news with deep market impact analysis
- Actionable trade ideas with entry levels
- Learns from yesterday's mistakes via prediction grading
- Futures, crypto, sector rotation, earnings, weather
"""

import sys
import io
from datetime import datetime

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from fetchers.market import format_market_section
from fetchers.premarket import format_premarket_section
from fetchers.weather import format_weather_section
from fetchers.news import collect_all_news
from fetchers.tech_news import get_all_market_news
from fetchers.events import format_events_section
from fetchers.watchlist import format_watchlist_section
from fetchers.analyzer import analyze_news, generate_ai_watchlist
from fetchers.memory import format_grading_section
from fetchers.sender import send_sms


def fetch_section(fn, fallback_label):
    """Safely fetch a section, returning error string on failure."""
    try:
        return fn()
    except Exception as e:
        return f"{fallback_label}\n  Error: {e}"


def build_full_report():
    """Build the complete AI-analyzed daily brief with learning feedback."""
    now = datetime.now()

    sections = [
        f"{'='*50}",
        f"  DAILY MARKET BRIEF - {now.strftime('%A, %B %d, %Y %I:%M %p')}",
        f"  Powered by Claude Opus 4.6",
        f"{'='*50}",
    ]

    # === SECTION 0: Grade yesterday's predictions ===
    print("  Grading yesterday's predictions...")
    grading = fetch_section(format_grading_section, "SCORECARD")
    if grading and grading.strip():
        sections.append("")
        sections.append(grading)

    # === SECTION 1: Market Data ===
    print("  Fetching futures & overnight data...")
    premarket = fetch_section(format_premarket_section, "FUTURES & OVERNIGHT")
    sections.append("")
    sections.append(premarket)

    print("  Fetching market indices...")
    market = fetch_section(format_market_section, "MARKETS")
    sections.append("")
    sections.append(market)

    print("  Fetching quantitative signals...")
    quant_watchlist = fetch_section(format_watchlist_section, "WATCHLIST")
    sections.append("")
    sections.append(quant_watchlist)

    # === SECTION 2: Collect ALL news ===
    print("  Collecting news from all sources...")
    all_news = {}
    try:
        all_news = collect_all_news()
    except Exception as e:
        print(f"  News collection error: {e}")

    print("  Collecting business deals & big moves...")
    biz_articles = []
    try:
        biz_articles = get_all_market_news()
    except Exception as e:
        print(f"  Business news error: {e}")

    # Combine and deduplicate
    all_articles = []
    for key, articles in all_news.items():
        all_articles.extend(articles)
    all_articles.extend(biz_articles)

    seen = set()
    unique_articles = []
    for a in all_articles:
        title = a.get("title", "").split(" - ")[0].strip()
        if title and title not in seen:
            seen.add(title)
            unique_articles.append(a)

    # === SECTION 3: AI Deep Analysis (Opus 4.6) ===
    ai_analysis = ""
    print(f"  Opus 4.6 analyzing {len(unique_articles)} articles...")
    if unique_articles:
        ai_analysis = analyze_news(unique_articles[:15])
        sections.append("")
        sections.append(f"{'='*50}")
        sections.append("  \U0001F9E0 AI MARKET ANALYSIS (Claude Opus 4.6)")
        sections.append(f"{'='*50}")
        sections.append(ai_analysis)

    # === SECTION 4: AI Action Plan (with learning context) ===
    print("  Opus 4.6 generating trade ideas (learning from past calls)...")
    context_parts = [premarket, market, quant_watchlist]
    if ai_analysis:
        context_parts.append(ai_analysis)
    full_context = "\n\n".join(context_parts)

    ai_watchlist = generate_ai_watchlist(full_context)
    if ai_watchlist:
        sections.append("")
        sections.append(f"{'='*50}")
        sections.append("  \U0001F3AF AI ACTION PLAN (Claude Opus 4.6)")
        sections.append(f"{'='*50}")
        sections.append(ai_watchlist)

    # === SECTION 5: Events & Weather ===
    print("  Fetching earnings & events...")
    sections.append("")
    sections.append(fetch_section(format_events_section, "EARNINGS & EVENTS"))

    print("  Fetching weather...")
    sections.append("")
    sections.append(fetch_section(format_weather_section, "WEATHER"))

    sections.append("")
    sections.append(f"{'='*50}")

    return "\n".join(sections)


def build_sms_message(full_report):
    """Extract the most actionable parts for SMS."""
    now = datetime.now()
    parts = [f"Daily Brief {now.strftime('%m/%d')}:\n"]

    # Include scorecard if present
    if "SCORECARD" in full_report and "Accuracy" in full_report:
        score_start = full_report.index("SCORECARD")
        score_lines = full_report[score_start:].split("\n")
        for line in score_lines[1:4]:
            if line.strip():
                parts.append(line)
        parts.append("")

    # Extract AI action plan
    if "AI ACTION PLAN" in full_report:
        action_start = full_report.index("AI ACTION PLAN")
        rest = full_report[action_start:]
        lines = rest.split("\n")
        action_lines = []
        for line in lines[2:]:
            if "=====" in line:
                break
            action_lines.append(line)
        parts.append("\n".join(action_lines[:20]))
    else:
        parts.append(fetch_section(format_premarket_section, "FUTURES"))

    parts.append(f"\n{fetch_section(format_weather_section, 'WEATHER')}")

    return "\n".join(parts)


def main():
    print(f"[{datetime.now()}] Building daily market brief (Opus 4.6)...\n")

    full_report = build_full_report()

    # Preview mode: print full report without sending
    if "--preview" in sys.argv:
        print(full_report)
        return

    # Always print full report to console/log
    print(full_report)

    # Send the FULL report via email (no need to truncate like SMS)
    print("\nSending email...")
    send_sms(full_report)
    print("Done.")


if __name__ == "__main__":
    main()
