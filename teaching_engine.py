"""Deterministic, beginner-first explanations for Conviction Gate.

The teaching engine never recommends a trade.  It translates the existing
Scout, Quant, and Risk Engine outputs into small lessons that can be safely
shown beside a decision and retained after a position closes.
"""

import json
import os
from datetime import datetime
from typing import Any

from config import ADX_TREND_THRESHOLD, ATR_VOLATILE_MULTIPLIER

_DATA_DIR = os.path.dirname(__file__)
PROGRESS_FILE = os.path.join(_DATA_DIR, "learning_progress.json")
JOURNAL_FILE = os.path.join(_DATA_DIR, "learning_journal.json")

FEATURE_POINTS = {
    "regime_lesson": 10,
    "strategy_explainer": 15,
    "rejection_explainer": 10,
    "risk_checks": 15,
    "trade_journal": 20,
}


def _read_json(path: str, default: Any) -> Any:
    try:
        with open(path) as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: str, value: Any) -> None:
    with open(path, "w") as file:
        json.dump(value, file, indent=2, default=str)


def _level(score: int) -> str:
    if score >= 70:
        return "Advanced"
    if score >= 30:
        return "Intermediate"
    return "Beginner"


def get_progress() -> dict:
    """Return the persisted learner profile, creating a safe default."""
    profile = _read_json(PROGRESS_FILE, {})
    explored = list(dict.fromkeys(profile.get("explored_features", [])))
    score = sum(FEATURE_POINTS.get(feature, 0) for feature in explored)
    return {
        "score": score,
        "level": _level(score),
        "explored_features": explored,
        "next_feature": next(
            (feature for feature in FEATURE_POINTS if feature not in explored), None
        ),
        "updated_at": profile.get("updated_at"),
    }


def record_feature_explored(feature: str) -> dict:
    """Credit a feature once; repeated clicks cannot inflate the score."""
    if feature not in FEATURE_POINTS:
        raise ValueError(f"Unknown learning feature: {feature}")
    profile = get_progress()
    if feature not in profile["explored_features"]:
        profile["explored_features"].append(feature)
        profile["updated_at"] = datetime.now().isoformat()
        _write_json(PROGRESS_FILE, profile)
    return get_progress()


def regime_lesson(regime_result: dict) -> dict:
    """Explain a Scout classification from its exact deterministic inputs."""
    metrics = regime_result.get("metrics", {})
    regime = regime_result.get("regime", "UNKNOWN")
    adx = float(metrics.get("adx", 0))
    rsi = float(metrics.get("rsi", 50))
    fast = float(metrics.get("ema_fast", 0))
    slow = float(metrics.get("ema_slow", 0))
    atr_ratio = float(metrics.get("atr_ratio", 1))
    price_above = bool(metrics.get("price_above_ema", False))
    macd_bullish = bool(metrics.get("macd_bullish", False))

    facts = [
        f"ADX is {adx:.1f}. A reading above {ADX_TREND_THRESHOLD} means the market is trending; below it means direction is less reliable.",
        f"The 20-day EMA is ${fast:.2f} and the 50-day EMA is ${slow:.2f}. The shorter average shows the recent trend; the longer one is the broader trend.",
        f"RSI is {rsi:.1f}. Around 50 is neutral; above 50 favors buyers and below 50 favors sellers.",
    ]
    if regime == "BULLISH":
        explanation = (
            f"{regime_result.get('reason', 'Several indicators are aligned.')}. "
            f"Price is {'above' if price_above else 'below'} its short-term average, "
            f"the fast EMA is {'above' if fast > slow else 'not above'} the slow EMA, and "
            f"momentum is {'improving' if macd_bullish else 'mixed'}. This is evidence of an upward trend, not a promise that it will continue."
        )
    elif regime == "BEARISH":
        explanation = (
            f"{regime_result.get('reason', 'Several indicators are aligned.')}. "
            f"Price is {'below' if not price_above else 'above'} its short-term average and the fast EMA is "
            f"{'below' if fast < slow else 'not below'} the slow EMA. Together with RSI at {rsi:.1f}, that points to sellers having control."
        )
    elif regime == "VOLATILE":
        explanation = (
            f"ATR is {atr_ratio:.2f}× its recent average (the caution threshold is {ATR_VOLATILE_MULTIPLIER:.1f}×). "
            "Large swings can make even a correct directional idea difficult to manage, so the system waits."
        )
    else:
        explanation = (
            f"ADX is only {adx:.1f}, below the {ADX_TREND_THRESHOLD} trend threshold. "
            "The market is giving mixed or weak directional evidence; waiting is disciplined risk management, not a missed opportunity."
        )
    return {"title": f"Why Scout says {regime}", "explanation": explanation, "facts": facts}


def strategy_explainer(proposal: dict) -> dict:
    """Explain debit spreads, each strike, and bounded payoff in plain English."""
    structure = proposal.get("structure", "")
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})
    underlying = proposal.get("underlying", "the underlying")
    long_strike = long_leg.get("strike", "?")
    short_strike = short_leg.get("strike", "?")
    debit = float(proposal.get("net_debit", 0))
    max_loss = float(proposal.get("max_loss_per_contract", 0))
    max_profit = float(proposal.get("max_profit_per_contract", 0))
    expiry = proposal.get("expiry", "expiration")

    is_call = structure == "BULL_CALL_SPREAD"
    direction = "rise" if is_call else "fall"
    option_word = "call" if is_call else "put"
    explanation = (
        f"A {structure.replace('_', ' ').title()} is a two-part, defined-risk trade for a possible {direction} in {underlying}. "
        f"We buy the ${long_strike} {option_word}, which benefits first if the move happens, and sell the ${short_strike} {option_word}, which helps pay for it. "
        f"The sold strike caps the upside, but it also caps the cash paid today at ${debit:.2f} per share (${max_loss:.0f} per contract). "
        f"At {expiry}, the best possible outcome is ${max_profit:.0f} per contract; the loss cannot exceed ${max_loss:.0f}."
    )
    return {
        "title": "How this defined-risk spread works",
        "explanation": explanation,
        "legs": [
            {"action": "BUY", "strike": long_strike, "meaning": f"The ${long_strike} strike is the option we own; it gains value as {underlying} moves in the predicted direction."},
            {"action": "SELL", "strike": short_strike, "meaning": f"The ${short_strike} strike finances part of the purchase and sets the maximum profit."},
        ],
    }


def rejection_explainer(regime_result: dict, proposal: dict | None = None, risk_check: dict | None = None) -> dict:
    """Give the user a patient, specific reason a trade did not proceed."""
    if risk_check and risk_check.get("status") == "REJECT":
        failures = risk_check.get("checks", [])
        failed = [check.get("detail", check.get("name", "a safety check")) for check in failures if check.get("status") == "REJECT"]
        reason = "; ".join(failed) or "A required safety check did not pass."
        text = f"No trade: the Risk Engine stopped it because {reason}. These limits exist to keep one idea from causing outsized damage."
    else:
        regime = regime_result.get("regime", "NEUTRAL")
        adx = float(regime_result.get("metrics", {}).get("adx", 0))
        if regime == "NEUTRAL" or adx < ADX_TREND_THRESHOLD:
            text = f"No trade: ADX is only {adx:.1f}, below {ADX_TREND_THRESHOLD}. The market is confused, so taking a directional options bet now would be closer to gambling than following evidence."
        elif regime == "VOLATILE":
            ratio = float(regime_result.get("metrics", {}).get("atr_ratio", 0))
            text = f"No trade: volatility is elevated (ATR is {ratio:.2f}× normal). Fast swings can overwhelm a controlled spread, so the system waits for calmer conditions."
        else:
            text = f"No trade: {proposal.get('reason', 'the available option contracts did not meet the system’s defined-risk requirements') if proposal else 'the setup did not meet the system’s requirements'}. Passing on a weak setup protects capital for a clearer one."
    return {"title": "Why the system chose not to trade", "explanation": text}


def generate_trade_journal(position: dict, trade_number: int) -> dict:
    """Persist a predicted-versus-actual learning report when a trade closes."""
    structure = position.get("structure", "defined-risk spread")
    underlying = position.get("underlying", "the underlying")
    predicted = f"{underlying} would {'rise' if structure == 'BULL_CALL_SPREAD' else 'fall'} enough for the {structure.replace('_', ' ').lower()} to gain value."
    pnl = float(position.get("pnl", 0) or 0)
    exit_reason = position.get("exit_reason", "an exit rule")
    max_loss = float(position.get("max_loss", 0) or 0)
    if pnl > 0:
        actual = f"The position closed with a ${pnl:,.2f} profit because {exit_reason.lower()}."
        lesson = "The thesis worked this time, but the lesson is not to assume certainty: defined risk and the exit plan made the win repeatable."
    elif pnl < 0:
        actual = f"The position closed with a ${pnl:,.2f} loss because {exit_reason.lower()}."
        lesson = f"The market disagreed with the prediction. The useful outcome is that the loss was controlled against the planned maximum of ${max_loss:,.2f}."
    else:
        actual = f"The position closed near flat because {exit_reason.lower()}."
        lesson = "Not every trade produces a meaningful gain or loss; respecting the exit plan prevents small uncertainty from becoming a large problem."
    report = {"trade_number": trade_number, "created_at": datetime.now().isoformat(), "predicted": predicted, "actual": actual, "lesson_learned": lesson, "pnl": pnl}
    journal = _read_json(JOURNAL_FILE, [])
    journal.append(report)
    _write_json(JOURNAL_FILE, journal)
    record_feature_explored("trade_journal")
    return report


def get_journal() -> list:
    return _read_json(JOURNAL_FILE, [])
