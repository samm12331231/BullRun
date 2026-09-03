"""
api.py — FastAPI Backend for BullRun

Provides:
- REST API for trade data, positions, audit trail
- WebSocket for real-time trade proposals and market data
- Integration point between Python agents and Next.js frontend
"""

import json
import asyncio
import hmac
import os
from datetime import datetime
from datetime import timedelta, timezone
from typing import Literal, Optional
from fastapi import Depends, FastAPI, Header, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import RISK_LIMITS, CONVICTION_APPROVE, CONVICTION_WATCH
from audit import get_trade_history, get_trade_summary


app = FastAPI(
    title="BullRun API",
    description="AI Options Trading Desk — Backend",
    version="1.0.0",
)

# CORS for Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket Manager ───────────────────────────────────────────────────────

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)

manager = ConnectionManager()


# ── Connect WebSocket manager to orchestrator on startup ─────────────
# In-memory proposal store for web consent flow
_pending_proposals: dict[int, dict] = {}
_proposal_lock = asyncio.Lock()
PROPOSAL_TTL_SECONDS = int(os.getenv("BULLRUN_PROPOSAL_TTL_SECONDS", "300"))


def _require_api_token(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Protect state-changing endpoints; fail closed when no token is configured."""
    expected = os.getenv("BULLRUN_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="BULLRUN_API_TOKEN must be configured for trade actions")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API token")

@app.on_event("startup")
async def startup():
    from orchestrator import _set_ws_manager
    _set_ws_manager(manager)
    app._pending_proposals = _pending_proposals


# ── Models ──────────────────────────────────────────────────────────────────

class TradeProposal(BaseModel):
    trade_number: int
    structure: str
    underlying: str
    direction: str
    long_leg: dict
    short_leg: dict
    net_debit: float
    spread_width: float
    max_loss: float
    max_profit: float
    breakeven: float
    risk_reward: float
    dte: int
    conviction_score: float
    regime: str

class ConsentDecision(BaseModel):
    trade_number: int
    decision: Literal["APPROVE", "REJECT"]
    reason: str = ""

class AIAnalysis(BaseModel):
    model: str
    role: str
    analysis: str
    confidence: float
    recommendation: str


# ── REST Endpoints ──────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "BullRun API",
        "version": "1.0.0",
        "tagline": "AI proposes. Evidence decides. Humans authorize.",
        "status": "running",
    }


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio state from Alpaca."""
    # Try to get real data from Alpaca first
    equity = 100_000.0
    cash = 100_000.0
    open_position_count = 0
    real_unrealized_pnl = 0.0
    alpaca_positions = []
    
    try:
        from agents.data_service import _get_trading_client
        client = _get_trading_client()
        if client:
            account = client.get_account()
            equity = float(account.equity)
            cash = float(account.cash)
            
            alpaca_positions = client.get_all_positions()
            open_position_count = len(alpaca_positions)
            real_unrealized_pnl = sum(float(p.unrealized_pl) for p in alpaca_positions)
    except Exception as e:
        print(f"[Portfolio] Alpaca fetch failed: {e}")
    
    summary = get_trade_summary(equity)
    
    # Use real position count from Alpaca, fall back to audit trail
    display_positions = open_position_count if open_position_count > 0 else (
        summary.get("executed", 0) - summary.get("closed", 0)
    )
    
    # Real P&L = realized from closed trades + unrealized from open positions
    realized_pnl = summary.get("total_pnl", 0)
    total_pnl = round(realized_pnl + real_unrealized_pnl, 2)
    return_pct = round(total_pnl / equity * 100, 2) if equity > 0 else 0
    
    _data_mode = "live" if open_position_count > 0 or equity != 100_000.0 else "fallback"
    return {
        "equity": round(equity, 2),
        "cash": round(cash, 2),
        "total_pnl": total_pnl,
        "unrealized_pnl": round(real_unrealized_pnl, 2),
        "return_pct": return_pct,
        "open_positions": display_positions,
        "total_trades": summary.get("total_proposals", 0),
        "win_rate": summary.get("win_rate", 0),
        "risk_used": round(sum(float(getattr(p, "cost_basis", 0) or 0) for p in alpaca_positions) if open_position_count > 0 else abs(real_unrealized_pnl), 2),
        "risk_limit": RISK_LIMITS.max_portfolio_exposure * equity,
        "data_mode": _data_mode,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/trades")
async def get_trades():
    """Get all trade history from audit trail."""
    history = get_trade_history()
    return {"trades": history}


@app.get("/api/trades/{trade_number}")
async def get_trade(trade_number: int):
    """Get a specific trade's full history."""
    history = get_trade_history()
    events = [e for e in history if e.get("trade_number") == trade_number]
    if not events:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"trade_number": trade_number, "events": events}


@app.get("/api/positions")
async def get_positions():
    """Get open positions."""
    try:
        from agents.data_service import get_open_positions
        positions = get_open_positions()
        return {"positions": positions}
    except Exception:
        return {"positions": []}


@app.get("/api/risk-limits")
async def get_risk_limits():
    """Get current risk engine configuration."""
    # Fetch real equity for accurate dollar limits
    _equity = 100_000.0
    try:
        from agents.data_service import _get_trading_client
        _client = _get_trading_client()
        if _client:
            _equity = float(_client.get_account().equity)
    except Exception:
        pass

    return {
        "max_risk_per_trade_pct": RISK_LIMITS.max_risk_per_trade,
        "max_risk_per_trade_dollars": RISK_LIMITS.max_risk_per_trade * _equity,
        "max_portfolio_exposure_pct": RISK_LIMITS.max_portfolio_exposure,
        "max_portfolio_exposure_dollars": RISK_LIMITS.max_portfolio_exposure * _equity,
        "max_concurrent_positions": RISK_LIMITS.max_concurrent_positions,
        "max_spread_width": RISK_LIMITS.max_spread_width,
        "min_dte": RISK_LIMITS.min_dte,
        "max_dte": RISK_LIMITS.max_dte,
        "take_profit_pct": RISK_LIMITS.take_profit_pct,
        "stop_loss_pct": RISK_LIMITS.stop_loss_pct,
    }


@app.get("/api/conviction")
async def get_conviction_thresholds():
    """Get conviction score thresholds."""
    return {
        "approve": CONVICTION_APPROVE,
        "watch": CONVICTION_WATCH,
        "reject": 0,
    }


@app.get("/api/audit-summary")
async def get_audit_summary():
    """Get summary statistics from the audit trail."""
    return get_trade_summary()


@app.get("/api/audit/verify")
async def verify_audit_chain():
    """Verify the integrity of the hash-chained audit trail."""
    from audit import verify_chain
    return verify_chain()


@app.get("/api/learning/progress")
async def get_learning_progress():
    """Return the learner's feature-based progress and current level."""
    from teaching_engine import get_progress
    return get_progress()


@app.post("/api/learning/explore/{feature}")
async def explore_learning_feature(feature: str, _: None = Depends(_require_api_token)):
    """Record a lesson that the user deliberately explored."""
    from teaching_engine import record_feature_explored
    try:
        return record_feature_explored(feature)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/learning/journal")
async def get_learning_journal():
    """Return post-trade predicted-versus-actual learning reports."""
    from teaching_engine import get_journal
    return {"reports": get_journal()}


@app.get("/api/regime")
async def get_current_regime():
    """Get current market regime (cached, refreshes every 5 min)."""
    try:
        from agents.scout_agent import run
        result = run()
        return result
    except Exception as e:
        return {"regime": "UNKNOWN", "error": str(e)}


@app.get("/api/market/tickers")
async def get_market_tickers():
    """Get real-time ticker quotes for the Bloomberg ticker tape."""
    try:
        from agents.data_service import get_ticker_quotes
        return {"tickers": get_ticker_quotes()}
    except Exception as e:
        return {"tickers": []}


@app.get("/api/chart")
async def get_chart_data():
    """Get 90 days of SPY OHLCV for the TradingView chart."""
    import time as _time
    now = _time.time()
    if not hasattr(get_chart_data, '_cache') or now - get_chart_data._cache.get('ts', 0) > 300:
        try:
            import yfinance as yf
            spy = yf.Ticker("SPY")
            hist = spy.history(period="3mo", interval="1d")
            bars = []
            for idx, row in hist.iterrows():
                bars.append({
                    "time": idx.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })
            get_chart_data._cache = {"ts": now, "data": bars}
        except Exception:
            get_chart_data._cache = {"ts": now, "data": []}
    return {"data": get_chart_data._cache["data"]}

@app.get("/api/backtest")
async def get_backtest():
    """Run historical backtest and return equity curve + stats."""
    import time as _time
    now = _time.time()
    if not hasattr(get_backtest, '_cache') or now - get_backtest._cache.get('ts', 0) > 600:
        try:
            from backtest import run_backtest
            results = run_backtest()
            get_backtest._cache = {"ts": now, "data": results}
        except Exception as e:
            get_backtest._cache = {"ts": now, "data": {"error": str(e)}}
    return get_backtest._cache["data"]



@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol."""
    try:
        from agents.data_service import get_current_price, get_historical_bars
        price = get_current_price(symbol)
        bars = get_historical_bars(symbol, days=30)
        return {
            "symbol": symbol,
            "price": price,
            "bars": bars.tail(20).reset_index().to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/scan")
async def trigger_scan(_: None = Depends(_require_api_token)):
    """Trigger a single pipeline scan (web-compatible, no CLI consent)."""
    from orchestrator import run_pipeline_web
    try:
        result = run_pipeline_web()
        # Store proposal for consent flow
        trade_num = result.get("trade_number")
        if trade_num and result.get("proposal"):
            _pending_proposals[trade_num] = {
                "proposal": result["proposal"],
                "created_at": datetime.now(timezone.utc),
            }
        return {"status": "completed", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/scan-cli")
async def trigger_scan_cli(_: None = Depends(_require_api_token)):
    """Trigger a pipeline scan with CLI consent (for terminal demo)."""
    from orchestrator import run_pipeline
    try:
        result = run_pipeline()
        return {"status": "completed", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/positions/live")
async def get_live_positions():
    """Get open positions with live P&L data."""
    from monitor import monitor
    details = monitor.get_position_details()
    summary = monitor.get_portfolio_summary()
    return {"positions": details, "summary": summary}


@app.post("/api/consent")
async def submit_consent(decision: ConsentDecision, _: None = Depends(_require_api_token)):
    """Submit a human consent decision for a trade and execute if approved."""
    from audit import log_consent
    from orchestrator import execute_after_consent

    async with _proposal_lock:
        record = _pending_proposals.pop(decision.trade_number, None)

    if not record:
        raise HTTPException(status_code=404, detail="Proposal not found, expired, or already decided")
    created_at = record["created_at"]
    if datetime.now(timezone.utc) - created_at > timedelta(seconds=PROPOSAL_TTL_SECONDS):
        raise HTTPException(status_code=410, detail="Proposal has expired; run a new scan")

    consent_dict = {"decision": decision.decision, "reason": decision.reason, "timestamp": datetime.now(timezone.utc).isoformat()}
    log_consent(consent_dict, decision.trade_number)

    # Broadcast consent decision
    await manager.broadcast({
        "type": "consent_decision",
        "trade_number": decision.trade_number,
        "decision": decision.decision,
        "reason": decision.reason,
        "timestamp": datetime.now().isoformat(),
    })

    # If approved, execute the trade
    if decision.decision == "APPROVE":
        try:
            execution = await asyncio.to_thread(
                execute_after_consent, decision.trade_number, record["proposal"], consent_dict
            )
            return {"status": "executed", "trade_number": decision.trade_number, "execution": execution}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    return {"status": "recorded", "trade_number": decision.trade_number}


# ── WebSocket Endpoints ─────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket for real-time trade updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg.get("type") == "request_regime":
                try:
                    from agents.scout_agent import run
                    result = run()
                    await websocket.send_json({
                        "type": "regime_update",
                        "data": result,
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Broadcast helpers (called by orchestrator) ──────────────────────────────

async def broadcast_trade_proposal(proposal: dict, thesis: dict, risk_check: dict, trade_number: int):
    """Broadcast a new trade proposal to all connected clients."""
    await manager.broadcast({
        "type": "trade_proposal",
        "trade_number": trade_number,
        "proposal": proposal,
        "thesis": thesis,
        "risk_check": risk_check,
        "timestamp": datetime.now().isoformat(),
    })


async def broadcast_trade_update(trade_number: int, status: str, details: dict):
    """Broadcast a trade status update."""
    await manager.broadcast({
        "type": "trade_update",
        "trade_number": trade_number,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat(),
    })


async def broadcast_market_data(data: dict):
    """Broadcast market data to all clients."""
    await manager.broadcast({
        "type": "market_data",
        "data": data,
        "timestamp": datetime.now().isoformat(),
    })


async def broadcast_ai_analysis(model: str, role: str, analysis: str, confidence: float):
    """Broadcast AI model analysis to all clients."""
    await manager.broadcast({
        "type": "ai_analysis",
        "model": model,
        "role": role,
        "analysis": analysis,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat(),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
