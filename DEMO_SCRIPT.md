# BullRun Demo Video Script (2:30-3:00 min)

## Recording Setup
- Screen: 1920x1080, browser full-screen on http://localhost:3000
- Terminal: visible in background showing Python backend logs
- Audio: voiceover narrating (or text overlays if no mic)

---

## Scene 1: Hook (0:00 - 0:20)

**Screen:** Show the dashboard loading with live SPY chart and metrics
**Narration:** "90% of beginners lose money on their first options trade. BullRun is an AI trading agent that teaches before it trades — every decision explained in plain English, every risk gate visible, every trade requiring your approval."

**Visual:** Dashboard loads, show real portfolio value ($100K), regime detection, live chart

---

## Scene 2: The Pipeline in Action (0:20 - 1:20)

**Step 1 — Scout (0:20-0:35)**
- Click "TRIGGER AI SCAN" button
- Show regime detection result (e.g., "BULLISH — ADX: 31.2")
- **Narration:** "Scout analyzes the market using ADX, EMA, RSI, and MACD to classify the regime."

**Step 2 — Quant (0:35-0:50)**
- Show trade proposal appearing: "Bull Call Spread on SPY"
- Show strikes, net debit, max profit, max loss
- **Narration:** "Quant selects a defined-risk spread — you can never lose more than the premium paid."

**Step 3 — Risk Engine (0:50-1:05)**
- Show the 12 risk gates checklist (all PASS in green)
- **Narration:** "The Risk Engine validates against 12 deterministic rules. The LLM cannot override these. The human cannot override these."

**Step 4 — CIO Thesis (1:05-1:20)**
- Show the plain-English thesis: "SPY is trending up. We're buying a call spread. Max gain: $330. Max loss: $670."
- **Narration:** "The CIO explains the trade in language anyone can understand."

---

## Scene 3: Human Consent (1:20 - 1:40)

**Screen:** Show the trade card with AUTHORIZE and REJECT buttons
**Action:** Click AUTHORIZE TRADE
**Narration:** "Nothing executes without your approval. The AI proposes. You decide."

**Visual:** Trade executes, show "TRADE AUTHORIZED & EXECUTED" confirmation

---

## Scene 4: Teaching Layer (1:40 - 2:10)

**Screen:** Click "Trading Academy" tab
**Action:** Show regime lesson, strategy explainer, risk gate explanations
**Narration:** "The teaching engine explains every decision. What is ADX? Why this spread? What could go wrong? Beginners learn by watching the system think."

**Visual:** Show learner progression (Beginner → Intermediate → Advanced)

---

## Scene 5: Audit Trail (2:10 - 2:25)

**Screen:** Show the audit trail section with SHA-256 hashes
**Narration:** "Every decision is hash-chained for tamper-evident audit. Signal → Proposal → Risk Check → Consent → Execution — immutable."

**Visual:** Show timeline dots with event labels and timestamps

---

## Scene 6: Close (2:25 - 2:40)

**Screen:** Pull back to full dashboard view
**Narration:** "BullRun: AI proposes. Evidence decides. Humans authorize. Built with Alpaca's Trading API, MCP server, and 12 deterministic risk gates."

**Visual:** Show the tagline on screen, end with BullRun logo/name

---

## Alternative: If Market is Closed (No Live Trade)

If you can't trigger a live scan, use the existing trade data from earlier:
1. Show the dashboard with real P&L from the Alpaca positions
2. Walk through the audit trail of a previously executed trade
3. Show the teaching engine explaining that trade
4. The story still works: "Here's a trade BullRun executed earlier today"

## Key Points to Hit
- [ ] Real Alpaca paper trading (not mock)
- [ ] 12 risk gates visible
- [ ] Plain-English thesis (teaching layer)
- [ ] Human consent gate
- [ ] SHA-256 audit trail
- [ ] Dashboard with live chart
