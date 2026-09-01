# BullRun Architecture

> AI proposes. Evidence decides. Humans authorize.

BullRun is a multi-agent options trading system built around one architectural principle: the LLM is never in the decision path. Python does all math and validation; the LLM only explains. Every trade must pass deterministic risk gates, produce a plain-English thesis, and receive explicit human consent before Alpaca executes.

## System Overview

BullRun runs as two cooperating processes:

1. **Python backend** (`api.py` on FastAPI + uvicorn, port 8000) — agents, risk engine, execution, audit trail, WebSocket
2. **Next.js dashboard** (port 3000) — React frontend with trade cards, TradingView charts, learning UI

### The Key Separation

```
DECISION PATH (Python)          EXPLANATION PATH (LLM)
Scout → Quant → Risk → Consent  CIO Agent (GPT-4o-mini) → thesis
(deterministic, no LLM)         (read-only, never decides)
```

## ASCII System Diagram

```
                    ┌──────────────────────────────────────────┐
                    │           MARKET DATA SOURCES            │
                    │   Yahoo Finance (fallback) · Alpaca      │
                    └──────────────┬──────────────┬────────────┘
                                   │              │
                                   ▼              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     BULLRUN BACKEND (FastAPI :8000)                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATOR (orchestrator.py)                │    │
│  │                                                                  │    │
│  │  STAGE 1         STAGE 2         STAGE 3         STAGE 4        │    │
│  │  ┌──────┐        ┌──────┐       ┌──────────┐   ┌──────┐       │    │
│  │  │SCOUT │───────▶│QUANT │──────▶│RISK ENG. │──▶│ CIO  │       │    │
│  │  │Agent │ regime │Agent │  prop │(8 gates) │the│(LLM) │       │    │
│  │  └──┬───┘        └──┬───┘       └────┬─────┘   └──┬───┘       │    │
│  │     │               │               │             │            │    │
│  │     ▼               ▼               ▼             ▼            │    │
│  │  regime         structure      PASS/REJECT    plain-English    │    │
│  │  (BULL/BEAR/    bull call /    (only Python)   thesis          │    │
│  │   NEUT/VOLAT)  bear put                                        │    │
│  └────┬──────────────┬───────────────┬─────────────┬──────────────┘    │
│       │              │               │             │                    │
│       │              │               │             ▼                    │
│       │              │               │      ┌──────────────┐           │
│       │              │               └─────▶│  TRADE CARD  │           │
│       │              │                      └──────┬───────┘           │
│       │              │                             ▼                    │
│       │              │                   ┌──────────────────┐          │
│       │              │                   │  CONSENT GATE   │          │
│       │              │                   │ (human APPROVE/ │          │
│       │              │                   │  REJECT)        │          │
│       │              │                   └────────┬─────────┘          │
│       │              │                            │ APPROVE            │
│       │              │                            ▼                     │
│       │              │                   ┌──────────────────┐          │
│       │              │                   │   EXECUTION     │          │
│       │              │                   │  (Alpaca SDK /  │          │
│       │              │                   │   DRY_RUN)      │          │
│       │              │                   └────────┬─────────┘          │
│       │              │                            ▼                     │
│       │              │                   ┌──────────────────┐          │
│       │              │                   │    MONITOR       │          │
│       │              │                   │ (TP/SL/DTE/time  │          │
│       │              │                   │  auto-exit)      │          │
│       │              │                   └────────┬─────────┘          │
│       │              │                            ▼                     │
│       │              │                   ┌──────────────────┐          │
│       │              └─────────────────▶│   AUDIT TRAIL   │          │
│       └────────────────────────────────▶│ (SHA-256 chain)  │          │
│                                         └──────────────────┘          │
│  ┌───────────────────┐                                                │
│  │ TEACHING ENGINE   │◀─── WebSocket Manager (broadcasts to dashboard) │
│  └───────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                          ┌──────────────────────────────────────┐
                          │      NEXT.JS DASHBOARD  (:3000)      │
                          │  · TradeCard.tsx  (approve/reject)    │
                          │  · Chart.tsx  (TradingView LWC)       │
                          │  · PayoffDiagram.tsx (interactive)    │
                          │  · TeachingPanel.tsx (learning)       │
                          │  · useWebSocket.ts (REST + WS client) │
                          └──────────────────────────────────────┘
```

## Component Reference

| Component | File | Role |
|-----------|------|------|
| Config | `config.py` | Alpaca keys, risk constants, conviction weights |
| Orchestrator | `orchestrator.py` | Runs 5-stage pipeline, broadcasts via WebSocket |
| Scout Agent | `agents/scout_agent.py` | Regime detection (ADX/ATR/EMA/MACD/RSI) |
| Quant Agent | `agents/quant_agent.py` | Options structure selection |
| Data Service | `agents/data_service.py` | Alpaca data layer |
| Risk Engine | `agents/risk_engine.py` | 8 deterministic gates |
| CIO Agent | `agents/cio_agent.py` | LLM thesis generation (GPT-4o-mini) |
| Trade Card | `trade_card.py` | Rich terminal trade cards |
| Consent Gate | `consent_gate.py` | Human approval checkpoint |
| Execution | `execution.py` | Alpaca order placement |
| Monitor | `monitor.py` | Position tracking + auto-exit |
| Teaching Engine | `teaching_engine.py` | Deterministic beginner-first explanations |
| Audit Trail | `audit.py` | SHA-256 hash-chained JSONL |
| API | `api.py` | FastAPI REST + WebSocket server |

## Risk Engine: The 8 Deterministic Gates

| # | Gate | Rule | Limit | Critical |
|---|------|------|-------|----------|
| 1 | 2% RULE | Max loss/trade ≤ 2% equity | $2,000 | Yes |
| 2 | EXPOSURE | Total risk ≤ 6% equity | $6,000 | No |
| 3 | POSITIONS | Concurrent < 3 | 3 | No |
| 4 | DAILY LIMIT | Daily loss ≤ 3% | $3,000 | Yes |
| 5 | DRAWDOWN | Drawdown < 10% | 10% | Yes |
| 6 | LIQUIDITY | Bid-ask ≤ $0.15 | $0.15 | No |
| 7 | SPREAD WIDTH | Width ≤ $5.00 | $5.00 | No |
| 8 | EXPIRATION | 7-21 DTE | 7-21 | No |

Critical fails trigger circuit breakers (stop trading for the day or until reset).

## Decision Tree

```
Scout: what is the regime?
    │
    ├── VOLATILE → NO TRADE ("waits for calmer conditions")
    ├── NEUTRAL (ADX < 25) → NO TRADE ("closer to gambling")
    └── BULLISH/BEARISH
         │
         ▼
    Quant selects debit spread
         │
         ├── No liquid legs → NO TRADE
         ├── Conviction 60-79 → WATCH (logged, not shown)
         └── Conviction ≥ 80 → PROPOSE
              │
              ▼
         Risk Engine: all 8 gates PASS?
              │
              ├── NO → RISK REJECTED (teaching: why)
              └── YES → CIO thesis + Trade Card → CONSENT
                   │
                   ├── REJECT → STAY QUIET
                   └── APPROVE → EXECUTE on Alpaca
```

## Teaching Engine Architecture

Deterministic explainers (no LLM):

1. `regime_lesson()` — explains WHY Scout says BULLISH/BEARISH/NEUTRAL
2. `strategy_explainer()` — teaches what spreads are
3. `rejection_explainer()` — patiently explains why NO TRADE
4. `generate_trade_journal()` — predicted vs actual after trade closes

## Audit Trail

SHA-256 hash-chained JSONL. Each event references the previous hash. Verifiable via `GET /api/audit/verify`.
