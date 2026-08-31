"""
execution.py — Alpaca Execution Layer

Role: Takes an approved trade proposal and executes it on Alpaca paper trading
via the MCP server (primary) or alpaca-py SDK (fallback).

This is the "hands" of Conviction Gate — it places the actual orders.

IMPORTANT: This only runs AFTER human consent is received.
"""

import os
import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from config import (
    ALPACA_API_KEY, ALPACA_SECRET_KEY,
    ALPACA_BASE_URL, AUDIT_LOG,
)

console = Console()


def run(proposal: dict, consent: dict, trade_number: int) -> dict:
    """
    Main entry point for the Execution Layer.
    Places the approved order on Alpaca paper trading.

    Returns:
        dict with order status, order IDs, and execution details
    """

    if consent.get("decision") != "APPROVE":
        console.print("[dim][Execution] Trade not approved — skipping execution[/dim]")
        return {
            "status": "SKIPPED",
            "reason": "Trade not approved",
            "timestamp": datetime.now().isoformat(),
        }

    console.print("[bold cyan][Execution][/bold cyan] Submitting order to Alpaca...")

    structure = proposal.get("structure", "")
    underlying = proposal.get("underlying", "SPY")

    # ── Build option symbols ────────────────────────────────────────────
    # Use Alpaca symbols directly from the quant agent if available
    long_leg = proposal.get("long_leg", {})
    short_leg = proposal.get("short_leg", {})

    long_sym = long_leg.get("alpaca_symbol", "")
    short_sym = short_leg.get("alpaca_symbol", "")

    # Fallback: construct from strike/expiry if symbols missing
    if not long_sym or not short_sym:
        expiry = _format_expiry(proposal)
        long_type_code = "C" if long_leg.get("type", "CALL") == "CALL" else "P"
        short_type_code = "C" if short_leg.get("type", "CALL") == "CALL" else "P"
        long_sym = long_sym or f"{underlying}{expiry}{long_type_code}{int(long_leg.get('strike', 0)):08d}"
        short_sym = short_sym or f"{underlying}{expiry}{short_type_code}{int(short_leg.get('strike', 0)):08d}"

    order_details = {
        "underlying": underlying,
        "structure": structure,
        "expiry": proposal.get("expiry", ""),
        "long_leg": {
            "symbol": long_sym,
            "strike": long_leg.get("strike"),
            "type": long_leg.get("type"),
            "side": "buy",
            "quantity": 1,
        },
        "short_leg": {
            "symbol": short_sym,
            "strike": short_leg.get("strike"),
            "type": short_leg.get("type"),
            "side": "sell",
            "quantity": 1,
        },
        "net_debit": proposal.get("net_debit"),
        "max_loss": proposal.get("max_loss_per_contract"),
    }

    console.print(f"[dim]Long: {long_sym} (buy)[/dim]")
    console.print(f"[dim]Short: {short_sym} (sell)[/dim]")
    console.print(f"[dim]Net debit: ${order_details['net_debit']:.2f}[/dim]")

    # ── Try MCP first, fallback to alpaca-py ─────────────────────────────
    try:
        result = _execute_via_mcp(order_details)
    except Exception as e:
        console.print(f"[yellow][Execution] MCP failed: {e} — trying alpaca-py fallback[/yellow]")
        try:
            result = _execute_via_sdk(order_details)
        except Exception as e2:
            console.print(f"[red][Execution] SDK also failed: {e2}[/red]")
            result = {
                "status": "FAILED",
                "error": str(e2),
                "timestamp": datetime.now().isoformat(),
            }

    # ── Log execution ────────────────────────────────────────────────────
    _log_execution(trade_number, order_details, result, consent)

    # ── Display result ───────────────────────────────────────────────────
    if result.get("status") in ("FILLED", "SUBMITTED"):
        console.print(Panel(
            Text(f"  Order submitted successfully!\n"
                 f"  Order ID: {result.get('order_id', 'N/A')}\n"
                 f"  Status: {result.get('status', 'N/A')}\n", style="bold green"),
            title=Text("CONVICTION GATE", style="bold gold1") + Text(" — EXECUTED", style="bold green"),
            border_style="green",
            width=62,
        ))
    else:
        console.print(Panel(
            Text(f"  Order failed: {result.get('error', 'Unknown error')}\n", style="bold red"),
            title=Text("CONVICTION GATE", style="bold gold1") + Text(" — FAILED", style="bold red"),
            border_style="red",
            width=62,
        ))

    return result


def _execute_via_mcp(order_details: dict) -> dict:
    """Execute order via Alpaca MCP server."""

    console.print("[dim]Attempting MCP execution...[/dim]")

    long_sym = order_details["long_leg"]["symbol"]
    short_sym = order_details["short_leg"]["symbol"]

    mcp_command = {
        "tool": "place_option_market_order",
        "params": {
            "order_legs": [
                {
                    "symbol": long_sym,
                    "qty": str(order_details["long_leg"]["quantity"]),
                    "side": "buy",
                },
                {
                    "symbol": short_sym,
                    "qty": str(order_details["short_leg"]["quantity"]),
                    "side": "sell",
                },
            ],
            "order_type": "limit",
            "limit_price": str(order_details["net_debit"]),
            "time_in_force": "day",
        },
    }

    console.print(f"[dim]MCP command: {json.dumps(mcp_command, indent=2)}[/dim]")

    # For now, simulate MCP execution
    # In production, this would call the actual MCP server via its SDK
    console.print("[yellow][Execution] MCP server integration — using SDK fallback for demo[/yellow]")
    raise NotImplementedError("MCP server integration pending — falling back to SDK")


def _execute_via_sdk(order_details: dict) -> dict:
    """Execute order via alpaca-py SDK (fallback)."""

    console.print("[dim]Executing via alpaca-py SDK...[/dim]")

    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        client = TradingClient(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            paper=True,
        )

        account = client.get_account()
        console.print(f"[dim]Account equity: ${float(account.equity):,.2f}[/dim]")

        long_sym = order_details["long_leg"]["symbol"]
        short_sym = order_details["short_leg"]["symbol"]

        # Calculate limit prices for each leg
        net_debit = order_details["net_debit"]
        long_mid = net_debit * 0.6  # Approximate long leg mid
        short_mid = net_debit * 0.4  # Approximate short leg mid

        # Buy long leg
        long_order = client.submit_order(
            LimitOrderRequest(
                symbol=long_sym,
                qty=order_details["long_leg"]["quantity"],
                side=OrderSide.BUY,
                limit_price=round(long_mid + 0.05, 2),  # Slightly above mid for fill
                time_in_force=TimeInForce.DAY,
            )
        )
        console.print(f"[green]Long leg submitted: {long_order.id}[/green]")

        # Sell short leg
        short_order = client.submit_order(
            LimitOrderRequest(
                symbol=short_sym,
                qty=order_details["short_leg"]["quantity"],
                side=OrderSide.SELL,
                limit_price=round(short_mid - 0.05, 2),  # Slightly below mid for fill
                time_in_force=TimeInForce.DAY,
            )
        )
        console.print(f"[green]Short leg submitted: {short_order.id}[/green]")

        return {
            "status": "SUBMITTED",
            "long_order_id": str(long_order.id),
            "short_order_id": str(short_order.id),
            "order_id": f"{long_order.id}/{short_order.id}",
            "long_symbol": long_sym,
            "short_symbol": short_sym,
            "timestamp": datetime.now().isoformat(),
        }

    except ImportError:
        console.print("[red][Execution] alpaca-py not installed — running in DRY RUN mode[/red]")
        return _dry_run(order_details)
    except Exception as e:
        console.print(f"[red][Execution] SDK error: {e} — running in DRY RUN mode[/red]")
        return _dry_run(order_details)


def _dry_run(order_details: dict) -> dict:
    """Simulate order execution for demo/testing."""

    order_id = f"DRY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    console.print("[yellow][Execution] DRY RUN — order not actually placed[/yellow]")
    console.print("[dim]Would have placed:[/dim]")
    console.print(f"[dim]  BUY  {order_details['long_leg']['symbol']} x{order_details['long_leg']['quantity']}[/dim]")
    console.print(f"[dim]  SELL {order_details['short_leg']['symbol']} x{order_details['short_leg']['quantity']}[/dim]")
    console.print(f"[dim]  Net debit: ${order_details['net_debit']:.2f}[/dim]")

    return {
        "status": "DRY_RUN",
        "order_id": order_id,
        "long_symbol": order_details["long_leg"]["symbol"],
        "short_symbol": order_details["short_leg"]["symbol"],
        "timestamp": datetime.now().isoformat(),
    }


def _format_expiry(proposal: dict) -> str:
    """Format expiration date for OCC option symbol format (YYMMDD)."""

    expiry = proposal.get("expiry", "")
    if expiry:
        try:
            dt = datetime.strptime(expiry, "%Y-%m-%d")
            return dt.strftime("%y%m%d")
        except ValueError:
            pass

    # If no expiry in proposal, calculate from DTE
    dte = proposal.get("dte", 14)
    future = datetime.now() + timedelta(days=dte)
    return future.strftime("%y%m%d")


def _log_execution(trade_number: int, order_details: dict, result: dict, consent: dict) -> None:
    """Log execution to audit trail."""

    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "EXECUTION",
        "trade_number": trade_number,
        "structure": order_details.get("structure"),
        "underlying": order_details.get("underlying"),
        "expiry": order_details.get("expiry"),
        "long_symbol": order_details["long_leg"]["symbol"],
        "short_symbol": order_details["short_leg"]["symbol"],
        "net_debit": order_details.get("net_debit"),
        "max_loss": order_details.get("max_loss"),
        "status": result.get("status"),
        "order_id": result.get("order_id"),
        "consent_decision": consent.get("decision"),
    }

    try:
        with open(AUDIT_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        console.print(f"[yellow][Audit] Failed to log execution: {e}[/yellow]")
