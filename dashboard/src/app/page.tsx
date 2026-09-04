"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  BarChart3,
  BookOpen,
  FileCheck,
  Layers,
  Clock,
  Zap,
  AlertTriangle,
} from "lucide-react";
import PriceChart from "@/components/Chart";
import TradeCard from "@/components/TradeCard";
import PayoffDiagram from "@/components/PayoffDiagram";
import TeachingPanel from "@/components/TeachingPanel";
import ProofTab from "@/components/ProofTab";
import AppHeader from "@/components/AppHeader";
import SystemStatusStrip from "@/components/SystemStatusStrip";
import MetricCard from "@/components/MetricCard";
import SectionHeading from "@/components/SectionHeading";
import RiskSummary from "@/components/RiskSummary";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { cn } from "@/lib/cn";
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
  const [rightPanelTab, setRightPanelTab] = useState<"proposal" | "academy" | "proof">("proposal");
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);

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
      if (!backtest) {
        fetchBacktest().then(bt => { if (bt) setBacktest(bt); }).catch(() => {});
      }
    } catch {
      // offline defaults
    }
  }, [backtest]);

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
    const variant =
      r === "BULLISH" ? "accent" as const :
      r === "BEARISH" ? "danger" as const :
      r === "VOLATILE" ? "warning" as const :
      "muted" as const;
    return <StatusBadge variant={variant}>{r}</StatusBadge>;
  };

  const eventIcon = (event: string) => {
    const map: Record<string, React.ReactNode> = {
      SCOUT_SCAN: <Search className="w-3.5 h-3.5 text-[var(--info)]" />,
      QUANT_PROPOSAL: <Layers className="w-3.5 h-3.5 text-[var(--info)]" />,
      RISK_VALIDATED: <ShieldCheck className="w-3.5 h-3.5 text-[var(--accent)]" />,
      CIO_THESIS: <BookOpen className="w-3.5 h-3.5 text-[var(--info)]" />,
      CONSENT_GATE: <Zap className="w-3.5 h-3.5 text-[var(--warning)]" />,
      EXECUTION_FILLED: <Zap className="w-3.5 h-3.5 text-[var(--accent)]" />,
      EXIT_TAKEN: <AlertTriangle className="w-3.5 h-3.5 text-[var(--danger)]" />,
    };
    return map[event] || <Clock className="w-3.5 h-3.5 text-[var(--muted)]" />;
  };

  const portfolioExt = portfolio as PortfolioData & { data_mode?: string; retrieved_at?: string | null; account_data_available?: boolean } | null;
  const dataMode = portfolioExt?.data_mode;
  const retrievedAt = portfolioExt?.retrieved_at;
  const accountAvailable = portfolioExt?.account_data_available;

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg)] text-[var(--text)]">
      {/* ── A. TOP HEADER ──────────────────────────────────────── */}
      <AppHeader
        connected={connected}
        scanning={scanning}
        dataMode={dataMode}
        auditValid={true}
        regime={regime}
        tickers={tickers}
        onScan={handleTriggerScan}
        regimeBadge={regimeBadge}
      />

      {/* ── B. TRUST / STATUS STRIP ───────────────────────────── */}
      <SystemStatusStrip
        dataMode={dataMode}
        accountDataAvailable={accountAvailable}
        retrievedAt={retrievedAt}
      />

      {/* ── Main content ───────────────────────────────────────── */}
      <main className="flex-1 p-4 md:p-5 space-y-4 max-w-[1920px] mx-auto w-full">
        {/* ── C. TOP METRICS (4 cards) ────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="Portfolio Equity"
            value={portfolio?.equity != null ? `$${portfolio.equity.toLocaleString()}` : "—"}
            sub={portfolio?.cash != null ? `Cash: $${portfolio.cash.toLocaleString()}` : undefined}
            variant="accent"
            icon={<TrendingUp className="w-3.5 h-3.5" />}
          />
          <MetricCard
            label="Total P&L"
            value={portfolio?.total_pnl != null ? `$${portfolio.total_pnl.toFixed(2)}` : "—"}
            sub={portfolio?.win_rate != null ? `Win rate: ${portfolio.win_rate}%` : undefined}
            variant={(portfolio?.total_pnl ?? 0) >= 0 ? "accent" : "danger"}
            icon={portfolio?.total_pnl != null && portfolio.total_pnl >= 0
              ? <TrendingUp className="w-3.5 h-3.5" />
              : <TrendingDown className="w-3.5 h-3.5" />}
          />
          <MetricCard
            label="Risk Used"
            value={portfolio?.risk_used != null ? `$${Math.round(portfolio.risk_used).toLocaleString()}` : "—"}
            sub={portfolio?.risk_limit != null ? `of $${Math.round(portfolio.risk_limit).toLocaleString()} limit` : undefined}
            variant="warning"
            icon={<BarChart3 className="w-3.5 h-3.5" />}
          />
          <MetricCard
            label="Open Positions"
            value={portfolio?.open_positions != null ? `${portfolio.open_positions} / 3` : "—"}
            sub="Max concurrent trades"
            variant="info"
            icon={<Layers className="w-3.5 h-3.5" />}
          />
        </div>

        {/* ── D. CORE DECISION AREA (2-column) ─────────────────── */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
          {/* LEFT: Chart + Audit Trail (~7 cols) */}
          <div className="xl:col-span-7 space-y-4">
            {/* Chart */}
            <div className="card p-4">
              <SectionHeading icon={<BarChart3 className="w-3.5 h-3.5" />}>
                SPY / S&P 500 ETF — Real-Time Regime Overlay
              </SectionHeading>
              <div className="h-[360px] w-full">
                {chartData.length > 0 ? (
                  <PriceChart data={chartData} symbol="SPY" />
                ) : (
                  <div className="h-full flex items-center justify-center text-[var(--muted)] font-mono text-xs">
                    Retrieving market data...
                  </div>
                )}
              </div>
            </div>

            {/* Audit Trail */}
            <div className="card p-4">
              <SectionHeading
                icon={<Clock className="w-3.5 h-3.5" />}
                action={<StatusBadge variant="accent"><ShieldCheck className="w-3 h-3" />SHA-256 Verified</StatusBadge>}
              >
                Agent Pipeline Activity
              </SectionHeading>
              <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1 font-mono text-xs">
                {trades.length === 0 ? (
                  <div className="text-center py-6 text-[var(--muted)] text-[11px]">
                    No pipeline activity yet. Trigger a scan to begin.
                  </div>
                ) : (
                  trades.map((t, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-[var(--surface-raised)] border border-[var(--border-subtle)] flex items-center justify-between hover:border-[var(--border)] transition-colors"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        {eventIcon(t.event)}
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-[var(--muted-strong)] truncate">
                              {t.event.replace(/_/g, " ")}
                            </span>
                            {t.structure && (
                              <span className="text-[10px] text-[var(--muted)]">
                                ({t.structure.replace(/_/g, " ")})
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-[var(--muted)]">
                            Trade #{t.trade_number} · <span suppressHydrationWarning>{new Date(t.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      </div>
                      <div className="shrink-0 ml-2">
                        {t.decision && (
                          <StatusBadge variant={t.decision === "APPROVE" ? "accent" : "danger"}>
                            {t.decision}
                          </StatusBadge>
                        )}
                        {t.status && !t.decision && (
                          <StatusBadge variant="info">{t.status}</StatusBadge>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* RIGHT: Proposal / Proof / Academy (~5 cols) */}
          <div className="xl:col-span-5 space-y-4">
            {/* Tab bar */}
            <div className="tab-bar grid-cols-3">
              <button
                onClick={() => setRightPanelTab("proposal")}
                aria-selected={rightPanelTab === "proposal"}
              >
                <Layers className="w-3.5 h-3.5" />
                Proposal
              </button>
              <button
                onClick={() => setRightPanelTab("proof")}
                aria-selected={rightPanelTab === "proof"}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Proof &amp; Safety
              </button>
              <button
                onClick={() => setRightPanelTab("academy")}
                aria-selected={rightPanelTab === "academy"}
              >
                <BookOpen className="w-3.5 h-3.5" />
                Academy
              </button>
            </div>

            {/* Tab content */}
            {rightPanelTab === "proposal" ? (
              activeProposal ? (
                <div className="space-y-4">
                  <TradeCard
                    proposal={activeProposal}
                    onDecision={() => { loadData(); }}
                  />
                  {/* Risk summary */}
                  {activeProposal.risk_check && (
                    <div className="card p-4">
                      <RiskSummary
                        checks={activeProposal.risk_check.checks}
                        allPassed={activeProposal.risk_check.all_passed}
                        failedChecks={activeProposal.risk_check.failed_checks}
                      />
                    </div>
                  )}
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
                <EmptyState
                  icon={<Search className="w-8 h-8" />}
                  title="No active trade proposal"
                  description="No qualified options setup found. BullRun will not create a trade without a validated setup."
                  action={
                    <button
                      onClick={handleTriggerScan}
                      disabled={scanning}
                      className="btn-primary px-4 py-2 rounded-lg text-xs font-mono cursor-pointer disabled:opacity-50"
                    >
                      {scanning ? "Scanning..." : "Trigger AI Scan"}
                    </button>
                  }
                />
              )
            ) : rightPanelTab === "proof" ? (
              <ProofTab />
            ) : (
              <TeachingPanel
                learning={learning}
                regime={regime}
                onProgressUpdate={(upd) => setLearning(upd)}
              />
            )}
          </div>
        </div>

        {/* ── Backtest Section ─────────────────────────────────── */}
        {backtest && (
          <div className="card">
            <div className="card-header">
              <span className="card-title flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5" />
                Historical Backtest
              </span>
              <span className="text-[10px] text-[var(--muted)] font-mono">
                {backtest.summary.backtest_period}
              </span>
            </div>
            <div className="card-body space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div>
                  <div className="text-[10px] font-mono text-[var(--muted)] uppercase">Total P&L</div>
                  <div className={cn(
                    "text-lg font-bold font-mono",
                    backtest.summary.total_pnl >= 0 ? "text-[var(--accent)]" : "text-[var(--danger)]"
                  )}>
                    ${backtest.summary.total_pnl >= 0 ? "+" : ""}{backtest.summary.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[var(--muted)] uppercase">Win Rate</div>
                  <div className="text-lg font-bold font-mono text-[var(--text)]">{backtest.summary.win_rate_pct}%</div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[var(--muted)] uppercase">Trades</div>
                  <div className="text-lg font-bold font-mono text-[var(--text)]">
                    {backtest.summary.total_trades}{" "}
                    <span className="text-xs text-[var(--muted)]">({backtest.summary.winning_trades}W/{backtest.summary.losing_trades}L)</span>
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[var(--muted)] uppercase">Max Drawdown</div>
                  <div className="text-lg font-bold font-mono text-[var(--warning)]">{backtest.summary.max_drawdown_pct}%</div>
                </div>
                <div>
                  <div className="text-[10px] font-mono text-[var(--muted)] uppercase">Gate Rejections</div>
                  <div className="text-lg font-bold font-mono text-[var(--text)]">{backtest.summary.risk_gate_rejections}</div>
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
                    return `${i === 0 ? "M" : "L"}${x},${y}`;
                  }).join(" ");
                  return (
                    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
                      <path d={path} fill="none" stroke="var(--accent)" strokeWidth="0.8" vectorEffect="non-scaling-stroke" />
                    </svg>
                  );
                })()}
              </div>
              {/* Trade list */}
              <div className="space-y-1">
                {backtest.trades.map((t, i) => (
                  <div key={i} className="flex items-center gap-3 text-[11px] font-mono">
                    <span className={t.pnl >= 0 ? "text-[var(--accent)]" : "text-[var(--danger)]"}>
                      {t.pnl >= 0 ? "\u25B2" : "\u25BC"}
                    </span>
                    <span className="text-[var(--muted)]">{t.entry_date} → {t.exit_date}</span>
                    <span className="text-[var(--muted-strong)]">{t.strategy} {t.qty}x</span>
                    <span className={t.pnl >= 0 ? "text-[var(--accent)]" : "text-[var(--danger)]"}>
                      ${t.pnl >= 0 ? "+" : ""}{t.pnl.toFixed(2)}
                    </span>
                    <span className="text-[var(--muted)]">{t.exit_reason}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="border-t border-[var(--border)] bg-[var(--surface)] px-4 md:px-6 py-2.5 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-[var(--muted)]">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="text-[var(--muted-strong)] font-semibold">SPY</span>
          <span>2% Rule ($2K max loss)</span>
          <span>Greeks Exit &lt; 0.10</span>
          <span>TP: 50% @ +30%</span>
        </div>
        <div className="flex items-center gap-2">
          <span>Alpaca Hackathon 2026</span>
          <span className="text-[var(--accent)] font-bold">BullRun</span>
        </div>
      </footer>
    </div>
  );
}
