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
from zoneinfo import ZoneInfo
import json as _json
import os as _os
from rich.console import Console
from config import RISK_LIMITS, UNDERLYING, AUDIT_LOG
from agents.data_service import check_upcoming_earnings

# Correlated ETF groups for the correlation guard
CORRELATED_GROUPS = {
    "us_equity_broad": {"SPY", "QQQ", "IWM", "VTI", "VOO", "IVV"},
    "tech_sector": {"QQQ", "XLK"},
}
STATE_FILE = "risk_engine_state.json"

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
        self._starting_equity: float | None = None
        self._peak_equity: float | None = None
        self._total_checked = 0
        self._total_blocked = 0
        self._blocked_by_gate: dict[str, int] = {}
        self._load_state()

    def _load_state(self):
        if _os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    state = _json.load(f)
                    self._daily_pnl = state.get("daily_pnl", 0.0)
                    self._daily_date = date.fromisoformat(state.get("daily_date", date.today().isoformat()))
                    self._peak_equity = state.get("peak_equity")
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(STATE_FILE, "w") as f:
                _json.dump({
                    "daily_pnl": self._daily_pnl,
                    "daily_date": self._daily_date.isoformat(),
                    "peak_equity": self._peak_equity,
                }, f)
        except Exception:
            pass

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
        if self._starting_equity is None:
            self._starting_equity = equity
        if self._peak_equity is None or equity > self._peak_equity:
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
                "unrealized_pnl": 0,
            }

        equity = float(portfolio_state.get("equity", portfolio_state.get("available_cash", 100_000.0)))
        checks = []

        # ── Check 1: 2% RULE (Total Trade Risk) ─────────────────────────
        max_loss_per_contract = float(proposal.get("max_loss_per_contract", 0))
        qty = int(proposal.get("quantity", proposal.get("recommended_contracts", 1)))
        computed_total = max_loss_per_contract * qty
        provided_total = float(proposal.get("total_risk_proposed", computed_total))
        max_allowed_risk = self.limits.max_risk_per_trade * equity
        # Fail-closed: missing/negative data = REJECT
        risk_valid = (
            max_loss_per_contract > 0
            and abs(provided_total - computed_total) < 0.01
            and provided_total <= max_allowed_risk
        )
        checks.append({
            "name": "2% RULE",
            "status": "PASS" if risk_valid else "REJECT",
            "detail": (
                f"Total risk ${provided_total:,.0f} ≤ ${max_allowed_risk:,.0f} "
                f" ({self.limits.max_risk_per_trade:.0%} of ${equity:,.0f})"
                if risk_valid else
                f"Total risk ${provided_total:,.0f} > ${max_allowed_risk:,.0f} — EXCEEDS 2% LIMIT"
            ),
            "critical": True,
        })

        # ── Check 2: CONVICTION SIZING (Position Sizing by Score) ──────────
        total_risk_proposed = provided_total
        conviction_score = float(proposal.get("conviction_score", 80))
        if conviction_score >= 95:
            conviction_cap = max_allowed_risk
        elif conviction_score >= 90:
            conviction_cap = max_allowed_risk * 0.75
        elif conviction_score >= 80:
            conviction_cap = max_allowed_risk * 0.50
        else:
            conviction_cap = 0.0
        max_contracts = int(conviction_cap / max_loss_per_contract) if max_loss_per_contract > 0 else 0
        passed_sizing = qty <= max_contracts and total_risk_proposed <= conviction_cap and max_loss_per_contract > 0
        checks.append({
            "name": "CONVICTION SIZING",
            "status": "PASS" if passed_sizing else "REJECT",
            "detail": (
                f"{qty} contract{'s' if qty > 1 else ''} (${total_risk_proposed:,.0f} risk) ≤ {max_contracts} max (conviction {conviction_score:.0f}, 2% cap ${max_allowed_risk:,.0f})"
                if passed_sizing else
                f"{qty} contracts exceed conviction-based limit of {max_contracts} (score {conviction_score:.0f}) or 2% cap"
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

        # ── Check 5: CORRELATION GUARD (Group-Aware) ───────────────────
        open_positions = portfolio_state.get("open_positions", [])
        proposed_dir = proposal.get("direction", "LONG")
        proposed_sym = proposal.get("underlying", UNDERLYING)
        
        proposed_group = None
        for group_name, symbols in CORRELATED_GROUPS.items():
            if proposed_sym in symbols:
                proposed_group = group_name
                break
        
        correlated_conflict = False
        conflict_reason = ""
        for pos in open_positions:
            pos_sym = pos.get("underlying", "")
            pos_dir = pos.get("direction", "")
            if pos.get("status") != "OPEN":
                continue
            # Exact duplicate
            if pos_sym == proposed_sym and pos_dir == proposed_dir:
                correlated_conflict = True
                conflict_reason = f"Duplicate {pos_dir} on {pos_sym} (Trade #{pos.get('trade_number')})"
                break
            # Correlated group duplicate
            if proposed_group and pos_sym in CORRELATED_GROUPS.get(proposed_group, set()) and pos_dir == proposed_dir:
                correlated_conflict = True
                conflict_reason = f"Correlated {pos_dir}: {proposed_sym} ↔ {pos_sym} ({proposed_group})"
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
        from zoneinfo import ZoneInfo
        now_est = datetime.now(ZoneInfo("America/New_York"))  # Market timezone
        current_time = now_est.time()
        # Market open 9:30 EST, close 16:00 EST
        # Block first 30 min (9:30-10:00) and last 30 min (15:30-16:00)
        market_open = time(9, 30)
        open_buffer_end = time(10, 0)   # 9:30 + 30min = 10:00
        close_buffer_start = time(15, 30)  # 16:00 - 30min = 15:30
        market_close = time(16, 0)
        
        in_open_buffer = market_open <= current_time < open_buffer_end
        in_close_buffer = close_buffer_start <= current_time < market_close
        outside_market = current_time < market_open or current_time >= market_close
        
        is_in_safe_window = (
            not in_open_buffer
            and not in_close_buffer
            and not outside_market
        ) if self.limits.enforce_market_hours else True
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
        unrealized_pnl = float(portfolio_state.get("unrealized_pnl", 0))
        effective_daily_pnl = self._daily_pnl + unrealized_pnl
        daily_loss_limit = self.limits.max_daily_loss * equity
        daily_remaining = daily_loss_limit + effective_daily_pnl
        passed_daily = daily_remaining > 0
        checks.append({
            "name": "DAILY LIMIT",
            "status": "PASS" if passed_daily else "REJECT",
            "detail": (
                f"Today's P&L: ${effective_daily_pnl:+,.0f} (realized: ${self._daily_pnl:+,.0f}, unrealized: ${unrealized_pnl:+,.0f}) | Budget: ${daily_remaining:,.0f} remaining"
                if passed_daily else
                f"DAILY LOSS LIMIT HIT: ${self._daily_pnl:+,.0f} (limit: -${daily_loss_limit:,.0f}) — TRADING HALTED"
            ),
            "critical": True,
        })

        # ── Check 9: MAX DRAWDOWN (Circuit Breaker) ───────────────────────
        if self._peak_equity is None or self._peak_equity <= 0:
            drawdown = 0.0  # Cannot compute drawdown without verified peak equity
        else:
            drawdown = (self._peak_equity - equity) / self._peak_equity
        max_dd = self.limits.max_drawdown
        passed_dd = drawdown <= max_dd
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
        bid_ask = float(proposal.get("bid_ask_spread", float("inf")))
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
        width = float(proposal.get("spread_width", float("inf")))
        passed_width = width <= self.limits.max_spread_width
        checks.append({
            "name": "SPREAD WIDTH",
            "status": "PASS" if passed_width else "REJECT",
            "detail": (
                f"${width:.2f} ≤ ${self.limits.max_spread_width:.2f}"
                if passed_width else
                f"${width:.2f} > ${self.limits.max_spread_width:.2f} — WIDTH EXCEEDS ${self.limits.max_spread_width:.2f} LIMIT"
            ),
        })

        # ── Check 12: EXPIRATION WINDOW (7-21 DTE) ────────────────────────
        dte = int(proposal.get("dte", 0))
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

        # Track statistics for proof dashboard
        self._total_checked += 1
        if status == "REJECT":
            self._total_blocked += 1
            for c in checks:
                if c["status"] == "REJECT":
                    self._blocked_by_gate[c["name"]] = self._blocked_by_gate.get(c["name"], 0) + 1

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

