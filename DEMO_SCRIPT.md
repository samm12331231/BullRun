# BullRun — 2-Minute Hackathon Demo Script

### 0:00–0:10 — Opening hook
> **[VISUAL: BullRun dashboard; signal and trade card appear.]**
>
> **SPEAKER:** “What if an AI could find an options trade—and teach you exactly why it wants the trade before you approve it?”

### 0:10–0:30 — The problem
> **[VISUAL: Briefly show a conventional signal/bot view with no explanation, then cut back to BullRun.]**
>
> **SPEAKER:** “Most trading bots are black boxes: they output BUY or SELL, but hide the reasoning, the payoff, and the failure mode. For beginners, that makes sophisticated automation impossible to trust or learn from. BullRun takes the opposite approach: AI proposes, evidence decides, and humans authorize.”

### 0:30–1:30 — Live demo: signal → proposal → teaching → consent → execution
> **[VISUAL: Trigger a BullRun scan.]**
>
> **SPEAKER:** “First, Scout reads the market and classifies the regime. Here we have a bullish setup.”
>
> **[VISUAL: Show Quant proposal and conviction score.]**
>
> “Quant turns that signal into a defined-risk options spread. The conviction card breaks the score into six weighted factors—regime strength, momentum, options pricing, liquidity, risk/reward, and time alignment—so we can see what is actually driving the decision.”
>
> **[VISUAL: Open the teaching sections on the trade card.]**
>
> “Now the important part: BullRun teaches. ‘Why This Matters’ connects the setup to real market context. Historical Context compares similar journal trades when enough data exists. The glossary explains terms like delta, theta, gamma, and implied volatility in plain English. And the explanation adapts: beginners get intuition, intermediate users get Greeks, and advanced users get the full mechanics.”
>
> **[VISUAL: Show risk meter and “What if I’m wrong?” section.]**
>
> “Before approval, the risk meter makes maximum loss visible as a percentage of the account, while ‘What if I’m wrong?’ translates the worst case into one sentence: this is the most the defined-risk structure is designed to lose per contract.”
>
> **[VISUAL: Risk checks PASS, then consent prompt.]**
>
> “The Risk Engine independently enforces the hard limits. The human sees the complete proposal, understands it, and explicitly consents.”
>
> **[VISUAL: Click APPROVE; show Alpaca execution status.]**
>
> “Only then does BullRun execute through Alpaca. The position is handed to the monitor with pre-authorized exit rules.”

### 1:30–1:50 — The teaching moment: rejected trade
> **[VISUAL: Trigger a setup that fails a risk gate or has a neutral/volatile regime.]**
>
> **SPEAKER:** “Here is where BullRun really earns its teaching layer. This trade is rejected. Instead of silently disappearing, the system tells us exactly why: the market is too weak, volatility is too high, or a deterministic risk limit failed. The lesson is simple—passing on a trade is a decision too. We preserve capital for a setup with better evidence.”

### 1:50–2:00 — Closing impact line
> **[VISUAL: Full dashboard showing the teaching card, risk controls, and journal.]**
>
> **SPEAKER:** “BullRun doesn’t ask beginners to trust an AI. It lets them watch the reasoning, understand the risk, and learn from every decision. This isn’t just a trading bot. It’s a trading school.”