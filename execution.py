"""Alpaca execution layer with atomic multi-leg fill verification.

An approved spread is submitted as one MLEG limit order. BullRun never
reports a live spread as executed until Alpaca confirms every intended leg is
fully filled. DRY_RUN is deliberately enabled by default for demo safety.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import (
    ALPACA_API_KEY, ALPACA_SECRET_KEY,
    EXECUTION_MAX_RETRIES, EXECUTION_BACKOFF_BASE
)

DRY_RUN = os.getenv("DRY_RUN", "true").strip().lower() in {"1", "true", "yes", "on"}
POLL_INTERVAL_SECONDS = 2
POLL_TIMEOUT_SECONDS = 60

console = Console()


def run(proposal: dict, consent: dict, trade_number: int) -> dict:
    """Submit an approved defined-risk spread and log every outcome."""
    if consent.get("decision") != "APPROVE":
        result = _result("SKIPPED", error="Trade not approved")
        _audit_attempt(result, trade_number, proposal, consent)
        return result

    try:
        order_details = _build_order_details(proposal)
    except ValueError as exc:
        result = _result("FAILED", error=str(exc))
        _audit_attempt(result, trade_number, proposal, consent)
        return result

    if DRY_RUN:
        result = _dry_run(order_details)
    else:
        result = _execute_with_retry(order_details)

    _audit_attempt(result, trade_number, proposal, consent, order_details)
    _render_result(result)
    return result


def _build_order_details(proposal: dict) -> dict:
    long_leg = proposal.get("long_leg") or {}
    short_leg = proposal.get("short_leg") or {}
    if long_leg.get("strike") is None or short_leg.get("strike") is None:
        raise ValueError("Invalid spread: both option strikes are required")
    if float(proposal.get("net_debit") or 0) <= 0:
        raise ValueError("Invalid spread: a positive net debit is required")
    expiry_raw = proposal.get("expiry", "")
    if not expiry_raw:
        raise ValueError("Invalid spread: an ISO expiry date is required")
    if _is_expired(expiry_raw):
        raise ValueError("Option contract expired; refusing order submission")

    underlying = str(proposal.get("underlying", "SPY")).strip().upper()
    if not underlying.isalpha() or len(underlying) > 6:
        raise ValueError("Invalid underlying symbol")
    expiry = _format_expiry(proposal)
    long_symbol = long_leg.get("alpaca_symbol") or _option_symbol(underlying, expiry, long_leg)
    short_symbol = short_leg.get("alpaca_symbol") or _option_symbol(underlying, expiry, short_leg)
    try:
        qty = int(proposal.get("quantity", proposal.get("recommended_contracts", 1)))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid contract quantity") from exc
    if not 1 <= qty <= 100:
        raise ValueError("Invalid contract quantity; must be between 1 and 100")

    return {
        "underlying": underlying,
        "structure": proposal.get("structure", "SPREAD"),
        "expiry": proposal.get("expiry", ""),
        "net_debit": round(float(proposal["net_debit"]), 2),
        "max_loss": proposal.get("max_loss_per_contract"),
        "quantity": qty,
        "legs": [
            {"symbol": long_symbol, "side": "buy", "quantity": qty},
            {"symbol": short_symbol, "side": "sell", "quantity": qty},
        ],
    }


def _execute_with_retry(order_details: dict) -> dict:
    """Execute order with exponential backoff retry for transient network / rate limits."""
    backend = os.getenv("EXECUTION_BACKEND", "sdk").strip().lower()
    if backend != "sdk":
        return _result("FAILED", error="Only the SDK backend is supported because it verifies multi-leg fills")
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        return _result("FAILED", error="Alpaca credentials are not configured")
    last_error = "Unknown error"
    
    for attempt in range(1, EXECUTION_MAX_RETRIES + 1):
        try:
            console.print(f"[dim][Execution] Attempt {attempt}/{EXECUTION_MAX_RETRIES} submitting multi-leg order (Backend: {backend.upper()})...[/dim]")
            return _execute_via_sdk(order_details)
        except Exception as exc:
            last_error = _classify_error(exc)
            console.print(f"[yellow][Execution] Attempt {attempt} failed: {last_error}[/yellow]")
            if attempt < EXECUTION_MAX_RETRIES:
                sleep_time = EXECUTION_BACKOFF_BASE ** attempt
                console.print(f"[dim][Execution] Backing off for {sleep_time:.1f}s before retry...[/dim]")
                time.sleep(sleep_time)

    return _result("FAILED", error=f"Max retries ({EXECUTION_MAX_RETRIES}) exceeded. Last error: {last_error}")


def _execute_via_cli(order_details: dict) -> dict:
    """Execute order via Alpaca CLI if available, falling back to Trading API SDK."""
    import subprocess
    import shutil

    alpaca_bin = shutil.which("alpaca")
    if not alpaca_bin:
        console.print("[dim][Execution] 'alpaca' CLI binary not found in PATH — routing to SDK[/dim]")
        return _execute_via_sdk(order_details)

    try:
        legs_json = json.dumps([
            {"symbol": leg["symbol"], "side": leg["side"], "quantity": leg["quantity"]}
            for leg in order_details["legs"]
        ])
        cmd = [
            alpaca_bin, "orders", "create",
            "--class", "mleg",
            "--type", "limit",
            "--limit-price", str(order_details["net_debit"]),
            "--time-in-force", "day",
            "--legs", legs_json,
            "--output", "json"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            parsed = json.loads(proc.stdout)
            order_id = parsed.get("id") or f"CLI-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return _result("FILLED", order_id=order_id, receipt=parsed, legs=order_details["legs"])
        else:
            console.print(f"[dim][Execution] CLI returned code {proc.returncode}: {proc.stderr} — falling back to SDK[/dim]")
            return _execute_via_sdk(order_details)
    except Exception as e:
        console.print(f"[dim][Execution] CLI invocation error: {e} — falling back to SDK[/dim]")
        return _execute_via_sdk(order_details)




def _option_symbol(underlying: str, expiry: str, leg: dict) -> str:
    option_type = "C" if leg.get("type", "CALL") == "CALL" else "P"
    strike = int(round(float(leg["strike"]) * 1000))
    return f"{underlying}{expiry}{option_type}{strike:08d}"


def _execute_via_sdk(order_details: dict) -> dict:
    """Submit one Alpaca MLEG order, then require both legs to fill."""
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, OptionLegRequest

        client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        account = client.get_account()
        buying_power = float(account.buying_power)
        required_cash = order_details["net_debit"] * 100 * order_details["quantity"]
        if buying_power < required_cash:
            return _result("FAILED", error=f"Insufficient buying power: ${buying_power:,.2f} available; ${required_cash:,.2f} required")

        legs = [
            OptionLegRequest(
                symbol=leg["symbol"], ratio_qty=1,
                side=OrderSide.BUY if leg["side"] == "buy" else OrderSide.SELL,
            )
            for leg in order_details["legs"]
        ]
        request = LimitOrderRequest(
            qty=order_details["quantity"],
            limit_price=order_details["net_debit"],
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.MLEG,
            legs=legs,
        )
        order = client.submit_order(request)
        order_id = str(order.id)
        console.print(f"[cyan][Execution] MLEG order submitted: {order_id}[/cyan]")
        return _poll_for_full_fill(client, order_id, order_details)
    except Exception as exc:
        return _result("FAILED", error=_classify_error(exc))


def _poll_for_full_fill(client, order_id: str, order_details: dict) -> dict:
    """Poll Alpaca every two seconds and cancel any non-complete spread."""
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    last_status = "submitted"
    while time.monotonic() < deadline:
        try:
            order = client.get_order_by_id(order_id)
            last_status = _status_value(getattr(order, "status", "unknown"))
            if _all_legs_filled(order, order_details["legs"]):
                receipt = _receipt(order, order_details)
                return _result("FILLED", order_id=order_id, receipt=receipt, legs=receipt["legs"])
            if last_status in {"canceled", "rejected", "expired", "suspended", "stopped"}:
                return _result("FAILED", order_id=order_id, error=f"Order {last_status}; both legs were not filled")
        except Exception as exc:
            return _result("FAILED", order_id=order_id, error=_classify_error(exc))
        time.sleep(POLL_INTERVAL_SECONDS)

    try:
        client.cancel_order_by_id(order_id)
        return _result("CANCELED", order_id=order_id, error=f"Not fully filled after {POLL_TIMEOUT_SECONDS}s; cancellation requested", last_status=last_status)
    except Exception as exc:
        return _result("FAILED", order_id=order_id, error=f"Not fully filled after {POLL_TIMEOUT_SECONDS}s and cancellation failed: {_classify_error(exc)}", last_status=last_status)


def _all_legs_filled(order, expected_legs: list[dict]) -> bool:
    """Verify each requested symbol has its required filled quantity."""
    filled = {}
    for leg in getattr(order, "legs", None) or []:
        symbol = getattr(leg, "symbol", None)
        qty = float(getattr(leg, "filled_qty", 0) or 0)
        if symbol:
            filled[symbol] = qty
    return bool(filled) and all(filled.get(leg["symbol"], 0) >= float(leg["quantity"]) for leg in expected_legs)


def _receipt(order, order_details: dict) -> dict:
    legs = []
    for expected in order_details["legs"]:
        matching = next((leg for leg in (getattr(order, "legs", None) or []) if getattr(leg, "symbol", None) == expected["symbol"]), None)
        legs.append({
            "symbol": expected["symbol"], "side": expected["side"],
            "filled_qty": float(getattr(matching, "filled_qty", 0) or 0),
            "fill_price": _float_or_none(getattr(matching, "filled_avg_price", None)),
        })
    return {
        "order_id": str(order.id), "fill_price": _float_or_none(getattr(order, "filled_avg_price", None)),
        "fill_time": _iso(getattr(order, "filled_at", None)),
        "commissions": _float_or_none(getattr(order, "commission", None)) or 0.0, "legs": legs,
    }


def _dry_run(order_details: dict) -> dict:
    order_id = f"DRY-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    receipt = {
        "order_id": order_id, "fill_price": order_details["net_debit"],
        "fill_time": datetime.now(timezone.utc).isoformat(), "commissions": 0.0,
        "legs": [{**leg, "filled_qty": leg["quantity"], "fill_price": None} for leg in order_details["legs"]],
    }
    console.print("[yellow][Execution] DRY_RUN=true — no Alpaca order submitted[/yellow]")
    return _result("DRY_RUN", order_id=order_id, receipt=receipt, legs=receipt["legs"])


def _audit_attempt(result: dict, trade_number: int, proposal: dict, consent: dict, order_details: dict | None = None) -> None:
    """Use the hash-chained audit API for every attempt and its receipt."""
    try:
        from audit import log_execution, log_event
        log_execution(result, trade_number)
        log_event("EXECUTION_RECEIPT", {
            "trade_number": trade_number, "status": result.get("status"), "order_id": result.get("order_id"),
            "error": result.get("error"), "structure": proposal.get("structure"), "underlying": proposal.get("underlying"),
            "consent_decision": consent.get("decision"), "receipt": result.get("receipt"),
            "legs": result.get("legs") or (order_details or {}).get("legs", []),
        })
    except Exception as exc:
        console.print(f"[yellow][Audit] Execution audit failed: {exc}[/yellow]")


def _render_result(result: dict) -> None:
    success = result.get("status") in {"FILLED", "DRY_RUN"}
    text = f"Order ID: {result.get('order_id', 'N/A')}\nStatus: {result.get('status', 'N/A')}"
    if result.get("receipt"):
        receipt = result["receipt"]
        text += f"\nFill price: ${receipt.get('fill_price', 0):.2f}\nFill time: {receipt.get('fill_time')}\nCommissions: ${receipt.get('commissions', 0):.2f}"
    if result.get("error"):
        text += f"\nReason: {result['error']}"
    console.print(Panel(Text(text, style="bold green" if success else "bold red"), title="BULLRUN — EXECUTION", border_style="green" if success else "red", width=62))


def _classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "buying power" in message or "insufficient" in message:
        return f"Insufficient buying power: {exc}"
    if "market" in message and ("closed" in message or "not open" in message):
        return f"Market is closed: {exc}"
    if "not found" in message or "invalid symbol" in message or "asset" in message:
        return f"Symbol not found: {exc}"
    if "expired" in message or "expiration" in message:
        return f"Option contract expired: {exc}"
    return f"Alpaca execution error: {exc}"


def _is_expired(expiry: str) -> bool:
    try:
        return datetime.strptime(expiry, "%Y-%m-%d").date() < datetime.now().date()
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid expiry; expected YYYY-MM-DD") from exc


def _format_expiry(proposal: dict) -> str:
    expiry = proposal.get("expiry", "")
    if expiry:
        try:
            return datetime.strptime(expiry, "%Y-%m-%d").strftime("%y%m%d")
        except ValueError as exc:
            raise ValueError("Invalid expiry; expected YYYY-MM-DD") from exc
    raise ValueError("Invalid spread: an expiry date is required")


def _result(status: str, **kwargs) -> dict:
    return {"status": status, "timestamp": datetime.now(timezone.utc).isoformat(), **kwargs}


def _status_value(status) -> str:
    return str(getattr(status, "value", status)).lower()


def _float_or_none(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _iso(value) -> str:
    return value.isoformat() if value else datetime.now(timezone.utc).isoformat()


def close_position_alpaca(position: dict) -> dict:
    """Submit a closing order to Alpaca for an open position.

    For options spreads, closes each leg individually as a closing sell/buy.
    Returns a result dict with status, fill info, and P&L.
    """
    if DRY_RUN:
        pnl = position.get("unrealized_pnl", 0)
        console.print(f"[yellow][Execution] DRY_RUN — simulating close of position #{position.get('trade_number')}[/yellow]")
        return _result("DRY_RUN", order_id=f"DRY-CLOSE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", pnl=pnl)

    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        return _result("FAILED", error="Alpaca credentials not configured", pnl=0)

    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
    underlying = position.get("underlying", "SPY")
    qty = int(position.get("quantity", 1))
    long_leg = position.get("long_leg", {})
    short_leg = position.get("short_leg", {})

    results = []
    # Close long leg: sell to close
    long_sym = long_leg.get("alpaca_symbol", "")
    if long_sym:
        try:
            order = client.submit_order(MarketOrderRequest(
                symbol=long_sym, qty=qty, side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY, 
                order_class=None,
            ))
            results.append({"leg": "long", "symbol": long_sym, "order_id": str(order.id), "status": _status_value(order.status)})
        except Exception as exc:
            results.append({"leg": "long", "symbol": long_sym, "error": str(exc)})

    # Close short leg: buy to cover
    short_sym = short_leg.get("alpaca_symbol", "")
    if short_sym:
        try:
            order = client.submit_order(MarketOrderRequest(
                symbol=short_sym, qty=qty, side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
                order_class=None,
            ))
            results.append({"leg": "short", "symbol": short_sym, "order_id": str(order.id), "status": _status_value(order.status)})
        except Exception as exc:
            results.append({"leg": "short", "symbol": short_sym, "error": str(exc)})

    any_error = any("error" in r for r in results)
    status = "FAILED" if any_error else "FILLED"
    pnl = position.get("unrealized_pnl", 0)

    console.print(f"[{'red' if any_error else 'green'}][Execution] Close position #{position.get('trade_number')}: {status} | P&L: ${pnl:+,.2f}[/{'red' if any_error else 'green'}]")

    return _result(status, order_id=results[0].get("order_id", "") if results else "", pnl=pnl, legs=results)
