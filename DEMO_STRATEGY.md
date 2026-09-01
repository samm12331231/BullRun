# BullRun — Brand Identity & Demo Strategy

> **AI options trading that teaches before it trades.**
>
> **Core principle:** The AI handles the complexity. The human handles the consent.

**Repository:** https://github.com/samm12331231/BullRun  
**Hackathon:** Alpaca AI Trading Agents Hackathon · August 28–September 4, 2026  
**Current campaign window:** September 1–4, 2026  
**Judging priorities from the project brief:** P&L performance · technology implementation · creativity · presentation quality

> **Prize-pool verification:** The supplied brief says **$6,300**, but the official lablab event page displayed **$6,000** on September 1, 2026. Use **$6,000** in public-facing copy unless the organizers directly confirm a different amount.

---

# 1. Brand Strategy

## Brand Positioning

BullRun is not "an AI that gambles for you." It is an **accountable trading mentor**:

- Deterministic code decides whether a trade is safe enough to propose.
- The AI translates the evidence into plain English.
- The human explicitly approves or rejects the entry.
- Every completed trade becomes a lesson, including losing trades and rejected setups.

### The memorable contrast

> **Other agents hide the decision. BullRun teaches the decision.**

The product should feel calm, precise, and educational—not like a casino, meme coin, or "get rich quick" app.

---

## 1.1 Logo Concept — "The Open-Book Bull"

### Primary concept

Create a compact mark where an **open book becomes a bull**:

- The two rising pages form the bull's horns.
- The center book seam becomes a single candlestick.
- A small page corner forms a checkmark, representing human approval.
- The silhouette feels like a bull charging upward, but the foundation is visibly a book.

This combines all three parts of BullRun in one symbol:

1. **Bull:** markets and forward motion.
2. **Book:** teaching and retained knowledge.
3. **Checkmark:** consent and accountable execution.

### Why it is stronger than a bull head

A bull head says only "finance." The open book changes the meaning to **"market knowledge."** The checkmark prevents the brand from implying blind automation.

### Construction rules

- Use a geometric, symmetrical silhouette.
- It must remain recognizable at 24 px.
- Avoid detailed eyes, fur, coins, flames, or Wall Street clichés.
- Use one-color versions for terminal screenshots and GitHub badges.
- In the full-color mark, make the book/candlestick accent amber and the approval check green.

### Wordmark

Use **Space Grotesk, Inter Tight, or Sora** in a bold weight:

- `Bull` in Cloud or Deep Ink.
- `Run` in Bull Green.
- Tight spacing, slightly rounded corners, no italics.

### Optional animated version

For the video intro, the book opens, its pages rise into horns, and the center seam becomes a green candlestick. The animation should take less than one second.

---

## 1.2 Color Palette

| Role | Color | Hex | Purpose |
|---|---|---:|---|
| **Primary** | Deep Ink | `#091A2F` | Main background, trust, technical depth |
| **Primary surface** | Midnight Slate | `#142B47` | Cards, terminal panels, architecture blocks |
| **Secondary** | Bull Green | `#18C98B` | Approved states, gains, primary CTA |
| **Secondary dark** | Market Emerald | `#0D9E6C` | Hover states, borders, gradients |
| **Teaching accent** | Lesson Amber | `#FFB547` | Explanations, lessons, glossary, journal |
| **Risk accent** | Guardrail Coral | `#FF647C` | Rejections, failed checks, bounded-risk warnings |
| **Light neutral** | Cloud | `#F4F7FB` | Primary text on dark backgrounds |
| **Muted neutral** | Steel Mist | `#8FA0B5` | Secondary text, metadata, inactive states |

### Semantic color rule

Color should communicate product logic consistently:

- **Amber = learning.** Every explanation, lesson, glossary term, and journal insight uses amber.
- **Green = approved or positive.** Do not use green merely as decoration.
- **Coral = blocked or risky.** A rejected trade is a successful safety outcome, not a product failure.
- **Navy = evidence and system logic.** Architecture, metrics, and deterministic checks live on navy surfaces.

This creates an instant visual language judges can understand without narration.

---

## 1.3 Taglines — Under Eight Words

1. **The AI trades. You learn. You approve.**
2. **Every trade explained before it happens.**
3. **Options intelligence, with a human in control.**
4. **Learn the trade before approving it.**
5. **Complexity automated. Decisions understood. Consent required.**

### Recommended hierarchy

- **Primary tagline:** "The AI trades. You learn. You approve."
- **Philosophy line:** "The AI handles the complexity. The human handles the consent."
- **Technical proof line:** "The LLM explains. Deterministic code decides."

---

## 1.4 Visual Identity

### GitHub README banner — 1280 × 640

Build the banner around one unmistakable product story rather than a generic chart.

#### Layout

**Left 42%**

- Open-Book Bull logo.
- `BullRun` wordmark.
- Primary tagline.
- Small line: **"Defined-risk SPY options spreads · deterministic risk gates · explicit consent."**

**Right 58%**

Show the actual three-part product interface:

1. **Evidence:** market regime and conviction score.
2. **Lesson:** amber plain-English explanation of the spread.
3. **Consent:** Approve and Reject controls, with exact maximum loss visible.

Across the top of the screenshot, include a small badge:

> **LLM explains · code validates · human authorizes**

#### Background treatment

- Deep Ink to Midnight Slate gradient.
- A very subtle options payoff curve behind the interface—not a decorative stock chart.
- One amber line connects Evidence → Lesson.
- One green line connects Lesson → Consent.

#### README badges

Keep badges focused and credible:

- Powered by Alpaca
- Defined-Risk Options
- Human Consent Required
- Deterministic Risk Engine
- Paper Trading Demo
- MIT License

Do not use a P&L badge unless it is generated from a reproducible result file.

### Demo video thumbnail — 1280 × 720

Show the **wow frame**, not a presenter headshot:

- Left: six risk checks with visible PASS/REJECT states.
- Center: amber card titled **"WHAT THIS MEANS"** with a one-sentence lesson.
- Right: the consent gate with exact maximum loss and **APPROVE / REJECT**.
- Large overlay: **"AI THAT SHOWS ITS WORK"**
- Small corner badge: **"2-MIN DEMO"**
- Logo in the upper-left corner.

If real paper-trading results are available, add a small evidence strip—period, trade count, realized P&L, and max drawdown. Never show an unexplained "+$X" number.

---

# 2. Demo Strategy

## The Two-Minute Thesis

The video is not primarily about generating a trade. Many agents can do that. The demo must prove four things:

1. BullRun understands the market context.
2. Deterministic safeguards—not an LLM—control risk eligibility.
3. A beginner can understand the proposed trade.
4. No entry reaches Alpaca without explicit consent.

---

## 2.1 Opening Hook — First 10 Seconds

> **"Most trading agents ask for your money before they earn your trust. BullRun shows its work—and waits for your permission."**

### Visual sequence

- **0:00–0:02:** animated Open-Book Bull logo.
- **0:02–0:05:** confusing raw options chain flashes on screen.
- **0:05–0:10:** it resolves into BullRun's simple Evidence → Lesson → Consent interface.

Do not open with team introductions, the hackathon name, installation steps, or a long market statistic.

---

## 2.2 The "Wow Moment"

### The frame judges should screenshot

At approximately **0:52**, freeze briefly on one screen containing:

- **6/6 deterministic risk checks** with their thresholds.
- The proposed SPY bull call or bear put spread.
- Exact **maximum profit, maximum loss, expiration, and account risk percentage**.
- An amber lesson explaining both option legs in beginner language.
- A badge reading **"LLM CANNOT PLACE ORDERS."**
- The human **APPROVE / REJECT** consent gate.

### The narration

> **"The model can explain this trade, but it cannot approve it, relax a risk limit, or place the order. Code enforces the rules. The human gives consent."**

Then show one safety rejection before the valid trade:

- A liquidity or max-loss check fails.
- The Approve button disappears or becomes disabled.
- BullRun explains why "no trade" protects the user.

This is more memorable than showing only a successful order because it proves the guardrails are real.

---

## 2.3 Emotional Arc

| Time | Desired feeling | What happens |
|---:|---|---|
| **0:10** | **Recognition:** "Options are intimidating." | Raw market complexity becomes one clear proposal flow. |
| **0:30** | **Credibility:** "This is real engineering, not an LLM wrapper." | Scout, Quant, deterministic Risk Engine, CIO explainer, and Alpaca execution path appear. |
| **1:00** | **Trust:** "The system can stop itself." | A failed setup is rejected; the explanation teaches why waiting matters. |
| **1:30** | **Agency:** "I understand the trade and control the decision." | Valid trade card shows bounded outcomes; human explicitly approves. |
| **2:00** | **Empowerment:** "I would become a better trader using this." | Alpaca paper order confirmation, results dashboard, learning progress, and trade journal close the loop. |

---

## 2.4 Shot-by-Shot Storyboard

### 0:00–0:10 — The problem and promise

Deliver the hook. Transform the complex options chain into the BullRun interface.

### 0:10–0:28 — Architecture without the lecture

Animate this pipeline:

`Scout → Quant → Risk Engine → CIO → Trade Card → Consent → Alpaca → Monitor`

Highlight one critical distinction:

> **"The LLM is not in the decision path. It translates the evidence."**

Keep code on screen for no more than two seconds at a time. Show filenames or tests as proof, not as the main story.

### 0:28–0:48 — Teach the market regime

Show a real Scout result and open **"Why Scout says BULLISH/BEARISH/NEUTRAL."**

The teaching card should translate ADX, RSI, moving averages, and volatility into one clear conclusion. Use the amber highlight system.

### 0:48–1:05 — Prove the safety layer

Run a setup that fails one deterministic check. Show:

- The failed threshold.
- The rejected status.
- The rejection explainer.
- No consent button and no Alpaca order.

Narration:

> **"BullRun also teaches when not to trade."**

### 1:05–1:28 — The wow frame and consent

Run a valid defined-risk spread. Show all checks, spread anatomy, bounded outcome, and account-risk percentage on the same screen. Pause long enough for the viewer to read the maximum-loss sentence.

The human clicks **Approve** only after the explanation.

### 1:28–1:42 — Alpaca execution proof

Show:

- Paper-trading label.
- Alpaca order submission.
- Order ID and status.
- Audit-log entry.

Avoid editing that makes a simulated or prerecorded result look live. Label everything accurately.

### 1:42–1:54 — P&L and learning proof

Show two linked dashboards:

**Performance evidence**

- Evaluation period.
- Number of closed trades.
- Realized P&L.
- Win rate.
- Maximum drawdown.
- Average return per trade.
- SPY or no-trade benchmark where appropriate.

**Learning evidence**

- Beginner/Intermediate/Advanced progress.
- Concepts explored.
- Predicted-versus-actual trade journal.
- Lesson from a profitable, losing, or flat trade.

The important message: the system does not rewrite a loss as success. It explains what happened and whether the planned risk boundary held.

### 1:54–2:00 — Close

Return to the Open-Book Bull, tagline, repository, and hackathon marks. Hold the final frame for at least two seconds.

---

## 2.5 How to Show the Teaching Layer

Use features already aligned with the repository rather than inventing a chatbot overlay.

### A. Teach before the decision

Open the **regime lesson** and **strategy explainer** beside the proposed trade. Explain:

- Why the market received its current classification.
- What the long option does.
- What the short option does.
- Why the spread caps both cost and upside.
- The exact planned maximum loss.

### B. Teach through rejection

The **rejection explainer** is a major differentiator. Most trading demos hide "no trade" outcomes. BullRun should celebrate them:

> **"Waiting is a decision backed by evidence."**

Show one failed check and explain the damage it prevents.

### C. Teach after the outcome

Show the **predicted-versus-actual journal** after a trade closes:

- What BullRun expected.
- What actually happened.
- Why the exit occurred.
- What the beginner should retain.

### D. Show learner progress

Use the existing Beginner → Intermediate → Advanced progression as a small, persistent indicator. This makes learning measurable instead of merely claimed.

### E. Optional stretch feature

If there is implementation time, add one comprehension check before consent:

> **"What is the most you can lose?"**

The answer must already be visible in the trade card. This should never become a dark pattern or block accessibility; it is a teaching reinforcement, not a test of worthiness.

---

## 2.6 P&L Presentation Rules

Because performance is a judging criterion, present it rigorously:

- Prefer a reproducible paper-trading or backtest report over one cherry-picked winner.
- State the exact start/end dates and whether results are paper, historical, or live.
- Include trade count; a return without sample size is weak evidence.
- Show maximum drawdown and losses, not only gross profit.
- Separate realized P&L from open-position P&L.
- Include transaction-cost/slippage assumptions if using a backtest.
- Keep the demo's claim proportional to the evidence.

### Recommended performance slide title

> **"Did it make money—and what risk did it take?"**

---

## 2.7 Closing Line

> **"A trading agent should leave you with more than a position. It should leave you a better trader."**

Then display:

> **BullRun — The AI trades. You learn. You approve.**

---

# 3. Social Campaign

## Campaign Principle

Do not make five versions of "we built a bot." Each post should prove a different judging dimension:

1. Creativity and brand.
2. Technical implementation.
3. Teaching and consent.
4. Performance evidence.
5. Presentation and submission.

Every post must tag **@lablabai** and **@AlpacaHQ**.

Because the current date is **Tuesday, September 1, 2026**, the actionable schedule below covers the remaining hackathon window through **Friday, September 4, 2026**.

---

## Post 1 — Brand Reveal

**Channel/time:** X · Tuesday, September 1 · **9:00 AM ET**; LinkedIn · **1:00 PM ET**

> If the morning X slot has already passed, publish immediately rather than waiting a full day.

### Hook

> Most trading agents hide the decision. BullRun teaches it. 🐂📖

### Value proposition

> BullRun is an AI options trading agent for beginners. Deterministic code checks the risk, the AI explains the evidence in plain English, and the human approves every entry before it reaches Alpaca.
>
> The AI handles the complexity. The human handles the consent.
>
> Building for the @AlpacaHQ AI Trading Agents Hackathon with @lablabai.

### CTA

> Follow the build and tell us: what would an AI need to explain before you trusted it with a trade?

**Creative:** Logo animation or README hero image.  
**X tags:** `#BullRun`  
**LinkedIn tags:** `#AITrading #ExplainableAI #Fintech`

---

## Post 2 — Technical Proof

**Channel/time:** X · Wednesday, September 2 · **10:00 AM ET**  
**LinkedIn version:** Wednesday · **4:00 PM ET**

### Hook

> The most important technical decision in BullRun: the LLM cannot decide whether a trade is safe.

### Value proposition

> Scout identifies the SPY market regime. Quant constructs a defined-risk spread. Six deterministic checks decide PASS or REJECT. Only then does the model translate the evidence into beginner-friendly language.
>
> The LLM cannot change a threshold, override a rejection, or place an order. Entries still require explicit human consent.
>
> Built with @AlpacaHQ for the @lablabai hackathon.

### CTA

> Review the architecture in the repo. What additional risk gate would you add?

**Creative:** Animated architecture diagram ending at the consent gate.  
**X tags:** `#BullRun`  
**LinkedIn tags:** `#AIAgents #AlgorithmicTrading #ResponsibleAI`

---

## Post 3 — The Teaching "Wow" Clip

**Channel/time:** X · Thursday, September 3 · **9:00 AM ET**  
**LinkedIn reuse:** Thursday · **3:00 PM ET**

### Hook

> A beginner should never have to approve a trade they cannot explain.

### Value proposition

> BullRun turns a SPY options spread into four things you can understand: the thesis, both option legs, the best possible outcome, and the exact maximum loss.
>
> Then it stops and asks for consent.
>
> @AlpacaHQ execution comes after understanding—not before. Built for @lablabai.

### CTA

> Watch this 12-second clip. Could you explain the trade back after seeing it once?

**Creative:** Silent, captioned clip: risk checks → amber lesson → Approve/Reject.  
**X tags:** `#BullRun #ExplainableAI`  
**LinkedIn tags:** `#OptionsTrading #FinancialEducation #HumanInTheLoop`

---

## Post 4 — Performance Without Hype

**Channel/time:** X · Thursday, September 3 · **11:00 AM ET**; LinkedIn · **4:00 PM ET**

### Hook

> A P&L number without its risk is marketing, not evidence.

### Value proposition

> Here is BullRun's paper-trading report: evaluation period, closed trades, realized P&L, win rate, maximum drawdown, and the risk taken per position.
>
> We also show rejected trades and losing trades—because the goal is accountable performance, not a cherry-picked screenshot.
>
> Built on @AlpacaHQ for the @lablabai AI Trading Agents Hackathon.

### CTA

> Inspect the results and assumptions in the repo. What metric should we add before final submission?

**Creative:** Clean results card with exact dates, sample size, P&L, and drawdown. Replace this post with a build-progress post if the sample is not yet credible.  
**X tags:** `#BullRun`  
**LinkedIn tags:** `#QuantTrading #RiskManagement #BuildInPublic`

---

## Post 5 — Final Submission

**Channel/time:** X · Friday, September 4 · **10:00 AM ET**; LinkedIn · **3:00 PM ET**, or immediately after the public submission is live

### Hook

> A trading agent should leave you with more than a position. It should leave you a better trader.

### Value proposition

> BullRun is our submission to the @AlpacaHQ AI Trading Agents Hackathon with @lablabai:
>
> ✓ Defined-risk SPY options spreads  
> ✓ Six deterministic risk gates  
> ✓ Plain-English lessons  
> ✓ Explicit human consent  
> ✓ Alpaca paper execution and audit trail  
> ✓ Predicted-versus-actual learning journal

### CTA

> Watch the two-minute demo, inspect the code, and star the repository if accountable AI trading should be the standard.

**Creative:** Demo thumbnail plus a 15-second highlight clip in the first reply/comment.  
**X tags:** `#BullRun #AIAgents`  
**LinkedIn tags:** `#AITrading #ExplainableAI #Alpaca`

---

## 3.1 Best Posting Times

Use these as starting windows, then prioritize moments when the team can reply for the first 30–60 minutes.

### X

- A 2026 Buffer analysis of 8.7 million posts found **Tuesday at 9:00 AM** strongest, followed by **Wednesday at 9:00–10:00 AM**, with weekday **9:00–11:00 AM local time** the most reliable window.
- For this US fintech/developer campaign, use **ET** as the scheduling reference and prioritize Tuesday–Thursday mornings.
- Friday is normally weaker, but the submission announcement should still publish promptly when the entry is live.
- Reply quickly with the repo, technical detail, and demo clip rather than putting several competing links in the main post.

### LinkedIn

- Current studies disagree on one universal hour. Buffer's 2026 analysis favors **late afternoon**, especially Wednesday at 4:00 PM; Sprout Social reports broad strength from **11:00 AM–5:00 PM Tuesday–Thursday**.
- For BullRun, test **3:00–4:00 PM ET** for the strongest visual/proof posts, while using midday when coordinating with the hackathon community.
- Post from a founder/builder's personal profile first; have teammates add substantive comments, not generic applause.
- Avoid publishing two major LinkedIn posts close together; leave several hours between campaign updates.

### What matters more than the exact minute

- A clear visual.
- A single message.
- Real replies during the first hour.
- Evidence rather than unsupported claims.
- Posting while the team is available to engage.

---

## 3.2 Hashtag Strategy

### X

Use **zero to two hashtags**. The required account tags already consume attention.

- Always seed: `#BullRun`
- Rotate one discovery tag only when relevant: `#ExplainableAI`, `#AIAgents`, or `#AITrading`
- Do not stack five or more hashtags.
- Keep `@lablabai` and `@AlpacaHQ` in natural sentences.

### LinkedIn

Use **three focused hashtags** at the end:

- Brand/event: `#BullRun` or `#Alpaca`
- Category: `#AITrading` or `#AIAgents`
- Differentiator: `#ExplainableAI`, `#FinancialEducation`, or `#HumanInTheLoop`

### Searchable vocabulary

Use these phrases naturally in body copy because judges and builders may search them without hashtags:

- AI trading agent
- Alpaca Trading API
- options trading
- deterministic risk engine
- explainable AI
- human consent
- defined-risk spread
- paper trading

---

# 4. Final Production Checklist

## Brand

- [ ] Open-Book Bull works in full color and one color.
- [ ] Amber is used only for learning moments.
- [ ] Green is used only for approved/positive states.
- [ ] README hero shows the real product, not a generic chart.
- [ ] All public prize references use the organizer-confirmed figure.

## Demo

- [ ] Opening hook lands within five seconds.
- [ ] Architecture explains that the LLM is outside the decision path.
- [ ] One rejected trade proves the risk gate works.
- [ ] Wow frame shows checks, lesson, bounded risk, and consent together.
- [ ] Alpaca paper status and order ID are visible.
- [ ] P&L includes dates, sample size, and drawdown.
- [ ] Teaching progress or trade journal closes the learning loop.
- [ ] Video is captioned and understandable without sound.
- [ ] Final frame remains visible for at least two seconds.

## Social

- [ ] Every post tags @lablabai and @AlpacaHQ.
- [ ] Every post has one clear CTA.
- [ ] Every post has a distinct proof point.
- [ ] Performance claims match published evidence.
- [ ] The team is available to respond after posting.

---

# 5. The One-Sentence Pitch

> **BullRun is an accountable AI options desk where deterministic code controls risk, AI explains every decision, and the human authorizes every trade—so beginners learn before they act.**

---

# 6. Verification Sources

Checked on **September 1, 2026**:

- **BullRun repository:** https://github.com/samm12331231/BullRun — architecture, six risk checks, defined-risk SPY spreads, consent gate, Alpaca execution, monitoring, and teaching components.
- **Official hackathon page:** https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon — August 28–September 4, 2026; currently lists a **$6,000 prize pool**.
- **Buffer X timing study:** https://buffer.com/resources/best-time-to-post-on-twitter-x/ — 2026 analysis of 8.7 million posts.
- **Buffer LinkedIn timing study:** https://buffer.com/resources/best-time-to-post-on-linkedin/ — 2026 analysis of 4.8 million posts.
- **Sprout Social LinkedIn timing study:** https://sproutsocial.com/insights/best-times-to-post-on-linkedin/ — 2026 engagement analysis; used as a second data point because optimal-hour studies differ.
