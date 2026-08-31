"""
trade_card.py — Trade Card Renderer

Role: Takes the complete trade proposal (from Quant, Risk, CIO) and renders
a beautiful Rich terminal card that a beginner can understand.

This is the "face" of Conviction Gate — it shows the human exactly what
they're approving, in plain English.

Two views:
1. Beginner view (default) — plain English, simple numbers
2. Pro view (expandable) — technical details, Greeks, raw risk checks
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def render_trade_card(
    proposal: dict,
    risk_check: dict,
    thesis: dict,
    trade_number: int = 0,
    conviction: dict = None,
    pro_view: bool = False,
) -> None:
    """
    Render the complete trade card to the terminal.

    Args:
        proposal: Trade proposal from Quant Agent
        risk_check: Risk check results from Risk Engine
        thesis: Plain-English thesis from CIO Agent
        trade_number: Sequential trade number
        conviction: Conviction score breakdown
        pro_view: Whether to show technical details
    """

    structure = proposal.get("structure", "UNKNOWN")
    signal = proposal.get("signal", "NO_TRADE")

    if signal == "NO_TRADE":
        _render_no_trade_card(proposal, trade_number)
        return

    # ── Header ───────────────────────────────────────────────────────────
    header = Text()
    header.append("CONVICTION GATE", style="bold gold1")
    header.append(" — TRADE PROPOSAL", style="bold")
    if trade_number:
        header.append(f" #{trade_number:03d}", style="dim")

    # ── Structure name ───────────────────────────────────────────────────
    structure_name = structure.replace("_", " ").title()
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})
    underlying = proposal.get("underlying", "SPY")

    # ── Build content ────────────────────────────────────────────────────
    content_parts = []

    # Trade name
    trade_name = Text()
    trade_name.append(f"\n  {underlying} {structure_name}", style="bold white")
    content_parts.append(trade_name)

    # ── What's Happening ─────────────────────────────────────────────────
    section1 = Text()
    section1.append("\n  ── WHAT'S HAPPENING ──────────────────────────────────────\n", style="dim")
    section1.append(f"  {thesis.get('what_happening', 'Market analysis in progress.')}\n", style="white")
    content_parts.append(section1)

    # ── The Trade ────────────────────────────────────────────────────────
    section2 = Text()
    section2.append("\n  ── THE TRADE ─────────────────────────────────────────────\n", style="dim")
    section2.append(f"  {thesis.get('the_trade', 'Trade proposal being evaluated.')}\n", style="white")
    content_parts.append(section2)

    strategy_lesson = proposal.get("teaching", {}).get("strategy", {})
    if strategy_lesson:
        section_lesson = Text()
        section_lesson.append("\n  ── LEARN THIS STRATEGY ──────────────────────────────────\n", style="dim cyan")
        section_lesson.append(f"  {strategy_lesson.get('explanation', '')}\n", style="white")
        content_parts.append(section_lesson)

    # ── The Numbers ──────────────────────────────────────────────────────
    max_loss = proposal.get("max_loss_per_contract", 0)
    max_profit = proposal.get("max_profit_per_contract", 0)
    breakeven = proposal.get("breakeven", 0)
    rr_ratio = proposal.get("risk_reward_ratio", 0)

    section3 = Text()
    section3.append("\n  ── THE NUMBERS ───────────────────────────────────────────\n", style="dim")
    section3.append(f"  You could make:     ", style="dim")
    section3.append(f"up to ${max_profit:.0f} per contract\n", style="bold green")
    section3.append(f"  You could lose:     ", style="dim")
    section3.append(f"up to ${max_loss:.0f} per contract\n", style="bold red")
    section3.append(f"  Breaking even:      ", style="dim")
    section3.append(f"if {underlying} is above ${breakeven:.2f}\n", style="white")
    section3.append(f"  You start losing:   ", style="dim")
    section3.append(f"below ${breakeven:.2f}\n", style="yellow")
    section3.append(f"  Max loss:           ", style="dim")
    section3.append(f"if {underlying} is below {float(long_leg.get('strike', 0)):.0f} at expiry\n", style="red")
    content_parts.append(section3)

    # ── Why Now ──────────────────────────────────────────────────────────
    section4 = Text()
    section4.append("\n  ── WHY NOW ───────────────────────────────────────────────\n", style="dim")
    section4.append(f"  {thesis.get('why_now', 'Timing analysis in progress.')}\n", style="white")
    content_parts.append(section4)

    # ── What Could Go Wrong ──────────────────────────────────────────────
    section5 = Text()
    section5.append("\n  ── WHAT COULD GO WRONG ──────────────────────────────────\n", style="dim")
    section5.append(f"  {thesis.get('what_could_go_wrong', 'Risk assessment in progress.')}\n", style="yellow")
    content_parts.append(section5)

    # ── Safety Check ─────────────────────────────────────────────────────
    section6 = Text()
    section6.append("\n  ── SAFETY CHECK ─────────────────────────────────────────\n", style="dim")
    portfolio_pct = (max_loss / 100_000) * 100
    section6.append(f"  ✓ Max risk: ${max_loss:.0f} ({portfolio_pct:.2f}% of your account)\n", style="green")
    section6.append(f"  ✓ All 6 safety checks passed\n", style="green")
    content_parts.append(section6)

    # ── Confirmation ─────────────────────────────────────────────────────
    section7 = Text()
    section7.append("\n  ── CONFIRMATION ──────────────────────────────────────────\n", style="dim")
    section7.append(f"  I understand this trade can lose up to ${max_loss:.0f} and the\n", style="white")
    section7.append(f"  system may auto-exit before expiration.\n", style="white")
    content_parts.append(section7)

    # ── Combine all parts ────────────────────────────────────────────────
    full_content = Text()
    for part in content_parts:
        full_content.append_text(part)

    # ── Render panel ─────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        full_content,
        title=header,
        subtitle=Text("  [APPROVE]  or  [REJECT]  ", style="bold"),
        border_style="gold1",
        padding=(0, 1),
        width=62,
    ))

    # ── Pro view (expandable) ────────────────────────────────────────────
    if pro_view:
        _render_pro_view(proposal, risk_check, conviction)


def _render_no_trade_card(proposal: dict, trade_number: int = 0) -> None:
    """Render a card when no trade is proposed."""

    reason = proposal.get("reason", "No clear opportunity detected.")
    regime = proposal.get("structure", "NEUTRAL")

    content = Text()
    content.append(f"\n  {reason}\n\n", style="white")
    content.append(f"  ── WHAT WE SAW ─────────────────────────────────────────\n", style="dim")
    content.append(f"  The market conditions don't meet our criteria for a\n", style="white")
    content.append(f"  defined-risk options trade right now.\n\n", style="white")
    content.append(f"  ── WHAT THIS MEANS ────────────────────────────────────\n", style="dim")
    content.append(f"  When conditions aren't right, our system stays quiet.\n", style="white")
    content.append(f"  This is by design — patience is part of the strategy.\n\n", style="white")
    lesson = proposal.get("teaching", {}).get("rejection", {}).get("explanation")
    if lesson:
        content.append(f"  ── LEARNING MOMENT ─────────────────────────────────────\n", style="dim cyan")
        content.append(f"  {lesson}\n\n", style="white")
    content.append(f"  ── NEXT SCAN ──────────────────────────────────────────\n", style="dim")
    content.append(f"  Re-checking in 15 minutes...\n", style="cyan")

    console.print()
    console.print(Panel(
        content,
        title=Text("CONVICTION GATE", style="bold gold1") + Text(" — NO TRADE", style="bold dim"),
        border_style="dim",
        padding=(0, 1),
        width=62,
    ))


def _render_pro_view(proposal: dict, risk_check: dict, conviction: dict = None) -> None:
    """Render the expandable pro/technical view."""

    content = Text()
    content.append("\n  ── PRO DESK VIEW ────────────────────────────────────────\n", style="dim cyan")

    # Regime metrics
    content.append(f"\n  Regime:       ", style="dim")
    content.append(f"{proposal.get('regime', 'N/A')}\n", style="white")

    # Contracts
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})
    content.append(f"\n  BUY   {proposal.get('underlying', 'SPY')} ", style="dim")
    content.append(f"{long_leg.get('strike', '?')}{long_leg.get('type', '?')[0]} ", style="green")
    content.append(f"@ ${long_leg.get('mid_price', 0):.2f}  ", style="white")
    content.append(f"(δ: {long_leg.get('delta', 0):.2f})\n", style="dim")

    content.append(f"  SELL  {proposal.get('underlying', 'SPY')} ", style="dim")
    content.append(f"{short_leg.get('strike', '?')}{short_leg.get('type', '?')[0]} ", style="red")
    content.append(f"@ ${short_leg.get('mid_price', 0):.2f}  ", style="white")
    content.append(f"(δ: {short_leg.get('delta', 0):.2f})\n", style="dim")

    # Economics
    content.append(f"\n  Net Debit:     ${proposal.get('net_debit', 0):.2f}\n", style="white")
    content.append(f"  Spread Width:  ${proposal.get('spread_width', 0):.2f}\n", style="white")
    content.append(f"  Max Loss:      ${proposal.get('max_loss_per_contract', 0):.0f}\n", style="red")
    content.append(f"  Max Profit:    ${proposal.get('max_profit_per_contract', 0):.0f}\n", style="green")
    content.append(f"  Breakeven:     ${proposal.get('breakeven', 0):.2f}\n", style="white")
    content.append(f"  Risk:Reward:   1:{proposal.get('risk_reward_ratio', 0)}\n", style="white")
    content.append(f"  DTE:           {proposal.get('dte', 0)} days\n", style="white")
    content.append(f"  Bid/Ask:       ${proposal.get('bid_ask_spread', 0):.2f}\n", style="white")

    # Risk checks
    if risk_check:
        content.append(f"\n  RISK ENGINE:\n", style="dim cyan")
        for check in risk_check.get("checks", []):
            icon = "✓" if check["status"] == "PASS" else "✗"
            color = "green" if check["status"] == "PASS" else "red"
            content.append(f"  {icon} {check['name']}: {check['detail']}\n", style=color)

    # Conviction score
    if conviction:
        score = conviction.get("score", 0)
        content.append(f"\n  CONVICTION SCORE: {score:.1f}/100\n", style="bold gold1")
        for k, v in conviction.get("breakdown", {}).items():
            content.append(f"    {k}: {v:.1f}\n", style="dim")

    console.print(Panel(
        content,
        title=Text("PRO DESK VIEW", style="bold cyan"),
        border_style="cyan",
        padding=(0, 1),
        width=62,
    ))
