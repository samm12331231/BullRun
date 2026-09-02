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
