"use client";

import { useEffect, useState, useCallback } from "react";
import PriceChart from "@/components/Chart";
import TradeCard from "@/components/TradeCard";
import {
  useWebSocket,
  fetchPortfolio,
  fetchTrades,
  fetchRegime,
  fetchLearningProgress,
  type PortfolioData,
  type LearningProgress,
  type RegimeData,
  type AuditEntry,
  type TradeProposal,
} from "@/lib/useWebSocket";

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
      open: +open.toFixed(2), high: +high.toFixed(2),
      low: +low.toFixed(2), close: +close.toFixed(2),
      volume: Math.floor(30000000 + Math.random() * 20000000),
    });
  }
  return data;
}

function generateMockProposal(): TradeProposal {
  return {
    trade_number: 1,
    proposal: {
      structure: "BULL_CALL_SPREAD", underlying: "SPY", direction: "LONG",
      long_leg: { type: "CALL", strike: 765, delta: 0.58, mid_price: 9.20 },
      short_leg: { type: "CALL", strike: 770, delta: 0.35, mid_price: 5.85 },
      net_debit: 3.35, spread_width: 5,
      max_loss_per_contract: 335, max_profit_per_contract: 165,
      breakeven: 768.35, risk_reward_ratio: 0.49, dte: 14, conviction_score: 78.2,
    },
    thesis: {
      what_happening: "SPY is in a strong uptrend — price above both the 20-day and 50-day moving averages, ADX reads 31.2, confirming the trend has strength.",
      the_trade: "We're buying a bull call spread: betting SPY continues rising. We buy the $765 call and sell the $770 call, capping both risk and reward.",
      the_numbers: "You could make up to $165 per contract, or lose up to $335 if SPY doesn't reach our target.",
      why_now: "Multiple indicators align: EMA crossover bullish, MACD histogram positive and rising, RSI at 62.3 confirms momentum without being overbought.",
      what_could_go_wrong: "If SPY reverses and drops below $768.35, this trade starts losing money. Maximum loss is $335 — no more.",
    },
    risk_check: {
      status: "PASS",
      checks: [
        { name: "2% RULE", status: "PASS", detail: "$335 ≤ $2,000" },
        { name: "EXPOSURE", status: "PASS", detail: "$335 ≤ $6,000" },
        { name: "POSITIONS", status: "PASS", detail: "0 < 3" },
        { name: "DAILY LIMIT", status: "PASS", detail: "Budget: $3,000 remaining" },
        { name: "LIQUIDITY", status: "PASS", detail: "Spread: $0.03 ≤ $0.15" },
        { name: "SPREAD WIDTH", status: "PASS", detail: "$5.00 ≤ $5.00" },
        { name: "EXPIRATION", status: "PASS", detail: "14 days (7-21)" },
        { name: "DRAWDOWN", status: "PASS", detail: "0.0% < 10%" },
      ],
    },
    timestamp: "",
  };
}

function generateMockTrades(): AuditEntry[] {
  const now = Date.now();
  return [
    { timestamp: new Date(now - 3600000).toISOString(), event: "SIGNAL", trade_number: 1, regime: "BULLISH" },
    { timestamp: new Date(now - 3500000).toISOString(), event: "PROPOSAL", trade_number: 1, structure: "BULL_CALL_SPREAD" },
    { timestamp: new Date(now - 3400000).toISOString(), event: "RISK_CHECK", trade_number: 1, status: "PASS" },
    { timestamp: new Date(now - 3300000).toISOString(), event: "CONSENT", trade_number: 1, decision: "APPROVE" },
    { timestamp: new Date(now - 3200000).toISOString(), event: "EXECUTION", trade_number: 1, status: "DRY_RUN" },
  ];
}

// ── Main Dashboard ─────────────────────────────────────────────────────────

export default function Dashboard() {
  const { connected, pendingProposal } = useWebSocket();
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [learning, setLearning] = useState<LearningProgress | null>(null);
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [trades, setTrades] = useState<AuditEntry[]>([]);
  const [chartData, setChartData] = useState<Array<{time:string;open:number;high:number;low:number;close:number;volume:number}>>([]);
  const [activeProposal, setActiveProposal] = useState<TradeProposal | null>(null);
  const [mounted, setMounted] = useState(false);

  // Initialize mock data only on client to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
    setChartData(generateMockChartData());
    setActiveProposal(generateMockProposal());
    setTrades(generateMockTrades());
  }, []);

  const loadData = useCallback(async () => {
    try {
      const [p, r, t, l] = await Promise.allSettled([
        fetchPortfolio(),
        fetchRegime(),
        fetchTrades(),
        fetchLearningProgress(),
      ]);
      if (p.status === "fulfilled") setPortfolio(p.value);
      if (r.status === "fulfilled") setRegime(r.value);
      if (t.status === "fulfilled") setTrades(t.value.trades);
      if (l.status === "fulfilled") setLearning(l.value);
    } catch {
      // Use mock data if API is not running
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    if (pendingProposal) {
      setActiveProposal(pendingProposal);
    }
  }, [pendingProposal]);

  const regimeBadge = (r: string) => {
    const cls =
      r === "BULLISH"
        ? "badge-bullish"
        : r === "BEARISH"
          ? "badge-bearish"
          : r === "VOLATILE"
            ? "badge-volatile"
            : "badge-neutral";
    return <span className={`badge ${cls}`}>{r}</span>;
  };

  const eventIcon = (event: string) => {
    const map: Record<string, { icon: string; cls: string }> = {
      SIGNAL: { icon: "🔍", cls: "agent-scout" },
      PROPOSAL: { icon: "📐", cls: "agent-quant" },
      RISK_CHECK: { icon: "🛡️", cls: "agent-risk" },
      CONSENT: { icon: "👤", cls: "agent-cio" },
      EXECUTION: { icon: "⚡", cls: "agent-scout" },
      EXIT: { icon: "📊", cls: "agent-quant" },
    };
    return map[event] || { icon: "📝", cls: "agent-scout" };
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-primary)" }}>
      {/* ── Top Bar ──────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-6 py-3 border-b" style={{ borderColor: "var(--border)", background: "var(--bg-secondary)" }}>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-lg" style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)" }}>
              ⚡
            </div>
            <span className="text-lg font-bold" style={{ color: "var(--gold)" }}>
              Conviction Gate
            </span>
          </div>
          <div className="text-xs text-[var(--text-muted)] font-mono hidden sm:block">
            AI proposes · Evidence decides · Humans authorize
          </div>
        </div>
        <div className="flex items-center gap-4">
          {regime && regimeBadge(regime.regime)}
          <div className="flex items-center gap-2">
            <div className={`pulse-dot ${connected ? "" : "opacity-0"}`} style={{ background: connected ? "var(--green)" : "var(--red)" }} />
            <span className="text-xs text-[var(--text-muted)] font-mono">
              {connected ? "LIVE" : "DEMO"}
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <div className="flex-1 p-4 overflow-hidden">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 h-full">
          {/* ── Left: Chart + Metrics ────────────────────────────────── */}
          <div className="xl:col-span-2 flex flex-col gap-4 min-h-0">
            {/* Chart */}
            <div className="card flex-1 min-h-[300px]">
              {chartData.length > 0 ? (
                <PriceChart data={chartData} symbol="SPY" />
              ) : (
                <div className="flex items-center justify-center h-full text-[var(--text-muted)]">
                  Loading chart...
                </div>
              )}
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="metric-box">
                <div className="metric-value" style={{ color: "var(--gold)" }}>
                  ${portfolio?.equity?.toLocaleString() ?? "100,000"}
                </div>
                <div className="metric-label">Portfolio</div>
              </div>
              <div className="metric-box">
                <div
                  className="metric-value"
                  style={{ color: (portfolio?.total_pnl ?? 0) >= 0 ? "var(--green)" : "var(--red)" }}
                >
                  ${portfolio?.total_pnl?.toFixed(0) ?? "0"}
                </div>
                <div className="metric-label">P&L</div>
              </div>
              <div className="metric-box">
                <div className="metric-value text-white">
                  {portfolio?.win_rate ?? 0}%
                </div>
                <div className="metric-label">Win Rate</div>
              </div>
              <div className="metric-box">
                <div className="metric-value text-cyan-400">
                  {regime?.metrics?.adx?.toFixed(1) ?? "—"}
                </div>
                <div className="metric-label">ADX</div>
              </div>
              <div className="metric-box">
                <div className="metric-value text-violet-300">
                  {learning?.level ?? "Beginner"}
                </div>
                <div className="metric-label">Learning · {learning?.score ?? 0} pts</div>
              </div>
            </div>
          </div>

          {/* ── Right: Trade Card + Activity ─────────────────────────── */}
          <div className="flex flex-col gap-4 min-h-0 overflow-y-auto">
            {/* Trade Card */}
            {activeProposal ? (
              <TradeCard
                proposal={activeProposal}
                onDecision={() => setActiveProposal(null)}
              />
            ) : (
              <div className="card flex flex-col items-center justify-center py-12">
                <div className="text-4xl mb-3">🔍</div>
                <div className="text-sm font-bold text-[var(--text-secondary)]">
                  Scanning for opportunities...
                </div>
                <div className="text-xs text-[var(--text-muted)] mt-1">
                  The Scout is analyzing SPY market conditions
                </div>
              </div>
            )}

            {/* AI Agent Log */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Agent Activity</span>
                <span className="text-xs text-[var(--text-muted)] font-mono">
                  {trades.length} events
                </span>
              </div>
              <div className="max-h-[200px] overflow-y-auto">
                {trades.length > 0
                  ? trades.slice(-8).reverse().map((t, i) => {
                      const { icon, cls } = eventIcon(t.event);
                      return (
                        <div key={i} className="agent-log-entry">
                          <div className={`agent-icon ${cls}`}>{icon}</div>
                          <div className="flex-1 min-w-0">
                            <div className="text-[var(--text-primary)]">
                              <span className="font-bold">{t.event.replace("_", " ")}</span>
                              {t.structure && (
                                <span className="ml-1 text-[var(--text-muted)]">
                                  {t.structure.replace(/_/g, " ")}
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-[var(--text-muted)] font-mono">
                              Trade #{t.trade_number} ·{" "}
                              <span suppressHydrationWarning>{new Date(t.timestamp).toLocaleTimeString()}</span>
                            </div>
                          </div>
                          {t.decision && (
                            <span
                              className={`badge ${
                                t.decision === "APPROVE" ? "badge-pass" : "badge-reject"
                              }`}
                            >
                              {t.decision}
                            </span>
                          )}
                          {t.pnl !== undefined && t.pnl !== null && (
                            <span
                              className="text-sm font-mono font-bold"
                              style={{ color: t.pnl >= 0 ? "var(--green)" : "var(--red)" }}
                            >
                              ${t.pnl >= 0 ? "+" : ""}
                              {t.pnl}
                            </span>
                          )}
                        </div>
                      );
                    })
                  : trades.map((t, i) => {
                      const { icon, cls } = eventIcon(t.event);
                      return (
                        <div key={i} className="agent-log-entry">
                          <div className={`agent-icon ${cls}`}>{icon}</div>
                          <div className="flex-1">
                            <div className="text-[var(--text-primary)]">
                              <span className="font-bold">{t.event}</span>
                              {t.structure && (
                                <span className="ml-1 text-[var(--text-muted)]">
                                  {t.structure.replace(/_/g, " ")}
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-[var(--text-muted)] font-mono">
                              Trade #{t.trade_number} ·{" "}
                              <span suppressHydrationWarning>{new Date(t.timestamp).toLocaleTimeString()}</span>
                            </div>
                          </div>
                          {t.decision && (
                            <span className={`badge ${t.decision === "APPROVE" ? "badge-pass" : "badge-reject"}`}>
                              {t.decision}
                            </span>
                          )}
                        </div>
                      );
                    })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Status Bar ────────────────────────────────────────── */}
      <footer className="flex items-center justify-between px-6 py-2 border-t text-xs font-mono" style={{ borderColor: "var(--border)", background: "var(--bg-secondary)", color: "var(--text-muted)" }}>
        <div className="flex items-center gap-4">
          <span>Underlying: SPY</span>
          <span>Risk: 2% / trade</span>
          <span>Max positions: 3</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Conviction Gate v1.0</span>
          <span>Alpaca Paper Trading</span>
        </div>
      </footer>
    </div>
  );
}
