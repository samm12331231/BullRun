# BullRun — Alpaca AI Trading Agents Hackathon

**Repository:** https://github.com/samm12331231/BullRun
**Paper Trading Account:** Connected via Alpaca SDK (paper mode)
**Event:** Alpaca AI Trading Agents Hackathon (Aug 28 – Sep 4, 2026)

---

## What BullRun Is

BullRun is an AI options trading agent built for beginners. It doesn't just trade — it teaches. Every decision is explained in plain English before execution. The system runs a 4-agent pipeline (Scout → Quant → Risk Engine → CIO) that analyzes SPY market regime, selects defined-risk options spreads, validates against 12 deterministic risk gates, generates a human-readable thesis, and requires explicit human consent before placing any order on Alpaca paper trading.

The core insight: most trading agents optimize for autonomy. BullRun optimizes for accountability. The LLM (GPT-4o-mini) never decides whether to trade — it only explains. Python does all math, validation, and execution. The human authorizes. Every decision is SHA-256 hash-chained for tamper-evident audit.

## Architecture

**Scout** (regime detection): Computes ADX, ATR, EMA, MACD, RSI to classify market into BULLISH/BEARISH/NEUTRAL/VOLATILE. Uses ta library with yfinance/Alpaca data.

**Quant** (options selection): Maps regime to defined-risk spread (bull call or bear put). Selects strikes by delta targeting (0.50-0.65 long, 0.25-0.40 short). Scores conviction on 6 weighted factors.

**Risk Engine** (12 deterministic gates): 2% rule, conviction sizing, portfolio heat cap, max positions, correlation guard (SPY/QQQ/IWM), time-of-day guard (market hours only), earnings proximity, daily loss circuit breaker (incl. unrealized P&L), drawdown halt, liquidity check (both legs), spread width limit, and expiration window. State persists across restarts. Missing data = fail-closed REJECT. The LLM cannot override any gate.

**CIO** (thesis generation): GPT-4o-mini generates plain-English explanation with timeout protection and deterministic fallback template.

**Execution**: Dual SDK + CLI backend. MLEG multi-leg limit orders with atomic fill verification (polls Alpaca until both legs confirm fill, cancels on partial fill). Exponential backoff retry. Dry-run mode for testing.

**Monitor**: Auto-exits positions via 7 deterministic rules (take profit, stop loss, trailing stop, Greeks delta exit, DTE exit, time exit, late-stage decay). Real-time P&L from Alpaca positions API.

**Audit Trail**: SHA-256 hash-chained append-only JSONL log. Every signal, proposal, risk check, consent, and execution is chained. Tamper-evident verification endpoint.

**Teaching Engine**: Deterministic plain-English explainers for regime, strategy, rejections, and post-trade journals. Learner progression tracking (Beginner → Intermediate → Advanced).

**Dashboard**: Next.js 16 + TradingView lightweight-charts + WebSocket real-time updates. Bloomberg-terminal aesthetic with live portfolio metrics, trade cards, payoff diagrams, and learning progress.

## Alpaca Infrastructure

- **Primary**: Alpaca Trading SDK (alpaca-py) for multi-leg options orders
- **Secondary**: Alpaca CLI fallback path
- **MCP Server**: JSON-RPC 2.0 stdio server exposing `execute_alpaca_trade`
- **Data**: Real-time option chains, Greeks, quotes via Alpaca market data API
- **Paper Trading**: $100K paper account, real order execution
- **Exit Management**: Automated position monitoring via Alpaca positions API

## Risk Management

All 12 risk gates are deterministic Python code — no LLM, no override, no ambiguity. The system is designed to fail-closed: missing proposal data defaults to REJECT, not PASS. Circuit breakers (daily loss, max drawdown) persist state across restarts. Correlation guard prevents same-direction exposure on correlated ETFs (SPY/QQQ/IWM).

## Results

- Real trades executed on Alpaca paper trading
- Real-time P&L tracking via Alpaca positions API
- SHA-256 audit trail with verifiable chain integrity
- Dashboard showing live portfolio state, regime detection, and trade history

This project was built for the Alpaca AI Trading Agents Hackathon (2026).
