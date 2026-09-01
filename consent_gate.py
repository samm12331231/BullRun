"""
consent_gate.py — Human Consent Gate

Role: The final human checkpoint. Displays the trade proposal and waits
for explicit human approval before any execution happens.

This is the "conscience" of BullRun — the human always has the final say.

The consent gate:
1. Shows the trade card
2. Asks for confirmation that the user understands the risk
3. Waits for APPROVE or REJECT
4. Logs the decision with timestamp
5. Returns the decision to the orchestrator
"""

import json
import os
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.text import Text
from config import AUDIT_LOG

console = Console()


def run(proposal: dict, risk_check: dict, thesis: dict, trade_number: int) -> dict:
    """
    Main entry point for the Consent Gate.
    Displays the proposal and waits for human decision.

    Returns:
        dict with decision (APPROVE/REJECT), timestamp, and reason
    """

    signal = proposal.get("signal", "NO_TRADE")

    # If no trade was proposed, skip consent
    if signal != "PROPOSE":
        return {
            "decision": "SKIPPED",
            "reason": "No trade proposed",
            "timestamp": datetime.now().isoformat(),
        }

    # ── Show the trade card (handled by trade_card.py in orchestrator) ───
    # ── Ask for comprehension confirmation ───────────────────────────────
    console.print()
    max_loss = proposal.get("max_loss_per_contract", 0)
    breakeven = proposal.get("breakeven", 0)

    confirm_text = Text()
    confirm_text.append("\n  Before you approve, please confirm:\n", style="bold yellow")
    confirm_text.append(f"  I understand this trade can lose up to ", style="white")
    confirm_text.append(f"${max_loss:.0f}", style="bold red")
    confirm_text.append(f" and the\n", style="white")
    confirm_text.append(f"  system may auto-exit before expiration.\n", style="white")

    console.print(confirm_text)

    # ── Get user decision ────────────────────────────────────────────────
    console.print()
    decision_input = Prompt.ask(
        "  Your decision",
        choices=["approve", "reject", "why"],
        default="approve",
        show_choices=True,
    )

    # ── Handle "why" — show expanded explanation ─────────────────────────
    if decision_input.lower() == "why":
        _show_expanded_explanation(proposal, risk_check, thesis)
        # Ask again after showing explanation
        decision_input = Prompt.ask(
            "  Your decision",
            choices=["approve", "reject"],
            default="approve",
            show_choices=True,
        )

    # ── Process decision ─────────────────────────────────────────────────
    decision = "APPROVE" if decision_input.lower() == "approve" else "REJECT"
    reason = ""

    if decision == "REJECT":
        reason = Prompt.ask("  Reason (optional)", default="User declined")

    # ── Display result ───────────────────────────────────────────────────
    if decision == "APPROVE":
        console.print()
        console.print(Panel(
            Text("  Trade approved. Submitting to Alpaca...\n", style="bold green"),
            title=Text("BULLRUN", style="bold gold1") + Text(" — APPROVED", style="bold green"),
            border_style="green",
            width=62,
        ))
    else:
        console.print()
        console.print(Panel(
            Text(f"  Trade rejected. No order submitted.\n  Reason: {reason}\n", style="bold red"),
            title=Text("BULLRUN", style="bold gold1") + Text(" — REJECTED", style="bold red"),
            border_style="red",
            width=62,
        ))

    # ── Log decision to audit trail ──────────────────────────────────────
    _log_decision(trade_number, decision, reason, proposal)

    return {
        "decision": decision,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    }


def _show_expanded_explanation(proposal: dict, risk_check: dict, thesis: dict) -> None:
    """Show expanded explanation when user types 'why'."""

    content = Text()
    content.append("\n  ── DETAILED EXPLANATION ──────────────────────────────────\n\n", style="dim cyan")

    # Signal check
    content.append("  SIGNAL CHECK:\n", style="bold white")
    content.append(f"    Regime:      ", style="dim")
    content.append(f"{proposal.get('regime', 'N/A')}\n", style="white")
    content.append(f"    Direction:   ", style="dim")
    content.append(f"{proposal.get('direction', 'N/A')}\n", style="white")
    content.append(f"    Structure:   ", style="dim")
    content.append(f"{proposal.get('structure', 'N/A').replace('_', ' ').title()}\n", style="white")

    # Risk checks
    if risk_check:
        content.append(f"\n  RISK ENGINE:\n", style="bold white")
        for check in risk_check.get("checks", []):
            icon = "✓" if check["status"] == "PASS" else "✗"
            color = "green" if check["status"] == "PASS" else "red"
            content.append(f"    {icon} {check['name']}: {check['detail']}\n", style=color)

    # Thesis
    content.append(f"\n  THESIS:\n", style="bold white")
    content.append(f"    {thesis.get('what_happening', 'N/A')}\n", style="white")
    content.append(f"    {thesis.get('why_now', 'N/A')}\n", style="white")
    content.append(f"\n  RISKS:\n", style="bold white")
    content.append(f"    {thesis.get('what_could_go_wrong', 'N/A')}\n", style="yellow")

    console.print(Panel(
        content,
        title=Text("WHY THIS TRADE?", style="bold cyan"),
        border_style="cyan",
        padding=(0, 1),
        width=62,
    ))


def _log_decision(trade_number: int, decision: str, reason: str, proposal: dict) -> None:
    """Log the consent decision to the audit trail."""

    entry = {
        "timestamp": datetime.now().isoformat(),
        "trade_number": trade_number,
        "decision": decision,
        "reason": reason,
        "structure": proposal.get("structure"),
        "underlying": proposal.get("underlying"),
        "max_loss": proposal.get("max_loss_per_contract"),
        "max_profit": proposal.get("max_profit_per_contract"),
    }

    try:
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        console.print(f"[yellow][Audit] Failed to log decision: {e}[/yellow]")
