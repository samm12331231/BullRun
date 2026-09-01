"""Rich terminal trade card for BullRun.

The card is intentionally presentation-only: it never changes a proposal,
risk decision, or consent decision. It turns the same deterministic inputs
into an approval surface that teaches the user what they are approving.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

CONVICTION_WEIGHTS = {
    "regime_strength": 25,
    "momentum_align": 20,
    "options_pricing": 15,
    "liquidity": 15,
    "risk_reward": 15,
    "time_alignment": 10,
}
DISPLAY_NAMES = {
    "regime_strength": "Regime strength",
    "momentum_align": "Momentum alignment",
    "options_pricing": "Options pricing",
    "liquidity": "Liquidity",
    "risk_reward": "Risk/reward",
    "time_alignment": "Time alignment",
}


def _account_value(proposal: dict) -> float:
    return float(proposal.get("account_value", proposal.get("portfolio_value", 100_000)) or 100_000)


def _risk_meter(max_loss: float, account_value: float) -> tuple[str, str, float]:
    """Return label, terminal gauge, and max-loss percentage of account."""
    pct = (max_loss / account_value * 100) if account_value > 0 else 100.0
    if pct <= 0.5:
        return "GREEN", "[████████████████████]", pct
    if pct <= 1.0:
        return "YELLOW", "[██████████████░░░░░░]", pct
    return "RED", "[██████████░░░░░░░░░░]", pct


def _conviction_table(conviction: dict | None, proposal: dict | None = None) -> Table:
    """Show all six conviction factors, their weights, and contribution."""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Factor")
    table.add_column("Weight", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Weighted", justify="right")
    conviction = conviction or {}
    breakdown = conviction.get("breakdown", {})
    for key, weight in CONVICTION_WEIGHTS.items():
        raw = breakdown.get(key, 0)
        try:
            score = float(raw)
        except (TypeError, ValueError):
            score = 0.0
        table.add_row(DISPLAY_NAMES[key], f"{weight}%", f"{score:.1f}/100", f"{score * weight / 100:.1f}")
    total = float(conviction.get("score", (proposal or {}).get("conviction_score", 0)) or 0)
    table.add_row("[bold]TOTAL[/bold]", "100%", f"[bold]{total:.1f}/100[/bold]", "[bold]—[/bold]")
    return table


def _render_learn_more(proposal: dict, conviction: dict | None = None, user_level: str = "Beginner") -> None:
    """Render an expandable-style technical strategy disclosure in Rich."""
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})
    structure = proposal.get("structure", "UNKNOWN").replace("_", " ").title()
    details = Text()
    details.append("\n  ── FULL STRATEGY DETAILS ───────────────────────────────\n", style="bold cyan")
    details.append(f"  Structure: {structure}\n", style="white")
    details.append(f"  BUY  {long_leg.get('strike', '?')} {long_leg.get('type', '?')} @ ${float(long_leg.get('mid_price', 0) or 0):.2f}\n", style="green")
    details.append(f"  SELL {short_leg.get('strike', '?')} {short_leg.get('type', '?')} @ ${float(short_leg.get('mid_price', 0) or 0):.2f}\n", style="red")
    details.append(f"  Expiry: {proposal.get('expiry', '?')} | DTE: {proposal.get('dte', '?')} | Width: ${float(proposal.get('spread_width', 0) or 0):.2f}\n", style="dim")
    details.append("\n  Payoff: the long leg supplies directional exposure; the short leg reduces entry cost and caps upside.\n", style="white")
    details.append("  Risk: the debit paid is the defined maximum loss at expiration, subject to execution, fees, and slippage.\n", style="white")
    if str(user_level).title() in {"Intermediate", "Advanced"}:
        details.append(f"\n  Greeks — long: Δ {float(long_leg.get('delta', 0) or 0):.3f}, Γ {float(long_leg.get('greeks', {}).get('gamma', 0) or 0):.4f}, Θ {float(long_leg.get('greeks', {}).get('theta', 0) or 0):.4f}, IV {float(long_leg.get('iv', 0) or 0):.3f}\n", style="cyan")
        details.append(f"  Greeks — short: Δ {float(short_leg.get('delta', 0) or 0):.3f}, Γ {float(short_leg.get('greeks', {}).get('gamma', 0) or 0):.4f}, Θ {float(short_leg.get('greeks', {}).get('theta', 0) or 0):.4f}, IV {float(short_leg.get('iv', 0) or 0):.3f}\n", style="cyan")
    if conviction:
        details.append(f"\n  Conviction: {float(conviction.get('score', 0) or 0):.1f}/100 across six weighted factors.\n", style="bold")
    console.print(Panel(details, title=Text("LEARN MORE", style="bold cyan"), border_style="cyan", padding=(0, 1), width=78))


def _render_risk_meter(max_loss: float, account_value: float) -> None:
    label, gauge, pct = _risk_meter(max_loss, account_value)
    style = "green" if label == "GREEN" else "yellow" if label == "YELLOW" else "red"
    content = Text()
    content.append("  MAX-LOSS RISK METER\n", style="bold")
    content.append(f"  {gauge}  {label}\n", style=f"bold {style}")
    content.append(f"  ${max_loss:,.0f} maximum loss = {pct:.2f}% of a ${account_value:,.0f} account.\n", style="white")
    content.append("  Green ≤ 0.50%   Yellow ≤ 1.00%   Red > 1.00%\n", style="dim")
    console.print(Panel(content, title=Text("RISK METER", style=f"bold {style}"), border_style=style, width=78, padding=(0, 1)))


def _render_wrong_scenario(proposal: dict) -> None:
    max_loss = float(proposal.get("max_loss_per_contract", 0) or 0)
    underlying = proposal.get("underlying", "the underlying")
    structure = proposal.get("structure", "the spread").replace("_", " ").lower()
    content = Text()
    content.append("\n  If the thesis is wrong and the position reaches its defined-loss boundary,\n", style="white")
    content.append(f"  the planned worst case is a ${max_loss:,.0f} loss per contract. {underlying} can keep moving,\n", style="white")
    content.append("  but the two-leg spread prevents the loss from expanding without bound at expiry.\n", style="white")
    content.append("  Fees, slippage, early exercise and exit prices can affect the realized result.\n", style="dim")
    console.print(Panel(content, title=Text("WHAT IF I'M WRONG?", style="bold yellow"), border_style="yellow", width=78, padding=(0, 1)))


def _ensure_teaching(proposal: dict, user_level: str) -> dict:
    """Fill teaching surfaces when the caller has not already attached them."""
    teaching = proposal.setdefault("teaching", {})
    if all(key in teaching for key in ("why_this_matters", "historical_context", "trade_comparison")):
        return teaching
    try:
        from teaching_engine import build_teaching_package
        package = build_teaching_package(proposal, user_level=user_level)
        for key, value in package.items():
            teaching.setdefault(key, value)
    except Exception:
        # Rendering must never block the existing trading/consent path.
        pass
    return teaching


def render_trade_card(proposal: dict, risk_check: dict, thesis: dict, trade_number: int = 0, conviction: dict = None, pro_view: bool = False, user_level: str = "Beginner") -> None:
    """Render the complete teaching-first trade card without changing decisions."""
    signal = proposal.get("signal", "NO_TRADE")
    if signal == "NO_TRADE":
        _render_no_trade_card(proposal, trade_number)
        return

    user_level = str(user_level or "Beginner").title()
    teaching = _ensure_teaching(proposal, user_level)
    structure = proposal.get("structure", "UNKNOWN")
    underlying = proposal.get("underlying", "SPY")
    long_leg = proposal.get("long_leg", {})
    max_loss = float(proposal.get("max_loss_per_contract", 0) or 0)
    max_profit = float(proposal.get("max_profit_per_contract", 0) or 0)
    breakeven = float(proposal.get("breakeven", 0) or 0)
    account = _account_value(proposal)

    header = Text("BULLRUN", style="bold gold1")
    header.append(" — TRADE PROPOSAL", style="bold")
    if trade_number:
        header.append(f" #{trade_number:03d}", style="dim")

    content = Text()
    content.append(f"\n  {underlying} {structure.replace('_', ' ').title()}\n", style="bold white")
    content.append("\n  ── WHAT'S HAPPENING ──────────────────────────────────────\n", style="dim")
    content.append(f"  {thesis.get('what_happening', 'Market analysis in progress.')}\n", style="white")
    content.append("\n  ── THE TRADE ─────────────────────────────────────────────\n", style="dim")
    content.append(f"  {thesis.get('the_trade', 'Trade proposal being evaluated.')}\n", style="white")

    for key, heading in (("why_this_matters", "WHY THIS MATTERS"), ("historical_context", "HISTORICAL CONTEXT"), ("trade_comparison", "JOURNAL COMPARISON")):
        lesson = teaching.get(key, {})
        if lesson and lesson.get("explanation"):
            content.append(f"\n  ── {heading} ─────────────────────────────────────\n", style="dim cyan")
            content.append(f"  {lesson['explanation']}\n", style="white")

    strategy = teaching.get("strategy")
    if strategy:
        content.append("\n  ── LEARN THIS STRATEGY ──────────────────────────────────\n", style="dim cyan")
        content.append(f"  {strategy.get('explanation', '')}\n", style="white")

    content.append("\n  ── THE NUMBERS ───────────────────────────────────────────\n", style="dim")
    content.append(f"  Max profit:   ${max_profit:,.0f} / contract\n", style="green")
    content.append(f"  Max loss:     ${max_loss:,.0f} / contract\n", style="red")
    content.append(f"  Breakeven:    ${breakeven:.2f}\n", style="white")
    content.append(f"  DTE:          {proposal.get('dte', '?')} days\n", style="white")

    label, _, pct = _risk_meter(max_loss, account)
    risk_style = "green" if label == "GREEN" else "yellow" if label == "YELLOW" else "red"
    content.append("\n  ── SAFETY CHECK ─────────────────────────────────────────\n", style="dim")
    content.append(f"  {label}: maximum loss is {pct:.2f}% of account\n", style=risk_style)
    checks = (risk_check or {}).get("checks", [])
    passed = sum(check.get("status") == "PASS" for check in checks)
    total = len(checks) or 6
    content.append(f"  ✓ {passed} of {total} deterministic checks passed\n", style="green" if passed == total else "yellow")

    content.append("\n  ── CONFIRMATION ──────────────────────────────────────────\n", style="dim")
    content.append(f"  I understand this trade can lose up to ${max_loss:,.0f} and\n  the system may auto-exit before expiration.\n", style="white")

    console.print()
    console.print(Panel(content, title=header, subtitle=Text("  [APPROVE]  or  [REJECT]  ", style="bold"), border_style="gold1", padding=(0, 1), width=78))

    # Rich is terminal UI, so "expandable" is represented by an explicit detail panel.
    if pro_view or user_level in {"Intermediate", "Advanced"}:
        _render_learn_more(proposal, conviction, user_level)
    _render_risk_meter(max_loss, account)
    _render_wrong_scenario(proposal)
    if conviction or proposal.get("conviction_breakdown"):
        conviction = conviction or {"score": proposal.get("conviction_score", 0), "breakdown": proposal.get("conviction_breakdown", {})}
        console.print(Panel(_conviction_table(conviction, proposal), title=Text(f"CONVICTION BREAKDOWN — {float(conviction.get('score', 0) or 0):.1f}/100", style="bold gold1"), border_style="gold1", width=78))


def _render_no_trade_card(proposal: dict, trade_number: int = 0) -> None:
    reason = proposal.get("reason", "No clear opportunity detected.")
    content = Text()
    content.append(f"\n  {reason}\n\n", style="white")
    content.append("  ── WHAT WE SAW ─────────────────────────────────────────\n", style="dim")
    content.append("  The market conditions do not meet our criteria for a defined-risk options trade right now.\n\n", style="white")
    content.append("  ── WHAT THIS MEANS ─────────────────────────────────────\n", style="dim")
    content.append("  BullRun stays quiet when evidence is weak. Passing is a decision: it protects capital and creates a teaching moment.\n\n", style="white")
    lesson = proposal.get("teaching", {}).get("rejection", {}).get("explanation")
    if lesson:
        content.append("  ── LEARNING MOMENT ─────────────────────────────────────\n", style="dim cyan")
        content.append(f"  {lesson}\n", style="white")
    console.print()
    console.print(Panel(content, title=Text("BULLRUN", style="bold gold1") + Text(" — NO TRADE", style="bold dim"), border_style="dim", padding=(0, 1), width=78))


def _render_pro_view(proposal: dict, risk_check: dict, conviction: dict = None) -> None:
    """Backward-compatible technical view used by older callers."""
    _render_learn_more(proposal, conviction, "Advanced")
    if risk_check:
        content = Text("\n  RISK ENGINE CHECKS\n", style="bold cyan")
        for check in risk_check.get("checks", []):
            icon = "✓" if check.get("status") == "PASS" else "✗"
            style = "green" if icon == "✓" else "red"
            content.append(f"  {icon} {check.get('name', 'check')}: {check.get('detail', '')}\n", style=style)
        console.print(Panel(content, title=Text("PRO DESK VIEW", style="bold cyan"), border_style="cyan", width=78, padding=(0, 1)))
