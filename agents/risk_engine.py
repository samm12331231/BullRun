"""
risk_engine.py — Risk Engine (Deterministic Risk Gates)

Role: The final checkpoint before human consent. Validates every trade proposal
against 12 hardcoded, non-negotiable deterministic risk rules.
Can only say PASS or REJECT. No LLM involved. No ambiguity. No override.

This is the "shield" of BullRun — it ensures no bad trade reaches the human.

The 12 Deterministic Risk Rules:
1.  2% Rule: No single trade can risk more than 2% of portfolio ($2,000 on $100K)
2.  Conviction Sizing: Scale contract allocation strictly within the 2% cap
3.  Portfolio Heat: Total exposure across all positions capped at 6% ($6,000)
4.  Concurrent Positions: Maximum 3 active open positions
5.  Correlation Guard: Reject duplicate directional exposure on correlated underlyings
6.  Time-of-Day Guard: No new entries during opening 30m (9:30-10:00) or closing 30m (15:30-16:00 EST)
7.  Earnings Proximity: Reject if company earnings announcement is within 5 DTE
8.  Daily Loss Circuit Breaker: Halt trading if daily loss exceeds 3% ($3,000)
9.  Max Drawdown Circuit Breaker: Halt trading if peak-to-trough drawdown exceeds 10% ($10,000)
10. Liquidity Guard: Bid-ask spread must be <= $0.15
11. Spread Width: Maximum spread width <= $5.00
12. Expiration Window: Days to Expiration must be between 7 and 21 days

Input:  trade proposal dict from quant_agent.py
Output: PASS/REJECT + list of 12 check results
"""

import json
import os
from datetime import datetime, date, time
from rich.console import Console
from config import RISK_LIMITS, UNDERLYING, AUDIT_LOG
from agents.data_service import check_upcoming_earnings

console = Console()


class RiskEngine:
    """
    Deterministic risk gates. Non-negotiable institutional rules.
    The LLM cannot override these. The human cannot override these.
    Only code configuration changes these.
    """

    def __init__(self):
        self.limits = RISK_LIMITS
        self._daily_pnl = 0.0
        self._daily_date = date.today()
        self._starting_equity = 100_000.0
        self._peak_equity = 100_000.0

    def _reset_daily(self):
        """Reset daily tracking if it's a new calendar day."""
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
        Run all 12 institutional risk checks on a trade proposal.

        Args:
            proposal: Trade proposal from Quant Agent
            portfolio_state: Current portfolio info (open positions, exposure, equity)

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
                "open_positions": [],
            }

        equity = float(portfolio_state.get("equity", portfolio_state.get("available_cash", 100_000.0)))
        checks = []

        # ── Check 1: 2% RULE (Max Loss Per Contract) ──────────────────────
        max_loss_per_contract = float(proposal.get("max_loss_per_contract", 0))
        max_allowed_risk = self.limits.max_risk_per_trade * equity
        passed_2pct = max_loss_per_contract <= max_allowed_risk
        checks.append({
            "name": "2% RULE",
            "status": "PASS" if passed_2pct else "REJECT",
            "detail": (
                f"${max_loss_per_contract:.0f} ≤ ${max_allowed_risk:.0f} "
                f"({self.limits.max_risk_per_trade:.0%} of ${equity:,.0f})"
                if passed_2pct else
                f"${max_loss_per_contract:.0f} > ${max_allowed_risk:.0f} — EXCEEDS 2% LIMIT"
            ),
            "critical": True,
        })

        # ── Check 2: CONVICTION SIZING (Position Sizing by Score) ──────────
        qty = int(proposal.get("quantity", proposal.get("recommended_contracts", 1)))
        total_risk_proposed = float(proposal.get("total_risk_proposed", max_loss_per_contract * qty))
        passed_sizing = total_risk_proposed <= max_allowed_risk
        checks.append({
            "name": "CONVICTION SIZING",
            "status": "PASS" if passed_sizing else "REJECT",
            "detail": (
                f"{qty} contract{'s' if qty > 1 else ''} (${total_risk_proposed:,.0f} risk) within 2% cap (${max_allowed_risk:,.0f})"
                if passed_sizing else
                f"{qty} contracts risk ${total_risk_proposed:,.0f} > ${max_allowed_risk:,.0f} 2% limit"
            ),
        })

        # ── Check 3: PORTFOLIO HEAT (Total Exposure <= 6%) ────────────────
        current_exposure = float(portfolio_state.get("current_portfolio_exposure", 0))
        new_exposure = current_exposure + total_risk_proposed
        max_exposure = self.limits.max_portfolio_exposure * equity
        passed_exposure = new_exposure <= max_exposure
        checks.append({
            "name": "EXPOSURE",
            "status": "PASS" if passed_exposure else "REJECT",
            "detail": (
                f"${new_exposure:,.0f} ≤ ${max_exposure:,.0f} ({self.limits.max_portfolio_exposure:.0%} portfolio heat cap)"
                if passed_exposure else
                f"${new_exposure:,.0f} > ${max_exposure:,.0f} — MAXIMUM PORTFOLIO HEAT EXCEEDED"
            ),
        })

        # ── Check 4: CONCURRENT POSITIONS (Max 3) ─────────────────────────
        open_count = int(portfolio_state.get("open_position_count", 0))
        passed_pos = open_count < self.limits.max_concurrent_positions
        checks.append({
            "name": "POSITIONS",
            "status": "PASS" if passed_pos else "REJECT",
            "detail": (
                f"{open_count} open positions < {self.limits.max_concurrent_positions} max allowed"
                if passed_pos else
                f"{open_count} ≥ {self.limits.max_concurrent_positions} — MAX ACTIVE POSITIONS REACHED"
            ),
        })

        # ── Check 5: CORRELATION GUARD (No Same-Direction Duplication) ───
        open_positions = portfolio_state.get("open_positions", [])
        proposed_dir = proposal.get("direction", "LONG")
        proposed_sym = proposal.get("underlying", UNDERLYING)
        
        correlated_conflict = False
        conflict_reason = ""
        for pos in open_positions:
            pos_sym = pos.get("underlying", "")
            pos_dir = pos.get("direction", "")
            if pos.get("status") == "OPEN" and pos_sym == proposed_sym and pos_dir == proposed_dir:
                correlated_conflict = True
                conflict_reason = f"Existing open {pos_dir} position on {pos_sym} (Trade #{pos.get('trade_number')})"
                break

        passed_correlation = not correlated_conflict
        checks.append({
            "name": "CORRELATION GUARD",
            "status": "PASS" if passed_correlation else "REJECT",
            "detail": (
                f"No directional correlation overlap on {proposed_sym}"
                if passed_correlation else
                f"Correlation overload: {conflict_reason} — NO DUPLICATE DIRECTION"
            ),
            "critical": True,
        })

        # ── Check 6: TIME-OF-DAY GUARD (No trades first/last 30 min) ─────
        now_est = datetime.now()  # Evaluated in local / EST context
        current_time = now_est.time()
        start_buffer = time(9, 30 + self.limits.market_guard_start_min)   # 10:00 AM EST
        end_buffer = time(16 - (self.limits.market_guard_end_min // 60), 60 - (self.limits.market_guard_end_min % 60) if self.limits.market_guard_end_min % 60 else 0)  # 3:30 PM EST
        
        # When market enforcement is active or during trading
        is_in_safe_window = (start_buffer <= current_time <= end_buffer) if self.limits.enforce_market_hours else True
        passed_time = is_in_safe_window
        checks.append({
            "name": "TIME-OF-DAY GUARD",
            "status": "PASS" if passed_time else "REJECT",
            "detail": (
                f"Trading window verified (outside 9:30-10:00 & 15:30-16:00 EST buffer)"
                if passed_time else
                f"Opening/Closing buffer active ({current_time.strftime('%H:%M')} EST) — no entries during high volatility spikes"
            ),
        })

        # ── Check 7: EARNINGS PROXIMITY CHECK (<= 5 DTE) ─────────────────
        earnings_res = check_upcoming_earnings(proposed_sym, within_days=self.limits.earnings_buffer_dte)
        has_earnings_conflict = earnings_res.get("has_earnings", False)
        passed_earnings = not has_earnings_conflict
        checks.append({
            "name": "EARNINGS GUARD",
            "status": "PASS" if passed_earnings else "REJECT",
            "detail": (
                earnings_res.get("reason", "No earnings risk within 5 DTE")
                if passed_earnings else
                f"Earnings in {earnings_res.get('days_to_earnings')} days ({earnings_res.get('earnings_date')}) — REJECT BINARY EVENT RISK"
            ),
            "critical": True,
        })

        # ── Check 8: DAILY LOSS LIMIT (Circuit Breaker) ───────────────────
        daily_loss_limit = self.limits.max_daily_loss * equity
        daily_remaining = daily_loss_limit + self._daily_pnl  # _daily_pnl is negative when losing
        passed_daily = daily_remaining > 0
        checks.append({
            "name": "DAILY LIMIT",
            "status": "PASS" if passed_daily else "REJECT",
            "detail": (
                f"Today's P&L: ${self._daily_pnl:+,.0f} | Budget: ${daily_remaining:,.0f} remaining"
                if passed_daily else
                f"DAILY LOSS LIMIT HIT: ${self._daily_pnl:+,.0f} (limit: -${daily_loss_limit:,.0f}) — TRADING HALTED"
            ),
            "critical": True,
        })

        # ── Check 9: MAX DRAWDOWN (Circuit Breaker) ───────────────────────
        drawdown = (self._peak_equity - equity) / self._peak_equity if self._peak_equity > 0 else 0
        max_dd = self.limits.max_drawdown
        passed_dd = drawdown < max_dd
        checks.append({
            "name": "DRAWDOWN",
            "status": "PASS" if passed_dd else "REJECT",
            "detail": (
                f"Peak drawdown: {drawdown:.1%} < {max_dd:.0%} maximum threshold"
                if passed_dd else
                f"DRAWDOWN LIMIT EXCEEDED: {drawdown:.1%} ≥ {max_dd:.0%} — CIRCUIT BREAKER TRIGGERED"
            ),
            "critical": True,
        })

        # ── Check 10: LIQUIDITY (Bid-Ask Spread <= $0.15) ─────────────────
        bid_ask = float(proposal.get("bid_ask_spread", 0.05))
        passed_liq = bid_ask <= 0.15
        checks.append({
            "name": "LIQUIDITY",
            "status": "PASS" if passed_liq else "REJECT",
            "detail": (
                f"Spread: ${bid_ask:.2f} ≤ $0.15"
                if passed_liq else
                f"Spread: ${bid_ask:.2f} > $0.15 — SPREAD TOO WIDE / LOW LIQUIDITY"
            ),
        })

        # ── Check 11: SPREAD WIDTH (Width <= $5.00) ───────────────────────
        width = float(proposal.get("spread_width", 5.0))
        passed_width = width <= self.limits.max_spread_width
        checks.append({
            "name": "SPREAD WIDTH",
            "status": "PASS" if passed_width else "REJECT",
            "detail": (
                f"${width:.2f} ≤ ${self.limits.max_spread_width:.2f}"
                if passed_width else
                f"${width:.2f} > ${self.limits.max_spread_width:.2f} — WIDTH EXCEEDS $5 LIMIT"
            ),
        })

        # ── Check 12: EXPIRATION WINDOW (7-21 DTE) ────────────────────────
        dte = int(proposal.get("dte", 14))
        passed_dte = self.limits.min_dte <= dte <= self.limits.max_dte
        checks.append({
            "name": "EXPIRATION",
            "status": "PASS" if passed_dte else "REJECT",
            "detail": (
                f"{dte} DTE within sweet spot ({self.limits.min_dte}-{self.limits.max_dte} days)"
                if passed_dte else
                f"{dte} DTE outside required {self.limits.min_dte}-{self.limits.max_dte} window"
            ),
        })

        # ── Final Verdict ─────────────────────────────────────────────────
        all_pass = all(c["status"] == "PASS" for c in checks)
        critical_fails = [c["name"] for c in checks if c["status"] == "REJECT" and c.get("critical")]
        status = "PASS" if all_pass else "REJECT"

        # ── Terminal Logging ──────────────────────────────────────────────
        if all_pass:
            console.print("[bold green][Risk Engine][/bold green] ✓ ALL 12 RISK GATES PASSED — approved for human consent")
        else:
            failed = [c["name"] for c in checks if c["status"] == "REJECT"]
            console.print(f"[bold red][Risk Engine][/bold red] ✗ REJECTED — failed {len(failed)}/12 gates: {', '.join(failed)}")
            if critical_fails:
                console.print(f"[bold red][Risk Engine] ⚠ CRITICAL RISK GATE: {', '.join(critical_fails)}[/bold red]")

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
            "allocated_contracts": qty,
            "total_risk_proposed": total_risk_proposed,
        }


# Singleton instance
risk_engine = RiskEngine()


if __name__ == "__main__":
    # Test with mock proposal
    mock_proposal = {
        "max_loss_per_contract": 335,
        "spread_width": 5.0,
        "dte": 14,
        "bid_ask_spread": 0.04,
        "direction": "LONG",
        "underlying": "SPY",
        "quantity": 2,
        "total_risk_proposed": 670,
    }
    mock_portfolio = {
        "open_position_count": 1,
        "current_portfolio_exposure": 335,
        "available_cash": 100_000,
        "equity": 100_000,
        "open_positions": [],
    }
    result = risk_engine.check(mock_proposal, mock_portfolio)
    print(json.dumps(result, indent=2, default=str))

