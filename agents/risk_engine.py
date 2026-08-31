"""
risk_engine.py — Risk Engine (Deterministic Risk Gates)

Role: The final checkpoint before human consent. Validates every trade proposal
against 8 hardcoded risk rules. Can only say PASS or REJECT.
No LLM involved. No ambiguity. No override.

This is the "shield" of Conviction Gate — it ensures no bad trade reaches the human.

The 2% Rule: No single trade can lose more than 2% of the portfolio.
On a $100K account, that's $2,000 max loss per trade.

Circuit Breakers:
- Daily loss limit: 3% ($3K) — stop trading for the day
- Max drawdown: 10% ($10K) — stop trading entirely until reset

Input:  trade proposal dict from quant_agent.py
Output: PASS/REJECT + list of check results
"""

import json
import os
from datetime import datetime, date
from rich.console import Console
from config import RISK_LIMITS, UNDERLYING, AUDIT_LOG

console = Console()


class RiskEngine:
    """
    Deterministic risk gates. Non-negotiable rules.
    The LLM cannot override these. The human cannot override these.
    Only the code can change them (by editing config.py).
    """

    def __init__(self):
        self.limits = RISK_LIMITS
        self._daily_pnl = 0.0
        self._daily_date = date.today()
        self._starting_equity = 100_000.0
        self._peak_equity = 100_000.0

    def _reset_daily(self):
        """Reset daily tracking if it's a new day."""
        today = date.today()
        if today != self._daily_date:
            self._daily_pnl = 0.0
            self._daily_date = today

    def update_daily_pnl(self, pnl: float):
        """Update running daily P&L (called after each trade closes)."""
        self._reset_daily()
        self._daily_pnl += pnl

    def update_equity(self, equity: float):
        """Update peak equity for drawdown tracking."""
        if equity > self._peak_equity:
            self._peak_equity = equity

    def check(self, proposal: dict, portfolio_state: dict = None) -> dict:
        """
        Run all 8 risk checks on a trade proposal.

        Args:
            proposal: Trade proposal from Quant Agent
            portfolio_state: Current portfolio info

        Returns:
            dict with status (PASS/REJECT), checks list, and summary
        """
        self._reset_daily()

        if portfolio_state is None:
            portfolio_state = {
                "open_position_count": 0,
                "current_portfolio_exposure": 0,
                "available_cash": 100_000,
                "equity": 100_000,
            }

        equity = portfolio_state.get("equity", portfolio_state.get("available_cash", 100_000))
        checks = []

        # ── Check 1: Max Loss Per Trade (2% Rule) ──────────────────────
        max_loss = proposal.get("max_loss_per_contract", 0)
        max_allowed = self.limits.max_risk_per_trade * equity
        passed = max_loss <= max_allowed
        checks.append({
            "name": "2% RULE",
            "status": "PASS" if passed else "REJECT",
            "detail": f"${max_loss:.0f} ≤ ${max_allowed:.0f} ({self.limits.max_risk_per_trade:.0%} of ${equity:,.0f})"
            if passed else
            f"${max_loss:.0f} > ${max_allowed:.0f} — EXCEEDS 2% LIMIT",
            "critical": True,
        })

        # ── Check 2: Portfolio Heat (total exposure) ───────────────────
        current_exposure = portfolio_state.get("current_portfolio_exposure", 0)
        new_exposure = current_exposure + max_loss
        max_exposure = self.limits.max_portfolio_exposure * equity
        passed = new_exposure <= max_exposure
        checks.append({
            "name": "EXPOSURE",
            "status": "PASS" if passed else "REJECT",
            "detail": f"${new_exposure:.0f} ≤ ${max_exposure:.0f} ({self.limits.max_portfolio_exposure:.0%} limit)"
            if passed else
            f"${new_exposure:.0f} > ${max_exposure:.0f} — TOO MUCH RISK",
        })

        # ── Check 3: Concurrent Positions ──────────────────────────────
        open_count = portfolio_state.get("open_position_count", 0)
        passed = open_count < self.limits.max_concurrent_positions
        checks.append({
            "name": "POSITIONS",
            "status": "PASS" if passed else "REJECT",
            "detail": f"{open_count} < {self.limits.max_concurrent_positions}" if passed
            else f"{open_count} ≥ {self.limits.max_concurrent_positions} — MAX REACHED",
        })

        # ── Check 4: Daily Loss Limit (circuit breaker) ────────────────
        daily_loss_limit = self.limits.max_daily_loss * equity
        daily_remaining = daily_loss_limit + self._daily_pnl  # _daily_pnl is negative when losing
        passed = daily_remaining > 0
        checks.append({
            "name": "DAILY LIMIT",
            "status": "PASS" if passed else "REJECT",
            "detail": f"Today's P&L: ${self._daily_pnl:+,.0f} | Budget: ${daily_remaining:,.0f} remaining"
            if passed else
            f"DAILY LOSS LIMIT HIT: ${self._daily_pnl:+,.0f} (limit: -${daily_loss_limit:,.0f}) — STOP TRADING",
            "critical": True,
        })

        # ── Check 5: Max Drawdown (circuit breaker) ────────────────────
        drawdown = (self._peak_equity - equity) / self._peak_equity if self._peak_equity > 0 else 0
        max_dd = self.limits.max_drawdown
        passed = drawdown < max_dd
        checks.append({
            "name": "DRAWDOWN",
            "status": "PASS" if passed else "REJECT",
            "detail": f"Drawdown: {drawdown:.1%} < {max_dd:.0%} limit" if passed
            else f"DRAWDOWN LIMIT: {drawdown:.1%} ≥ {max_dd:.0%} — TRADING HALTED",
            "critical": True,
        })

        # ── Check 6: Liquidity (bid-ask spread) ────────────────────────
        bid_ask = proposal.get("bid_ask_spread", 999)
        passed = bid_ask <= 0.15
        checks.append({
            "name": "LIQUIDITY",
            "status": "PASS" if passed else "REJECT",
            "detail": f"Spread: ${bid_ask:.2f} ≤ $0.15" if passed
            else f"Spread: ${bid_ask:.2f} > $0.15 — TOO WIDE",
        })

        # ── Check 7: Spread Width ──────────────────────────────────────
        width = proposal.get("spread_width", 999)
        passed = width <= self.limits.max_spread_width
        checks.append({
            "name": "SPREAD WIDTH",
            "status": "PASS" if passed else "REJECT",
            "detail": f"${width:.2f} ≤ ${self.limits.max_spread_width}" if passed
            else f"${width:.2f} > ${self.limits.max_spread_width} — TOO WIDE",
        })

        # ── Check 8: Days to Expiration ────────────────────────────────
        dte = proposal.get("dte", 0)
        passed = self.limits.min_dte <= dte <= self.limits.max_dte
        checks.append({
            "name": "EXPIRATION",
            "status": "PASS" if passed else "REJECT",
            "detail": f"{dte} days (range: {self.limits.min_dte}-{self.limits.max_dte})" if passed
            else f"{dte} days — OUTSIDE RANGE",
        })

        # ── Final verdict ──────────────────────────────────────────────
        all_pass = all(c["status"] == "PASS" for c in checks)
        critical_fails = [c["name"] for c in checks if c["status"] == "REJECT" and c.get("critical")]
        status = "PASS" if all_pass else "REJECT"

        # ── Log results ────────────────────────────────────────────────
        if all_pass:
            console.print("[bold green][Risk Engine][/bold green] ✓ ALL 8 CHECKS PASSED — approved for consent")
        else:
            failed = [c["name"] for c in checks if c["status"] == "REJECT"]
            console.print(f"[bold red][Risk Engine][/bold red] ✗ REJECTED — failed: {', '.join(failed)}")
            if critical_fails:
                console.print(f"[bold red][Risk Engine] ⚠ CIRCUIT BREAKER: {', '.join(critical_fails)}[/bold red]")

        for check in checks:
            icon = "✓" if check["status"] == "PASS" else "✗"
            color = "green" if check["status"] == "PASS" else "red"
            console.print(f"  [{color}]{icon} {check['name']}: {check['detail']}[/{color}]")

        return {
            "status": status,
            "checks": checks,
            "all_passed": all_pass,
            "failed_checks": [c["name"] for c in checks if c["status"] == "REJECT"],
            "critical_fails": critical_fails,
            "daily_pnl": self._daily_pnl,
            "drawdown_pct": round(drawdown * 100, 2),
        }


# Singleton instance
risk_engine = RiskEngine()


if __name__ == "__main__":
    # Test with mock proposal
    mock_proposal = {
        "max_loss_per_contract": 500,
        "spread_width": 3.0,
        "dte": 14,
        "bid_ask_spread": 0.05,
    }
    mock_portfolio = {
        "open_position_count": 1,
        "current_portfolio_exposure": 500,
        "available_cash": 100_000,
        "equity": 100_000,
    }
    result = risk_engine.check(mock_proposal, mock_portfolio)
    print(json.dumps(result, indent=2, default=str))
