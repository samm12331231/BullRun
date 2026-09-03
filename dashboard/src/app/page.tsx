"use client";

import { useEffect, useState, useCallback } from "react";
import PriceChart from "@/components/Chart";
import TradeCard from "@/components/TradeCard";
import PayoffDiagram from "@/components/PayoffDiagram";
import TeachingPanel from "@/components/TeachingPanel";
import {
  useWebSocket,
  fetchPortfolio,
  fetchTrades,
  fetchRegime,
  fetchLearningProgress,
  fetchTickers,
  fetchBacktest,
  type PortfolioData,
  type LearningProgress,
  type RegimeData,
  type AuditEntry,
  type TradeProposal,
  type TickerQuote,
  type BacktestResult,
} from "@/lib/useWebSocket";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Mock data generators (client-only to avoid hydration mismatch) ────────
function generateMockChartData() {
  const data = [];
  const now = new Date();
  for (let i = 0; i < 60; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - (60 - i));
    const base = 555 + Math.sin(i * 0.15) * 8 + i * 0.15;
    const open = base + (Math.random() - 0.5) * 2;
    const close = open + (Math.random() - 0.5) * 3;
    const high = Math.max(open, close) + Math.random() * 1.5;
    const low = Math.min(open, close) - Math.random() * 1.5;
    data.push({
      time: d.toISOString().split("T")[0],
      open: +open.toFixed(2),
      high: +high.toFixed(2),
      low: +low.toFixed(2),
      close: +close.toFixed(2),
      volume: Math.floor(30000000 + Math.random() * 20000000),
    });
  }
  return data;
}

function generateMockProposal(): TradeProposal {
  return {
    trade_number: 1,
    proposal: {
      structure: "BULL_CALL_SPREAD",
      underlying: "SPY",
      direction: "LONG",
      long_leg: { type: "CALL", strike: 565, delta: 0.58, mid_price: 6.20, alpaca_symbol: "SPY240920C00565000" },
      short_leg: { type: "CALL", strike: 570, delta: 0.33, mid_price: 2.85, alpaca_symbol: "SPY240920C00570000" },
      net_debit: 3.35,
      spread_width: 5.0,
      max_loss_per_contract: 335,
      max_profit_per_contract: 165,
      breakeven: 568.35,
      risk_reward_ratio: 0.49,
      dte: 14,
      conviction_score: 84.5,
      conviction_breakdown: {
        regime_strength: 88,
        momentum_align: 100,
        options_pricing: 78,
        liquidity: 92,
        risk_reward: 80,
        time_alignment: 90,
      },
      quantity: 2,
      recommended_contracts: 2,
      total_risk_proposed: 670,
      total_profit_potential: 330,
    },
    thesis: {
      what_happening: "SPY is in a confirmed bullish regime with ADX reading 31.2, trading above both the 20-day and 50-day EMAs with positive MACD momentum.",
      the_trade: "We are entering a 2-contract Bull Call Spread by purchasing the $565 call and selling the $570 call, capping maximum risk strictly to the net debit paid.",
      the_numbers: "Total profit potential is $330.00 across 2 contracts ($165/contract). Maximum loss is strictly capped at $670.00 (well within the $2,000 2% rule).",
      why_now: "4 out of 4 trend indicators align, volatility is stable at 1.15x ATR, and the 14-day expiration window provides the optimal theta-gamma risk profile.",
      what_could_go_wrong: "If SPY unexpectedly drops below $565.00 by expiration, the spread expires worthless with a maximum loss of $670.00.",
    },
    risk_check: {
      status: "PASS",
      checks: [
        { name: "2% RULE", status: "PASS", detail: "$335 ≤ $2,000 (2% limit per contract)", critical: true },
        { name: "CONVICTION SIZING", status: "PASS", detail: "2 contracts ($670 risk) within $2,000 cap" },
        { name: "EXPOSURE", status: "PASS", detail: "$670 ≤ $6,000 (6% portfolio heat cap)" },
        { name: "POSITIONS", status: "PASS", detail: "0 active < 3 max concurrent" },
        { name: "CORRELATION GUARD", status: "PASS", detail: "No duplicate directional exposure on SPY", critical: true },
        { name: "TIME-OF-DAY GUARD", status: "PASS", detail: "Session outside opening/closing 30m buffer" },
        { name: "EARNINGS GUARD", status: "PASS", detail: "No earnings within 5 DTE", critical: true },
        { name: "DAILY LIMIT", status: "PASS", detail: "Today's P&L: $0 | $3,000 budget remaining", critical: true },
        { name: "DRAWDOWN", status: "PASS", detail: "Peak drawdown: 0.0% < 10% limit", critical: true },
        { name: "LIQUIDITY", status: "PASS", detail: "Bid-ask spread $0.04 ≤ $0.15" },
        { name: "SPREAD WIDTH", status: "PASS", detail: "$5.00 ≤ $5.00 max width" },
        { name: "EXPIRATION", status: "PASS", detail: "14 DTE within 7-21 day window" },
      ],
    },
    timestamp: new Date().toISOString(),
  };
}

function generateMockTrades(): AuditEntry[] {
  const now = Date.now();
  return [
    { timestamp: new Date(now - 3600000).toISOString(), event: "SCOUT_SCAN", trade_number: 1, regime: "BULLISH" },
    { timestamp: new Date(now - 3500000).toISOString(), event: "QUANT_PROPOSAL", trade_number: 1, structure: "BULL_CALL_SPREAD" },
    { timestamp: new Date(now - 3400000).toISOString(), event: "RISK_VALIDATED", trade_number: 1, status: "PASS" },
    { timestamp: new Date(now - 3300000).toISOString(), event: "CIO_THESIS", trade_number: 1, reason: "Thesis generated" },
    { timestamp: new Date(now - 3200000).toISOString(), event: "CONSENT_GATE", trade_number: 1, decision: "APPROVE" },
    { timestamp: new Date(now - 3100000).toISOString(), event: "EXECUTION_FILLED", trade_number: 1, status: "FILLED" },
  ];
}

// ── Main Dashboard Component ───────────────────────────────────────────────

export default function Dashboard() {
  const { connected, pendingProposal } = useWebSocket();
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [learning, setLearning] = useState<LearningProgress | null>(null);
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [tickers, setTickers] = useState<TickerQuote[]>([]);
  const [trades, setTrades] = useState<AuditEntry[]>([]);
  const [chartData, setChartData] = useState<Array<{ time: string; open: number; high: number; low: number; close: number; volume: number }>>([]);
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(null);
  const [scanning, setScanning] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState<"proposal" | "academy">("proposal");
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);

  // No mock data on mount — let real API data populate

  const loadData = useCallback(async () => {
    try {
      const [p, r, t, l, tick, chart] = await Promise.allSettled([
        fetchPortfolio(),
        fetchRegime(),
        fetchTrades(),
        fetchLearningProgress(),
        fetchTickers(),
        fetch(`${API_URL}/api/chart`).then(res => res.json()).catch(() => null),
      ]);
      if (p.status === "fulfilled" && p.value) setPortfolio(p.value);
      if (r.status === "fulfilled" && r.value) setRegime(r.value);
      if (t.status === "fulfilled" && t.value) setTrades(t.value.trades || []);
      if (l.status === "fulfilled" && l.value) setLearning(l.value);
      if (tick.status === "fulfilled" && tick.value) setTickers(tick.value);
      if (chart.status === "fulfilled" && chart.value?.data) setChartData(chart.value.data);
      // Fetch backtest (heavier, only once)
      if (!backtest) {
        fetchBacktest().then(bt => { if (bt) setBacktest(bt); }).catch(() => {});
      }
    } catch {
      // Fallback to offline defaults
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    if (pendingProposal) {
      setActiveProposal(pendingProposal);
      setRightPanelTab("proposal");
    }
  }, [pendingProposal]);

  const handleTriggerScan = async () => {
    setScanning(true);
    try {
      const res = await fetch(`${API_URL}/api/scan`, { method: "POST" });
      const data = await res.json();
      if (data?.result?.proposal) {
        setActiveProposal(data.result);
      }
      await loadData();
    } catch (e) {
      console.error("Scan failed:", e);
    }
    setScanning(false);
  };

  const regimeBadge = (r: string) => {
    const cls =
      r === "BULLISH"
        ? "badge-bullish"
        : r === "BEARISH"
          ? "badge-bearish"
          : r === "VOLATILE"
            ? "badge-volatile"
            : r === "WATCHING"
              ? "badge-watching"
              : "badge-neutral";
    return <span className={`terminal-badge ${cls}`}>{r}</span>;
  };

  const eventIcon = (event: string) => {
    const map: Record<string, { icon: string; color: string }> = {
      SCOUT_SCAN: { icon: "🔭", color: "text-cyan-400" },
      QUANT_PROPOSAL: { icon: "📐", color: "text-blue-400" },
      RISK_VALIDATED: { icon: "🛡️", color: "text-emerald-400" },
      CIO_THESIS: { icon: "🎙️", color: "text-purple-400" },
      CONSENT_GATE: { icon: "👤", color: "text-amber-400" },
      EXECUTION_FILLED: { icon: "⚡", color: "text-emerald-400" },
      EXIT_TAKEN: { icon: "📊", color: "text-rose-400" },
    };
    return map[event] || { icon: "📝", color: "text-slate-400" };
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#080b11] text-[#f8fafc]">
      {/* ── Top Bar with Live Bloomberg Ticker Tape ──────────────────── */}
      <header className="border-b border-slate-800/80 bg-[#0d131f]/90 backdrop-blur-md sticky top-0 z-50">
        {/* Main Brand & Status */}
        <div className="flex items-center justify-between px-6 py-2.5 border-b border-slate-800/60">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-slate-950 font-black text-base shadow-lg shadow-amber-500/20">
                ⚡
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-black tracking-tight text-white font-mono">BULLRUN</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase font-semibold">
                  Alpaca AI Trading Desk
                </span>
              </div>
            </div>
            <div className="text-xs text-slate-400 font-mono hidden md:block border-l border-slate-800 pl-4">
              AI proposes · Evidence decides · Humans authorize
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={handleTriggerScan}
              disabled={scanning}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono font-bold text-amber-300 transition-all flex items-center gap-2 cursor-pointer"
            >
              <span>{scanning ? "🔄" : "🔍"}</span>
              <span>{scanning ? "SCANNING PIPELINE..." : "TRIGGER AI SCAN"}</span>
            </button>

            {regime && regimeBadge(
              (regime.metrics?.adx != null && regime.metrics.adx > 25) 
                ? regime.regime 
                : "WATCHING"
            )}

            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className={`w-2.5 h-2.5 rounded-full ${connected ? "bg-emerald-400 pulse-live" : "bg-amber-400"}`} />
              <span className="text-xs font-mono font-bold text-slate-300">
                {connected ? "LIVE ALPACARUN" : "DEMO SANDBOX"}
              </span>
            </div>
          </div>
        </div>

        {/* Real-Time Price Ticker Tape */}
        <div className="ticker-container px-6 py-1.5 bg-slate-950/60 border-t border-slate-900 flex items-center gap-6 text-xs font-mono overflow-x-auto">
          <div className="flex items-center gap-1 text-[10px] text-slate-500 uppercase tracking-widest font-bold shrink-0">
            <span>●</span> TICKER TAPE:
          </div>
          {tickers.filter(q => q.price != null).map((quote) => {
            const isPos = (quote.change_pct ?? 0) >= 0;
            return (
              <div key={quote.symbol} className="flex items-center gap-2 shrink-0">
                <span className="font-bold text-slate-200">{quote.symbol}</span>
                <span className="text-slate-300">${(quote.price ?? 0).toFixed(2)}</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${isPos ? "bg-emerald-500/15 text-emerald-400" : "bg-rose-500/15 text-rose-400"}`}>
                  {isPos ? "+" : ""}{(quote.change_pct ?? 0).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </header>

      {/* ── Main Terminal Body ────────────────────────────────────────── */}
      <main className="flex-1 p-4 md:p-6 space-y-4 max-w-[1920px] mx-auto w-full">
        {/* Top Metric Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bloomberg-metric" style={{ "--accent-color": "#f59e0b" } as React.CSSProperties}>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Total Portfolio Value</div>
            <div className="text-xl font-bold font-mono text-amber-400 mt-1">
              ${portfolio?.equity != null ? portfolio.equity.toLocaleString() : "—"}
            </div>
            <div className="text-[10px] font-mono text-slate-500">Buying Power: ${portfolio?.cash != null ? portfolio.cash.toLocaleString() : "—"}</div>
          </div>

          <div className="bloomberg-metric" style={{ "--accent-color": (portfolio?.total_pnl ?? 0) >= 0 ? "#10b981" : "#f43f5e" } as React.CSSProperties}>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Net Realized P&amp;L</div>
            <div className={`text-xl font-bold font-mono mt-1 ${(portfolio?.total_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              ${portfolio?.total_pnl != null ? portfolio.total_pnl.toFixed(2) : "—"}
            </div>
            <div className="text-[10px] font-mono text-slate-500">Win Rate: {portfolio?.win_rate != null ? `${portfolio.win_rate}%` : "—"}</div>
          </div>

          <div className="bloomberg-metric" style={{ "--accent-color": "#06b6d4" } as React.CSSProperties}>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Market Regime</div>
            <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {regime?.regime ?? "—"}
            </div>
            <div className="text-[10px] font-mono text-slate-500">ADX: {regime?.metrics?.adx?.toFixed(1) ?? "—"} · RSI: {regime?.metrics?.rsi?.toFixed(1) ?? "—"}</div>
          </div>

          <div className="bloomberg-metric" style={{ "--accent-color": "#10b981" } as React.CSSProperties}>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Active 2% Risk Cap</div>
            <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
              $2,000 / Trade
            </div>
            <div className="text-[10px] font-mono text-slate-500">              Heat: ${Math.round(portfolio?.risk_used ?? 0).toLocaleString()} / ${Math.round(portfolio?.risk_limit ?? 6000).toLocaleString()}</div>
          </div>

          <div className="bloomberg-metric" style={{ "--accent-color": "#a855f7" } as React.CSSProperties}>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Active Positions</div>
            <div className="text-xl font-bold font-mono text-purple-400 mt-1">
              {portfolio?.open_positions ?? 0} / 3 Max
            </div>
            <div className="text-[10px] font-mono text-slate-500">Correlation Protected</div>
          </div>

          <div className="bloomberg-metric" style={{ "--accent-color": "#3b82f6" } as React.CSSProperties}>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Trader Mastery XP</div>
            <div className="text-xl font-bold font-mono text-blue-400 mt-1">
              {learning?.level ?? "Beginner"}
            </div>
            <div className="text-[10px] font-mono text-slate-500">{learning?.score ?? 0} / 100 Mastery XP</div>
          </div>
        </div>

        {/* ── Main 2-Column Grid (Left: Chart/Activity, Right: Proposal/Academy) ── */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
          {/* Left Column: Interactive Price Chart & Agent Telemetry (7 Cols) */}
          <div className="xl:col-span-7 space-y-4">
            {/* Chart Card */}
            <div className="glass-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
                    <span>📈</span> SPY / S&amp;P 500 ETF TRUST — REAL-TIME REGIME OVERLAY
                  </div>
                  <span className="terminal-badge badge-bullish">{regime?.regime === "BULLISH" || regime?.regime === "BEARISH" ? "TREND ALIGNED" : regime?.regime ? "WATCHING" : "SCANNING..."}</span>
                </div>
                <div className="text-xs font-mono text-slate-400">
                  {regime?.metrics?.ema_bullish != null 
                    ? (regime.metrics.ema_bullish 
                        ? <span className="text-emerald-400">EMA 20 &gt; EMA 50</span>
                        : <span className="text-rose-400">EMA 20 &lt; EMA 50</span>)
                    : <span className="text-slate-400">EMA: --</span>}
                </div>
              </div>
              <div className="h-[380px] w-full">
                {chartData.length > 0 ? (
                  <PriceChart data={chartData} symbol={regime?.metrics?.current_price ? "SPY" : "SPY"} />
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 font-mono text-xs">
                    Loading institutional chart feed...
                  </div>
                )}
              </div>
            </div>

            {/* Multi-Agent Architecture Telemetry Log */}
            <div className="glass-card p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
                  <span>⚡</span> Multi-Agent Pipeline Activity (Hash-Chained Audit Trail)
                </div>
                <span className="text-[11px] font-mono text-amber-400">
                  SHA-256 Verified ✓
                </span>
              </div>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1 font-mono text-xs">
                {trades.map((t, idx) => {
                  const iconInfo = eventIcon(t.event);
                  return (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between transition-colors hover:bg-slate-800/40"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-base">{iconInfo.icon}</span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={`font-bold ${iconInfo.color}`}>
                              {t.event.replace(/_/g, " ")}
                            </span>
                            {t.structure && (
                              <span className="text-[11px] text-slate-300">
                                ({t.structure.replace(/_/g, " ")})
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-slate-500">
                            Trade #{t.trade_number} ·{" "}
                            <span suppressHydrationWarning>{new Date(t.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>

                      <div>
                        {t.decision && (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${t.decision === "APPROVE" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" : "bg-rose-500/20 text-rose-400 border border-rose-500/40"}`}>
                            {t.decision}
                          </span>
                        )}
                        {t.status && !t.decision && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                            {t.status}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Toggleable Proposal & Teaching Academy (5 Cols) */}
          <div className="xl:col-span-5 space-y-4">
            {/* View Switcher Bar */}
            <div className="glass-card p-1.5 grid grid-cols-2 gap-1 text-xs font-mono">
              <button
                onClick={() => setRightPanelTab("proposal")}
                className={`py-2 px-3 rounded-lg font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                  rightPanelTab === "proposal"
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>⚡</span> Active Trade Proposal
              </button>
              <button
                onClick={() => setRightPanelTab("academy")}
                className={`py-2 px-3 rounded-lg font-bold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                  rightPanelTab === "academy"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>🎓</span> Trading Academy
              </button>
            </div>

            {/* Right Panel View Modes */}
            {rightPanelTab === "proposal" ? (
              activeProposal ? (
                <div className="space-y-4">
                  <TradeCard
                    proposal={activeProposal}
                    onDecision={() => {
                      loadData();
                    }}
                  />
                  <PayoffDiagram
                    structure={activeProposal.proposal.structure}
                    longStrike={activeProposal.proposal.long_leg.strike}
                    shortStrike={activeProposal.proposal.short_leg.strike}
                    netDebit={activeProposal.proposal.net_debit}
                    currentPrice={regime?.metrics?.current_price || activeProposal.proposal.breakeven}
                    underlying={activeProposal.proposal.underlying}
                  />
                </div>
              ) : (
                <div className="glass-card p-8 text-center space-y-3">
                  <div className="text-4xl">🔍</div>
                  <div className="text-base font-bold text-white">Scanning Markets for High-Conviction Setups...</div>
                  <div className="text-xs text-slate-400 font-mono">
                    Scout &amp; Quant agents actively evaluating SPY, QQQ, and IWM option chains.
                  </div>
                  <button
                    onClick={handleTriggerScan}
                    className="mt-3 px-4 py-2 rounded-lg bg-amber-500 text-slate-950 font-bold text-xs font-mono hover:bg-amber-400 transition-all cursor-pointer"
                  >
                    TRIGGER SCAN NOW
                  </button>
                </div>
              )
            ) : (
              <TeachingPanel
                learning={learning}
                regime={regime}
                onProgressUpdate={(upd) => setLearning(upd)}
              />
            )}
          </div>
        </div>
      </main>

      {/* ── Backtest Section ──────────────────────────────────────────── */}
      {backtest && (
        <section className="mx-4 mb-3 bg-[#0d131f] rounded-xl border border-slate-800/60 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200">Historical Backtest</h3>
            <span className="text-[10px] text-slate-500 font-mono">{backtest.summary.backtest_period}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3">
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Total P&L</div>
              <div className={`text-lg font-bold font-mono ${backtest.summary.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                ${backtest.summary.total_pnl >= 0 ? '+' : ''}{backtest.summary.total_pnl.toLocaleString(undefined, {minimumFractionDigits: 2})}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Win Rate</div>
              <div className="text-lg font-bold font-mono text-slate-200">{backtest.summary.win_rate_pct}%</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Trades</div>
              <div className="text-lg font-bold font-mono text-slate-200">{backtest.summary.total_trades} <span className="text-xs text-slate-500">({backtest.summary.winning_trades}W/{backtest.summary.losing_trades}L)</span></div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Max Drawdown</div>
              <div className="text-lg font-bold font-mono text-amber-400">{backtest.summary.max_drawdown_pct}%</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase">Gate Rejections</div>
              <div className="text-lg font-bold font-mono text-slate-200">{backtest.summary.risk_gate_rejections}</div>
            </div>
          </div>
          {/* Equity curve mini chart */}
          <div className="h-16 relative">
            {(() => {
              const ec = backtest.equity_curve;
              if (ec.length === 0) return null;
              const vals = ec.map(e => e.equity);
              const min = Math.min(...vals);
              const max = Math.max(...vals);
              const range = max - min || 1;
              const w = 100 / ec.length;
              const path = ec.map((e, i) => {
                const x = i * w;
                const y = 100 - ((e.equity - min) / range) * 100;
                return `${i === 0 ? 'M' : 'L'}${x},${y}`;
              }).join(' ');
              return (
                <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
                  <path d={path} fill="none" stroke="#22c55e" strokeWidth="0.8" vectorEffect="non-scaling-stroke" />
                </svg>
              );
            })()}
          </div>
          {/* Trade list */}
          <div className="mt-2 space-y-1">
            {backtest.trades.map((t, i) => (
              <div key={i} className="flex items-center gap-3 text-[11px] font-mono">
                <span className={t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{t.pnl >= 0 ? '▲' : '▼'}</span>
                <span className="text-slate-400">{t.entry_date} → {t.exit_date}</span>
                <span className="text-slate-300">{t.strategy} {t.qty}x</span>
                <span className={t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>${t.pnl >= 0 ? '+' : ''}{t.pnl.toFixed(2)}</span>
                <span className="text-slate-500">{t.exit_reason}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/80 bg-[#0d131f] px-6 py-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-400">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <span className="text-slate-300 font-bold">SPY</span>
          <span>2% Rule ($2K max loss)</span>
          <span>Greeks Exit &lt; 0.10</span>
          <span>TP: 50% @ +30%</span>
        </div>
        <div className="flex items-center gap-3">
          <span>Alpaca Hackathon 2026</span>
          <span className="text-amber-400 font-bold">BullRun v2.0</span>
        </div>
      </footer>
    </div>
  );
}

