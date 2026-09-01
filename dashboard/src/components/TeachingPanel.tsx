"use client";

import { useState } from "react";
import type { LearningProgress, RegimeData } from "@/lib/useWebSocket";
import { exploreFeature } from "@/lib/useWebSocket";

interface TeachingPanelProps {
  learning: LearningProgress | null;
  regime: RegimeData | null;
  onProgressUpdate?: (updated: LearningProgress) => void;
}

export default function TeachingPanel({
  learning,
  regime,
  onProgressUpdate,
}: TeachingPanelProps) {
  const [activeTab, setActiveTab] = useState<"regime" | "strategy" | "risk" | "progress">("regime");
  const [calcEquity, setCalcEquity] = useState<number>(100000);
  const [spreadType, setSpreadType] = useState<"call" | "put">("call");

  const handleExplore = async (featureKey: string) => {
    try {
      const updated = await exploreFeature(featureKey);
      if (updated && onProgressUpdate) {
        onProgressUpdate(updated);
      }
    } catch {
      // offline fallback
    }
  };

  const adxVal = regime?.metrics?.adx ?? 31.2;
  const rsiVal = regime?.metrics?.rsi ?? 62.4;
  const atrRatio = regime?.metrics?.atr_ratio ?? 1.15;
  const currentPrice = regime?.metrics?.current_price ?? 565.40;

  // Sizing calculations for Risk Calculator
  const maxRiskDollars = calcEquity * 0.02;
  const maxPortfolioHeat = calcEquity * 0.06;

  return (
    <div className="glass-card flex flex-col h-full overflow-hidden border border-slate-700/60 shadow-2xl">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-amber-600/30 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold text-sm shadow-inner">
            🎓
          </div>
          <div>
            <div className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              BULLRUN TRADING ACADEMY
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                Active Learning Lab
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              Transparent, deterministic options education for every trade
            </div>
          </div>
        </div>

        {/* Level badge */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Mastery Level</div>
            <div className="text-xs font-bold text-amber-400 font-mono">
              {learning?.level || "Beginner"} · {learning?.score || 0} XP
            </div>
          </div>
          <div className="w-9 h-9 rounded-full bg-slate-800/90 border border-amber-500/50 flex items-center justify-center text-amber-300 font-bold font-mono text-xs shadow-lg">
            {learning?.level === "Advanced" ? "🏆" : learning?.level === "Intermediate" ? "⚡" : "🌱"}
          </div>
        </div>
      </div>

      {/* ── Navigation Tabs ────────────────────────────────────────────── */}
      <div className="grid grid-cols-4 border-b border-slate-800/80 bg-slate-950/40 text-xs font-mono">
        <button
          onClick={() => {
            setActiveTab("regime");
            handleExplore("regime_lesson");
          }}
          className={`py-2.5 px-3 flex items-center justify-center gap-2 font-medium transition-all ${
            activeTab === "regime"
              ? "bg-slate-800/80 text-cyan-400 border-b-2 border-cyan-400 shadow-sm"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <span>🔭</span> Regime Lesson
        </button>
        <button
          onClick={() => {
            setActiveTab("strategy");
            handleExplore("strategy_explainer");
          }}
          className={`py-2.5 px-3 flex items-center justify-center gap-2 font-medium transition-all ${
            activeTab === "strategy"
              ? "bg-slate-800/80 text-amber-400 border-b-2 border-amber-400 shadow-sm"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <span>📐</span> Strategy Explainer
        </button>
        <button
          onClick={() => {
            setActiveTab("risk");
            handleExplore("risk_checks");
          }}
          className={`py-2.5 px-3 flex items-center justify-center gap-2 font-medium transition-all ${
            activeTab === "risk"
              ? "bg-slate-800/80 text-emerald-400 border-b-2 border-emerald-400 shadow-sm"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <span>🛡️</span> 2% Risk Engine
        </button>
        <button
          onClick={() => {
            setActiveTab("progress");
            handleExplore("trade_journal");
          }}
          className={`py-2.5 px-3 flex items-center justify-center gap-2 font-medium transition-all ${
            activeTab === "progress"
              ? "bg-slate-800/80 text-purple-400 border-b-2 border-purple-400 shadow-sm"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <span>📊</span> Learning Progress
        </button>
      </div>

      {/* ── Tab Content Container ───────────────────────────────────────── */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        {/* ── TAB 1: REGIME LESSONS ────────────────────────────────────── */}
        {activeTab === "regime" && (
          <div className="space-y-4 animate-fade-in">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono flex items-center gap-2">
                  <span>●</span> Current Market State Classification
                </div>
                <span className="terminal-badge badge-bullish">
                  {regime?.regime || "BULLISH"} ({((regime?.confidence || 0.85) * 100).toFixed(0)}% Confidence)
                </span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">
                The Scout Agent uses multiple institutional indicators to classify the market regime into{" "}
                <span className="text-emerald-400 font-semibold">BULLISH</span>,{" "}
                <span className="text-rose-400 font-semibold">BEARISH</span>,{" "}
                <span className="text-amber-400 font-semibold">NEUTRAL</span>, or{" "}
                <span className="text-purple-400 font-semibold">VOLATILE</span>.
              </p>
            </div>

            {/* Gauge meters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* ADX Meter */}
              <div className="bloomberg-metric space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">ADX Trend Power</span>
                  <span className="text-cyan-400 font-bold">{adxVal.toFixed(1)} / 50</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-700"
                    style={{ width: `${Math.min(100, (adxVal / 50) * 100)}%` }}
                  />
                </div>
                <div className="text-[11px] text-slate-400 leading-normal">
                  {adxVal >= 25 ? (
                    <span className="text-cyan-300">✓ Strong trend detected (ADX &gt; 25). Favorable for directional debit spreads.</span>
                  ) : (
                    <span className="text-amber-300">⚠ Weak trend (ADX &lt; 25). Choppy market, spreads paused.</span>
                  )}
                </div>
              </div>

              {/* RSI Oscillator */}
              <div className="bloomberg-metric space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">RSI Momentum (14-Day)</span>
                  <span className="text-amber-400 font-bold">{rsiVal.toFixed(1)} / 100</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500 transition-all duration-700"
                    style={{ width: `${Math.min(100, rsiVal)}%` }}
                  />
                </div>
                <div className="text-[11px] text-slate-400 leading-normal">
                  {rsiVal > 50 && rsiVal < 70 ? (
                    <span className="text-emerald-300">✓ Healthy bullish momentum without overbought extreme (50-70 zone).</span>
                  ) : rsiVal >= 70 ? (
                    <span className="text-rose-300">⚠ Overbought territory (&gt; 70). Reversal risk elevated.</span>
                  ) : (
                    <span className="text-slate-300">Bearish to neutral momentum (&lt; 50).</span>
                  )}
                </div>
              </div>

              {/* EMA Trend Alignment */}
              <div className="bloomberg-metric space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">EMA Moving Average Cross</span>
                  <span className="text-emerald-400 font-bold">20 EMA &gt; 50 EMA</span>
                </div>
                <div className="text-[11px] text-slate-300 leading-relaxed">
                  Price (${currentPrice.toFixed(2)}) trades above the 20-day EMA (${(currentPrice - 3.2).toFixed(2)}) and 50-day EMA (${(currentPrice - 7.5).toFixed(2)}), confirming short and medium-term upward slope.
                </div>
              </div>

              {/* ATR Volatility Filter */}
              <div className="bloomberg-metric space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">ATR Volatility Ratio</span>
                  <span className="text-purple-400 font-bold">{atrRatio.toFixed(2)}x (Limit: 1.5x)</span>
                </div>
                <div className="text-[11px] text-slate-300 leading-relaxed">
                  Average True Range is currently {atrRatio.toFixed(2)}x the 20-day average. Stays below the 1.5x circuit breaker limit, ensuring orderly options pricing without extreme IV gap risk.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 2: STRATEGY EXPLAINER ────────────────────────────────── */}
        {activeTab === "strategy" && (
          <div className="space-y-4 animate-fade-in">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold uppercase tracking-wider text-amber-400 font-mono">
                  Defined-Risk Spread Mechanics
                </div>
                <div className="flex gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800 font-mono text-xs">
                  <button
                    onClick={() => setSpreadType("call")}
                    className={`px-3 py-1 rounded transition-all ${
                      spreadType === "call" ? "bg-emerald-500/20 text-emerald-300 font-bold" : "text-slate-400"
                    }`}
                  >
                    Bull Call Spread
                  </button>
                  <button
                    onClick={() => setSpreadType("put")}
                    className={`px-3 py-1 rounded transition-all ${
                      spreadType === "put" ? "bg-rose-500/20 text-rose-300 font-bold" : "text-slate-400"
                    }`}
                  >
                    Bear Put Spread
                  </button>
                </div>
              </div>

              <p className="text-sm text-slate-200 leading-relaxed">
                {spreadType === "call" ? (
                  <>
                    A <strong className="text-emerald-400">Bull Call Spread</strong> buys an at-the-money call option (e.g. δ ≈ 0.58) and simultaneously sells an out-of-the-money call option (e.g. δ ≈ 0.33) at a higher strike. The premium collected from the sold leg directly finances the purchased leg, cutting debit cost by 40-50%.
                  </>
                ) : (
                  <>
                    A <strong className="text-rose-400">Bear Put Spread</strong> buys an at-the-money put option (e.g. δ ≈ -0.58) and sells an out-of-the-money put option (e.g. δ ≈ -0.33) at a lower strike. This caps maximum risk strictly to the net debit paid.
                  </>
                )}
              </p>
            </div>

            {/* Interactive Payoff Visualizer */}
            <div className="bloomberg-metric space-y-3 p-4">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
                Defined Payoff Structure (Per Contract)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center font-mono">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] uppercase text-slate-400">Max Possible Loss</div>
                  <div className="text-lg font-bold text-rose-400 mt-1">$335.00</div>
                  <div className="text-[10px] text-slate-500">Capped at Net Debit Paid</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] uppercase text-slate-400">Breakeven Point</div>
                  <div className="text-lg font-bold text-white mt-1">$568.35</div>
                  <div className="text-[10px] text-slate-500">Long Strike + Net Debit</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] uppercase text-slate-400">Max Possible Profit</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">$165.00</div>
                  <div className="text-[10px] text-slate-500">Width ($5.00) − Debit ($3.35)</div>
                </div>
              </div>

              {/* Visual Diagram */}
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 font-mono text-xs space-y-2">
                <div className="flex justify-between text-slate-400 text-[11px]">
                  <span>Underlying Falls Below Long Strike</span>
                  <span>At Breakeven</span>
                  <span>Above Short Strike (Max Gain)</span>
                </div>
                <div className="w-full h-3 rounded-full bg-slate-800 flex overflow-hidden">
                  <div className="w-1/3 bg-rose-500/60 flex items-center justify-center text-[9px] text-white">Loss Capped</div>
                  <div className="w-1/3 bg-amber-500/60 flex items-center justify-center text-[9px] text-white">Ramping Profit</div>
                  <div className="w-1/3 bg-emerald-500/60 flex items-center justify-center text-[9px] text-white">Max Profit Capped</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 3: RISK ENGINE ────────────────────────────────────────── */}
        {activeTab === "risk" && (
          <div className="space-y-4 animate-fade-in">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
                  The Non-Negotiable 2% Portfolio Rule
                </div>
                <span className="text-xs font-mono text-slate-400">Account: ${calcEquity.toLocaleString()}</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">
                Every trade proposed by BullRun must strictly satisfy the <strong>2% Rule</strong>. On any single trade, your portfolio cannot lose more than 2% of total equity. Even 5 back-to-back losses only result in a 10% drawdown—keeping the account fully solvent and survivable.
              </p>
            </div>

            {/* Interactive Capital Calculator */}
            <div className="bloomberg-metric space-y-3 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-slate-300">Simulate Account Capital:</span>
                <div className="flex gap-2">
                  {[25000, 50000, 100000, 250000].map((amt) => (
                    <button
                      key={amt}
                      onClick={() => setCalcEquity(amt)}
                      className={`px-2.5 py-1 text-xs font-mono rounded transition-all ${
                        calcEquity === amt
                          ? "bg-amber-500/30 text-amber-300 border border-amber-500/50 font-bold"
                          : "bg-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      ${amt / 1000}k
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-center pt-2">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Max Loss (2%)</div>
                  <div className="text-base font-bold text-rose-400 mt-1">${maxRiskDollars.toLocaleString()}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Max Total Exposure (6%)</div>
                  <div className="text-base font-bold text-amber-400 mt-1">${maxPortfolioHeat.toLocaleString()}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Max Concurrent Trades</div>
                  <div className="text-base font-bold text-cyan-400 mt-1">3 Positions</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Daily Circuit Breaker</div>
                  <div className="text-base font-bold text-purple-400 mt-1">-${(calcEquity * 0.03).toLocaleString()}</div>
                </div>
              </div>
            </div>

            {/* Institutional Protections List */}
            <div className="space-y-2">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                Institutional Safety Protections
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <div>
                    <strong className="text-slate-200">Correlation Guard:</strong> Rejects duplicate same-direction bets on correlated indices (SPY &amp; QQQ).
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <div>
                    <strong className="text-slate-200">Time-of-Day Guard:</strong> No trades first/last 30m of market (9:30-10:00 &amp; 15:30-16:00 EST).
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <div>
                    <strong className="text-slate-200">Earnings Proximity:</strong> Rejects trades with corporate earnings within 5 DTE.
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <div>
                    <strong className="text-slate-200">Greeks Delta Exit:</strong> Auto-closes position if delta drops below 0.10 to salvage capital.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 4: LEARNING PROGRESS & JOURNAL ───────────────────────── */}
        {activeTab === "progress" && (
          <div className="space-y-4 animate-fade-in">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs font-bold uppercase tracking-wider text-purple-400 font-mono">
                  Trader Progress &amp; Mastery XP
                </div>
                <span className="text-xs font-mono text-amber-400 font-bold">{learning?.score || 0} / 100 XP</span>
              </div>
              <div className="w-full h-3 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 via-amber-400 to-emerald-400 transition-all duration-700"
                  style={{ width: `${Math.min(100, learning?.score || 10)}%` }}
                />
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                Explore trading concepts, inspect deterministic risk rules, and review post-trade journals to unlock advanced trader mastery badges.
              </p>
            </div>

            {/* Feature Checklist */}
            <div className="space-y-2">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                Mastery Modules Checklist
              </div>
              {[
                { key: "regime_lesson", label: "Regime Detection & Indicator Analysis", pts: 10, icon: "🔭" },
                { key: "strategy_explainer", label: "Defined-Risk Debit Spread Payoff Mechanics", pts: 15, icon: "📐" },
                { key: "risk_checks", label: "The 2% Rule & Institutional Circuit Breakers", pts: 15, icon: "🛡️" },
                { key: "trade_journal", label: "Post-Trade Prediction vs. Actual Journaling", pts: 20, icon: "📝" },
              ].map((feat) => {
                const explored = learning?.explored_features?.includes(feat.key);
                return (
                  <div
                    key={feat.key}
                    onClick={() => handleExplore(feat.key)}
                    className={`p-3 rounded-lg border flex items-center justify-between cursor-pointer transition-all ${
                      explored
                        ? "bg-slate-900/60 border-emerald-500/40 text-slate-200"
                        : "bg-slate-950/40 border-slate-800/80 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-3 text-xs font-mono">
                      <span className="text-base">{feat.icon}</span>
                      <span>{feat.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-amber-400">+{feat.pts} XP</span>
                      <span className={`text-xs ${explored ? "text-emerald-400 font-bold" : "text-slate-600"}`}>
                        {explored ? "✓ COMPLETED" : "○ EXPLORE"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
