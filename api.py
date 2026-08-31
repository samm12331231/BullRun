"""
api.py — FastAPI Backend for Conviction Gate

Provides:
- REST API for trade data, positions, audit trail
- WebSocket for real-time trade proposals and market data
- Integration point between Python agents and Next.js frontend
"""

import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import RISK_LIMITS, CONVICTION_APPROVE, CONVICTION_WATCH
from audit import get_trade_history, get_trade_summary


app = FastAPI(
    title="Conviction Gate API",
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
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()


# ── Connect WebSocket manager to orchestrator on startup ─────────────
@app.on_event("startup")
async def startup():
    from orchestrator import _set_ws_manager
    _set_ws_manager(manager)


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
    decision: str  # APPROVE or REJECT
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
        "name": "Conviction Gate API",
        "version": "1.0.0",
        "tagline": "AI proposes. Evidence decides. Humans authorize.",
        "status": "running",
    }


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio state."""
    summary = get_trade_summary()
    return {
        "equity": 100_000,
        "cash": 100_000,
        "total_pnl": summary.get("total_pnl", 0),
        "return_pct": summary.get("return_pct", 0),
        "open_positions": summary.get("executed", 0) - summary.get("closed", 0),
        "total_trades": summary.get("total_proposals", 0),
        "win_rate": summary.get("win_rate", 0),
        "risk_used": 0,
        "risk_limit": RISK_LIMITS.max_portfolio_exposure * 100_000,
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
    return {
        "max_risk_per_trade_pct": RISK_LIMITS.max_risk_per_trade,
        "max_risk_per_trade_dollars": RISK_LIMITS.max_risk_per_trade * 100_000,
        "max_portfolio_exposure_pct": RISK_LIMITS.max_portfolio_exposure,
        "max_portfolio_exposure_dollars": RISK_LIMITS.max_portfolio_exposure * 100_000,
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
async def explore_learning_feature(feature: str):
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
async def trigger_scan():
    """Trigger a single pipeline scan."""
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
async def submit_consent(decision: ConsentDecision):
    """Submit a human consent decision for a trade."""
    from audit import log_consent
    log_consent(
        {"decision": decision.decision, "reason": decision.reason},
        decision.trade_number,
    )
    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "consent_decision",
        "trade_number": decision.trade_number,
        "decision": decision.decision,
        "reason": decision.reason,
        "timestamp": datetime.now().isoformat(),
    })
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
