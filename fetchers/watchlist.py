"""Generate actionable stock & crypto watchlist based on catalysts, volume, and momentum."""

import yfinance as yf
from datetime import datetime, timedelta


# Stocks universe to scan
SCAN_STOCKS = [
    # Mega-cap tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AVGO", "ORCL", "CRM",
    # High-beta / momentum names
    "AMD", "SMCI", "PLTR", "MSTR", "COIN", "SNOW", "NET", "CRWD", "PANW", "DDOG",
    "SHOP", "ROKU", "RBLX", "AFRM", "SOFI", "HOOD", "RIVN", "LCID", "NIO", "MARA",
    # Financials
    "JPM", "GS", "MS", "BAC", "WFC", "C", "V", "MA", "AXP", "SCHW",
    # Healthcare / Pharma
    "UNH", "LLY", "NVO", "JNJ", "MRK", "PFE", "ABBV", "BMY", "MRNA", "BNTX",
    # Energy
    "XOM", "CVX", "COP", "OXY", "SLB",
    # Consumer / Industrial
    "WMT", "COST", "HD", "TGT", "NKE", "DIS", "BA", "CAT", "GE", "UPS",
    # ETFs for broad signals
    "SPY", "QQQ", "IWM", "XLK", "XLE", "XLF", "GLD", "TLT", "HYG",
]

# Crypto universe
SCAN_CRYPTO = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD",
    "ADA-USD", "AVAX-USD", "DOT-USD", "LINK-USD", "PEPE-USD",
    "ATOM-USD", "LTC-USD", "ARB-USD", "NEAR-USD", "INJ-USD",
    "HBAR-USD", "TRX-USD", "SHIB-USD", "BCH-USD", "AAVE-USD",
]


def scan_for_unusual_moves(symbols, asset_type="stock"):
    """Find assets with unusual price moves or volume spikes."""
    signals = []

    for symbol in symbols:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if hist.empty or len(hist) < 2:
                continue

            latest = hist.iloc[-1]
            prev = hist.iloc[-2]

            price = latest["Close"]
            prev_close = prev["Close"]
            pct_change = ((price - prev_close) / prev_close) * 100

            # Volume spike: today's volume vs 5-day average
            avg_vol = hist["Volume"].mean()
            vol_ratio = latest["Volume"] / avg_vol if avg_vol > 0 else 1

            # Momentum: 5-day cumulative move
            five_day_pct = ((price - hist.iloc[0]["Close"]) / hist.iloc[0]["Close"]) * 100

            # Signal scoring - crypto uses higher thresholds (more volatile)
            score = 0
            reasons = []
            move_thresh = 5 if asset_type == "crypto" else 3
            vol_thresh = 2.0 if asset_type == "crypto" else 1.8
            momentum_thresh = 10 if asset_type == "crypto" else 5

            if abs(pct_change) > move_thresh:
                score += 3
                direction = "up" if pct_change > 0 else "down"
                reasons.append(f"{pct_change:+.1f}% {direction}")

            if vol_ratio > vol_thresh:
                score += 2
                reasons.append(f"{vol_ratio:.1f}x avg vol")

            if abs(five_day_pct) > momentum_thresh:
                score += 1
                reasons.append(f"{five_day_pct:+.1f}% over 5d")

            if score >= 2:
                display = symbol.replace("-USD", "") if asset_type == "crypto" else symbol
                signals.append((display, price, pct_change, score, reasons))

        except Exception:
            continue

    signals.sort(key=lambda x: x[3], reverse=True)
    return signals[:6]


def scan_near_key_levels():
    """Find stocks near 52-week highs/lows (breakout/breakdown candidates)."""
    near_levels = []

    check_tickers = SCAN_STOCKS[:40]
    for symbol in check_tickers:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="1y")
            if hist.empty or len(hist) < 20:
                continue

            price = hist.iloc[-1]["Close"]
            high_52w = hist["High"].max()
            low_52w = hist["Low"].min()

            if price >= high_52w * 0.97:
                pct_from_high = ((price - high_52w) / high_52w) * 100
                near_levels.append((symbol, price, "near 52w HIGH", pct_from_high))
            elif price <= low_52w * 1.05:
                pct_from_low = ((price - low_52w) / low_52w) * 100
                near_levels.append((symbol, price, "near 52w LOW", pct_from_low))

        except Exception:
            continue

    return near_levels[:5]


def get_crypto_snapshot():
    """Get quick overview of major crypto prices."""
    lines = []
    top_crypto = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"]
    for symbol in top_crypto:
        try:
            t = yf.Ticker(symbol)
            info = t.fast_info
            price = info.last_price
            prev = info.previous_close
            pct = ((price - prev) / prev) * 100
            name = symbol.replace("-USD", "")
            if price > 100:
                lines.append(f"  {name}: ${price:,.0f} ({pct:+.2f}%)")
            else:
                lines.append(f"  {name}: ${price:,.4f} ({pct:+.2f}%)")
        except Exception:
            continue
    return lines


def format_watchlist_section():
    """Return formatted actionable watchlist section."""
    parts = ["\U0001F3AF TODAY'S STOCK WATCHLIST"]

    # Unusual stock activity
    stock_signals = scan_for_unusual_moves(SCAN_STOCKS, "stock")
    if stock_signals:
        parts.append("Unusual Activity:")
        for symbol, price, pct, score, reasons in stock_signals:
            reason_str = " | ".join(reasons)
            parts.append(f"  {'*' * min(score, 3)} {symbol} ${price:,.2f} - {reason_str}")
    else:
        parts.append("  No unusual stock signals")

    # Key levels
    levels = scan_near_key_levels()
    if levels:
        parts.append("\nKey Levels:")
        for symbol, price, level_type, pct in levels:
            parts.append(f"  {symbol} ${price:,.2f} - {level_type} ({pct:+.1f}%)")

    # Crypto section
    parts.append(f"\n\U0001FA99 CRYPTO")
    crypto_prices = get_crypto_snapshot()
    if crypto_prices:
        parts.extend(crypto_prices)

    crypto_signals = scan_for_unusual_moves(SCAN_CRYPTO, "crypto")
    if crypto_signals:
        parts.append("\nCrypto Movers:")
        for symbol, price, pct, score, reasons in crypto_signals:
            reason_str = " | ".join(reasons)
            if price > 100:
                parts.append(f"  {'*' * min(score, 3)} {symbol} ${price:,.0f} - {reason_str}")
            else:
                parts.append(f"  {'*' * min(score, 3)} {symbol} ${price:,.4f} - {reason_str}")

    return "\n".join(parts)
