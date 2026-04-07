"""Prediction tracking and learning system.

Saves daily predictions, grades them against actual outcomes the next day,
and builds a track record the AI uses to improve future calls.
"""

import json
import os
from datetime import datetime, date, timedelta

import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PREDICTIONS_FILE = os.path.join(DATA_DIR, "predictions.json")
TRACK_RECORD_FILE = os.path.join(DATA_DIR, "track_record.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_json(path, data):
    _ensure_data_dir()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def save_predictions(predictions):
    """Save today's AI predictions for grading tomorrow.

    Args:
        predictions: dict with keys like:
            {
                "date": "2026-04-07",
                "trade_ideas": [
                    {"ticker": "XLE", "direction": "Buy", "reason": "..."},
                    ...
                ],
                "sectors_favor": ["Energy", "Financials"],
                "sectors_avoid": ["Consumer Disc", "Healthcare"],
                "risk_level": "Extreme",
                "sector_calls": [
                    {"sector": "Energy", "etf": "XLE", "direction": "Bullish"},
                    ...
                ]
            }
    """
    all_preds = _load_json(PREDICTIONS_FILE)
    today = date.today().isoformat()
    predictions["date"] = today
    all_preds[today] = predictions
    _save_json(PREDICTIONS_FILE, all_preds)
    print(f"  Saved {len(predictions.get('trade_ideas', []))} predictions for grading tomorrow")


def grade_yesterdays_predictions():
    """Compare yesterday's predictions against actual market outcomes.

    Returns:
        dict: grading results with hits, misses, and accuracy stats
        None: if no predictions to grade
    """
    all_preds = _load_json(PREDICTIONS_FILE)
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # Try yesterday, or the last weekday if yesterday was weekend
    pred = all_preds.get(yesterday)
    if not pred:
        # Check last 3 days for most recent prediction
        for i in range(2, 5):
            check_date = (date.today() - timedelta(days=i)).isoformat()
            pred = all_preds.get(check_date)
            if pred:
                yesterday = check_date
                break
    if not pred:
        return None

    results = {
        "prediction_date": yesterday,
        "graded_date": date.today().isoformat(),
        "trade_grades": [],
        "sector_grades": [],
        "total_correct": 0,
        "total_calls": 0,
    }

    # Grade individual trade ideas
    for idea in pred.get("trade_ideas", []):
        ticker = idea.get("ticker", "")
        direction = idea.get("direction", "").lower()
        if not ticker:
            continue

        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) < 2:
                continue

            prev_close = hist.iloc[-2]["Close"]
            today_close = hist.iloc[-1]["Close"]
            actual_pct = ((today_close - prev_close) / prev_close) * 100

            # Determine if prediction was correct
            predicted_up = direction in ["buy", "bullish", "long"]
            predicted_down = direction in ["sell", "short", "bearish"]
            actual_up = actual_pct > 0.1   # >0.1% counts as up
            actual_down = actual_pct < -0.1

            correct = (predicted_up and actual_up) or (predicted_down and actual_down)
            # "Watch" is always neutral - neither right nor wrong
            if direction == "watch":
                continue

            results["total_calls"] += 1
            if correct:
                results["total_correct"] += 1

            results["trade_grades"].append({
                "ticker": ticker,
                "predicted": direction,
                "actual_move": f"{actual_pct:+.2f}%",
                "correct": correct,
            })
        except Exception:
            continue

    # Grade sector calls
    sector_etfs = {
        "energy": "XLE", "tech": "XLK", "technology": "XLK",
        "financials": "XLF", "healthcare": "XLV",
        "consumer disc": "XLY", "consumer discretionary": "XLY",
        "consumer staples": "XLP", "industrials": "XLI",
        "utilities": "XLU", "real estate": "XLRE", "materials": "XLB",
    }

    for call in pred.get("sector_calls", []):
        sector = call.get("sector", "").lower()
        direction = call.get("direction", "").lower()
        etf = sector_etfs.get(sector, call.get("etf", ""))
        if not etf:
            continue

        try:
            t = yf.Ticker(etf)
            hist = t.history(period="2d")
            if len(hist) < 2:
                continue

            prev_close = hist.iloc[-2]["Close"]
            today_close = hist.iloc[-1]["Close"]
            actual_pct = ((today_close - prev_close) / prev_close) * 100

            predicted_up = direction in ["bullish", "favor", "buy"]
            predicted_down = direction in ["bearish", "avoid", "sell"]
            actual_up = actual_pct > 0.1
            actual_down = actual_pct < -0.1

            correct = (predicted_up and actual_up) or (predicted_down and actual_down)
            results["total_calls"] += 1
            if correct:
                results["total_correct"] += 1

            results["sector_grades"].append({
                "sector": call.get("sector", sector),
                "etf": etf,
                "predicted": direction,
                "actual_move": f"{actual_pct:+.2f}%",
                "correct": correct,
            })
        except Exception:
            continue

    # Calculate accuracy
    if results["total_calls"] > 0:
        results["accuracy"] = round(results["total_correct"] / results["total_calls"] * 100, 1)
    else:
        results["accuracy"] = None

    # Save to track record
    track = _load_json(TRACK_RECORD_FILE)
    track[results["graded_date"]] = results
    _save_json(TRACK_RECORD_FILE, track)

    return results


def get_learning_context(lookback_days=14):
    """Build a learning context string from recent track record.

    Returns a formatted string summarizing recent prediction accuracy,
    common mistakes, and patterns to adjust for.
    """
    track = _load_json(TRACK_RECORD_FILE)
    if not track:
        return ""

    # Get recent entries
    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    recent = {k: v for k, v in track.items() if k >= cutoff}
    if not recent:
        return ""

    # Aggregate stats
    total_correct = 0
    total_calls = 0
    sector_misses = {}  # Track which sectors we get wrong most
    ticker_misses = {}  # Track which tickers we get wrong most
    direction_bias = {"bullish_correct": 0, "bullish_total": 0,
                      "bearish_correct": 0, "bearish_total": 0}
    wrong_calls = []    # Recent wrong calls for learning

    for date_key, result in sorted(recent.items()):
        total_correct += result.get("total_correct", 0)
        total_calls += result.get("total_calls", 0)

        for grade in result.get("trade_grades", []):
            direction = grade.get("predicted", "").lower()
            is_bull = direction in ["buy", "bullish", "long"]
            is_bear = direction in ["sell", "short", "bearish"]

            if is_bull:
                direction_bias["bullish_total"] += 1
                if grade.get("correct"):
                    direction_bias["bullish_correct"] += 1
            elif is_bear:
                direction_bias["bearish_total"] += 1
                if grade.get("correct"):
                    direction_bias["bearish_correct"] += 1

            if not grade.get("correct"):
                ticker = grade.get("ticker", "")
                ticker_misses[ticker] = ticker_misses.get(ticker, 0) + 1
                wrong_calls.append(
                    f"  - {date_key}: Called {direction.upper()} on {ticker}, "
                    f"actual was {grade.get('actual_move', '?')}"
                )

        for grade in result.get("sector_grades", []):
            if not grade.get("correct"):
                sector = grade.get("sector", "")
                sector_misses[sector] = sector_misses.get(sector, 0) + 1
                wrong_calls.append(
                    f"  - {date_key}: Called {grade.get('predicted', '?').upper()} on "
                    f"{sector} ({grade.get('etf', '')}), actual was {grade.get('actual_move', '?')}"
                )

    if total_calls == 0:
        return ""

    accuracy = round(total_correct / total_calls * 100, 1)

    # Build learning summary
    lines = [
        f"\n=== YOUR TRACK RECORD (last {lookback_days} days) ===",
        f"Overall accuracy: {accuracy}% ({total_correct}/{total_calls} correct)",
    ]

    # Directional bias check
    if direction_bias["bullish_total"] > 0:
        bull_acc = round(direction_bias["bullish_correct"] / direction_bias["bullish_total"] * 100, 1)
        lines.append(f"Bullish call accuracy: {bull_acc}% ({direction_bias['bullish_correct']}/{direction_bias['bullish_total']})")
    if direction_bias["bearish_total"] > 0:
        bear_acc = round(direction_bias["bearish_correct"] / direction_bias["bearish_total"] * 100, 1)
        lines.append(f"Bearish call accuracy: {bear_acc}% ({direction_bias['bearish_correct']}/{direction_bias['bearish_total']})")

    # Sectors we keep getting wrong
    if sector_misses:
        worst_sectors = sorted(sector_misses.items(), key=lambda x: x[1], reverse=True)[:3]
        lines.append(f"\nSectors you've been WRONG on most: {', '.join(f'{s} ({c}x)' for s, c in worst_sectors)}")
        lines.append("  -> Be extra cautious with directional calls on these sectors")

    # Tickers we keep getting wrong
    if ticker_misses:
        worst_tickers = sorted(ticker_misses.items(), key=lambda x: x[1], reverse=True)[:3]
        lines.append(f"Tickers you've been WRONG on most: {', '.join(f'{t} ({c}x)' for t, c in worst_tickers)}")
        lines.append("  -> Reconsider your assumptions about these names")

    # Recent wrong calls for direct learning
    if wrong_calls:
        lines.append(f"\nRecent WRONG calls to learn from:")
        lines.extend(wrong_calls[-10:])  # Last 10 wrong calls

    lines.append("\nUse this track record to calibrate your confidence. If you've been wrong on a sector or ticker recently, either flip your bias or downgrade to 'Watch' instead of a directional call.")
    lines.append("=== END TRACK RECORD ===\n")

    return "\n".join(lines)


def format_grading_section():
    """Format yesterday's prediction grades for the daily brief."""
    results = grade_yesterdays_predictions()
    if not results:
        return ""

    lines = ["\U0001F4CA YESTERDAY'S SCORECARD"]

    if results["accuracy"] is not None:
        emoji = "\u2705" if results["accuracy"] >= 60 else "\u26A0\uFE0F" if results["accuracy"] >= 40 else "\u274C"
        lines.append(f"  {emoji} Accuracy: {results['accuracy']}% ({results['total_correct']}/{results['total_calls']} correct)")

    for grade in results.get("trade_grades", []):
        icon = "\u2705" if grade["correct"] else "\u274C"
        lines.append(
            f"  {icon} {grade['ticker']}: called {grade['predicted'].upper()}, "
            f"moved {grade['actual_move']}"
        )

    for grade in results.get("sector_grades", []):
        icon = "\u2705" if grade["correct"] else "\u274C"
        lines.append(
            f"  {icon} {grade['sector']} ({grade['etf']}): called {grade['predicted'].upper()}, "
            f"moved {grade['actual_move']}"
        )

    return "\n".join(lines)
