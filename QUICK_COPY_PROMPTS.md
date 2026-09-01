# Quick Copy Prompts — One per AI

Copy the relevant section and paste into each AI.

---

## CLAUDE → Risk Engine + Monitor Hardening

```
Working on BullRun (HACKATHON 2/bullrun/). Read agents/risk_engine.py and monitor.py. 

Add to risk_engine.py:
1. Position sizing by conviction (higher score = larger position, within 2% rule)
2. Correlation check (reject if correlated with existing positions)
3. Time-of-day guard (no trades first/last 30 min)
4. Earnings check (avoid if earnings within 5 DTE)

Add to monitor.py:
1. Real P&L from Alpaca API (not time heuristics)
2. Greeks-based exit (close if delta < 0.1)
3. Volatility exit (close if IV spikes > 20%)
4. Partial profit taking (close 50% at +30%)

Test: python -m py_compile <file>
```

---

## GEMINI → Dashboard UI/UX

```
Working on BullRun dashboard (HACKATHON 2/bullrun/dashboard/). Read src/app/globals.css and src/app/page.tsx.

Make it look like a $10M hedge fund terminal:
1. Add smooth animations (fade-in, slide-up, pulse)
2. Add glass morphism (backdrop-filter blur)
3. Add Inter font from Google Fonts
4. Add gradient backgrounds for metrics
5. Add hover glow effects
6. Add mobile responsive breakpoints
7. Create src/components/TeachingPanel.tsx for learning features

Test: npm run build
```

---

## CHATGPT → Teaching Engine + Write-up

```
Working on BullRun (HACKATHON 2/bullrun/). Read teaching_engine.py and trade_card.py.

Upgrade teaching_engine.py:
1. Add "Why This Matters" (connect to real events)
2. Add historical context (similar past trades)
3. Add options glossary (delta, theta, gamma, IV)
4. Add progressive complexity (more detail as user advances)

Write SUBMISSION.md (one-page hackathon write-up):
- Title: BullRun — Teaching Quantitative Trading to Beginners
- 3 paragraphs: AI logic, risk gates, teaching layer
- End with: "This isn't just a trading bot. It's a trading school."

Write DEMO_SCRIPT.md (2-minute video script).

Test: python -m py_compile teaching_engine.py
```

---

## CODEX → Execution + Monitoring

```
Working on BullRun (HACKATHON 2/bullrun/). Read execution.py and monitor.py.

Upgrade execution.py:
1. Multi-leg order support (verify both legs fill)
2. Order status polling with timeout
3. Paper trading mode flag
4. Error handling (insufficient funds, market closed)
5. Logging to audit trail

Upgrade monitor.py:
1. Real P&L from Alpaca positions API
2. Greeks tracking (delta, theta, gamma)
3. End-of-day summary
4. Alert when stop loss approaching (within 10%)

Test: python -m py_compile execution.py monitor.py
```

---

## KIMI → Research

```
Help me research for BullRun hackathon project (AI options trading agent that teaches beginners).

Research:
1. Top 3 winning hackathon trading projects (features, presentation style)
2. Alpaca API best practices (common mistakes, paper trading edge cases)
3. Options trading education (what beginners get wrong, how pros explain)
4. Competitor analysis (other submissions to this hackathon)

Save findings as RESEARCH.md with actionable recommendations.
```

---

## SAKANA AI → Demo Strategy

```
Help me create the most memorable demo for BullRun (AI trading agent that TEACHES beginners).

Design:
1. Hook in first 10 seconds
2. "Wow moment" judges remember
3. Visual identity (logo, colors, tagline)
4. Presentation narrative (story arc)
5. Social media campaign (5 posts for X/LinkedIn)

Save as DEMO_STRATEGY.md
```

---

## PERPLEXITY → Documentation

```
Document BullRun (HACKATHON 2/bullrun/). Read all Python files and dashboard.

Write:
1. API_DOCS.md (REST endpoints, WebSocket, errors)
2. ARCHITECTURE.md (system diagram, data flow, decision tree)
3. DEPLOYMENT.md (local setup, cloud deploy, troubleshooting)
4. CONTRIBUTING.md (code style, adding features, tests)

Make it clear and beginner-friendly.
```

---

## 🚀 LAUNCH SEQUENCE

1. Open 7 browser tabs (one per AI)
2. Paste the corresponding prompt into each
3. Wait for all to complete (15-30 min)
4. Tell me when done — I'll integrate everything
5. Final test + push to GitHub
