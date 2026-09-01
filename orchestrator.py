"""
orchestrator.py — Master Orchestrator

Role: The central coordinator of BullRun. Runs each agent in the
correct sequence, passes data between them, and handles the full pipeline:

  Scout → Quant → Risk Engine → CIO → Trade Card → Consent → Execution → Monitor

This is the "conductor" of BullRun — it keeps all players in sync.

Broadcasts every stage event via WebSocket so the Next.js dashboard
updates in real-time.
"""

import json
import asyncio
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

from agents import scout_agent, quant_agent, risk_engine, cio_agent
from trade_card import render_trade_card
from consent_gate import run as consent_run
from execution import run as execution_run
from monitor import monitor, render_dashboard
from results import generate_learning_report, generate_session_summary
from teaching_engine import regime_lesson, strategy_explainer, rejection_explainer, generate_trade_journal
from audit import (
    log_signal, log_proposal, log_risk_check,
    log_consent, log_execution,
)

console = Console()

# Global trade counter
_trade_counter = 0

# ── WebSocket broadcast helper ──────────────────────────────────────────────

_ws_manager = None


def _set_ws_manager(manager):
    """Set the WebSocket manager for broadcasting (called from api.py)."""
    global _ws_manager
    _ws_manager = manager


def _broadcast(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    if _ws_manager is None:
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_ws_manager.broadcast(message))
        else:
            loop.run_until_complete(_ws_manager.broadcast(message))
    except RuntimeError:
        # No event loop running — skip broadcast (CLI-only mode)
        pass
    except Exception:
        pass


def run_pipeline() -> dict:
    """
    Execute the full BullRun pipeline.
    Returns all intermediate and final results.
    """

    global _trade_counter
    _trade_counter += 1

    console.print()
    console.rule("[bold gold1]  BULLRUN  |  Starting Pipeline  [/bold gold1]")
    console.print()

    results = {}

    # ── Stage 1: Scout — Regime Detection ────────────────────────────────
    console.print("[bold cyan]Stage 1/5:[/bold cyan] Scout scanning market regime...")
    try:
        regime_result = scout_agent.run()
        regime_result["lesson"] = regime_lesson(regime_result)
        results["regime"] = regime_result
        log_signal(regime_result, _trade_counter)

        # Broadcast to dashboard
        _broadcast({
            "type": "regime_update",
            "data": regime_result,
            "trade_number": _trade_counter,
            "timestamp": datetime.now().isoformat(),
        })
        _broadcast({
            "type": "agent_log",
            "agent": "scout",
            "message": f"Regime: {regime_result['regime']} (ADX: {regime_result['metrics']['adx']:.1f})",
            "trade_number": _trade_counter,
        })
        _broadcast({
            "type": "teaching_update",
            "lesson_type": "regime_lesson",
            "data": regime_result["lesson"],
            "trade_number": _trade_counter,
        })
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Scout failed: {e}[/bold red]")
        return {"error": f"Scout failed: {e}"}

    regime = regime_result["regime"]
    console.print(f"[cyan][Orchestrator][/cyan] Regime: [bold]{regime}[/bold]")

    # ── Stage 2: Quant — Options Structure Selection ─────────────────────
    console.print(f"\n[bold cyan]Stage 2/5:[/bold cyan] Quant selecting options structure...")
    try:
        proposal = quant_agent.run(regime_result)
        results["proposal"] = proposal
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Quant failed: {e}[/bold red]")
        return {"error": f"Quant failed: {e}"}

    # If no trade proposed, show the no-trade card and exit
    if proposal.get("signal") == "NO_TRADE":
        proposal["teaching"] = {"rejection": rejection_explainer(regime_result, proposal)}
        console.print(f"[yellow][Orchestrator] No trade proposed — {proposal.get('reason', 'unknown')}[/yellow]")
        render_trade_card(proposal, None, {"what_happening": proposal.get("reason", "")}, _trade_counter)

        _broadcast({
            "type": "no_trade",
            "reason": proposal.get("reason", ""),
            "teaching": proposal["teaching"],
            "trade_number": _trade_counter,
        })

        results["decision"] = "NO_TRADE"
        return results

    if proposal.get("signal") in ("REJECT", "WATCH"):
        proposal["teaching"] = {"rejection": rejection_explainer(regime_result, proposal)}
        console.print(f"[yellow][Orchestrator] Conviction too low — {proposal.get('signal')}[/yellow]")
        _broadcast({
            "type": "no_trade",
            "reason": proposal.get("reason", "Conviction did not meet the approval threshold."),
            "teaching": proposal["teaching"],
            "trade_number": _trade_counter,
        })
        results["decision"] = proposal.get("signal")
        return results

    log_proposal(proposal, _trade_counter)
    proposal["teaching"] = {"regime": regime_result["lesson"], "strategy": strategy_explainer(proposal)}

    _broadcast({
        "type": "agent_log",
        "agent": "quant",
        "message": f"Proposed {proposal.get('structure', '').replace('_', ' ')} — conviction {proposal.get('conviction_score', 0):.1f}",
        "trade_number": _trade_counter,
    })

    # ── Stage 3: Risk Engine — Deterministic Validation ──────────────────
    console.print(f"\n[bold cyan]Stage 3/5:[/bold cyan] Risk Engine validating...")
    try:
        portfolio_state = {
            "open_position_count": len(monitor.get_open_positions()),
            "current_portfolio_exposure": sum(
                p.get("max_loss", 0) or 0 for p in monitor.get_open_positions()
            ),
            "available_cash": 100_000,
            "equity": 100_000,
            "open_positions": monitor.get_open_positions(),
        }
        risk_check = risk_engine.risk_engine.check(proposal, portfolio_state)
        results["risk_check"] = risk_check
        log_risk_check(risk_check, _trade_counter)

        _broadcast({
            "type": "agent_log",
            "agent": "risk",
            "message": f"Risk Engine: {risk_check['status']} ({len(risk_check.get('checks', []))} checks)",
            "trade_number": _trade_counter,
        })
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Risk Engine failed: {e}[/bold red]")
        return {"error": f"Risk Engine failed: {e}"}

    if risk_check["status"] == "REJECT":
        proposal["teaching"] = {
            "regime": regime_result["lesson"],
            "strategy": strategy_explainer(proposal),
            "rejection": rejection_explainer(regime_result, proposal, risk_check),
        }
        console.print(f"[red][Orchestrator] Risk Engine REJECTED trade[/red]")
        proposal["signal"] = "RISK_REJECTED"
        render_trade_card(proposal, risk_check, {"what_happening": "Trade failed risk checks"}, _trade_counter)

        _broadcast({
            "type": "risk_rejected",
            "failed_checks": risk_check.get("failed_checks", []),
            "teaching": proposal["teaching"],
            "trade_number": _trade_counter,
        })

        results["decision"] = "RISK_REJECTED"
        return results

    # ── Stage 4: CIO — Plain-English Thesis ──────────────────────────────
    console.print(f"\n[bold cyan]Stage 4/5:[/bold cyan] CIO generating thesis...")
    try:
        thesis = cio_agent.run(regime_result, proposal, risk_check)
        results["thesis"] = thesis

        _broadcast({
            "type": "agent_log",
            "agent": "cio",
            "message": f"Thesis generated: {thesis.get('what_happening', '')[:60]}...",
            "trade_number": _trade_counter,
        })
    except Exception as e:
        console.print(f"[yellow][Orchestrator] CIO failed: {e} — using fallback[/yellow]")
        thesis = {
            "what_happening": f"The market is showing a {regime.lower()} bias.",
            "the_trade": f"We're placing a {proposal.get('structure', 'spread').replace('_', ' ').title()}.",
            "the_numbers": f"Max gain: ${proposal.get('max_profit_per_contract', 0):.0f}, Max loss: ${proposal.get('max_loss_per_contract', 0):.0f}.",
            "why_now": "Multiple indicators confirm the direction.",
            "what_could_go_wrong": "The market could reverse, causing a loss.",
        }
        results["thesis"] = thesis

    # ── Broadcast full trade proposal to dashboard ───────────────────────
    _broadcast({
        "type": "trade_proposal",
        "trade_number": _trade_counter,
        "proposal": proposal,
        "thesis": thesis,
        "risk_check": risk_check,
        "timestamp": datetime.now().isoformat(),
    })

    # ── Stage 5: Trade Card + Consent Gate ───────────────────────────────
    console.print(f"\n[bold cyan]Stage 5/5:[/bold cyan] Awaiting human consent...")
    render_trade_card(proposal, risk_check, thesis, _trade_counter, proposal.get("conviction_breakdown"))

    # In CLI mode, use the terminal consent gate
    # In API mode, the dashboard handles consent via WebSocket
    consent = consent_run(proposal, risk_check, thesis, _trade_counter)
    results["consent"] = consent
    log_consent(consent, _trade_counter)

    # Broadcast consent decision
    _broadcast({
        "type": "consent_decision",
        "trade_number": _trade_counter,
        "decision": consent["decision"],
        "reason": consent.get("reason", ""),
        "timestamp": datetime.now().isoformat(),
    })

    if consent["decision"] == "REJECT":
        console.print(f"[yellow][Orchestrator] Human REJECTED trade[/yellow]")
        results["decision"] = "REJECTED"
        return results

    # ── Execute the trade ────────────────────────────────────────────────
    console.print(f"\n[bold cyan]Executing:[/bold cyan] Submitting to Alpaca...")
    execution = execution_run(proposal, consent, _trade_counter)
    results["execution"] = execution
    log_execution(execution, _trade_counter)

    _broadcast({
        "type": "execution_result",
        "trade_number": _trade_counter,
        "status": execution.get("status"),
        "order_id": execution.get("order_id"),
        "timestamp": datetime.now().isoformat(),
    })

    # ── Add to monitor ───────────────────────────────────────────────────
    if execution.get("status") in ("SUBMITTED", "FILLED", "DRY_RUN"):
        monitor.add_position(proposal, execution, _trade_counter)

    results["decision"] = "APPROVED"
    results["trade_number"] = _trade_counter

    console.print(f"\n[bold green][Orchestrator] Pipeline completed for trade #{_trade_counter}[/bold green]")
    return results


def run_pipeline_web() -> dict:
    """
    Web-compatible pipeline: runs Scout → Quant → Risk → CIO,
    broadcasts the trade proposal via WebSocket, and returns
    WITHOUT blocking on consent. The dashboard handles consent
    via the /api/consent endpoint.
    """
    global _trade_counter
    _trade_counter += 1

    console.print()
    console.rule("[bold gold1]  BULLRUN  |  Web Pipeline  [/bold gold1]")
    console.print()

    results = {}

    # Stage 1: Scout
    console.print("[bold cyan]Stage 1/4:[/bold cyan] Scout scanning market regime...")
    try:
        regime_result = scout_agent.run()
        regime_result["lesson"] = regime_lesson(regime_result)
        results["regime"] = regime_result
        log_signal(regime_result, _trade_counter)
        _broadcast({"type": "regime_update", "data": regime_result, "trade_number": _trade_counter, "timestamp": datetime.now().isoformat()})
        _broadcast({"type": "agent_log", "agent": "scout", "message": f"Regime: {regime_result['regime']} (ADX: {regime_result['metrics']['adx']:.1f})", "trade_number": _trade_counter})
        _broadcast({"type": "teaching_update", "lesson_type": "regime_lesson", "data": regime_result["lesson"], "trade_number": _trade_counter})
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Scout failed: {e}[/bold red]")
        return {"error": f"Scout failed: {e}"}

    regime = regime_result["regime"]

    # Stage 2: Quant
    console.print(f"\n[bold cyan]Stage 2/4:[/bold cyan] Quant selecting options structure...")
    try:
        proposal = quant_agent.run(regime_result)
        results["proposal"] = proposal
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Quant failed: {e}[/bold red]")
        return {"error": f"Quant failed: {e}"}

    if proposal.get("signal") == "NO_TRADE":
        proposal["teaching"] = {"rejection": rejection_explainer(regime_result, proposal)}
        _broadcast({"type": "no_trade", "reason": proposal.get("reason", ""), "teaching": proposal["teaching"], "trade_number": _trade_counter})
        results["decision"] = "NO_TRADE"
        return results

    if proposal.get("signal") in ("REJECT", "WATCH"):
        proposal["teaching"] = {"rejection": rejection_explainer(regime_result, proposal)}
        _broadcast({"type": "no_trade", "reason": proposal.get("reason", ""), "teaching": proposal["teaching"], "trade_number": _trade_counter})
        results["decision"] = proposal.get("signal")
        return results

    log_proposal(proposal, _trade_counter)
    proposal["teaching"] = {"regime": regime_result["lesson"], "strategy": strategy_explainer(proposal)}

    # Stage 3: Risk Engine
    console.print(f"\n[bold cyan]Stage 3/4:[/bold cyan] Risk Engine validating...")
    try:
        portfolio_state = {
            "open_position_count": len(monitor.get_open_positions()),
            "current_portfolio_exposure": sum(p.get("max_loss", 0) or 0 for p in monitor.get_open_positions()),
            "available_cash": 100_000,
            "equity": 100_000,
            "open_positions": monitor.get_open_positions(),
        }
        risk_check = risk_engine.risk_engine.check(proposal, portfolio_state)
        results["risk_check"] = risk_check
        log_risk_check(risk_check, _trade_counter)
    except Exception as e:
        console.print(f"[bold red][Orchestrator] Risk Engine failed: {e}[/bold red]")
        return {"error": f"Risk Engine failed: {e}"}

    if risk_check["status"] == "REJECT":
        proposal["teaching"] = {
            "regime": regime_result["lesson"],
            "strategy": strategy_explainer(proposal),
            "rejection": rejection_explainer(regime_result, proposal, risk_check),
        }
        proposal["signal"] = "RISK_REJECTED"
        _broadcast({"type": "risk_rejected", "failed_checks": risk_check.get("failed_checks", []), "teaching": proposal["teaching"], "trade_number": _trade_counter})
        results["decision"] = "RISK_REJECTED"
        return results

    # Stage 4: CIO
    console.print(f"\n[bold cyan]Stage 4/4:[/bold cyan] CIO generating thesis...")
    try:
        thesis = cio_agent.run(regime_result, proposal, risk_check)
        results["thesis"] = thesis
    except Exception as e:
        console.print(f"[yellow][Orchestrator] CIO failed: {e} — using fallback[/yellow]")
        thesis = {
            "what_happening": f"The market is showing a {regime.lower()} bias.",
            "the_trade": f"We're placing a {proposal.get('structure', 'spread').replace('_', ' ').title()}.",
            "the_numbers": f"Max gain: ${proposal.get('max_profit_per_contract', 0):.0f}, Max loss: ${proposal.get('max_loss_per_contract', 0):.0f}.",
            "why_now": "Multiple indicators confirm the direction.",
            "what_could_go_wrong": "The market could reverse, causing a loss.",
        }
        results["thesis"] = thesis

    # Broadcast full trade proposal — dashboard handles consent
    _broadcast({
        "type": "trade_proposal",
        "trade_number": _trade_counter,
        "proposal": proposal,
        "thesis": thesis,
        "risk_check": risk_check,
        "timestamp": datetime.now().isoformat(),
    })

    results["decision"] = "AWAITING_CONSENT"
    results["trade_number"] = _trade_counter
    return results


def execute_after_consent(trade_number: int, proposal: dict, consent: dict) -> dict:
    """Execute a trade after web consent is received."""
    execution = execution_run(proposal, consent, trade_number)
    log_execution(execution, trade_number)
    _broadcast({
        "type": "execution_result",
        "trade_number": trade_number,
        "status": execution.get("status"),
        "order_id": execution.get("order_id"),
        "timestamp": datetime.now().isoformat(),
    })
    if execution.get("status") in ("SUBMITTED", "FILLED", "DRY_RUN"):
        monitor.add_position(proposal, execution, trade_number)
    return execution


def run_monitor_check() -> list:
    """
    Check all open positions for exit conditions.
    Uses live P&L data from Alpaca/yfinance.
    Run this periodically (every 5-15 minutes during market hours).
    """

    console.print("[bold cyan][Monitor Check][/bold cyan] Checking open positions...")

    exits = monitor.check_positions()

    for pos in exits:
        console.print(f"[yellow]Position #{pos['trade_number']} triggered exit: {pos['exit_reason']}[/yellow]")

        # Close the position with actual P&L
        entry = monitor.close_position(pos, pos["exit_reason"])

        # Broadcast exit to dashboard
        _broadcast({
            "type": "trade_exit",
            "trade_number": pos["trade_number"],
            "exit_reason": pos["exit_reason"],
            "pnl": pos.get("unrealized_pnl", 0),
            "timestamp": datetime.now().isoformat(),
        })

        # Generate learning report
        generate_learning_report(pos, pos["trade_number"])
        journal = generate_trade_journal(pos, pos["trade_number"])
        _broadcast({
            "type": "learning_report",
            "trade_number": pos["trade_number"],
            "data": journal,
            "timestamp": datetime.now().isoformat(),
        })

    if not exits:
        # Broadcast portfolio status
        summary = monitor.get_portfolio_summary()
        _broadcast({
            "type": "portfolio_update",
            "data": summary,
            "timestamp": datetime.now().isoformat(),
        })
        console.print("[dim]All positions within parameters — no exits needed[/dim]")

    return exits


def run_dashboard():
    """Render the full portfolio dashboard."""
    render_dashboard(monitor)


def run_summary():
    """Generate and display session summary."""
    generate_session_summary(monitor.positions)


if __name__ == "__main__":
    console.print("[bold gold1]BullRun — Master Orchestrator[/bold gold1]")
    console.print("Running single pipeline test...\n")
    result = run_pipeline()
    console.print("\nResult:")
    print(json.dumps(result, indent=2, default=str))
