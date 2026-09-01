"""Deterministic, progressive teaching layer for BullRun.

The teaching engine never recommends or overrides a trade. It translates the
existing deterministic signals, proposal, risk checks, market context and
journal history into lessons that are understandable at three skill levels.
"""

import json
import os
from datetime import datetime, timedelta
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

GLOSSARY = {
    "delta": "How much an option's price tends to move when the stock moves $1. A 0.50 delta roughly means a $1 stock move changes the option by about $0.50, all else equal.",
    "theta": "The daily time-decay effect. Options generally lose some value as expiration gets closer, especially when nothing else changes.",
    "gamma": "How quickly delta changes when the stock moves. Higher gamma means the option's sensitivity can change faster.",
    "iv": "Implied volatility: the market's estimate of how much the stock may move. Higher IV usually means more expensive options.",
    "spread": "A strategy using two or more option legs together. In BullRun, the spread buys one option and sells another to keep risk defined.",
    "debit": "Money paid to open the spread. For BullRun's debit spreads, this amount is the planned maximum loss per share, before contract multiplier effects.",
    "credit": "Money received to open a trade. It is not automatically profit: the position can still lose money if the market moves against it.",
    "breakeven": "The underlying price where the position is approximately neither profitable nor losing money at expiration, before fees and slippage.",
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
        "next_feature": next((feature for feature in FEATURE_POINTS if feature not in explored), None),
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


def options_glossary(terms: list[str] | None = None) -> dict:
    """Return plain-English definitions for common options terms.

    ``terms`` may contain any glossary key; with no argument all nine terms
    are returned. Unknown terms are ignored so the teaching UI stays safe.
    """
    selected = terms or list(GLOSSARY)
    return {term.lower(): GLOSSARY[term.lower()] for term in selected if term.lower() in GLOSSARY}


def _user_level(user_level: str | None) -> str:
    value = (user_level or get_progress().get("level", "Beginner")).strip().title()
    return value if value in {"Beginner", "Intermediate", "Advanced"} else "Beginner"


def progressive_explanation(beginner: str, intermediate: str, advanced: str, user_level: str | None = None) -> str:
    """Select the appropriate depth without changing the underlying decision."""
    level = _user_level(user_level)
    if level == "Advanced":
        return advanced
    if level == "Intermediate":
        return intermediate
    return beginner


def why_this_matters(proposal: dict, regime_result: dict | None = None, market_context: dict | None = None, user_level: str | None = None) -> dict:
    """Explain the real-world significance of a decision without inventing news.

    ``market_context`` can contain verified fields such as ``headline``,
    ``event``, ``rates`` or ``volatility`` supplied by the data layer. If none
    are supplied, the lesson deliberately stays grounded in observed signals.
    """
    regime_result = regime_result or {}
    context = market_context or proposal.get("market_context", {}) or {}
    regime = regime_result.get("regime", proposal.get("regime", "UNKNOWN"))
    structure = proposal.get("structure", "defined-risk spread")
    event = context.get("headline") or context.get("event")

    if event:
        context_sentence = f"A verified market event is also relevant: {event}."
    elif regime == "BULLISH":
        context_sentence = "The broader context is an upward market regime, so a bullish defined-risk spread expresses a directional view while putting a ceiling on loss."
    elif regime == "BEARISH":
        context_sentence = "The broader context is a downward market regime, so a bearish defined-risk spread expresses that view while putting a ceiling on loss."
    elif regime == "VOLATILE":
        context_sentence = "The market is unusually volatile, which matters because fast price changes can make option spreads harder to enter and manage."
    else:
        context_sentence = "The market context is mixed, which matters because options amplify the cost of being early or directionally wrong."

    beginner = f"This matters because BullRun is not trading a number in isolation: it is matching a {regime.lower()} market environment to a {structure.replace('_', ' ').lower()} with a known risk limit. {context_sentence}"
    intermediate = f"The decision matters because regime, momentum, volatility and option pricing interact. BullRun uses the {regime.lower()} regime to choose direction, then uses a defined-risk {structure.replace('_', ' ').lower()} so the thesis has explicit payoff boundaries. {context_sentence}"
    advanced = f"The decision matters because the signal-to-structure mapping determines the distribution of outcomes: regime alignment drives directional exposure while the multi-leg structure truncates tail loss and changes sensitivity to delta, gamma, theta and IV. {context_sentence}"
    return {"title": "Why This Matters", "explanation": progressive_explanation(beginner, intermediate, advanced, user_level), "context": context}


def _similarity_score(candidate: dict, proposal: dict) -> int:
    score = 0
    for key in ("underlying", "structure"):
        if candidate.get(key) and candidate.get(key) == proposal.get(key):
            score += 2
    if candidate.get("regime") and candidate.get("regime") == proposal.get("regime"):
        score += 2
    return score


def historical_context(proposal: dict, journal: list | None = None, days: int = 30) -> dict:
    """Summarize comparable closed trades from the recent journal.

    The journal is the source of truth. If there is insufficient history, the
    function says so rather than fabricating a win rate.
    """
    journal = journal if journal is not None else get_journal()
    cutoff = datetime.now() - timedelta(days=days)
    candidates = []
    for trade in journal:
        try:
            created = datetime.fromisoformat(str(trade.get("created_at", "")))
        except ValueError:
            continue
        if created >= cutoff and _similarity_score(trade, proposal) >= 4:
            candidates.append(trade)

    if not candidates:
        return {"title": f"Historical Context — last {days} days", "sample_size": 0, "win_rate": None, "average_return": None, "explanation": "Not enough comparable journal history yet. BullRun will replace this with a measured result as similar trades accumulate."}

    pnls = [float(t.get("pnl", 0) or 0) for t in candidates]
    wins = sum(pnl > 0 for pnl in pnls)
    win_rate = wins / len(pnls) * 100
    average_return = sum(pnls) / len(pnls)
    return {
        "title": f"Historical Context — last {days} days",
        "sample_size": len(candidates),
        "win_rate": win_rate,
        "average_return": average_return,
        "explanation": f"Similar setups in the past {days} days won {win_rate:.1f}% of the time, with an average realized return of ${average_return:,.2f} across {len(candidates)} closed trades. Historical results are context, not a guarantee.",
    }


def compare_to_journal(proposal: dict, journal: list | None = None) -> dict:
    """Find the most similar prior trade and teach from its realized outcome."""
    journal = journal if journal is not None else get_journal()
    ranked = sorted(journal, key=lambda trade: (_similarity_score(trade, proposal), trade.get("trade_number", 0)), reverse=True)
    best = next((trade for trade in ranked if _similarity_score(trade, proposal) >= 4), None)
    if not best:
        return {"title": "Trade Comparison", "match": None, "explanation": "No sufficiently similar closed trade is in the journal yet."}
    pnl = float(best.get("pnl", 0) or 0)
    outcome = "gained" if pnl >= 0 else "lost"
    return {"title": "Trade Comparison", "match": best, "explanation": f"This trade is similar to trade #{best.get('trade_number', '?')}, which {outcome} ${abs(pnl):,.2f}. Use the comparison to study the setup—not to assume the same outcome will repeat."}


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
        explanation = f"{regime_result.get('reason', 'Several indicators are aligned.')}. Price is {'above' if price_above else 'below'} its short-term average, the fast EMA is {'above' if fast > slow else 'not above'} the slow EMA, and momentum is {'improving' if macd_bullish else 'mixed'}. This is evidence of an upward trend, not a promise that it will continue."
    elif regime == "BEARISH":
        explanation = f"{regime_result.get('reason', 'Several indicators are aligned.')}. Price is {'below' if not price_above else 'above'} its short-term average and the fast EMA is {'below' if fast < slow else 'not below'} the slow EMA. Together with RSI at {rsi:.1f}, that points to sellers having control."
    elif regime == "VOLATILE":
        explanation = f"ATR is {atr_ratio:.2f}× its recent average (the caution threshold is {ATR_VOLATILE_MULTIPLIER:.1f}×). Large swings can make even a correct directional idea difficult to manage, so the system waits."
    else:
        explanation = f"ADX is only {adx:.1f}, below the {ADX_TREND_THRESHOLD} trend threshold. The market is giving mixed or weak directional evidence; waiting is disciplined risk management, not a missed opportunity."
    return {"title": f"Why Scout says {regime}", "explanation": explanation, "facts": facts}


def strategy_explainer(proposal: dict, user_level: str | None = None) -> dict:
    """Explain the spread at the learner's appropriate technical depth."""
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
    beginner = f"A {structure.replace('_', ' ').title()} uses two options to express a possible {direction} in {underlying}. We buy the ${long_strike} {option_word} and sell the ${short_strike} {option_word}; the second leg helps pay for the first. The planned maximum loss is ${max_loss:.0f} per contract, while the maximum profit is ${max_profit:.0f}."
    intermediate = beginner + f" The net debit is ${debit:.2f} per share. The long and short legs have different Greeks, so delta, theta and gamma can change the spread's value before {expiry}."
    advanced = intermediate + f" Structurally, the short leg offsets part of the long-leg exposure and truncates the payoff. Evaluate net delta, gamma, theta, IV sensitivity, liquidity and DTE together rather than interpreting any single Greek in isolation."
    return {"title": "How this defined-risk spread works", "explanation": progressive_explanation(beginner, intermediate, advanced, user_level), "legs": [{"action": "BUY", "strike": long_strike, "meaning": f"The ${long_strike} strike is the option we own; it gains value as {underlying} moves in the predicted direction."}, {"action": "SELL", "strike": short_strike, "meaning": f"The ${short_strike} strike finances part of the purchase and sets the maximum profit."}]}


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
    report = {"trade_number": trade_number, "created_at": datetime.now().isoformat(), "predicted": predicted, "actual": actual, "lesson_learned": lesson, "pnl": pnl, "underlying": underlying, "structure": structure, "regime": position.get("regime")}
    journal = _read_json(JOURNAL_FILE, [])
    journal.append(report)
    _write_json(JOURNAL_FILE, journal)
    record_feature_explored("trade_journal")
    return report


def get_journal() -> list:
    return _read_json(JOURNAL_FILE, [])
