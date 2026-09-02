"""
quant_agent.py — Quant Agent (Options Structure Selection)

Role: Takes the regime from Scout and selects the appropriate options structure.
Picks specific contracts (strikes, expiry) based on delta, liquidity, and DTE.
Calculates max loss, max profit, and breakeven for the proposed trade.

This is the "brain" of BullRun — it decides WHAT to trade.

Input:  regime_result dict from scout_agent.py
Output: A trade proposal dictionary with structure, legs, and risk metrics
"""

from datetime import datetime
from rich.console import Console
from config import (
    UNDERLYING, OPTION_CHAIN_EXPIRY_RANGE,
    LONG_LEG_DELTA_MIN, LONG_LEG_DELTA_MAX,
    SHORT_LEG_DELTA_MIN, SHORT_LEG_DELTA_MAX,
    MIN_SPREAD_WIDTH, MAX_SPREAD_WIDTH,
    MAX_BID_ASK_SPREAD, CONVICTION_WEIGHTS,
    CONVICTION_APPROVE, CONVICTION_WATCH,
)
from agents.data_service import get_option_chain

console = Console()


def run(regime_result: dict) -> dict:
    """Main entry point. Selects options structure based on regime."""

    regime = regime_result["regime"]
    metrics = regime_result["metrics"]

    console.print("[bold cyan][Quant][/bold cyan] Analyzing options opportunities...")

    # ── Step 1: Determine direction ────────────────────────────────────────
    if regime == "BULLISH":
        structure = "BULL_CALL_SPREAD"
        option_type = "call"
        console.print("[green][Quant][/green] Regime BULLISH → Bull Call Spread")
    elif regime == "BEARISH":
        structure = "BEAR_PUT_SPREAD"
        option_type = "put"
        console.print("[red][Quant][/red] Regime BEARISH → Bear Put Spread")
    else:
        console.print(f"[yellow][Quant][/yellow] Regime {regime} → NO TRADE")
        return _no_trade(regime)

    # ── Step 2: Fetch option chain via Alpaca ──────────────────────────────
    min_dte, max_dte = OPTION_CHAIN_EXPIRY_RANGE
    current_price = metrics["current_price"]

    chain = get_option_chain(
        symbol=UNDERLYING,
        min_dte=min_dte,
        max_dte=max_dte,
        option_type=option_type,
        min_strike=current_price - 15,
        max_strike=current_price + 15,
    )

    if not chain:
        console.print("[yellow][Quant] Live chain unavailable — creating structured options candidates[/yellow]")
        # Synthetic high-quality candidates around ATM for offline demo/paper testing
        chain = _generate_synthetic_chain(UNDERLYING, current_price, option_type, min_dte)

    console.print(f"[dim]Analyzing {len(chain)} contracts for optimal delta spread...[/dim]")

    # ── Step 3: Select legs ────────────────────────────────────────────────
    if structure == "BULL_CALL_SPREAD":
        result = _select_bull_call_spread(chain, current_price)
    else:
        result = _select_bear_put_spread(chain, current_price)

    if result["signal"] == "NO_TRADE":
        return result

    # ── Step 4: Conviction score & Dynamic Sizing ───────────────────────────
    conviction = _calculate_conviction(metrics, result, result.get("dte", 14), regime)
    result["conviction_score"] = conviction["score"]
    result["conviction_breakdown"] = conviction["breakdown"]

    # Position sizing by conviction (higher score = bigger position, within 2% rule)
    score = conviction["score"]
    max_loss_contract = result.get("max_loss_per_contract", 250.0)
    from config import RISK_LIMITS as _RL
    max_risk_allowed = _RL.max_risk_per_trade * 100_000

    if score >= 93:
        target_contracts = 3
    elif score >= 85:
        target_contracts = 2
    else:
        target_contracts = 1

    # Strictly cap contracts so total loss cannot exceed 2% portfolio risk
    max_contracts_by_risk = max(1, int(max_risk_allowed // max(1.0, max_loss_contract)))
    contracts = min(target_contracts, max_contracts_by_risk)

    result["quantity"] = contracts
    result["recommended_contracts"] = contracts
    result["total_risk_proposed"] = round(max_loss_contract * contracts, 2)
    result["total_profit_potential"] = round(result.get("max_profit_per_contract", 250.0) * contracts, 2)

    if score >= CONVICTION_APPROVE:
        result["signal"] = "PROPOSE"
        console.print(f"[bold green][Quant] Conviction: {score:.1f}/100 → PROPOSE ({contracts} contract{'s' if contracts > 1 else ''}, risk: ${result['total_risk_proposed']:,.0f})[/bold green]")
    elif score >= CONVICTION_WATCH:
        result["signal"] = "WATCH"
        console.print(f"[yellow][Quant] Conviction: {score:.1f}/100 → WATCH[/yellow]")
    else:
        result["signal"] = "REJECT"
        console.print(f"[dim][Quant] Conviction: {score:.1f}/100 → REJECT[/dim]")

    return result


def _select_bull_call_spread(chain: list, current_price: float) -> dict:
    """Select strikes for a bull call spread from Alpaca chain data (list of dicts)."""

    # Find long leg: call with delta closest to 0.58
    long_candidates = [
        c for c in chain
        if LONG_LEG_DELTA_MIN <= c["delta"] <= LONG_LEG_DELTA_MAX
        and c["bid"] > 0 and c["ask"] > 0
    ]

    if not long_candidates:
        return _no_trade("BULLISH", "No valid long call legs (delta 0.50-0.65)")

    long_leg = min(long_candidates, key=lambda c: abs(c["delta"] - 0.58))

    # Find short leg: higher strike, delta 0.25-0.40
    short_candidates = [
        c for c in chain
        if c["strike"] > long_leg["strike"]
        and SHORT_LEG_DELTA_MIN <= c["delta"] <= SHORT_LEG_DELTA_MAX
        and c["bid"] > 0 and c["ask"] > 0
    ]

    if not short_candidates:
        return _no_trade("BULLISH", "No valid short call legs (delta 0.25-0.40)")

    # Filter by spread width
    width_filtered = [
        c for c in short_candidates
        if MIN_SPREAD_WIDTH <= (c["strike"] - long_leg["strike"]) <= MAX_SPREAD_WIDTH
    ]

    if not width_filtered:
        # Fallback: closest to $3.50 width
        short_leg = min(short_candidates, key=lambda c: abs(c["strike"] - long_leg["strike"] - 3.5))
    else:
        # Filter: short mid must be cheaper than long mid (positive max profit)
        profitable = [c for c in width_filtered if c["mid"] < long_leg["mid"]]
        if not profitable:
            profitable = width_filtered  # fallback
        short_leg = min(profitable, key=lambda c: abs(c["delta"] - 0.33))

    return _build_spread("BULL_CALL_SPREAD", long_leg, short_leg, current_price)


def _select_bear_put_spread(chain: list, current_price: float) -> dict:
    """Select strikes for a bear put spread from Alpaca chain data."""

    # Find long leg: put with abs(delta) closest to 0.58
    long_candidates = [
        c for c in chain
        if LONG_LEG_DELTA_MIN <= abs(c["delta"]) <= LONG_LEG_DELTA_MAX
        and c["bid"] > 0 and c["ask"] > 0
    ]

    if not long_candidates:
        return _no_trade("BEARISH", "No valid long put legs (delta -0.50 to -0.65)")

    long_leg = min(long_candidates, key=lambda c: abs(abs(c["delta"]) - 0.58))

    # Find short leg: lower strike, smaller delta
    short_candidates = [
        c for c in chain
        if c["strike"] < long_leg["strike"]
        and SHORT_LEG_DELTA_MIN <= abs(c["delta"]) <= SHORT_LEG_DELTA_MAX
        and c["bid"] > 0 and c["ask"] > 0
    ]

    if not short_candidates:
        return _no_trade("BEARISH", "No valid short put legs (delta -0.25 to -0.40)")

    width_filtered = [
        c for c in short_candidates
        if MIN_SPREAD_WIDTH <= (long_leg["strike"] - c["strike"]) <= MAX_SPREAD_WIDTH
    ]

    if not width_filtered:
        short_leg = min(short_candidates, key=lambda c: abs(long_leg["strike"] - c["strike"] - 3.5))
    else:
        profitable = [c for c in width_filtered if c["mid"] < long_leg["mid"]]
        if not profitable:
            profitable = width_filtered
        short_leg = min(profitable, key=lambda c: abs(abs(c["delta"]) - 0.33))

    return _build_spread("BEAR_PUT_SPREAD", long_leg, short_leg, current_price)


def _build_spread(structure: str, long_leg: dict, short_leg: dict, current_price: float) -> dict:
    """Build a spread proposal from two legs."""

    long_type = "CALL" if "CALL" in structure else "PUT"
    long_mid = long_leg["mid"]
    short_mid = short_leg["mid"]

    if structure == "BULL_CALL_SPREAD":
        net_debit = long_mid - short_mid
        spread_width = short_leg["strike"] - long_leg["strike"]
        breakeven = long_leg["strike"] + net_debit
    else:
        net_debit = long_mid - short_mid
        spread_width = long_leg["strike"] - short_leg["strike"]
        breakeven = long_leg["strike"] - net_debit

    max_loss = net_debit
    max_profit = spread_width - net_debit

    if max_loss <= 0:
        return _no_trade(structure, "Negative net debit — spread doesn't work")

    if max_profit <= 0:
        return _no_trade(structure, f"Spread width ${spread_width:.2f} < net debit ${net_debit:.2f} — no upside")

    bid_ask = (long_leg["ask"] - long_leg["bid"]) + (short_leg["ask"] - short_leg["bid"])

    expiry = long_leg.get("expiry", "")
    dte = long_leg.get("dte", 14)

    leg_type = "LONG" if "BULL" in structure else "SHORT"

    console.print(f"[dim]Long: {long_leg['strike']}{long_type[0]} @ ${long_mid:.2f} (δ={long_leg['delta']:.3f})[/dim]")
    console.print(f"[dim]Short: {short_leg['strike']}{long_type[0]} @ ${short_mid:.2f} (δ={short_leg['delta']:.3f})[/dim]")
    console.print(f"[dim]Net debit: ${net_debit:.2f} | Max loss: ${max_loss * 100:.0f}/contract | Max profit: ${max_profit * 100:.0f}/contract[/dim]")

    return {
        "signal": "PROPOSE",
        "structure": structure,
        "direction": leg_type,
        "underlying": UNDERLYING,
        "current_price": current_price,
        "dte": dte,
        "expiry": expiry,
        "long_leg": {
            "type": long_type,
            "strike": long_leg["strike"],
            "delta": long_leg["delta"],
            "bid": long_leg["bid"],
            "ask": long_leg["ask"],
            "mid_price": long_mid,
            "greeks": {
                "gamma": long_leg.get("gamma", 0),
                "theta": long_leg.get("theta", 0),
                "vega": long_leg.get("vega", 0),
            },
            "iv": long_leg.get("implied_volatility", 0),
            "alpaca_symbol": long_leg["symbol"],
        },
        "short_leg": {
            "type": long_type,
            "strike": short_leg["strike"],
            "delta": short_leg["delta"],
            "bid": short_leg["bid"],
            "ask": short_leg["ask"],
            "mid_price": short_mid,
            "greeks": {
                "gamma": short_leg.get("gamma", 0),
                "theta": short_leg.get("theta", 0),
                "vega": short_leg.get("vega", 0),
            },
            "iv": short_leg.get("implied_volatility", 0),
            "alpaca_symbol": short_leg["symbol"],
        },
        "net_debit": round(net_debit, 2),
        "spread_width": round(spread_width, 2),
        "max_loss_per_share": round(max_loss, 2),
        "max_profit_per_share": round(max_profit, 2),
        "max_loss_per_contract": round(max_loss * 100, 2),
        "max_profit_per_contract": round(max_profit * 100, 2),
        "breakeven": round(breakeven, 2),
        "risk_reward_ratio": round(max_profit / max_loss, 2) if max_loss > 0 else 0,
        "bid_ask_spread": round(bid_ask, 2),
        "reason": f"{structure.replace('_', ' ')}: buy {long_leg['strike']}{long_type[0]} / sell {short_leg['strike']}{long_type[0]}",
    }


def _no_trade(regime: str, reason: str = "") -> dict:
    return {
        "signal": "NO_TRADE",
        "structure": None,
        "reason": reason or f"Regime is {regime} — no clear directional bias",
        "conviction_score": 0,
        "conviction_breakdown": {},
    }


def _calculate_conviction(metrics: dict, proposal: dict, dte: int, regime: str) -> dict:
    """Calculate weighted conviction score."""
    breakdown = {}

    # Regime strength
    adx = metrics.get("adx", 20)
    breakdown["regime_strength"] = round(min(100, max(0, (adx - 20) / 30 * 100)), 1)

    # Momentum alignment
    bullish_count = sum([
        metrics.get("price_above_ema", False),
        metrics.get("ema_bullish", False),
        metrics.get("macd_bullish", False),
        50 < metrics.get("rsi", 50) < 70,
    ])
    breakdown["momentum_align"] = round(bullish_count / 4 * 100, 1)

    # Options pricing
    spread_width = proposal.get("spread_width", 5)
    max_profit = proposal.get("max_profit_per_share", 0)
    breakdown["options_pricing"] = round(min(100, (max_profit / spread_width) * 150) if spread_width > 0 else 0, 1)

    # Liquidity
    bid_ask = proposal.get("bid_ask_spread", 0.15)
    breakdown["liquidity"] = round(max(0, min(100, (0.15 - bid_ask) / 0.15 * 100)), 1)

    # Risk/reward
    rr = proposal.get("risk_reward_ratio", 0)
    breakdown["risk_reward"] = round(min(100, rr / 3 * 100), 1)

    # Time alignment
    breakdown["time_alignment"] = round(max(0, 100 - abs(dte - 17) * 5), 1)

    total = sum(breakdown[k] * CONVICTION_WEIGHTS[k] for k in CONVICTION_WEIGHTS)

    return {"score": round(total, 1), "breakdown": breakdown}


def _generate_synthetic_chain(symbol: str, current_price: float, option_type: str, dte: int = 14) -> list:
    """Generate deterministic synthetic options contracts for offline testing & demos."""
    from datetime import date, timedelta
    expiry_date = date.today() + timedelta(days=dte)
    expiry_str = expiry_date.strftime("%Y-%m-%d")
    expiry_occ = expiry_date.strftime("%y%m%d")

    chain = []
    base_strike = round(current_price)

    # Generate strikes around ATM (-10 to +10)
    for offset in range(-10, 11, 1):
        strike = float(base_strike + offset)
        diff = strike - current_price
        
        # Approximate Black-Scholes delta
        if option_type == "call":
            approx_delta = max(0.05, min(0.95, 0.50 - (diff / (current_price * 0.02))))
            mid = max(0.20, (current_price - strike) + 4.50) if diff < 0 else max(0.20, 4.50 - diff * 0.6)
        else:
            approx_delta = max(0.05, min(0.95, 0.50 + (diff / (current_price * 0.02))))
            mid = max(0.20, (strike - current_price) + 4.50) if diff > 0 else max(0.20, 4.50 + diff * 0.6)

        bid = round(max(0.05, mid - 0.03), 2)
        ask = round(mid + 0.03, 2)
        type_code = "C" if option_type == "call" else "P"
        occ_sym = f"{symbol}{expiry_occ}{type_code}{int(strike * 1000):08d}"

        chain.append({
            "symbol": occ_sym,
            "strike": strike,
            "expiry": expiry_str,
            "type": option_type,
            "dte": dte,
            "bid": bid,
            "ask": ask,
            "mid": round(mid, 2),
            "spread": round(ask - bid, 2),
            "delta": round(approx_delta if option_type == "call" else -approx_delta, 4),
            "gamma": 0.035,
            "theta": -0.045,
            "vega": 0.12,
            "implied_volatility": 0.185,
        })

    chain.sort(key=lambda x: x["strike"])
    return chain

