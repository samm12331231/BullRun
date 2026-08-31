"""
results.py — Results Agent (Post-Trade Learning Reports)

Role: After a trade closes, generates a learning report that explains
what happened, why, and what can be learned. This turns every trade
into a teaching moment.

This is the "teacher" of Conviction Gate — it helps beginners learn by doing.
"""

import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


def generate_learning_report(position: dict, trade_number: int) -> str:
    """
    Generate a post-trade learning report.

    Args:
        position: The closed position data
        trade_number: Sequential trade number

    Returns:
        Formatted report string
    """

    structure = position.get("structure", "UNKNOWN")
    pnl = position.get("pnl", 0) or 0
    exit_reason = position.get("exit_reason", "Unknown")
    entry_time = position.get("entry_time", "")
    exit_time = position.get("exit_time", "")
    max_loss = position.get("max_loss", 0)
    max_profit = position.get("max_profit", 0)

    # Calculate days held
    try:
        entry_dt = datetime.fromisoformat(entry_time)
        exit_dt = datetime.fromisoformat(exit_time) if exit_time else datetime.now()
        days_held = (exit_dt - entry_dt).days
    except Exception:
        days_held = 0

    # Determine outcome type
    if pnl > 0:
        outcome = "WIN"
        outcome_color = "green"
        outcome_text = "This trade was profitable."
    elif pnl < 0:
        outcome = "LOSS"
        outcome_color = "red"
        outcome_text = "This trade lost money."
    else:
        outcome = "BREAKEVEN"
        outcome_color = "yellow"
        outcome_text = "This trade broke even."

    # Build the report
    content = Text()
    content.append(f"\n  Result:  ", style="dim")
    content.append(f"${pnl:+,.2f}", style=f"bold {outcome_color}")
    content.append(f" ({outcome})\n", style=outcome_color)
    content.append(f"  Duration: {days_held} days\n\n", style="dim")

    # What we predicted
    content.append("  ── WHAT WE PREDICTED ──────────────────────────────────\n", style="dim")
    if structure == "BULL_CALL_SPREAD":
        content.append("  SPY would continue rising above our short strike.\n", style="white")
    elif structure == "BEAR_PUT_SPREAD":
        content.append("  SPY would continue falling below our short strike.\n", style="white")
    else:
        content.append("  The market would move in our predicted direction.\n", style="white")

    # What happened
    content.append("\n  ── WHAT HAPPENED ──────────────────────────────────────\n", style="dim")
    content.append(f"  {outcome_text}\n", style="white")
    content.append(f"  Exit reason: {exit_reason}\n", style="white")

    # What worked / what didn't
    content.append("\n  ── ANALYSIS ──────────────────────────────────────────\n", style="dim")
    if pnl > 0:
        content.append("  ✓ The directional thesis was correct\n", style="green")
        content.append("  ✓ Risk management (TP/SL) worked as designed\n", style="green")
        content.append("  ✓ The defined-risk structure limited downside\n", style="green")
    else:
        content.append("  ✗ The directional thesis was incorrect\n", style="red")
        content.append("  ✓ Risk management limited the loss to max_loss\n", style="green")
        content.append("  ✓ The system exited automatically per rules\n", style="green")

    # Lesson
    content.append("\n  ── LESSON ────────────────────────────────────────────\n", style="dim")
    if pnl > 0:
        content.append("  When multiple indicators agree, the probability of success\n", style="white")
        content.append("  increases. The key: we never risked more than we could\n", style="white")
        content.append("  afford to lose to find out.\n", style="white")
    else:
        content.append("  Markets don't always do what indicators suggest. The value\n", style="white")
        content.append("  of this system isn't that it's always right — it's that\n", style="white")
        content.append("  when it's wrong, the loss is bounded and predictable.\n", style="white")

    # Running total
    content.append("\n  ── RUNNING TOTAL ─────────────────────────────────────\n", style="dim")

    # Render the panel
    console.print()
    console.print(Panel(
        content,
        title=Text("CONVICTION GATE", style="bold gold1") + Text(f" — TRADE RESULT #{trade_number:03d}", style="bold"),
        border_style=outcome_color,
        padding=(0, 1),
        width=62,
    ))

    return str(content)


def generate_session_summary(positions: list) -> None:
    """Generate an end-of-session summary of all trades."""

    if not positions:
        console.print("[dim]No trades to summarize.[/dim]")
        return

    closed = [p for p in positions if p["status"] == "CLOSED"]
    if not closed:
        console.print("[dim]No closed trades to summarize.[/dim]")
        return

    total_pnl = sum(p.get("pnl", 0) or 0 for p in closed)
    wins = sum(1 for p in closed if (p.get("pnl", 0) or 0) > 0)
    losses = sum(1 for p in closed if (p.get("pnl", 0) or 0) < 0)
    win_rate = (wins / len(closed) * 100) if closed else 0

    pnl_color = "green" if total_pnl >= 0 else "red"

    content = Text()
    content.append(f"\n  Total Trades:     {len(closed)}\n", style="white")
    content.append(f"  Winners:          {wins}\n", style="green")
    content.append(f"  Losers:           {losses}\n", style="red")
    content.append(f"  Win Rate:         {win_rate:.1f}%\n", style="bold white")
    content.append(f"  Total P&L:        ${total_pnl:+,.2f}\n", style=f"bold {pnl_color}")
    content.append(f"  Return:           {(total_pnl / 100_000 * 100):+.2f}%\n", style=f"bold {pnl_color}")

    console.print()
    console.print(Panel(
        content,
        title=Text("CONVICTION GATE", style="bold gold1") + Text(" — SESSION SUMMARY", style="bold"),
        border_style=pnl_color,
        padding=(0, 1),
        width=62,
    ))
