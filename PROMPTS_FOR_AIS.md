# BullRun — AI Task Assignments

Each AI works on a DIFFERENT component. Do NOT overlap.

---

## 🧠 CLAUDE (Architecture + Risk Hardening)

**Paste this prompt:**

```
You are working on "BullRun" — an AI options trading agent for a hackathon. 
The project is at HACKATHON 2/bullrun/.

YOUR MISSION: Harden the risk engine and monitor for production.

1. Read these files first:
   - config.py (risk constants)
   - agents/risk_engine.py (8 deterministic gates)
   - monitor.py (position tracking + auto-exit)
   - execution.py (Alpaca order placement)

2. UPGRADE the risk engine to add:
   - Position sizing based on conviction score (higher conviction = larger position, but always within 2% rule)
   - Correlation check: reject if opening a position correlated with existing ones
   - Time-of-day guard: no new trades in first/last 30 min of market (volatility spike)
   - Earnings awareness: check if underlying has earnings within 5 DTE (avoid)
   
3. UPGRADE the monitor to add:
   - Real-time P&L from Alpaca API (not time heuristics)
   - Greeks-based exit: close if delta drops below 0.1 (position dying)
   - Volatility exit: close if IV spikes > 20% from entry (regime change)
   - Partial profit taking: close 50% at +30%, let rest run with trailing stop

4. UPGRADE execution.py to add:
   - Retry logic with exponential backoff for API failures
   - Order validation before submission (verify Greeks, price, quantity)
   - Fallback to market order if limit order doesn't fill in 30 seconds

Test your changes compile: python -m py_compile <file>
```

---

## 🎨 GEMINI (Dashboard UI/UX)

**Paste this prompt:**

```
You are working on "BullRun" — an AI options trading dashboard built with Next.js + TradingView.
The project is at HACKATHON 2/bullrun/dashboard/.

YOUR MISSION: Make the dashboard look like a $10M hedge fund terminal.

1. Read these files first:
   - src/app/globals.css (current styles)
   - src/app/page.tsx (main dashboard)
   - src/components/Chart.tsx (TradingView chart)
   - src/components/TradeCard.tsx (trade proposal card)

2. UPGRADE globals.css to add:
   - Smooth animations (fade-in, slide-up, pulse effects)
   - Glass morphism effects (backdrop-filter blur)
   - Better typography (use Inter font from Google Fonts)
   - Gradient backgrounds for metric boxes
   - Hover states with subtle glow effects
   - Mobile responsive breakpoints (sm, md, lg, xl)
   - Dark mode improvements (better contrast, eye strain reduction)
   - Custom scrollbar styling
   - Loading skeleton animations

3. UPGRADE TradeCard.tsx to add:
   - Animated risk check badges (green/red with icons)
   - Progress bar for conviction score
   - Collapsible "Learn More" section with strategy explainer
   - Visual risk/reward ratio meter
   - Approval confirmation animation (green checkmark pulse)

4. UPGRADE page.tsx to add:
   - Smooth transitions between states
   - Real-time price ticker in header
   - Mini portfolio sparkline chart
   - Teaching layer panel (shows regime lessons, learning progress)
   - Better empty states (scanning animation)
   - Mobile hamburger menu

5. Add new component: src/components/TeachingPanel.tsx
   - Shows regime lesson (why Scout says BULLISH/BEARISH)
   - Shows strategy explainer (what spread means)
   - Shows learning progress (Beginner → Advanced)
   - Shows trade journal entries

Test: npm run build
```

---

## 📝 CHATGPT (Teaching Engine + Documentation)

**Paste this prompt:**

```
You are working on "BullRun" — an AI options trading agent with a teaching layer.
The project is at HACKATHON 2/bullrun/.

YOUR MISSION: Make the teaching engine world-class and write the submission write-up.

1. Read these files first:
   - teaching_engine.py (current teaching logic)
   - trade_card.py (terminal trade cards)
   - orchestrator.py (pipeline coordinator)

2. UPGRADE teaching_engine.py to add:
   - "Why This Matters" section: connect each trade to real-world events (Fed meeting, earnings, etc.)
   - Historical context: "Similar setups in the past 30 days resulted in X% win rate"
   - Risk education: explain each risk gate in beginner terms
   - Options glossary: definitions of delta, theta, gamma, IV, spreads, etc.
   - Progressive complexity: show more detail as user level increases
   - Trade comparison: "This trade is similar to trade #5 which gained $XXX"

3. UPGRADE trade_card.py to add:
   - "Learn More" expandable section with strategy details
   - Risk meter visual (green/yellow/red gauge)
   - Conviction score breakdown visualization
   - Historical performance comparison
   - "What if I'm wrong?" section with max loss explanation

4. WRITE the one-page hackathon submission (save as SUBMISSION.md):
   - Title: BullRun — Teaching Quantitative Trading to Beginners
   - 3 paragraphs max
   - Focus on: AI logic, risk gates, Alpaca infrastructure, teaching layer
   - End with: "This isn't just a trading bot. It's a trading school."
   - Make it sound like a Jane Street recruiter would be impressed

5. WRITE a 2-minute demo script (save as DEMO_SCRIPT.md):
   - Opening hook (10 seconds)
   - Show the problem (20 seconds): "Most trading bots are black boxes"
   - Show the solution (60 seconds): live demo of BullRun
   - Show the teaching moment (20 seconds): explain a rejected trade
   - Closing impact (10 seconds): "By day 5, you're not just watching the AI"

Test: python -m py_compile teaching_engine.py trade_card.py
```

---

## 🔧 CODEX (Execution + Monitoring)

**Paste this prompt:**

```
You are working on "BullRun" — an AI options trading agent for a hackathon.
The project is at HACKATHON 2/bullrun/.

YOUR MISSION: Make the execution and monitoring bulletproof.

1. Read these files first:
   - execution.py (Alpaca order placement)
   - monitor.py (position tracking)
   - agents/data_service.py (Alpaca data layer)
   - config.py (risk constants)

2. UPGRADE execution.py to add:
   - Multi-leg order support (verify both legs fill together)
   - Order status polling with timeout (cancel if not filled in 60s)
   - Paper trading mode flag (DRY_RUN vs LIVE)
   - Order confirmation receipt (order ID, fill price, timestamp)
   - Error handling for: insufficient funds, market closed, invalid symbol
   - Logging every order attempt to audit trail

3. UPGRADE monitor.py to add:
   - Real-time P&L calculation using Alpaca positions API
   - Position Greeks tracking (delta, theta, gamma exposure)
   - Automated rebalancing: if delta > 0.7, suggest rolling up
   - End-of-day summary: total P&L, best/worst trade, risk used
   - Alert system: notify when stop loss is approaching (within 10%)

4. UPGRADE agents/data_service.py to add:
   - Caching: don't re-fetch data within 5 minutes
   - Rate limiting: respect Alpaca API limits
   - Fallback chain: Alpaca → cached → error (never crash)
   - Historical data batching (efficient backtesting)

5. Add new file: monitor_dashboard.py
   - Rich terminal dashboard showing:
     - Open positions with live P&L
     - Risk usage meter (how much of $6K exposure used)
     - Today's P&L chart
     - Next scan countdown
     - Recent exits with reasons

Test: python -m py_compile execution.py monitor.py agents/data_service.py
```

---

## 🔍 KIMI (Research + Competitive Analysis)

**Paste this prompt:**

```
You are helping "BullRun" — an AI options trading agent for a hackathon.
The project is at HACKATHON 2/bullrun/.

YOUR MISSION: Research what winning hackathon projects do and find our competitive edge.

1. Read the README.md to understand the project

2. RESEARCH these topics:
   - What are the top 3 hackathon-winning trading projects in the last year?
   - What features do they have that we don't?
   - What presentation style won over judges?
   - What's the most impressive demo format?

3. RESEARCH Alpaca best practices:
   - What are the most common API mistakes?
   - What's the best way to handle paper trading edge cases?
   - What do judges look for in Alpaca integration quality?

4. RESEARCH options trading education:
   - What's the #1 thing beginners get wrong about options?
   - How do professional traders explain spreads to clients?
   - What's the best way to visualize risk/reward?

5. RESEARCH the competition:
   - Look at other submissions to this hackathon
   - What are their strengths/weaknesses?
   - How can we differentiate?

Save your findings as RESEARCH.md with actionable recommendations.
```

---

## 🎭 SAKANA AI (Creative + Demo Strategy)

**Paste this prompt:**

```
You are helping "BullRun" — an AI options trading agent that TEACHES beginners.
The project is at HACKATHON 2/bullrun/.

YOUR MISSION: Create the most memorable demo in hackathon history.

1. Read README.md to understand the project

2. DESIGN a demo strategy that will blow judges away:
   - What's the hook in the first 10 seconds?
   - What's the "wow moment" they'll remember?
   - How do we show the teaching layer in action?
   - What's the emotional arc of the demo?

3. CREATE a visual identity:
   - Color scheme (beyond just dark mode)
   - Logo concept (bull + something)
   - Tagline options (5 variations)
   - Social media post templates (X, LinkedIn)

4. DESIGN the presentation narrative:
   - Opening story (personal connection to trading)
   - Problem statement (black box bots are dangerous)
   - Solution reveal (BullRun shows its work)
   - Live demo flow
   - Impact statement (teaching > automation)
   - Closing: "This isn't just a trading bot"

5. PLAN the social media campaign:
   - 5 posts across X/LinkedIn during the hackathon
   - Each post has: hook, value, CTA
   - Tag @lablabai and @AlpacaHQ
   - Best times to post
   - Hashtag strategy

Save as DEMO_STRATEGY.md
```

---

## 🌐 PERPLEXITY (Technical Documentation)

**Paste this prompt:**

```
You are documenting "BullRun" — an AI options trading agent for a hackathon.
The project is at HACKATHON 2/bullrun/.

YOUR MISSION: Create world-class technical documentation.

1. Read these files:
   - README.md
   - config.py
   - requirements.txt
   - All files in agents/

2. WRITE API documentation (save as API_DOCS.md):
   - All REST endpoints with request/response examples
   - WebSocket message formats
   - Error codes and handling
   - Authentication (none needed for local)

3. WRITE architecture documentation (save as ARCHITECTURE.md):
   - System diagram (ASCII art)
   - Data flow through the pipeline
   - Decision tree for trade proposals
   - Risk engine logic flow
   - Teaching engine architecture

4. WRITE deployment guide (save as DEPLOYMENT.md):
   - How to run locally
   - How to deploy to cloud (AWS/GCP/Vercel)
   - Environment variables reference
   - Troubleshooting common issues

5. WRITE contributing guide (save as CONTRIBUTING.md):
   - Code style requirements
   - How to add a new risk gate
   - How to add a new teaching feature
   - How to run tests

Make all documentation clear, concise, and beginner-friendly.
```

---

## 📋 EXECUTION ORDER

1. **Start all 7 AIs simultaneously** (different tabs/windows)
2. **Wait for all to complete** (15-30 minutes)
3. **I'll integrate everything** (read all outputs, merge, test, push)
4. **Final verification** (all tests pass, build clean)
5. **Push to GitHub** (final version)

## ⚠️ IMPORTANT RULES

- Each AI works on ONLY their assigned files
- Do NOT modify files outside your assignment
- Test your changes before submitting
- Save all outputs as .md files for review
