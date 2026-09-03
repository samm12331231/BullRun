"""Smoke tests for BullRun's 12 deterministic risk gates."""

import pytest
from agents.risk_engine import RiskEngine

@pytest.fixture
def engine():
    return RiskEngine()

@pytest.fixture
def base_proposal():
    return {
        "max_loss_per_contract": 335,
        "quantity": 2,
        "total_risk_proposed": 670,
        "conviction_score": 84.5,
        "spread_width": 5.0,
        "dte": 14,
        "bid_ask_spread": 0.04,
        "direction": "LONG",
        "underlying": "SPY",
    }

@pytest.fixture
def base_portfolio():
    return {
        "open_position_count": 0,
        "current_portfolio_exposure": 0,
        "equity": 100_000,
        "open_positions": [],
        "unrealized_pnl": 0,
    }

def test_all_gates_pass(engine, base_proposal, base_portfolio):
    result = engine.check(base_proposal, base_portfolio)
    assert result["status"] == "PASS"
    assert result["all_passed"] is True
    assert len(result["checks"]) == 12

def test_2pct_rule_rejects_overlimit(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 3000, "quantity": 1, "total_risk_proposed": 3000,
                "conviction_score": 95, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert result["status"] == "REJECT"
    assert "2% RULE" in result["failed_checks"]

def test_2pct_rule_rejects_zero_loss(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 0, "quantity": 1, "total_risk_proposed": 0,
                "conviction_score": 80, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert result["status"] == "REJECT"

def test_2pct_rule_rejects_negative_loss(engine, base_portfolio):
    proposal = {"max_loss_per_contract": -500, "quantity": 1, "total_risk_proposed": -500,
                "conviction_score": 80, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert result["status"] == "REJECT"

def test_conviction_sizing_rejects_below_80(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 500, "quantity": 3, "total_risk_proposed": 1500,
                "conviction_score": 50, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "CONVICTION SIZING" in result["failed_checks"]

def test_correlation_guard_blocks_same_direction(engine, base_portfolio):
    base_portfolio["open_position_count"] = 1
    base_portfolio["open_positions"] = [{"underlying": "SPY", "direction": "LONG", "status": "OPEN", "trade_number": 1}]
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "CORRELATION GUARD" in result["failed_checks"]

def test_correlation_guard_blocks_correlated_etfs(engine, base_portfolio):
    base_portfolio["open_position_count"] = 1
    base_portfolio["open_positions"] = [{"underlying": "QQQ", "direction": "LONG", "status": "OPEN", "trade_number": 1}]
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "CORRELATION GUARD" in result["failed_checks"]

def test_max_positions_rejects(engine, base_portfolio):
    base_portfolio["open_position_count"] = 3
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "POSITIONS" in result["failed_checks"]

def test_spread_width_rejects_wide(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 10.0, "dte": 14, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "SPREAD WIDTH" in result["failed_checks"]

def test_expiration_rejects_short_dte(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 5.0, "dte": 3, "bid_ask_spread": 0.05,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "EXPIRATION" in result["failed_checks"]

def test_liquidity_rejects_wide_spread(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14, "bid_ask_spread": 0.50,
                "direction": "LONG", "underlying": "SPY"}
    result = engine.check(proposal, base_portfolio)
    assert "LIQUIDITY" in result["failed_checks"]

def test_missing_data_fail_closed(engine, base_portfolio):
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85}
    result = engine.check(proposal, base_portfolio)
    assert result["status"] == "REJECT"


def test_equity_scaling_50k():
    """2% of $50K = $1,000 max risk per trade, not $2,000."""
    engine = RiskEngine()
    proposal = {"max_loss_per_contract": 500, "quantity": 1, "total_risk_proposed": 500,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14,
                "bid_ask_spread": 0.04, "direction": "LONG", "underlying": "SPY"}
    portfolio = {"equity": 50_000, "open_position_count": 0,
                 "current_portfolio_exposure": 0, "open_positions": []}
    result = engine.check(proposal, portfolio)
    assert result["status"] == "PASS"
    # But 3 contracts at $500 = $1,500 should be rejected (exceeds 2% of $50K)
    proposal["quantity"] = 3
    proposal["total_risk_proposed"] = 1500
    result = engine.check(proposal, portfolio)
    assert result["status"] == "REJECT"
    assert "2% RULE" in result["failed_checks"]


def test_equity_scaling_100k():
    """2% of $100K = $2,000 max risk per trade."""
    engine = RiskEngine()
    proposal = {"max_loss_per_contract": 335, "quantity": 2, "total_risk_proposed": 670,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14,
                "bid_ask_spread": 0.04, "direction": "LONG", "underlying": "SPY"}
    portfolio = {"equity": 100_000, "open_position_count": 0,
                 "current_portfolio_exposure": 0, "open_positions": []}
    result = engine.check(proposal, portfolio)
    assert result["status"] == "PASS"
    # 18% of $100K = $18,000 risk should be rejected
    proposal["quantity"] = 54
    proposal["total_risk_proposed"] = 18090
    result = engine.check(proposal, portfolio)
    assert result["status"] == "REJECT"
    assert "2% RULE" in result["failed_checks"]


def test_peak_equity_initialization():
    """First update_equity call initializes both starting and peak."""
    engine = RiskEngine()
    assert engine._starting_equity is None
    assert engine._peak_equity is None
    engine.update_equity(50_000)
    assert engine._starting_equity == 50_000
    assert engine._peak_equity == 50_000


def test_peak_equity_tracks_high():
    """Peak equity only goes up, never down."""
    engine = RiskEngine()
    engine.update_equity(50_000)
    engine.update_equity(52_000)
    assert engine._peak_equity == 52_000
    engine.update_equity(48_000)
    assert engine._peak_equity == 52_000  # unchanged


def test_drawdown_from_real_peak():
    """Drawdown is calculated from peak, not from nominal $100K."""
    engine = RiskEngine()
    engine.update_equity(50_000)
    engine.update_equity(52_000)  # peak = $52K
    engine._daily_pnl = 0.0  # Reset daily P&L so only drawdown triggers
    proposal = {"max_loss_per_contract": 335, "quantity": 1, "total_risk_proposed": 335,
                "conviction_score": 85, "spread_width": 5.0, "dte": 14,
                "bid_ask_spread": 0.04, "direction": "LONG", "underlying": "SPY"}
    portfolio = {"equity": 46_000, "open_position_count": 0,
                 "current_portfolio_exposure": 0, "open_positions": []}
    result = engine.check(proposal, portfolio)
    # Equity dropped from $52K peak to $46K = 11.5% drawdown > 10% limit
    assert "DRAWDOWN" in result["failed_checks"]
