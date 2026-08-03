"""AI-powered market insight analyzer using Gemini 3.6 Flash (free tier)."""

import os
import re
import time
from datetime import datetime

from openai import OpenAI
from config import GEMINI_API_KEY
from fetchers.memory import DATA_DIR, get_learning_context, save_predictions

MODEL = "gemini-3.6-flash"
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5
FAILURE_LOG = os.path.join(DATA_DIR, "generation_failures.log")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=GEMINI_API_KEY,
        )
    return _client


def _log_failure(step, error):
    """Persist AI-call failures so silent outages (e.g. a dead GEMINI_API_KEY)
    are visible after the fact, not just lost in a print() nobody reads."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FAILURE_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}  [{step}]  {error}\n")


def _call_with_retries(step, **kwargs):
    """Call the AI with retries on transient failures. Raises the last
    exception if every attempt fails."""
    client = _get_client()
    last_error = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            if response.choices[0].finish_reason == "length":
                # Response got cut off mid-output (e.g. max_tokens too small
                # for this model's reasoning-token overhead) — visible but
                # not treated as a hard failure, since partial output may
                # still parse fine.
                msg = f"response truncated (finish_reason=length, max_tokens={kwargs.get('max_tokens')})"
                print(f"  [{step}] warning: {msg}")
                _log_failure(step, msg)
            return response
        except Exception as e:
            last_error = e
            print(f"  [{step}] attempt {attempt}/{RETRY_ATTEMPTS} failed: {e}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS)
    _log_failure(step, last_error)
    raise last_error


ANALYSIS_PROMPT = """You are a world-class market strategist at a top hedge fund, writing the morning intelligence brief that portfolio managers read before the opening bell.

{learning_context}

For EACH news item below, provide deep analysis in this exact format:

**[HEADLINE]**
WHAT: [1-2 sentences - the actual substance. Not "JPMorgan said something about rates" but "JPMorgan's chief economist warned the Fed may not cut rates until Q1 2027 due to sticky services inflation at 4.2%"]
WHY IT MATTERS: [2-3 sentences - the second and third order effects. Connect the dots between this news and specific market mechanics. Example: "This kills the rate-cut narrative that's been supporting tech multiples at 28x forward earnings. If the 10Y reprices to 4.5%, the fair value on QQQ drops ~8%"]
TRADE SIGNAL: [Bullish/Bearish/Neutral] for [specific sectors, stocks, or asset classes]
CONFIDENCE: [High/Medium/Low] - [why this confidence level — is this priced in already? Is there ambiguity?]
WATCH: [1-3 specific ticker symbols to monitor today because of this news]

---

Rules:
- Be SPECIFIC. Not "tech stocks may fall" but "NVDA and AMD face 5-8% downside risk if 10Y breaks 4.5%"
- Explain the MECHANISM. Why does this news cause that price action? What's the transmission channel?
- Flag if the news is ALREADY PRICED IN. A headline from 2 days ago reprinted today has zero alpha.
- If two headlines are about the same event, consolidate them into one deeper analysis.
- Skip irrelevant noise (local news, human interest stories, entertainment).

Here are the news items to analyze:

{articles}
"""

WATCHLIST_PROMPT = """You are the head of trading at a top fund. Based on ALL of today's intelligence below, generate the morning action plan.

{learning_context}

Format your response EXACTLY like this:

TOP PLAYS TODAY:
1. [TICKER] - [Buy/Sell/Short/Watch] at [approximate entry price or "market open"] - [2 sentences: the specific catalyst driving this trade today, and where you'd take profit or cut loss]
2. [TICKER] - [action] at [price] - [reasoning]
3. [TICKER] - [action] at [price] - [reasoning]
4. [TICKER] - [action] at [price] - [reasoning]
5. [TICKER] - [action] at [price] - [reasoning]

SECTOR ROTATION PLAYS:
  OVERWEIGHT: [2-3 sectors] - [specific reason tied to today's news/data]
  UNDERWEIGHT: [1-2 sectors] - [specific reason]

RISK LEVEL TODAY: [Low/Medium/High/Extreme]
KEY RISK: [The single biggest thing that could blow up today's thesis — be specific]

CONTRARIAN TAKE: [One non-consensus view worth considering — what is the market getting wrong today?]

Rules:
- Every trade idea needs a SPECIFIC CATALYST happening TODAY, not "long-term growth story"
- Include approximate entry levels, not just "buy"
- If your track record shows you've been wrong on a sector/ticker, acknowledge it and adjust
- Don't just chase momentum — identify where the market is mispricing the news

Here is today's complete market intelligence:
{context}
"""


def analyze_news(articles):
    """Send articles to Gemini 3.6 Flash for deep market impact analysis."""
    if not GEMINI_API_KEY:
        return _fallback_analysis(articles)

    learning = get_learning_context()

    # Build article summaries for the prompt
    article_text = ""
    for i, a in enumerate(articles, 1):
        content = a.get("summary") or (a.get("text") or "")[:800]
        article_text += f"\n{i}. {a['title']}\n{content}\n"

    try:
        response = _call_with_retries(
            "analyze_news",
            model=MODEL,
            reasoning_effort="high",
            messages=[
                {"role": "user", "content": ANALYSIS_PROMPT.format(
                    articles=article_text,
                    learning_context=learning,
                )},
            ],
            max_tokens=36000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  AI analysis failed after retries ({e}), using fallback")
        return _fallback_analysis(articles)


def generate_ai_watchlist(news_context):
    """Generate AI-powered actionable watchlist and save predictions for grading."""
    if not GEMINI_API_KEY:
        return ""

    learning = get_learning_context()

    try:
        response = _call_with_retries(
            "generate_ai_watchlist",
            model=MODEL,
            reasoning_effort="high",
            messages=[
                {"role": "user", "content": WATCHLIST_PROMPT.format(
                    context=news_context,
                    learning_context=learning,
                )},
            ],
            max_tokens=30000,
        )
        watchlist_text = response.choices[0].message.content

        # Extract and save predictions for tomorrow's grading
        _extract_and_save_predictions(watchlist_text)

        return watchlist_text
    except Exception as e:
        print(f"  AI watchlist generation failed after retries: {e}")
        return (
            "⚠️ AI ACTION PLAN GENERATION FAILED — no new trade ideas were "
            f"recorded today.\nError: {e}\nCheck GEMINI_API_KEY and Gemini API status; "
            f"see {FAILURE_LOG} for the full history."
        )


def _extract_and_save_predictions(watchlist_text):
    """Parse the AI's watchlist output and save structured predictions."""
    predictions = {
        "trade_ideas": [],
        "sector_calls": [],
    }

    sector_etf_map = {
        "energy": "XLE", "tech": "XLK", "technology": "XLK",
        "financials": "XLF", "healthcare": "XLV",
        "consumer disc": "XLY", "consumer discretionary": "XLY",
        "consumer staples": "XLP", "industrials": "XLI",
        "utilities": "XLU", "real estate": "XLRE", "materials": "XLB",
        "communication": "XLC", "communications": "XLC",
    }

    lines = watchlist_text.split("\n")
    current_sector_direction = None  # Track OVERWEIGHT vs UNDERWEIGHT context

    for line in lines:
        line = line.strip()

        # Parse trade ideas: "1. TICKER - Buy/Sell/Short/Watch ..."
        trade_match = re.match(
            r'^\d+\.\s*\*?\*?([A-Z]{1,5})\*?\*?\s*[-–]\s*(Buy|Sell|Short|Watch|Long)',
            line, re.IGNORECASE
        )
        if trade_match:
            ticker = trade_match.group(1)
            direction = trade_match.group(2)
            predictions["trade_ideas"].append({
                "ticker": ticker,
                "direction": direction,
                "raw": line,
            })

        # Track which section we're in (OVERWEIGHT or UNDERWEIGHT)
        if "OVERWEIGHT" in line.upper() and "UNDER" not in line.upper():
            current_sector_direction = "Bullish"
        elif "UNDERWEIGHT" in line.upper() or "AVOID" in line.upper():
            current_sector_direction = "Bearish"
        elif line.startswith("#") or "RISK LEVEL" in line.upper() or "CONTRARIAN" in line.upper():
            current_sector_direction = None

        # Parse sector mentions within OVERWEIGHT/UNDERWEIGHT context
        if current_sector_direction:
            for sector, etf in sector_etf_map.items():
                if sector in line.lower():
                    # Avoid duplicates
                    already = any(
                        s["sector"].lower() == sector and s["direction"] == current_sector_direction
                        for s in predictions["sector_calls"]
                    )
                    if not already:
                        predictions["sector_calls"].append({
                            "sector": sector.title(),
                            "etf": etf,
                            "direction": current_sector_direction,
                        })

    if predictions["trade_ideas"] or predictions["sector_calls"]:
        save_predictions(predictions)


def _fallback_analysis(articles):
    """Keyword-based analysis when AI is unavailable."""
    lines = []
    for a in articles:
        title = a.get("title", "")
        text = (a.get("text") or a.get("summary") or "").lower()
        combined = (title + " " + text).lower()

        sentiment = "Neutral"
        bullish = ["surge", "soar", "rally", "beat", "upgrade", "buy", "growth", "record high", "deal"]
        bearish = ["crash", "plunge", "downgrade", "sell", "layoff", "miss", "warning", "cut", "tariff"]

        bull_count = sum(1 for w in bullish if w in combined)
        bear_count = sum(1 for w in bearish if w in combined)
        if bull_count > bear_count:
            sentiment = "Bullish"
        elif bear_count > bull_count:
            sentiment = "Bearish"

        sectors = []
        sector_map = {
            "tech": ["tech", "ai", "software", "chip", "semiconductor", "nvidia", "apple", "google"],
            "finance": ["bank", "fed", "rate", "jpmorgan", "goldman", "treasury", "yield"],
            "energy": ["oil", "gas", "opec", "crude", "energy"],
            "healthcare": ["pharma", "drug", "fda", "biotech"],
            "crypto": ["bitcoin", "crypto", "ethereum"],
            "defense": ["military", "defense", "war", "strike"],
        }
        for sector, keywords in sector_map.items():
            if any(kw in combined for kw in keywords):
                sectors.append(sector)

        sector_str = ", ".join(sectors) if sectors else "broad market"
        lines.append(f"  {title}")
        lines.append(f"    Signal: {sentiment} | Sectors: {sector_str}")
        lines.append("")

    return "\n".join(lines)
