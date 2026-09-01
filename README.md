# 🐂 BullRun

**AI proposes. Evidence decides. Humans authorize.**

An AI options trading desk that doesn't just trade for you — it teaches you to think like a quant. Every decision is explained in plain English. By day 5, you're not just watching the AI — you're starting to see what it sees.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![Alpaca](https://img.shields.io/badge/Alpaca-Paper%20Trading-green)](https://alpaca.markets)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎯 What BullRun Does

BullRun is a multi-agent trading system that:

1. **Scout** scans SPY market regime (BULLISH/BEARISH/NEUTRAL/VOLATILE)
2. **Quant** selects defined-risk options spreads (bull call / bear put)
3. **Risk Engine** validates against 8 deterministic rules (PASS/REJECT only)
4. **CIO** generates plain-English trade thesis via GPT-4o-mini
5. **Teaching Engine** explains every decision to beginners
6. **Trade Card** displays the proposal in beginner-friendly language
7. **Human Consent** — you approve or reject before execution
8. **Alpaca SDK** executes the approved trade
9. **Monitor** manages positions automatically (TP/SL/DTE exits)

## 🧠 The Key Insight

> "Most AI trading agents are designed to maximize autonomy. We designed ours to maximize accountability."

BullRun combines multiple independent signals to generate options trades, but the AI never receives unrestricted execution authority. Every trade must pass:

- **Deterministic risk gates** (Python, not LLM)
- **Human consent** (explicit approval)
- **Pre-authorized exit rules** (automatic management)
- **Teaching layer** (plain-English explanations)

## 🏗️ Architecture

```
Scout → Quant → Risk Engine → CIO → Teaching Engine → Trade Card → Consent → Alpaca → Monitor
  ↓        ↓         ↓          ↓           ↓              ↓           ↓          ↓        ↓
Regime  Structure  8 checks   Thesis    Explains        Plain-     Approve   Execute  Auto-exit
                       ↓          ↓      everything                ↓
                  2% Rule    Bounded      ↓
                  Daily Loss  Risk    Learner Level
                  Drawdown            (Beginner→Advanced)
```

**Key architectural rule:** The LLM is NEVER in the decision path. Python does all math and validation. The LLM only explains.

## 🎓 Teaching Engine

BullRun doesn't just trade — it teaches. Every decision includes:

| Feature | What It Does |
|---------|--------------|
| **Regime Lessons** | Explains WHY Scout says BULLISH/BEARISH/NEUTRAL (ADX, EMA, RSI conditions) |
| **Strategy Explainer** | Teaches what spreads are, why these strikes were chosen |
| **Rejection Explainers** | Patiently explains why system said NO TRADE |
| **Trade Journal** | Post-trade learning reports (predicted vs actual) |
| **Progression Tracking** | Beginner → Intermediate → Advanced based on features explored |

## 📊 Risk Engine (8 Hardcoded Checks)

| Check | Rule | Why |
|-------|------|-----|
| **2% Rule** | ≤ $2,000/trade | No single trade can blow up the account |
| **Exposure Cap** | ≤ $6,000 total | Max 3 positions × $2K = 6% total risk |
| **Max Positions** | < 3 concurrent | Diversification without over-complication |
| **Daily Loss** | ≤ $3,000/day | Stop trading after 3% daily loss |
| **Drawdown Brake** | ≤ 10% ($10K) | Halt all trading if account drops 10% |
| **Liquidity** | Bid-ask ≤ $0.15 | Ensure we can enter/exit cleanly |
| **Spread Width** | ≤ $5.00 | Keep defined-risk structures tight |
| **Expiration** | 7-21 DTE | Sweet spot for gamma exposure vs theta decay |

**Non-negotiable.** The LLM cannot override these. The human cannot override these. Only the code can change them (by editing config.py).

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/samm12331231/BullRun.git
cd BullRun
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your Alpaca paper trading credentials
```

### 3. Run

```bash
# Single pipeline run
python main.py

# Start the API server (for dashboard)
python api.py

# In another terminal, start the dashboard
cd dashboard
npm install
npm run dev
```

Open **http://localhost:3000** to see the live trading terminal.

## 🖥️ Dashboard

The Next.js dashboard provides:

- **TradingView candlestick charts** with volume
- **Live trade proposal cards** with approve/reject buttons
- **Portfolio metrics** (P&L, win rate, ADX, learner level)
- **Agent activity log** showing every signal, proposal, risk check, consent
- **Teaching layer** with regime lessons and strategy explainers
- **WebSocket** for real-time updates from the Python backend
- **Dark mode** — professional trading terminal aesthetic

## 📈 Strategy

**Directional debit spreads on SPY:**

| Regime | Strategy | When |
|--------|----------|------|
| **BULLISH** | Bull Call Spread | Profit if SPY rises |
| **BEARISH** | Bear Put Spread | Profit if SPY falls |
| **NEUTRAL** | NO TRADE | Wait for clarity |
| **VOLATILE** | NO TRADE | Wait for calmer conditions |

All trades are defined-risk: max loss = premium paid (known upfront).

## 🎯 Conviction Score

Every proposal is scored on 6 weighted factors:

- Regime strength (25%)
- Momentum alignment (20%)
- Options pricing (15%)
- Liquidity (15%)
- Risk/reward (15%)
- Time alignment (10%)

| Score | Action |
|-------|--------|
| ≥ 80 | Show to human for approval |
| 60-79 | Watch (logged, not proposed) |
| < 60 | Reject (skipped silently) |

## 🛡️ Exit Rules (Automatic)

| Rule | Trigger | Action |
|------|---------|--------|
| Take Profit | +50% of max profit | Close position |
| Stop Loss | -30% of debit paid | Close position |
| Trailing Stop | -40% from peak | Close position |
| Late-Stage Stop | -20% in last 5 days | Close position |
| DTE Exit | < 3 days to expiry | Close position |
| Time Exit | 10 days max hold | Close position |

**Entries require consent. Exits are pre-authorized.**

## 🏛️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Data** | Alpaca SDK (real-time quotes, option chains, Greeks) |
| **Execution** | Alpaca SDK + MCP server |
| **Indicators** | ta (ADX, ATR, EMA, MACD, RSI) |
| **Terminal UI** | Rich |
| **LLM** | GPT-4o-mini (thesis generation only) |
| **Backend** | FastAPI + WebSocket |
| **Frontend** | Next.js 15 + TradingView lightweight-charts |
| **Audit** | SHA-256 hash-chained JSONL |

## 📁 Project Structure

```
bullrun/
├── config.py              # Settings, risk constants, Alpaca keys
├── main.py                # Entry point (run/monitor/dashboard/loop)
├── api.py                 # FastAPI backend (REST + WebSocket)
├── orchestrator.py        # Pipeline coordinator
├── teaching_engine.py     # 🎓 Plain-English explanations
├── trade_card.py          # Rich terminal trade cards
├── consent_gate.py        # Human approval flow
├── execution.py           # Alpaca order placement
├── monitor.py             # Position tracking + auto-exit
├── results.py             # Post-trade learning reports
├── audit.py               # SHA-256 hash-chained audit trail
├── agents/
│   ├── scout_agent.py     # Regime detection
│   ├── quant_agent.py     # Options structure selection
│   ├── risk_engine.py     # 8 deterministic risk gates
│   ├── cio_agent.py       # LLM thesis generation
│   └── data_service.py    # Alpaca data layer
├── dashboard/             # Next.js frontend
│   ├── src/
│   │   ├── app/page.tsx   # Main dashboard
│   │   ├── components/    # Chart, TradeCard
│   │   └── lib/           # WebSocket hook
│   └── package.json
└── requirements.txt
```

## 🎤 The Pitch

> "I built an options trading agent that generates plain-English trade proposals for beginners. But the real engineering challenge wasn't the trading logic — it was the teaching layer. I had to decompose complex quantitative decisions into explanations a complete beginner could understand, while keeping the underlying system deterministic and auditable."

## 🏆 Hackathon Submission

**Event:** Alpaca AI Trading Agents Hackathon (Aug 28 – Sep 4, 2026)

**What we built:**
- Autonomous AI trading agent using Alpaca's Trading API
- Deterministic risk engine with 8 hardcoded safety gates
- Human consent gate before every trade
- Teaching layer that explains every decision in plain English
- Real-time dashboard with TradingView charts
- SHA-256 hash-chained audit trail

**Why it's different:**
- Most teams build autonomous bots. We built a trust architecture.
- Most teams optimize for speed. We optimize for understanding.
- Most teams hide the AI. We explain it.

## 📄 License

MIT

---

Built with 🐂 by [samm12331231](https://github.com/samm12331231)
