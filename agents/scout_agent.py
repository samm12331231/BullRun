"""
scout_agent.py — Scout Agent (Regime Detection)

Role: Fetches SPY price data and uses technical indicators to classify
the current market into one of four regimes: BULLISH, BEARISH, NEUTRAL, VOLATILE.

This is the "eyes" of BullRun — it tells us WHAT the market is doing.

Input:  None (fetches its own data from Alpaca/Yahoo Finance)
Output: A dictionary with regime label, confidence, and key metrics
"""

import yfinance as yf
import pandas as pd
import ta
from rich.console import Console
from config import (
    UNDERLYING, LOOKBACK_DAYS, ADX_TREND_THRESHOLD,
    ATR_VOLATILE_MULTIPLIER, EMA_FAST, EMA_SLOW
)

console = Console()


def run() -> dict:
    """
    Main entry point for the Scout Agent.
    Classifies the current SPY market regime.
    """

    console.print("[bold cyan][Scout][/bold cyan] Scanning market regime...")

    # ── Step 1: Fetch historical OHLCV data ──────────────────────────────
    console.print(f"[dim]Fetching {LOOKBACK_DAYS} days of {UNDERLYING} data...[/dim]")
    raw = yf.download(UNDERLYING, period=f"{LOOKBACK_DAYS}d", interval="1d", progress=False)

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)

    if raw.empty or len(raw) < 30:
        raise ValueError("Not enough data from Yahoo Finance. Check ticker or connection.")

    df = raw.copy()
    current_price = float(df["Close"].iloc[-1])
    console.print(f"[dim]Loaded {len(df)} days. Latest close: ${current_price:,.2f}[/dim]")

    # ── Step 2: Compute ADX (trend strength) ─────────────────────────────
    df["ADX"] = ta.trend.adx(df["High"], df["Low"], df["Close"], window=14)
    current_adx = float(df["ADX"].iloc[-1])

    # ── Step 3: Compute ATR (volatility) ─────────────────────────────────
    df["ATR"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14)
    df["ATR_20avg"] = df["ATR"].rolling(20).mean()

    current_atr = float(df["ATR"].iloc[-1])
    avg_atr = float(df["ATR_20avg"].iloc[-1])
    atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0

    # ── Step 4: Compute EMAs ─────────────────────────────────────────────
    df["EMA_fast"] = ta.trend.ema_indicator(df["Close"], window=EMA_FAST)
    df["EMA_slow"] = ta.trend.ema_indicator(df["Close"], window=EMA_SLOW)

    ema_fast = float(df["EMA_fast"].iloc[-1])
    ema_slow = float(df["EMA_slow"].iloc[-1])
    price_above_ema = current_price > ema_fast
    ema_bullish = ema_fast > ema_slow

    # ── Step 5: Compute MACD ─────────────────────────────────────────────
    df["MACD"] = ta.trend.macd(df["Close"])
    df["MACD_hist"] = ta.trend.macd_diff(df["Close"])

    macd_now = float(df["MACD"].iloc[-1])
    hist_now = float(df["MACD_hist"].iloc[-1])
    hist_prev = float(df["MACD_hist"].iloc[-2])
    macd_bullish = macd_now > 0 and hist_now > hist_prev
    macd_bearish = macd_now < 0 and hist_now < hist_prev

    # ── Step 6: Compute RSI ──────────────────────────────────────────────
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    current_rsi = float(df["RSI"].iloc[-1])

    # ── Step 7: Classify regime ──────────────────────────────────────────
    # Priority: VOLATILE > TRENDING (BULLISH/BEARISH) > NEUTRAL
    if atr_ratio >= ATR_VOLATILE_MULTIPLIER:
        regime = "VOLATILE"
        confidence = min(1.0, (atr_ratio - ATR_VOLATILE_MULTIPLIER) / ATR_VOLATILE_MULTIPLIER + 0.5)
        reason = f"ATR is {atr_ratio:.2f}x its 20-day average (threshold: {ATR_VOLATILE_MULTIPLIER}x) — too volatile for defined-risk trades"

    elif current_adx > ADX_TREND_THRESHOLD:
        # Trending — determine direction
        bullish_signals = sum([
            price_above_ema,       # Price above fast EMA
            ema_bullish,           # Fast EMA above slow EMA
            macd_bullish,          # MACD positive and rising
            current_rsi > 50,      # RSI above neutral
        ])
        bearish_signals = sum([
            not price_above_ema,
            not ema_bullish,
            macd_bearish,
            current_rsi < 50,
        ])

        if bullish_signals >= 3:
            regime = "BULLISH"
            confidence = min(1.0, (current_adx - ADX_TREND_THRESHOLD) / 25 + 0.5)
            reason = f"ADX={current_adx:.1f} (>{ADX_TREND_THRESHOLD}), {bullish_signals}/4 indicators bullish"
        elif bearish_signals >= 3:
            regime = "BEARISH"
            confidence = min(1.0, (current_adx - ADX_TREND_THRESHOLD) / 25 + 0.5)
            reason = f"ADX={current_adx:.1f} (>{ADX_TREND_THRESHOLD}), {bearish_signals}/4 indicators bearish"
        else:
            regime = "NEUTRAL"
            confidence = min(1.0, (ADX_TREND_THRESHOLD - current_adx) / ADX_TREND_THRESHOLD + 0.3)
            reason = f"ADX={current_adx:.1f} but mixed signals — {bullish_signals} bullish, {bearish_signals} bearish"

    else:
        regime = "NEUTRAL"
        confidence = min(1.0, (ADX_TREND_THRESHOLD - current_adx) / ADX_TREND_THRESHOLD + 0.3)
        reason = f"ADX={current_adx:.1f} (<{ADX_TREND_THRESHOLD}) — no clear trend"

    confidence = round(confidence, 2)

    # ── Log results ──────────────────────────────────────────────────────
    regime_colors = {
        "BULLISH": "green", "BEARISH": "red",
        "NEUTRAL": "yellow", "VOLATILE": "magenta"
    }
    color = regime_colors.get(regime, "white")

    console.print(f"[bold {color}][Scout][/bold {color}] Regime: [bold]{regime}[/bold] (confidence: {confidence:.0%})")
    console.print(f"[dim]  ADX: {current_adx:.1f} | ATR ratio: {atr_ratio:.2f} | EMA: {'above' if price_above_ema else 'below'} | RSI: {current_rsi:.1f}[/dim]")
    console.print(f"[dim]  Reason: {reason}[/dim]")

    return {
        "regime": regime,
        "confidence": confidence,
        "reason": reason,
        "metrics": {
            "adx": round(current_adx, 2),
            "atr": round(current_atr, 2),
            "atr_20avg": round(avg_atr, 2),
            "atr_ratio": round(atr_ratio, 2),
            "current_price": round(current_price, 2),
            "ema_fast": round(ema_fast, 2),
            "ema_slow": round(ema_slow, 2),
            "price_above_ema": price_above_ema,
            "ema_bullish": ema_bullish,
            "macd": round(macd_now, 2),
            "macd_histogram": round(hist_now, 2),
            "macd_bullish": macd_bullish,
            "rsi": round(current_rsi, 2),
        },
    }


if __name__ == "__main__":
    result = run()
    import json
    print(json.dumps(result, indent=2))
