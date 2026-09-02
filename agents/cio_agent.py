"""
cio_agent.py — CIO Agent (Chief Investment Officer)

Role: Takes the trade proposal and generates a plain-English explanation
that a complete beginner can understand. Uses GPT-4o-mini to translate
technical trade parameters into human-readable language.

This is the "voice" of BullRun — it explains WHY the trade makes sense.

IMPORTANT: The LLM NEVER decides whether to trade. It only explains.
The Risk Engine decides. The human decides. The LLM just talks.

Input:  regime_result, proposal, risk_check dicts
Output: A dictionary with plain-English thesis text
"""

from openai import OpenAI
from rich.console import Console
from config import OPENAI_API_KEY, LLM_MODEL, UNDERLYING

console = Console()

SYSTEM_PROMPT = """You are a plain-English financial explainer for a beginner trading system called BullRun.

Your job is to explain a trade proposal in simple, clear language that someone with ZERO trading experience can understand.

Rules:
1. Never use jargon without explaining it
2. Always state the maximum loss clearly
3. Always state the potential gain clearly
4. Explain what "could go wrong" honestly
5. Keep it to 3-5 sentences
6. Be honest, not hype-y
7. Use words like "bet", "risk", "potential gain", "maximum loss"
8. Never promise profits or guarantees

Format your response as a JSON with these keys:
{
  "what_happening": "1-2 sentences about what the market is doing",
  "the_trade": "1-2 sentences about what we're doing",
  "the_numbers": "1 sentence about gain/loss potential",
  "why_now": "1-2 sentences about why this is a good time",
  "what_could_go_wrong": "1-2 sentences about risks"
}"""


def run(regime_result: dict, proposal: dict, risk_check: dict) -> dict:
    """
    Main entry point for the CIO Agent.
    Generates plain-English thesis for the trade proposal.
    """

    console.print("[bold cyan][CIO][/bold cyan] Generating trade thesis...")

    # Build the prompt for the LLM
    prompt = _build_prompt(regime_result, proposal, risk_check)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.4,
            response_format={"type": "json_object"},
            timeout=15,
        )

        import json
        thesis = json.loads(response.choices[0].message.content)

        console.print("[green][CIO][/green] Thesis generated")

        return {
            "what_happening": thesis.get("what_happening", "Market analysis in progress."),
            "the_trade": thesis.get("the_trade", "Trade proposal being evaluated."),
            "the_numbers": thesis.get("the_numbers", "Risk and reward being calculated."),
            "why_now": thesis.get("why_now", "Timing analysis in progress."),
            "what_could_go_wrong": thesis.get("what_could_go_wrong", "Risk assessment in progress."),
            "raw_thesis": thesis,
        }

    except Exception as e:
        console.print(f"[yellow][CIO] LLM call failed: {e} — using fallback templates[/yellow]")
        return _fallback_thesis(proposal)


def _build_prompt(regime_result: dict, proposal: dict, risk_check: dict) -> str:
    """Construct the prompt for the LLM from structured data."""

    structure = proposal.get("structure", "UNKNOWN")
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})
    max_loss = proposal.get("max_loss_per_contract", 0)
    max_profit = proposal.get("max_profit_per_contract", 0)
    breakeven = proposal.get("breakeven", 0)
    dte = proposal.get("dte", 0)

    regime = regime_result.get("regime", "UNKNOWN")
    regime_reason = regime_result.get("reason", "No reason provided")
    adx = regime_result.get("metrics", {}).get("adx", 0)
    rsi = regime_result.get("metrics", {}).get("rsi", 0)

    return f"""
TRADE PROPOSAL TO EXPLAIN:

Underlying: {UNDERLYING}
Structure: {structure.replace('_', ' ')}
Regime: {regime} (ADX: {adx}, RSI: {rsi})
Regime reason: {regime_reason}

Long leg: {long_leg.get('type', '?')} {long_leg.get('strike', '?')} @ ${long_leg.get('mid_price', 0):.2f} (delta: {long_leg.get('delta', 0):.2f})
Short leg: {short_leg.get('type', '?')} {short_leg.get('strike', '?')} @ ${short_leg.get('mid_price', 0):.2f} (delta: {short_leg.get('delta', 0):.2f})

Net debit: ${proposal.get('net_debit', 0):.2f}
Max loss: ${max_loss:.0f} per contract
Max profit: ${max_profit:.0f} per contract
Breakeven: ${breakeven:.2f}
Risk/Reward: 1:{proposal.get('risk_reward_ratio', 0)}
DTE: {dte} days

Risk Engine: {risk_check.get('status', 'UNKNOWN')}

Explain this trade to a complete beginner in plain English. Focus on:
1. What the market is doing (regime)
2. What this trade does (simple language)
3. The numbers (gain/loss)
4. Why this might work
5. What could go wrong
"""


def _fallback_thesis(proposal: dict) -> dict:
    """Fallback thesis when LLM is unavailable."""

    structure = proposal.get("structure", "spread")
    max_loss = proposal.get("max_loss_per_contract", 0)
    max_profit = proposal.get("max_profit_per_contract", 0)
    breakeven = proposal.get("breakeven", 0)
    direction = "up" if "CALL" in structure else "down"

    return {
        "what_happening": f"The market is showing a clear directional bias, suggesting {UNDERLYING} may continue {direction}.",
        "the_trade": f"We're placing a {structure.replace('_', ' ').title()} — a defined-risk options trade that profits if {UNDERLYING} moves {direction}.",
        "the_numbers": f"You could make up to ${max_profit:.0f} per contract, but you could lose up to ${max_loss:.0f} if the trade goes against you.",
        "why_now": "Multiple technical indicators confirm the trend direction, and options pricing is reasonable.",
        "what_could_go_wrong": f"If {UNDERLYING} reverses direction, this trade will lose money. The system will auto-exit if the trend breaks.",
        "raw_thesis": {},
    }


if __name__ == "__main__":
    # Test with mock data
    mock_regime = {
        "regime": "BULLISH",
        "reason": "ADX=31.2, 4/4 indicators bullish",
        "metrics": {"adx": 31.2, "rsi": 62.3},
    }
    mock_proposal = {
        "structure": "BULL_CALL_SPREAD",
        "long_leg": {"type": "CALL", "strike": 563, "mid_price": 4.20, "delta": 0.58},
        "short_leg": {"type": "CALL", "strike": 568, "mid_price": 1.85, "delta": 0.35},
        "net_debit": 2.35,
        "max_loss_per_contract": 235,
        "max_profit_per_contract": 265,
        "breakeven": 565.35,
        "risk_reward_ratio": 1.13,
        "dte": 12,
    }
    mock_risk = {"status": "PASS"}
    result = run(mock_regime, mock_proposal, mock_risk)
    import json
    print(json.dumps(result, indent=2))
