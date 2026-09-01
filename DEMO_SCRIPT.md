# BullRun — Hackathon Demo Video Script (2-Minute Pitch)

**Target Duration:** 120 seconds (2:00)  
**Tone:** Confident, institutional, crisp, founder-grade  
**Visuals:** Fullscreen screen recording of BullRun Bloomberg Terminal UI and CLI terminal side-by-side.

---

### [0:00 – 0:20] The Hook & The Problem
> **[VISUAL: Zoom in on Bloomberg terminal interface showing real-time price ticker, glowing metrics, and candlestick chart]**
>
> **SPEAKER:**  
> "Retail investors lose billions in options trading every year. Not because they can’t predict market direction, but because single-leg options suffer from brutal time decay, volatility crush, and catastrophic margin risk.  
> 
> Meanwhile, most AI trading agents make this worse: they’re black-box autonomous bots that hallucinate order sizes and take unhedged risks.  
>
> Meet **BullRun**—an institutional AI options trading desk built for the Alpaca Trading Platform that operates on a single core principle: **AI proposes, Evidence decides, Humans authorize.**"

---

### [0:20 – 0:50] The Multi-Agent Pipeline & 12-Gate Risk Engine
> **[VISUAL: Click 'Trigger AI Scan'. Telemetry stream flashes with Scout, Quant, Risk, and CIO agent status logs]**
>
> **SPEAKER:**  
> "Behind this Bloomberg-grade terminal is a four-agent pipeline.  
> First, our **Scout Agent** ingests historical bars from Alpaca, measuring ADX trend power, EMA 20/50 alignment, and ATR volatility to classify the regime as Bullish.  
>
> Next, our **Quant Agent** scans Alpaca options chains, prices Black-Scholes Greeks, and structures a defined-risk debit spread—capping maximum risk strictly to the cash paid at entry.  
>
> But here’s what makes BullRun winning tech: before any trade reaches the user, it must pass our **12 Deterministic Risk Gates**. The non-negotiable 2% portfolio loss rule, conviction-scaled sizing, a 6% portfolio heat limit, correlation checks across indices, market open/close time-of-day guards, and earnings proximity filters. Zero LLM hallucinations—pure mathematical enforcement."

---

### [0:50 – 1:20] The Plain-English CIO & Human-in-the-Loop Consent
> **[VISUAL: Focus on the Trade Card: Plain-English thesis, Greeks breakdown, and one-click 'AUTHORIZE TRADE' button]**
>
> **SPEAKER:**  
> "The LLM NEVER decides whether to trade. Instead, our **CIO Agent** acts as the user's educator, translating complex options math into plain English: What’s happening, what we’re buying, our exact maximum gain, and what could go wrong.  
>
> In the Trading Academy tab, users can interactively simulate their portfolio sizing and understand why debit spreads eliminate catastrophic tail risk.  
>
> Now, the human trader reviews the exact parameters and clicks **Authorize Trade**."

---

### [1:20 – 1:45] Multi-Leg Alpaca Execution & Dynamic Autopilot
> **[VISUAL: Click 'Authorize Trade'. Order status flips to FILLED. Position Monitor logs position and live P&L]**
>
> **SPEAKER:**  
> "Instantly, BullRun’s execution engine submits an atomic multi-leg order to the Alpaca API with exponential backoff retries and two-leg fill verification.  
>
> Post-entry, our **Position Monitor Autopilot** takes over: tracking account-native P&L from Alpaca, taking 50% partial profits at +30%, alerting if within 5% of stop loss, and executing automated Greeks-based exits if delta falls below 0.10.  
>
> Every signal, proposal, and consent decision is sealed with a **SHA-256 hash-chained audit log**."

---

### [1:45 – 2:00] The Closing
> **[VISUAL: Return to full dashboard view showing portfolio gains, win rate, and verified audit chain]**
>
> **SPEAKER:**  
> "BullRun turns every trader into a disciplined, educated options desk. Production-ready, deterministic, and built natively for Alpaca.  
> 
> Thank you, and welcome to the future of intelligent options trading."

---

### Demo Checklist Before Recording:
1. Ensure FastAPI backend is running (`python3 api.py`).
2. Ensure Next.js dashboard is running (`npm run dev` in `dashboard/`).
3. Verify Alpaca Paper API keys are configured in `.env`.
4. Open `http://localhost:3000` in fullscreen browser with dark mode.
5. Have terminal open side-by-side with rich terminal formatting.
