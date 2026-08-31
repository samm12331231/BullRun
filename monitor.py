"""
monitor.py — Position Monitor Engine

Role: Monitors open positions and executes pre-authorized exits.
Entries require human consent. Exits are automatic based on deterministic rules.

This is the "autopilot" of Conviction Gate — it manages positions after entry.

Exit rules (from config.py):
- Stop loss: position drops 30% from entry (tight!)
- Take profit: position reaches +50% of max profit
- DTE exit: close if DTE < 3 (avoid gamma risk)
- Trailing stop: close if dropped 40% from peak value
- Time exit: force close after 10 days max
- Daily loss circuit breaker: stop all trading if daily loss exceeds 3%

Uses Alpaca data service for real-time position pricing.
"""

import json
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich import box
from config import RISK_LIMITS, AUDIT_LOG
from audit import log_exit

console = Console()


class PositionMonitor:
    """Monitors open positions and triggers pre-authorized exits."""

    def __init__(self):
        self.positions = []
        self._daily_pnl = 0.0
        self._daily_date = None
        self._load_positions()

    def _load_positions(self):
        """Load positions from disk if available."""
        pos_file = "positions.json"
        if os.path.exists(pos_file):
            try:
                with open(pos_file) as f:
                    self.positions = json.load(f)
            except Exception:
                self.positions = []

    def _save_positions(self):
        """Save positions to disk."""
        with open("positions.json", "w") as f:
            json.dump(self.positions, f, indent=2, default=str)

    def add_position(self, proposal: dict, execution: dict, trade_number: int) -> None:
        """Add a new position to track."""

        position = {
            "trade_number": trade_number,
            "structure": proposal.get("structure"),
            "underlying": proposal.get("underlying"),
            "long_leg": proposal.get("long_leg"),
            "short_leg": proposal.get("short_leg"),
            "expiry": proposal.get("expiry", ""),
            "net_debit": proposal.get("net_debit"),
            "max_loss": proposal.get("max_loss_per_contract"),
            "max_profit": proposal.get("max_profit_per_contract"),
            "breakeven": proposal.get("breakeven"),
            "dte": proposal.get("dte", 14),
            "entry_time": datetime.now().isoformat(),
            "order_id": execution.get("order_id"),
            "status": "OPEN",
            "exit_time": None,
            "exit_reason": None,
            "pnl": None,
            "current_value": proposal.get("net_debit"),
            "unrealized_pnl": 0,
            "peak_value": proposal.get("net_debit"),
        }

        self.positions.append(position)
        self._save_positions()
        console.print(f"[green][Monitor] Position #{trade_number} added to tracking[/green]")

    def check_positions(self) -> list:
        """
        Check all open positions against exit rules.
        Uses live data when available, falls back to time-based heuristics.
        Returns list of positions that should be closed.
        """
        exits = []

        for pos in self.positions:
            if pos["status"] != "OPEN":
                continue

            # Fetch live position value
            self._update_position_value(pos)

            exit_reason = self._check_exit_rules(pos)
            if exit_reason:
                pos["exit_reason"] = exit_reason
                exits.append(pos)

        return exits

    def _update_position_value(self, position: dict) -> None:
        """Fetch live spread value from Alpaca and update position."""
        try:
            from agents.data_service import get_option_quote

            long_leg = position.get("long_leg", {})
            short_leg = position.get("short_leg", {})
            underlying = position.get("underlying", "SPY")
            expiry = position.get("expiry", "")

            if not expiry or not long_leg.get("strike"):
                return

            # Use Alpaca symbols if available, otherwise construct
            long_sym = long_leg.get("alpaca_symbol", "")
            short_sym = short_leg.get("alpaca_symbol", "")

            if not long_sym or not short_sym:
                from datetime import datetime as dt
                try:
                    exp_dt = dt.strptime(expiry, "%Y-%m-%d")
                    exp_fmt = exp_dt.strftime("%y%m%d")
                except (ValueError, TypeError):
                    return

                long_type = "C" if long_leg.get("type", "CALL") == "CALL" else "P"
                short_type = "C" if short_leg.get("type", "CALL") == "CALL" else "P"
                long_sym = long_sym or f"{underlying}{exp_fmt}{long_type}{int(long_leg['strike']):08d}"
                short_sym = short_sym or f"{underlying}{exp_fmt}{short_type}{int(short_leg['strike']):08d}"

            long_quote = get_option_quote(long_sym)
            short_quote = get_option_quote(short_sym)

            if long_quote["mid"] > 0 and short_quote["mid"] > 0:
                current_value = long_quote["mid"] - short_quote["mid"]
                position["current_value"] = round(current_value, 2)

                entry_value = position.get("net_debit", 0)
                position["unrealized_pnl"] = round((current_value - entry_value) * 100, 2)

                if current_value > position.get("peak_value", 0):
                    position["peak_value"] = current_value

        except Exception:
            pass

    def _check_exit_rules(self, position: dict) -> str | None:
        """
        Check if a position should be exited based on deterministic rules.
        Priority: DTE > Stop Loss > Take Profit > Trailing > Time
        """
        entry_time = datetime.fromisoformat(position["entry_time"])
        days_held = (datetime.now() - entry_time).days
        original_dte = position.get("dte", 14)
        estimated_dte = original_dte - days_held

        # ── Rule 1: DTE Exit (highest priority — avoid gamma risk) ─────
        if estimated_dte <= RISK_LIMITS.min_dte_exit:
            return f"DTE exit: {estimated_dte} days remaining (min: {RISK_LIMITS.min_dte_exit})"

        # ── Rule 2: Stop Loss (30% of debit — TIGHT) ──────────────────
        current_value = position.get("current_value", position.get("net_debit", 0))
        entry_debit = position.get("net_debit", 0)

        if entry_debit > 0:
            loss_pct = (entry_debit - current_value) / entry_debit
            if loss_pct >= RISK_LIMITS.stop_loss_pct:
                return f"Stop loss: down {loss_pct:.0%} from entry (limit: -{RISK_LIMITS.stop_loss_pct:.0%})"

        # ── Rule 3: Take Profit (+50% of max profit) ───────────────────
        max_profit = position.get("max_profit", 0)
        if max_profit > 0 and entry_debit > 0:
            gain_pct = (current_value - entry_debit) / max_profit
            if gain_pct >= RISK_LIMITS.take_profit_pct:
                return f"Take profit: +{gain_pct:.0%} of max profit (target: +{RISK_LIMITS.take_profit_pct:.0%})"

        # ── Rule 4: Trailing Stop (dropped 40% from peak) ──────────────
        peak = position.get("peak_value", entry_debit)
        if peak > 0 and current_value < peak:
            drop_from_peak = (peak - current_value) / peak
            if drop_from_peak >= RISK_LIMITS.trailing_stop_pct:
                return f"Trailing stop: -{drop_from_peak:.0%} from peak ${peak:.2f} (limit: -{RISK_LIMITS.trailing_stop_pct:.0%})"

        # ── Rule 5: Time Exit (force close after max hold) ─────────────
        if days_held >= RISK_LIMITS.max_hold_days:
            return f"Time exit: held {days_held} days (max: {RISK_LIMITS.max_hold_days})"

        # ── Rule 6: Time-decay acceleration (last 3 days, tighten stop) ─
        if estimated_dte <= 5 and entry_debit > 0:
            # In the last 5 days, tighten stop to 20%
            loss_pct = (entry_debit - current_value) / entry_debit
            if loss_pct >= 0.20:
                return f"Late-stage stop: down {loss_pct:.0%} with only {estimated_dte} DTE (accelerated stop: -20%)"

        return None

    def close_position(self, position: dict, reason: str, pnl: float = None) -> dict:
        """Close a position and log the result."""
        if pnl is None:
            pnl = position.get("unrealized_pnl", 0)

        position["status"] = "CLOSED"
        position["exit_time"] = datetime.now().isoformat()
        position["exit_reason"] = reason
        position["pnl"] = pnl

        self._save_positions()
        self._daily_pnl += pnl

        entry = log_exit(position, reason, pnl)

        pnl_color = "green" if pnl >= 0 else "red"
        console.print(f"[bold {pnl_color}][Monitor] Position #{position['trade_number']} closed: {reason} | P&L: ${pnl:+,.2f}[/{pnl_color}]")

        return entry

    def get_open_positions(self) -> list:
        return [p for p in self.positions if p["status"] == "OPEN"]

    def get_closed_positions(self) -> list:
        return [p for p in self.positions if p["status"] == "CLOSED"]

    def get_portfolio_summary(self) -> dict:
        open_pos = self.get_open_positions()
        closed_pos = self.get_closed_positions()

        total_pnl = sum(p.get("pnl", 0) or 0 for p in closed_pos)
        unrealized = sum(p.get("unrealized_pnl", 0) or 0 for p in open_pos)
        total_risk = sum(p.get("max_loss", 0) or 0 for p in open_pos)
        max_possible_loss = sum(p.get("max_loss", 0) or 0 for p in open_pos)

        return {
            "open_count": len(open_pos),
            "closed_count": len(closed_pos),
            "total_pnl": round(total_pnl, 2),
            "unrealized_pnl": round(unrealized, 2),
            "combined_pnl": round(total_pnl + unrealized, 2),
            "total_risk": round(total_risk, 2),
            "max_possible_loss": round(max_possible_loss, 2),
            "win_rate": self._calculate_win_rate(closed_pos),
            "daily_pnl": round(self._daily_pnl, 2),
        }

    def _calculate_win_rate(self, closed_positions: list) -> float:
        if not closed_positions:
            return 0.0
        wins = sum(1 for p in closed_positions if (p.get("pnl", 0) or 0) > 0)
        return round(wins / len(closed_positions) * 100, 1)

    def get_position_details(self) -> list:
        details = []
        for pos in self.get_open_positions():
            entry_time = datetime.fromisoformat(pos["entry_time"])
            days_held = (datetime.now() - entry_time).days
            details.append({
                "trade_number": pos["trade_number"],
                "structure": pos.get("structure", "").replace("_", " ").title(),
                "underlying": pos.get("underlying", "SPY"),
                "net_debit": pos.get("net_debit", 0),
                "current_value": pos.get("current_value", pos.get("net_debit", 0)),
                "unrealized_pnl": pos.get("unrealized_pnl", 0),
                "max_loss": pos.get("max_loss", 0),
                "max_profit": pos.get("max_profit", 0),
                "breakeven": pos.get("breakeven", 0),
                "days_held": days_held,
                "estimated_dte": pos.get("dte", 14) - days_held,
                "status": "OPEN",
            })
        return details


def render_dashboard(monitor: PositionMonitor) -> None:
    """Render the portfolio dashboard."""
    summary = monitor.get_portfolio_summary()
    open_pos = monitor.get_open_positions()
    closed_pos = monitor.get_closed_positions()

    console.print()
    console.rule("[bold gold1]  CONVICTION GATE — PORTFOLIO DASHBOARD  [/bold gold1]")

    summary_table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold white")
    summary_table.add_column("Metric", style="dim", width=20)
    summary_table.add_column("Value", justify="right", width=15)
    summary_table.add_column("Metric", style="dim", width=20)
    summary_table.add_column("Value", justify="right", width=15)

    pnl_color = "green" if summary["combined_pnl"] >= 0 else "red"
    risk_color = "green" if summary["total_risk"] < 3000 else "yellow" if summary["total_risk"] < 5000 else "red"

    summary_table.add_row(
        "Open Positions", f"[bold]{summary['open_count']}[/bold] / {RISK_LIMITS.max_concurrent_positions}",
        "Total P&L", f"[bold {pnl_color}]${summary['combined_pnl']:+,.2f}[/bold {pnl_color}]",
    )
    summary_table.add_row(
        "Closed Trades", f"{summary['closed_count']}",
        "Win Rate", f"[bold]{summary['win_rate']}%[/bold]",
    )
    summary_table.add_row(
        "Realized P&L", f"${summary['total_pnl']:+,.2f}",
        "Unrealized", f"${summary['unrealized_pnl']:+,.2f}",
    )
    summary_table.add_row(
        "Current Risk", f"[{risk_color}]${summary['total_risk']:,.0f}[/{risk_color}]",
        "Max Risk (2%)", f"${RISK_LIMITS.max_risk_per_trade * 100_000:,.0f}/trade",
    )

    console.print(summary_table)

    if open_pos:
        console.print()
        console.print("[bold]OPEN POSITIONS[/bold]", style="white")

        pos_table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
        pos_table.add_column("#", width=4)
        pos_table.add_column("Structure", width=22)
        pos_table.add_column("Entry", justify="right", width=8)
        pos_table.add_column("Current", justify="right", width=8)
        pos_table.add_column("P&L", justify="right", width=10)
        pos_table.add_column("Stop", justify="right", width=8)
        pos_table.add_column("Days", justify="right", width=6)

        for pos in open_pos:
            days_held = (datetime.now() - datetime.fromisoformat(pos["entry_time"])).days
            pnl = pos.get("unrealized_pnl", 0)
            pnl_color = "green" if pnl >= 0 else "red"

            # Calculate stop level
            entry = pos.get("net_debit", 0)
            stop_price = entry * (1 - RISK_LIMITS.stop_loss_pct) if entry > 0 else 0

            pos_table.add_row(
                str(pos["trade_number"]),
                pos["structure"].replace("_", " ").title() if pos["structure"] else "N/A",
                f"${pos.get('net_debit', 0):.2f}",
                f"${pos.get('current_value', 0):.2f}",
                f"[{pnl_color}]${pnl:+,.2f}[/{pnl_color}]",
                f"[red]${stop_price:.2f}[/red]",
                str(days_held),
            )

        console.print(pos_table)

    if closed_pos:
        console.print()
        console.print("[bold]CLOSED TRADES[/bold]", style="white")

        closed_table = Table(box=box.ROUNDED, show_header=True, header_style="bold white")
        closed_table.add_column("#", width=4)
        closed_table.add_column("Structure", width=22)
        closed_table.add_column("Exit Reason", width=35)
        closed_table.add_column("P&L", justify="right", width=10)

        for pos in closed_pos[-5:]:
            pnl = pos.get("pnl", 0) or 0
            pnl_color = "green" if pnl >= 0 else "red"
            closed_table.add_row(
                str(pos["trade_number"]),
                pos["structure"].replace("_", " ").title() if pos["structure"] else "N/A",
                pos.get("exit_reason", "N/A")[:35],
                f"[{pnl_color}]${pnl:+,.2f}[/{pnl_color}]",
            )

        console.print(closed_table)

    console.rule("[dim]End of Dashboard[/dim]")
    console.print()


# Singleton instance
monitor = PositionMonitor()
