"""Rich terminal trade card for BullRun.

The card keeps the existing approval flow but adds learner-friendly risk,
conviction, strategy and failure-mode views. It never changes the trade.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def _account_value(proposal: dict) -> float:
    return float(proposal.get("account_value", proposal.get("portfolio_value", 100_000)) or 100_000)


def _risk_meter(max_loss: float, account_value: float) -> tuple[str, str, float]:
    pct = (max_loss / account_value * 100) if account_value > 0 else 100.0
    if pct <= 0.5:
        return "GREEN", "[████████████████████]", pct
    if pct <= 1.0:
        return "YELLOW", "[██████████████░░░░░░]", pct
    return "RED", "[██████████░░░░░░░░░░]", pct


def _conviction_table(conviction: dict) -> Table:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Factor")
    table.add_column("Weight", justify="right")
    table.add_column("Score", justify="right")
    breakdown = conviction.get("breakdown", {}) if conviction else {}
    weights = conviction.get("weights", {}) if conviction else {}
    if not weights:
        weights = {"Regime strength": 25, "Momentum alignment": 20, "Options pricing": 15, "Liquidity": 15, "Risk/reward": 15, "Time alignment": 10}
    for factor, weight in weights.items():
        raw = breakdown.get(factor, breakdown.get(factor.lower().replace(" ", "_"), 0))
        try:
            score = float(raw)
        except (TypeError, ValueError):
            score = 0.0
        table.add_row(str(factor), f"{float(weight):.0f}%", f"{score:.1f}/100")
    return table


def _render_learn_more(proposal: dict, conviction: dict = None) -> None:
    """Render the expandable/full strategy details view."""
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})
    details = Text()
    details.append("\n  ── LEARN MORE: FULL STRATEGY ────────────────────────────\n", style="bold cyan")
    details.append(f"  Structure: {proposal.get('structure', 'UNKNOWN').replace('_', ' ').title()}\n", style="white")
    details.append(f"  Long leg:  BUY {long_leg.get('strike', '?')} {long_leg.get('type', '?')} @ ${float(long_leg.get('mid_price', 0) or 0):.2f}\n", style="green")
    details.append(f"  Short leg: SELL {short_leg.get('strike', '?')} {short_leg.get('type', '?')} @ ${float(short_leg.get('mid_price', 0) or 0):.2f}\n", style="red")
    details.append(f"  DTE: {proposal.get('dte', '?')} | Width: ${float(proposal.get('spread_width', 0) or 0):.2f} | Bid/ask: ${float(proposal.get('bid_ask_spread', 0) or 0):.2f}\n", style="dim")
    details.append("\n  Payoff logic: own the directional option, sell the farther strike to reduce entry cost, and accept capped upside in exchange for defined downside.\n", style="white")
    details.append("  Before expiry, price also responds to Greeks and implied volatility; at expiry, the payoff is determined by the strikes and premium paid.\n", style="white")
    if conviction:
        details.append(f"\n  Conviction model: {float(conviction.get('score', proposal.get('conviction_score', 0))):.1f}/100 across six weighted factors.\n", style="bold")
    console.print(Panel(details, title=Text("LEARN MORE", style="bold cyan"), border_style="cyan", padding=(0, 1), width=72))


def _render_risk_meter(max_loss: float, account_value: float) -> None:
    label, gauge, pct = _risk_meter(max_loss, account_value)
    style = "green" if label == "GREEN" else "yellow" if label == "YELLOW" else "red"
    content = Text()
    content.append("  MAX-LOSS RISK METER\n", style="bold")
    content.append(f"  {gauge}  ", style=style)
    content.append(f"{label}\n", style=f"bold {style}")
    content.append(f"  ${max_loss:,.0f} maximum loss = {pct:.2f}% of a ${account_value:,.0f} account.\n", style="white")
    console.print(Panel(content, border_style=style, width=72, padding=(0, 1)))


def _render_wrong_scenario(proposal: dict) -> None:
    max_loss = float(proposal.get("max_loss_per_contract", 0) or 0)
    underlying = proposal.get("underlying", "the underlying")
    structure = proposal.get("structure", "the spread").replace("_", " ").lower()
    content = Text()
    content.append("\n  ── WHAT IF I'M WRONG? ───────────────────────────────────\n", style="bold yellow")
    content.append(f"  If {underlying} moves against the {structure} and the position reaches its defined-loss boundary,\n", style="white")
    content.append(f"  the worst planned outcome is a loss of ${max_loss:,.0f} per contract. You do not lose more simply\n", style="white")
    content.append("  because the market keeps moving—the spread's structure caps the loss. Fees, slippage and early\n", style="dim")
    content.append("  exit mechanics can affect the realized result, so max loss is a boundary, not a promise of execution at one price.\n", style="dim")
    console.print(Panel(content, title=Text("FAILURE MODE", style="bold yellow"), border_style="yellow", width=72, padding=(0, 1)))


def render_trade_card(proposal: dict, risk_check: dict, thesis: dict, trade_number: int = 0, conviction: dict = None, pro_view: bool = False, user_level: str = "Beginner") -> None:
    """Render the complete trade card; optional views are additive only."""
    structure = proposal.get("structure", "UNKNOWN")
    signal = proposal.get("signal", "NO_TRADE")
    if signal == "NO_TRADE":
        _render_no_trade_card(proposal, trade_number)
        return

    header = Text()
    header.append("BULLRUN", style="bold gold1")
    header.append(" — TRADE PROPOSAL", style="bold")
    if trade_number:
        header.append(f" #{trade_number:03d}", style="dim")

    structure_name = structure.replace("_", " ").title()
    long_leg = proposal.get("long_leg", {})
    underlying = proposal.get("underlying", "SPY")
    content_parts = []

    trade_name = Text()
    trade_name.append(f"\n  {underlying} {structure_name}", style="bold white")
    content_parts.append(trade_name)

    section1 = Text()
    section1.append("\n  ── WHAT'S HAPPENING ──────────────────────────────────────\n", style="dim")
    section1.append(f"  {thesis.get('what_happening', 'Market analysis in progress.')}\n", style="white")
    content_parts.append(section1)

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

    why = proposal.get("teaching", {}).get("why_this_matters", {})
    if why:
        section = Text()
        section.append("\n  ── WHY THIS MATTERS ─────────────────────────────────────\n", style="dim cyan")
        section.append(f"  {why.get('explanation', '')}\n", style="white")
        content_parts.append(section)

    history = proposal.get("teaching", {}).get("historical_context", {})
    if history:
        section = Text()
        section.append("\n  ── HISTORICAL CONTEXT ───────────────────────────────────\n", style="dim cyan")
        section.append(f"  {history.get('explanation', '')}\n", style="white")
        content_parts.append(section)

    comparison = proposal.get("teaching", {}).get("trade_comparison", {})
    if comparison and comparison.get("match"):
        section = Text()
        section.append("\n  ── JOURNAL COMPARISON ───────────────────────────────────\n", style="dim cyan")
        section.append(f"  {comparison.get('explanation', '')}\n", style="white")
        content_parts.append(section)

    max_loss = float(proposal.get("max_loss_per_contract", 0) or 0)
    max_profit = float(proposal.get("max_profit_per_contract", 0) or 0)
    breakeven = float(proposal.get("breakeven", 0) or 0)

    section3 = Text()
    section3.append("\n  ── THE NUMBERS ───────────────────────────────────────────\n", style="dim")
    section3.append("  You could make:     ", style="dim")
    section3.append(f"up to ${max_profit:.0f} per contract\n", style="bold green")
    section3.append("  You could lose:     ", style="dim")
    section3.append(f"up to ${max_loss:.0f} per contract\n", style="bold red")
    section3.append("  Breaking even:      ", style="dim")
    section3.append(f"if {underlying} is above ${breakeven:.2f}\n", style="white")
    section3.append("  Max loss:           ", style="dim")
    section3.append(f"if {underlying} is below {float(long_leg.get('strike', 0) or 0):.0f} at expiry\n", style="red")
    content_parts.append(section3)

    section4 = Text()
    section4.append("\n  ── WHY NOW ───────────────────────────────────────────────\n", style="dim")
    section4.append(f"  {thesis.get('why_now', 'Timing analysis in progress.')}\n", style="white")
    content_parts.append(section4)

    section5 = Text()
    section5.append("\n  ── WHAT COULD GO WRONG ──────────────────────────────────\n", style="dim")
    section5.append(f"  {thesis.get('what_could_go_wrong', 'Risk assessment in progress.')}\n", style="yellow")
    content_parts.append(section5)

    account = _account_value(proposal)
    label, _, pct = _risk_meter(max_loss, account)
    risk_style = "green" if label == "GREEN" else "yellow" if label == "YELLOW" else "red"
    section6 = Text()
    section6.append("\n  ── SAFETY CHECK ─────────────────────────────────────────\n", style="dim")
    section6.append(f"  {label}: max risk ${max_loss:.0f} ({pct:.2f}% of account)\n", style=risk_style)
    passed = sum(check.get("status") == "PASS" for check in (risk_check or {}).get("checks", []))
    total = len((risk_check or {}).get("checks", [])) or 6
    section6.append(f"  ✓ {passed or total} of {total} safety checks passed\n", style="green")
    content_parts.append(section6)

    section7 = Text()
    section7.append("\n  ── CONFIRMATION ──────────────────────────────────────────\n", style="dim")
    section7.append(f"  I understand this trade can lose up to ${max_loss:.0f} and the\n  system may auto-exit before expiration.\n", style="white")
    content_parts.append(section7)

    full_content = Text()
    for part in content_parts:
        full_content.append_text(part)

    console.print()
    console.print(Panel(full_content, title=header, subtitle=Text("  [APPROVE]  or  [REJECT]  ", style="bold"), border_style="gold1", padding=(0, 1), width=72))

    # Rich cannot create interactive disclosure controls in a terminal, so
    # these are rendered as explicit expandable-style views when requested.
    if pro_view or str(user_level).title() in {"Intermediate", "Advanced"}:
        _render_learn_more(proposal, conviction)
    _render_risk_meter(max_loss, account)
    _render_wrong_scenario(proposal)

    if conviction:
        console.print(Panel(_conviction_table(conviction), title=Text(f"CONVICTION BREAKDOWN — {float(conviction.get('score', proposal.get('conviction_score', 0))):.1f}/100", style="bold gold1"), border_style="gold1", width=72))


def _render_no_trade_card(proposal: dict, trade_number: int = 0) -> None:
    reason = proposal.get("reason", "No clear opportunity detected.")
    regime = proposal.get("structure", "NEUTRAL")
    content = Text()
    content.append(f"\n  {reason}\n\n", style="white")
    content.append("  ── WHAT WE SAW ─────────────────────────────────────────\n", style="dim")
    content.append("  The market conditions don't meet our criteria for a\n  defined-risk options trade right now.\n\n", style="white")
    content.append("  ── WHAT THIS MEANS ────────────────────────────────────\n", style="dim")
    content.append("  When conditions aren't right, our system stays quiet.\n  This is by design — patience is part of the strategy.\n\n", style="white")
    lesson = proposal.get("teaching", {}).get("rejection", {}).get("explanation")
    if lesson:
        content.append("  ── LEARNING MOMENT ─────────────────────────────────────\n", style="dim cyan")
        content.append(f"  {lesson}\n\n", style="white")
    content.append("  ── NEXT SCAN ──────────────────────────────────────────\n  Re-checking in 15 minutes...\n", style="cyan")
    console.print()
    console.print(Panel(content, title=Text("BULLRUN", style="bold gold1") + Text(" — NO TRADE", style="bold dim"), border_style="dim", padding=(0, 1), width=72))


def _render_pro_view(proposal: dict, risk_check: dict, conviction: dict = None) -> None:
    """Backward-compatible alias for the detailed view."""
    _render_learn_more(proposal, conviction)
    if risk_check:
        content = Text("\n  RISK ENGINE CHECKS\n", style="bold cyan")
        for check in risk_check.get("checks", []):
            icon = "✓" if check.get("status") == "PASS" else "✗"
            style = "green" if icon == "✓" else "red"
            content.append(f"  {icon} {check.get('name', 'check')}: {check.get('detail', '')}\n", style=style)
        console.print(Panel(content, title=Text("PRO DESK VIEW", style="bold cyan"), border_style="cyan", width=72, padding=(0, 1)))
