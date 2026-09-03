"""
backtest.py — Historical backtest for BullRun

Runs the Scout's regime detection + Risk Engine gates on 90 days of SPY data.
Simulates bull call spread entries when regime is BULLISH, tracks P&L with
take-profit (50%) and stop-loss (30%) rules, and outputs an equity curve.

Usage:
    python backtest.py              # prints stats + saves backtest_results.json
    python backtest.py --json       # JSON only (for API endpoint)
"""

import json
import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import RISK_LIMITS, ADX_TREND_THRESHOLD, ATR_VOLATILE_MULTIPLIER, EMA_FAST, EMA_SLOW
from agents.risk_engine import RiskEngine


# ── Config ──────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 100_000.0
LOOKBACK = 90           # days of history
ENTRYDelta_LONG = 0.58  # long leg delta target
ENTRY_WIDTH = 3.0       # spread width target
MAX_CONTRACTS = 2       # max contracts per trade
TAKE_PROFIT_PCT = 0.50  # close at +50% of max profit
STOP_LOSS_PCT = 0.30    # close at -30% of debit


def fetch_data() -> pd.DataFrame:
    """Fetch 90+ days of SPY OHLCV from yfinance."""
    ticker = yf.Ticker("SPY")
    df = ticker.history(period="120d")  # extra buffer for indicator warmup
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def compute_regime(df: pd.DataFrame, i: int) -> dict:
    """Compute regime at index i using data up to that point."""
    window = df.iloc[max(0, i - 60):i + 1].copy()
    if len(window) < 35:
        return {"regime": "NEUTRAL", "adx": 0, "rsi": 50, "atr_ratio": 1.0, "current_price": float(window["Close"].iloc[-1])}

    close = window["Close"]
    high = window["High"]
    low = window["Low"]

    adx_series = ta.trend.adx(high, low, close, window=14)
    adx = float(adx_series.iloc[-1]) if not np.isnan(adx_series.iloc[-1]) else 0

    atr = ta.volatility.average_true_range(high, low, close, window=14)
    atr_20 = atr.rolling(20).mean()
    current_atr = float(atr.iloc[-1]) if not np.isnan(atr.iloc[-1]) else 1.0
    avg_atr = float(atr_20.iloc[-1]) if not np.isnan(atr_20.iloc[-1]) else current_atr
    atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0

    ema_fast = ta.trend.ema_indicator(close, window=EMA_FAST)
    ema_slow = ta.trend.ema_indicator(close, window=EMA_SLOW)
    ef = float(ema_fast.iloc[-1]) if not np.isnan(ema_fast.iloc[-1]) else close.iloc[-1]
    es = float(ema_slow.iloc[-1]) if not np.isnan(ema_slow.iloc[-1]) else close.iloc[-1]

    rsi_series = ta.momentum.rsi(close, window=14)
    rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50

    macd_hist = ta.trend.macd_diff(close)
    mh_now = float(macd_hist.iloc[-1]) if not np.isnan(macd_hist.iloc[-1]) else 0
    mh_prev = float(macd_hist.iloc[-2]) if len(macd_hist) > 1 and not np.isnan(macd_hist.iloc[-2]) else 0

    current_price = float(close.iloc[-1])
    price_above_ema = current_price > ef
    ema_bullish = ef > es
    macd_bullish = mh_now > 0 and mh_now > mh_prev

    # Classify regime (same logic as scout_agent.py)
    if atr_ratio >= ATR_VOLATILE_MULTIPLIER:
        regime = "VOLATILE"
    elif adx > ADX_TREND_THRESHOLD:
        bullish_signals = sum([price_above_ema, ema_bullish, macd_bullish, rsi > 50])
        bearish_signals = sum([not price_above_ema, not ema_bullish, mh_now < 0 and mh_now < mh_prev, rsi < 50])
        if bullish_signals >= 2:
            regime = "BULLISH"
        elif bearish_signals >= 2:
            regime = "BEARISH"
        else:
            regime = "NEUTRAL"
    else:
        regime = "NEUTRAL"

    return {
        "regime": regime,
        "adx": round(adx, 2),
        "rsi": round(rsi, 2),
        "atr_ratio": round(atr_ratio, 2),
        "current_price": round(current_price, 2),
    }


def simulate_option_price(current_price: float, strike_offset: float, days_to_exp: int, iv: float = 0.20) -> float:
    """Rough Black-Scholes-inspired option price estimate for backtesting."""
    # Simplified: intrinsic + time value approximation
    intrinsic = max(0, current_price - (current_price + strike_offset))
    time_value = current_price * iv * np.sqrt(days_to_exp / 365) * 0.4
    return round(max(0.05, intrinsic + time_value), 2)


def run_backtest() -> dict:
    """Run the full backtest and return results."""
    print("[Backtest] Fetching SPY data...")
    df = fetch_data()
    print(f"[Backtest] Loaded {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}")

    engine = RiskEngine()
    capital = INITIAL_CAPITAL
    peak_equity = INITIAL_CAPITAL
    equity_curve = []
    trades = []
    open_position = None

    # Daily tracking
    daily_pnl = 0.0
    winning_days = 0
    losing_days = 0

    for i in range(35, len(df)):  # start after indicator warmup
        date = df.index[i].date()
        current_price = float(df["Close"].iloc[i])
        day_high = float(df["High"].iloc[i])
        day_low = float(df["Low"].iloc[i])

        # ── Check open position exits ───────────────────────────────────
        if open_position is not None:
            entry = open_position["entry_price"]
            width = open_position["width"]
            max_profit = (width - open_position["net_debit"]) * 100 * open_position["qty"]
            max_loss = open_position["net_debit"] * 100 * open_position["qty"]

            # Simulate current option value (simplified)
            price_change = current_price - open_position["entry_underlying"]
            # Long call gains, short call loses — net effect for bull call spread
            long_gained = max(0, price_change * 0.6)  # delta ~0.6
            short_lost = max(0, price_change * 0.33)   # delta ~0.33
            current_spread_value = open_position["net_debit"] + long_gained - short_lost
            unrealized_pnl = (current_spread_value - open_position["net_debit"]) * 100 * open_position["qty"]

            # Take profit check
            if unrealized_pnl >= max_profit * TAKE_PROFIT_PCT:
                realized = round(unrealized_pnl, 2)
                capital += realized
                trades.append({
                    "entry_date": open_position["entry_date"],
                    "exit_date": str(date),
                    "underlying": "SPY",
                    "strategy": "BULL_CALL_SPREAD",
                    "entry_price": entry,
                    "exit_price": round(current_price, 2),
                    "qty": open_position["qty"],
                    "pnl": realized,
                    "exit_reason": "TAKE_PROFIT",
                    "regime_at_entry": open_position["regime"],
                })
                daily_pnl += realized
                open_position = None

            # Stop loss check
            elif unrealized_pnl <= -max_loss * STOP_LOSS_PCT:
                realized = round(unrealized_pnl, 2)
                capital += realized
                trades.append({
                    "entry_date": open_position["entry_date"],
                    "exit_date": str(date),
                    "underlying": "SPY",
                    "strategy": "BULL_CALL_SPREAD",
                    "entry_price": entry,
                    "exit_price": round(current_price, 2),
                    "qty": open_position["qty"],
                    "pnl": realized,
                    "exit_reason": "STOP_LOSS",
                    "regime_at_entry": open_position["regime"],
                })
                daily_pnl += realized
                open_position = None

            # Max hold (10 days)
            elif (i - open_position["entry_idx"]) >= 10:
                realized = round(unrealized_pnl, 2)
                capital += realized
                trades.append({
                    "entry_date": open_position["entry_date"],
                    "exit_date": str(date),
                    "underlying": "SPY",
                    "strategy": "BULL_CALL_SPREAD",
                    "entry_price": entry,
                    "exit_price": round(current_price, 2),
                    "qty": open_position["qty"],
                    "pnl": realized,
                    "exit_reason": "MAX_HOLD",
                    "regime_at_entry": open_position["regime"],
                })
                daily_pnl += realized
                open_position = None

        # ── Compute regime ──────────────────────────────────────────────
        regime_data = compute_regime(df, i)
        regime = regime_data["regime"]

        # ── Only enter on BULLISH with ADX > threshold ──────────────────
        if regime == "BULLISH" and open_position is None:
            # Simulate a bull call spread proposal
            net_debit = round(ENTRY_WIDTH * 0.35, 2)  # ~35% of width as debit
            max_loss_per = net_debit * 100
            max_profit_per = (ENTRY_WIDTH - net_debit) * 100
            qty = min(MAX_CONTRACTS, max(1, int(RISK_LIMITS.max_risk_per_trade * capital / max_loss_per)))

            proposal = {
                "underlying": "SPY",
                "direction": "LONG",
                "strategy": "BULL_CALL_SPREAD",
                "max_loss_per_contract": max_loss_per,
                "max_profit_per_contract": max_profit_per,
                "quantity": qty,
                "recommended_contracts": qty,
                "total_risk_proposed": round(max_loss_per * qty, 2),
                "conviction_score": 82,  # Assume qualifying conviction for backtest
                "bid_ask_spread": 0.10,
                "spread_width": ENTRY_WIDTH,
                "dte": 14,
            }

            portfolio_state = {
                "equity": capital,
                "open_position_count": 0,
                "current_portfolio_exposure": 0,
                "available_cash": capital,
                "open_positions": [],
                "unrealized_pnl": 0,
            }

            result = engine.check(proposal, portfolio_state)

            if result["status"] == "PASS":
                cost = net_debit * 100 * qty
                capital -= cost  # debit paid
                open_position = {
                    "entry_date": str(date),
                    "entry_idx": i,
                    "entry_price": net_debit,
                    "entry_underlying": current_price,
                    "width": ENTRY_WIDTH,
                    "net_debit": net_debit,
                    "qty": qty,
                    "regime": regime,
                }

        # ── Record equity ───────────────────────────────────────────────
        unrealized = 0
        if open_position is not None:
            price_change = current_price - open_position["entry_underlying"]
            long_gained = max(0, price_change * 0.6)
            short_lost = max(0, price_change * 0.33)
            current_val = open_position["net_debit"] + long_gained - short_lost
            unrealized = (current_val - open_position["net_debit"]) * 100 * open_position["qty"]

        equity = capital + unrealized
        peak_equity = max(peak_equity, equity)

        equity_curve.append({
            "date": str(date),
            "equity": round(equity, 2),
            "regime": regime,
            "adx": regime_data["adx"],
            "price": regime_data["current_price"],
            "has_position": open_position is not None,
        })

    # ── Force close any open position at end ─────────────────────────────
    if open_position is not None:
        final_price = float(df["Close"].iloc[-1])
        price_change = final_price - open_position["entry_underlying"]
        long_gained = max(0, price_change * 0.6)
        short_lost = max(0, price_change * 0.33)
        current_val = open_position["net_debit"] + long_gained - short_lost
        realized = round((current_val - open_position["net_debit"]) * 100 * open_position["qty"], 2)
        capital += realized
        trades.append({
            "entry_date": open_position["entry_date"],
            "exit_date": str(df.index[-1].date()),
            "underlying": "SPY",
            "strategy": "BULL_CALL_SPREAD",
            "entry_price": open_position["entry_price"],
            "exit_price": round(final_price, 2),
            "qty": open_position["qty"],
            "pnl": realized,
            "exit_reason": "BACKTEST_END",
            "regime_at_entry": open_position["regime"],
        })

    # ── Compute stats ────────────────────────────────────────────────────
    total_pnl = round(capital - INITIAL_CAPITAL, 2)
    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] <= 0]
    total_trades = len(trades)

    # Regime distribution
    regimes = [e["regime"] for e in equity_curve]
    regime_counts = {r: regimes.count(r) for r in set(regimes)}

    # Risk gate rejections (count how many times gates would have blocked)
    rejections = 0
    for i in range(35, len(df)):
        rd = compute_regime(df, i)
        if rd["regime"] == "BULLISH":
            price = rd["current_price"]
            net_debit = round(ENTRY_WIDTH * 0.35, 2)
            max_loss_per = net_debit * 100
            qty = min(MAX_CONTRACTS, max(1, int(RISK_LIMITS.max_risk_per_trade * INITIAL_CAPITAL / max_loss_per)))
            proposal = {
                "underlying": "SPY", "direction": "LONG", "strategy": "BULL_CALL_SPREAD",
                "max_loss_per_contract": max_loss_per, "quantity": qty,
                "total_risk_proposed": round(max_loss_per * qty, 2),
                "conviction_score": 82, "bid_ask_spread": 0.10,
                "spread_width": ENTRY_WIDTH, "dte": 14,
            }
            ps = {"equity": INITIAL_CAPITAL, "open_position_count": 0, "open_positions": [], "unrealized_pnl": 0}
            r = engine.check(proposal, ps)
            if r["status"] == "REJECT":
                rejections += 1

    # Max drawdown from equity curve
    equities = [e["equity"] for e in equity_curve]
    peak = equities[0]
    max_dd = 0
    for eq in equities:
        peak = max(peak, eq)
        dd = (peak - eq) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)

    results = {
        "summary": {
            "initial_capital": INITIAL_CAPITAL,
            "final_capital": round(capital, 2),
            "total_pnl": total_pnl,
            "total_return_pct": round(total_pnl / INITIAL_CAPITAL * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate_pct": round(len(winning_trades) / total_trades * 100, 1) if total_trades > 0 else 0,
            "avg_win": round(np.mean([t["pnl"] for t in winning_trades]), 2) if winning_trades else 0,
            "avg_loss": round(np.mean([t["pnl"] for t in losing_trades]), 2) if losing_trades else 0,
            "risk_gate_rejections": rejections,
            "regime_distribution": regime_counts,
            "backtest_period": f"{df.index[35].date()} to {df.index[-1].date()}",
            "data_points": len(equity_curve),
        },
        "trades": trades,
        "equity_curve": equity_curve,
    }

    return results


def print_results(results: dict):
    """Pretty-print backtest results."""
    s = results["summary"]
    print("\n" + "=" * 60)
    print("  BULLRUN BACKTEST RESULTS")
    print("=" * 60)
    print(f"  Period:          {s['backtest_period']}")
    print(f"  Data Points:     {s['data_points']} days")
    print(f"  Initial Capital: ${s['initial_capital']:,.2f}")
    print(f"  Final Capital:   ${s['final_capital']:,.2f}")
    print(f"  Total P&L:       ${s['total_pnl']:+,.2f} ({s['total_return_pct']:+.2f}%)")
    print(f"  Max Drawdown:    {s['max_drawdown_pct']:.2f}%")
    print(f"  Total Trades:    {s['total_trades']}")
    print(f"  Win Rate:        {s['win_rate_pct']:.1f}% ({s['winning_trades']}W / {s['losing_trades']}L)")
    print(f"  Avg Win:         ${s['avg_win']:+,.2f}")
    print(f"  Avg Loss:        ${s['avg_loss']:+,.2f}")
    print(f"  Gate Rejections: {s['risk_gate_rejections']}")
    print(f"  Regime Mix:      {s['regime_distribution']}")
    print("=" * 60)

    if results["trades"]:
        print("\n  TRADES:")
        for t in results["trades"]:
            emoji = "✅" if t["pnl"] > 0 else "❌"
            print(f"  {emoji} {t['entry_date']} → {t['exit_date']} | {t['strategy']} | {t['qty']}x | "
                  f"P&L: ${t['pnl']:+,.2f} | Exit: {t['exit_reason']}")


if __name__ == "__main__":
    results = run_backtest()

    # Save results
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Backtest] Results saved to {out_path}")

    print_results(results)
