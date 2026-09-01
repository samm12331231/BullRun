# BullRun

**AI proposes. Evidence decides. Humans authorize.**

An AI options trading desk that makes risk understandable and bounded. Every trade must pass deterministic risk gates, produce a plain-English explanation, and receive explicit human consent before Alpaca executes.

## What It Does

BullRun is a multi-agent trading system that:

1. **Scout** scans SPY market regime (BULLISH/BEARISH/NEUTRAL/VOLATILE)
2. **Quant** selects defined-risk options spreads (bull call / bear put)
3. **Risk Engine** validates against 6 deterministic rules (PASS/REJECT only)
4. **CIO** generates plain-English trade thesis via GPT-4o-mini
5. **Trade Card** displays the proposal in beginner-friendly language
6. **Human Consent** — you approve or reject before execution
7. **Alpaca MCP** executes the approved trade
8. **Monitor** manages positions automatically (TP/SL/DTE exits)

## The Key Insight

> "The hardest part of trading isn't the math — it's the trust."

Most AI trading agents optimize for autonomy. BullRun optimizes for **accountability**. The AI never receives unrestricted execution authority. Every trade must pass:
- Deterministic risk gates (Python, not LLM)
- Human consent (explicit approval)
- Pre-authorized exit rules (automatic management)

## Architecture

```
Scout → Quant → Risk Engine → CIO → Trade Card → Consent → Alpaca → Monitor
  ↓        ↓         ↓          ↓         ↓           ↓          ↓        ↓
Regime  Structure  6 checks   Thesis   Plain-English  Approve   Execute  Auto-exit
```

**Key architectural rule:** The LLM is NEVER in the decision path. Python does all math and validation. The LLM only explains.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Alpaca

Edit `config.py` with your Alpaca paper trading credentials:

```python
ALPACA_API_KEY = "your-key"
ALPACA_SECRET_KEY = "your-secret"
```

### 3. Run

```bash
# Single pipeline run
python main.py

# Monitor open positions
python main.py --monitor

# Show portfolio dashboard
python main.py --dashboard

# Continuous scanning (every 15 min)
python main.py --loop

# Session summary
python main.py --summary
```

## Strategy

**Directional debit spreads on SPY:**

- **BULLISH regime** → Bull Call Spread (profit if SPY rises)
- **BEARISH regime** → Bear Put Spread (profit if SPY falls)
- **NEUTRAL/VOLATILE** → NO TRADE (wait for clarity)

All trades are defined-risk: max loss = premium paid (known upfront).

## Risk Engine (6 Hardcoded Checks)

| Check | Rule |
|-------|------|
| MAX LOSS | ≤ 1% of portfolio ($1,000) |
| PORTFOLIO HEAT | ≤ 5% total exposure ($5,000) |
| POSITIONS | < 3 concurrent |
| LIQUIDITY | Bid-ask spread ≤ $0.15 |
| SPREAD WIDTH | ≤ $5.00 |
| EXPIRATION | 7-21 DTE |

**Non-negotiable.** The LLM cannot override these. The human cannot override these. Only the code can change them (by editing config.py).

## Trade Card

Every trade proposal is displayed as a beginner-friendly card:

```
╔══════════════════════════════════════════════════════════╗
║         BULLRUN — TRADE PROPOSAL #017           ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  SPY Bull Call Spread                                    ║
║                                                          ║
║  ── WHAT'S HAPPENING ──────────────────────────────────  ║
║  The S&P 500 is trending upward. Our system found a     ║
║  trade that profits if this continues — and caps the    ║
║  maximum loss upfront.                                   ║
║                                                          ║
║  ── THE NUMBERS ───────────────────────────────────────  ║
║  You could make:       up to $265 per contract          ║
║  You could lose:       up to $235 per contract          ║
║                                                          ║
║           ┌──────────────┐  ┌──────────────┐            ║
║           │   APPROVE    │  │   REJECT     │            ║
║           └──────────────┘  └──────────────┘            ║
╚══════════════════════════════════════════════════════════╝
```

## Conviction Score

Every proposal is scored on 6 weighted factors:

- Regime strength (25%)
- Momentum alignment (20%)
- Options pricing (15%)
- Liquidity (15%)
- Risk/reward (15%)
- Time alignment (10%)

Score ≥ 80 → show to human
Score 60-79 → watch (logged)
Score < 60 → reject (skipped)

## Exit Rules (Automatic)

- Take profit: +50% of max profit
- Stop loss: -50% of debit paid
- DTE exit: close if DTE < 3
- Time exit: close after 10 days max

**Entries require consent. Exits are pre-authorized.**

## Tech Stack

- **Data:** alpaca-py + yfinance
- **Execution:** Alpaca MCP server + alpaca-py SDK
- **Indicators:** pandas-ta
- **Terminal UI:** Rich
- **LLM:** GPT-4o-mini (thesis only)
- **Scheduling:** APScheduler
- **Audit:** JSONL append-only log

## Project Structure

```
bullrun/
├── config.py              # Settings, risk constants, Alpaca keys
├── main.py                # Entry point
├── orchestrator.py        # Pipeline coordinator
├── agents/
│   ├── scout_agent.py     # Regime detection
│   ├── quant_agent.py     # Options structure selection
│   ├── risk_engine.py     # Deterministic risk gates
│   └── cio_agent.py       # LLM thesis generation
├── trade_card.py          # Rich terminal trade cards
├── consent_gate.py        # Human approval flow
├── execution.py           # Alpaca order placement
├── monitor.py             # Position tracking + auto-exit
├── results.py             # Post-trade learning reports
├── audit.py               # JSONL audit trail
└── requirements.txt       # Dependencies
```

## The Pitch

> "Most AI trading agents are designed to maximize autonomy. We designed ours to maximize accountable autonomy. BullRun combines multiple independent signals to generate options trades, but the AI never receives unrestricted execution authority. Every trade must pass deterministic risk controls, produce an auditable thesis, and receive explicit human consent before reaching Alpaca."

## License

MIT
