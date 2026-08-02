"""Build the local trading-desk dashboard: simulated P&L, accuracy over time,
trade reasoning, and the AI's self-correction notes — from predictions.json
and track_record.json. No network calls; pure local data crunching.
"""

import json
import os
import re
from datetime import date, timedelta

from fetchers.memory import (
    DATA_DIR,
    PREDICTIONS_FILE,
    TRACK_RECORD_FILE,
    get_learning_context,
)

DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
DASHBOARD_HTML = os.path.join(DASHBOARD_DIR, "index.html")
TEMPLATE_PATH = os.path.join(DASHBOARD_DIR, "template.html")

NOTIONAL_PER_TRADE = 1000  # simulated $ risked per trade idea, equal-weighted

LONG_WORDS = {"buy", "bullish", "long"}
SHORT_WORDS = {"sell", "short", "bearish"}

_REASONING_RE = re.compile(
    r'^\d+\.\s*\*?\*?[A-Z]{1,5}\*?\*?\s*[-–]\s*'
    r'(?:Buy|Sell|Short|Watch|Long)\*?\*?\s*[-–]?\s*(.*)$',
    re.IGNORECASE,
)


def _load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _as_bool(value):
    return value is True or value == "True" or value == "true"


def _pct(actual_move):
    try:
        return float(str(actual_move).replace("%", "").replace("+", ""))
    except (TypeError, ValueError):
        return None


def _clean_reasoning(raw):
    if not raw:
        return ""
    m = _REASONING_RE.match(raw.strip())
    text = m.group(1) if m else raw
    return text.strip(" -–")


def _direction_sign(direction):
    d = (direction or "").lower()
    if d in LONG_WORDS:
        return 1
    if d in SHORT_WORDS:
        return -1
    return 0


def build_dashboard_data():
    predictions = _load_json(PREDICTIONS_FILE)
    track_record = _load_json(TRACK_RECORD_FILE)

    # ticker reasoning lookup: (prediction_date, ticker) -> cleaned reasoning text
    reasoning_lookup = {}
    for pred_date, pred in predictions.items():
        for idea in pred.get("trade_ideas", []):
            key = (pred_date, idea.get("ticker", ""))
            reasoning_lookup[key] = _clean_reasoning(idea.get("raw", ""))

    trades = []
    ticker_misses = {}
    sector_misses = {}

    for pred_date_key, result in sorted(track_record.items()):
        pred_date = result.get("prediction_date", pred_date_key)
        graded_date = result.get("graded_date", pred_date_key)

        for grade in result.get("trade_grades", []):
            sign = _direction_sign(grade.get("predicted"))
            pct = _pct(grade.get("actual_move"))
            if sign == 0 or pct is None:
                continue
            correct = _as_bool(grade.get("correct"))
            pnl_pct = sign * pct
            trades.append({
                "graded_date": graded_date,
                "prediction_date": pred_date,
                "ticker": grade.get("ticker", ""),
                "direction": grade.get("predicted", ""),
                "actual_move": grade.get("actual_move", ""),
                "correct": correct,
                "pnl_pct": round(pnl_pct, 2),
                "pnl_dollars": round(NOTIONAL_PER_TRADE * pnl_pct / 100, 2),
                "reasoning": reasoning_lookup.get((pred_date, grade.get("ticker", "")), ""),
            })
            if not correct:
                ticker_misses[grade.get("ticker", "")] = ticker_misses.get(grade.get("ticker", ""), 0) + 1

        for grade in result.get("sector_grades", []):
            if not _as_bool(grade.get("correct")):
                sector = grade.get("sector", "")
                sector_misses[sector] = sector_misses.get(sector, 0) + 1

    # equity curve: cumulative simulated $ P&L over time, ordered by when each
    # trade was actually resolved (graded), one point per graded trade
    trades.sort(key=lambda t: t["graded_date"])
    cumulative = 0
    equity_curve = []
    for t in trades:
        cumulative += t["pnl_dollars"]
        equity_curve.append({"date": t["graded_date"], "cumulative": round(cumulative, 2)})

    # accuracy over time: the combined (trades + sectors) accuracy already stored per
    # resolved prediction, ordered by when it was actually graded
    accuracy_curve = sorted(
        (
            {"date": r.get("graded_date", d), "accuracy": r["accuracy"]}
            for d, r in track_record.items()
            if r.get("accuracy") is not None
        ),
        key=lambda p: p["date"],
    )

    total_correct = sum(1 for t in trades if t["correct"])
    total_trades = len(trades)
    win_rate = round(total_correct / total_trades * 100, 1) if total_trades else None

    best_trade = max(trades, key=lambda t: t["pnl_dollars"], default=None)
    worst_trade = min(trades, key=lambda t: t["pnl_dollars"], default=None)

    top_ticker_misses = sorted(ticker_misses.items(), key=lambda x: -x[1])[:5]
    top_sector_misses = sorted(sector_misses.items(), key=lambda x: -x[1])[:5]

    return {
        "generated_at": date.today().isoformat(),
        "notional_per_trade": NOTIONAL_PER_TRADE,
        "summary": {
            "total_pnl": round(cumulative, 2),
            "total_trades": total_trades,
            "win_rate": win_rate,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
        },
        "equity_curve": equity_curve,
        "accuracy_curve": accuracy_curve,
        "trades": list(reversed(trades)),  # newest first for the table
        "learning_context": get_learning_context(lookback_days=30),
        "misses": {
            "tickers": [{"name": k, "count": v} for k, v in top_ticker_misses],
            "sectors": [{"name": k, "count": v} for k, v in top_sector_misses],
        },
    }


def write_dashboard_html(data, out_path=DASHBOARD_HTML):
    with open(TEMPLATE_PATH, "r") as f:
        template = f.read()

    html = template.replace(
        "/*__DASHBOARD_DATA__*/null",
        json.dumps(data),
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(html)

    return out_path


def build_dashboard():
    """Regenerate dashboard/index.html from the latest predictions/track record."""
    data = build_dashboard_data()
    return write_dashboard_html(data)


if __name__ == "__main__":
    path = build_dashboard()
    print(f"Dashboard written to {path}")
