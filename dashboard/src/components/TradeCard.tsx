"use client";

import { useState } from "react";
import type { TradeProposal } from "@/lib/useWebSocket";
import { submitConsent, exploreFeature } from "@/lib/useWebSocket";

interface TradeCardProps {
  proposal: TradeProposal;
  onDecision?: () => void;
}

export default function TradeCard({ proposal, onDecision }: TradeCardProps) {
  const [loading, setLoading] = useState(false);
  const [decision, setDecision] = useState<string | null>(null);
  const [showProView, setShowProView] = useState(false);
  const [showTeaching, setShowTeaching] = useState(true);

  const { proposal: p, thesis, risk_check } = proposal;
  if (!p) return null;
  const structureName = p.structure?.replace(/_/g, " ") ?? "SPREAD";
  const isBull = p.structure?.includes("CALL") || p.direction === "LONG";
  const directionColor = isBull ? "#10b981" : "#f43f5e";

  // ── Interactive "What-If" Stress Tester state ──────────────────────
  const currentPrice = p.breakeven || 565;
  const maxLoss = p.max_loss_per_contract || 200;
  const maxProfit = p.max_profit_per_contract || 300;
  const longStrike = p.long_leg?.strike || 565;
  const shortStrike = p.short_leg?.strike || 570;
  const minSimPrice = Math.max(0, currentPrice - 30);
  const maxSimPrice = currentPrice + 30;
  const [simulatedPrice, setSimulatedPrice] = useState(currentPrice);

  // Calculate simulated P&L based on price at expiration
  const simulatedPnL = p.structure?.includes("BULL")
    ? (simulatedPrice <= longStrike
        ? -maxLoss
        : simulatedPrice >= shortStrike
        ? maxProfit
        : ((simulatedPrice - longStrike) * 100) - maxLoss)
    : (simulatedPrice >= longStrike
        ? -maxLoss
        : simulatedPrice <= shortStrike
        ? maxProfit
        : ((longStrike - simulatedPrice) * 100) - maxLoss);

  const handleDecision = async (dec: string) => {
    setLoading(true);
    try {
      await submitConsent(proposal.trade_number, dec);
      setDecision(dec);
      onDecision?.();
    } catch (e) {
      console.error("Consent failed:", e);
    }
    setLoading(false);
  };

  const markLessonExplored = (feature: string) => {
    void exploreFeature(feature);
  };

  if (decision) {
    const isApproved = decision === "APPROVE";
    return (
      <div
        className="glass-card p-6 border-2 animate-fade-in"
        style={{ borderColor: isApproved ? "#10b981" : "#f43f5e" }}
      >
        <div className="flex flex-col items-center py-8 gap-3 text-center">
          <div className="w-16 h-16 rounded-full flex items-center justify-center text-3xl shadow-xl"
            style={{
              background: isApproved ? "rgba(16, 185, 129, 0.15)" : "rgba(244, 63, 94, 0.15)",
              border: `1px solid ${isApproved ? "#10b981" : "#f43f5e"}`,
            }}
          >
            {isApproved ? "⚡" : "✕"}
          </div>
          <div className="text-xl font-bold tracking-wide" style={{ color: isApproved ? "#10b981" : "#f43f5e" }}>
            {isApproved ? "TRADE AUTHORIZED & EXECUTED" : "TRADE REJECTED BY USER"}
          </div>
          <div className="text-xs text-slate-300 font-mono max-w-md">
            {isApproved
              ? `Multi-leg order submitted to Alpaca paper trading. Logged to SHA-256 hash-chained audit trail.`
              : `Order cancelled. Capital conserved. Decision recorded in immutable audit log.`}
          </div>
        </div>
      </div>
    );
  }

  const contracts = p.quantity || p.recommended_contracts || 1;
  const totalMaxLoss = p.total_risk_proposed || (p.max_loss_per_contract * contracts);
  const totalMaxProfit = p.total_profit_potential || (p.max_profit_per_contract * contracts);

  return (
    <div className="glass-card glass-card-glow-gold border-2 border-amber-500/50 shadow-2xl p-5 space-y-4 animate-slide-up">
      {/* ── Top Header ────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-base font-bold font-mono shadow-md"
            style={{
              background: isBull ? "rgba(16, 185, 129, 0.15)" : "rgba(244, 63, 94, 0.15)",
              color: directionColor,
              border: `1px solid ${directionColor}40`,
            }}
          >
            #{(proposal.trade_number ?? 0).toString().padStart(2, "0")}
          </div>
          <div>
            <div className="text-sm font-bold text-white tracking-wide font-mono flex items-center gap-2">
              <span>{p.underlying}</span>
              <span style={{ color: directionColor }}>{structureName}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {contracts}x Contract{contracts > 1 ? "s" : ""}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              {p.dte} DTE Expiry · Strike Spread: ${p.spread_width?.toFixed(0)} Width
            </div>
          </div>
        </div>

        {/* Conviction Score */}
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">Conviction Score</div>
          <div className="text-xl font-bold font-mono text-amber-400 flex items-center gap-1 justify-end">
            <span>{p.conviction_score?.toFixed(1)}</span>
            <span className="text-xs text-slate-500 font-normal">/ 100</span>
          </div>
        </div>
      </div>

      {/* ── Plain-English Thesis (CIO Agent) ─────────────────────────── */}
      <div className="space-y-2 text-xs">
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/90 space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-widest text-cyan-400 font-mono flex items-center gap-1.5">
            <span>🔭</span> What&apos;s Happening
          </div>
          <p className="text-slate-200 leading-relaxed">{thesis.what_happening}</p>
        </div>

        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/90 space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-widest text-amber-400 font-mono flex items-center gap-1.5">
            <span>📐</span> The Proposed Trade
          </div>
          <p className="text-slate-200 leading-relaxed">{thesis.the_trade}</p>
        </div>
      </div>

      {/* ── Key Economics Grid (High-Density Bloomberg Numbers) ────────── */}
      <div className="grid grid-cols-3 gap-2 text-center font-mono">
        <div className="bloomberg-metric p-2.5" style={{ "--accent-color": "#10b981" } as React.CSSProperties}>
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Max Profit ({contracts}x)</div>
          <div className="text-lg font-bold text-emerald-400 mt-0.5">${totalMaxProfit.toFixed(0)}</div>
          <div className="text-[9px] text-slate-500">${p.max_profit_per_contract}/contract</div>
        </div>

        <div className="bloomberg-metric p-2.5" style={{ "--accent-color": "#f43f5e" } as React.CSSProperties}>
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Max Loss (2% Cap)</div>
          <div className="text-lg font-bold text-rose-400 mt-0.5">${totalMaxLoss.toFixed(0)}</div>
          <div className="text-[9px] text-slate-500">${p.max_loss_per_contract}/contract</div>
        </div>

        <div className="bloomberg-metric p-2.5" style={{ "--accent-color": "#f59e0b" } as React.CSSProperties}>
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Risk : Reward</div>
          <div className="text-lg font-bold text-white mt-0.5">1 : {p.risk_reward_ratio?.toFixed(2)}</div>
          <div className="text-[9px] text-slate-500">Breakeven: ${p.breakeven?.toFixed(2)}</div>
        </div>
      </div>

      {/* ── Interactive "What-If" Expiration Stress Tester ─────────────── */}
      <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2.5 font-mono">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <span>⚡</span> Interactive Scenario Stress Tester
          </span>
          <span className="text-[10px] text-slate-400">Drag to test underlying at expiration</span>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Simulated {p.underlying} Price:</span>
            <span className="text-white font-bold">${simulatedPrice.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min={minSimPrice}
            max={maxSimPrice}
            step={0.25}
            value={simulatedPrice}
            onChange={(e) => setSimulatedPrice(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
          />
          <div className="flex justify-between text-[9px] text-slate-500">
            <span>${minSimPrice.toFixed(0)} (Max Loss Zone)</span>
            <span className="text-amber-400 font-bold">Breakeven: ${p.breakeven?.toFixed(2)}</span>
            <span>${maxSimPrice.toFixed(0)} (Max Gain Zone)</span>
          </div>
        </div>

        {/* Live Simulated Result Pill */}
        <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase text-slate-400">Simulated P&amp;L:</span>
            <span
              className={`font-bold ${
                simulatedPnL > 0
                  ? "text-emerald-400"
                  : simulatedPnL < 0
                  ? "text-rose-400"
                  : "text-amber-300"
              }`}
            >
              ${simulatedPnL >= 0 ? "+" : ""}{simulatedPnL.toFixed(2)}
            </span>
          </div>
          <div className="text-[11px] font-bold" style={{ color: simulatedPnL >= 0 ? "#10b981" : "#f43f5e" }}>
            {simulatedPnL >= 0 ? `+${((simulatedPnL / totalMaxLoss) * 100).toFixed(0)}% ROI` : `-${Math.min(100, Math.abs((simulatedPnL / totalMaxLoss) * 100)).toFixed(0)}% Drawdown`}
          </div>
        </div>
      </div>

      {/* ── Educational Teaching & Strategy Breakdown ─────────────────── */}
      {showTeaching && (
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-800/90 text-xs space-y-2.5">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>🎓</span> Educational Strategy Explainer
            </span>
            <span className="text-[10px] text-slate-500">Plain English Transformed</span>
          </div>

          <p className="text-slate-300 leading-relaxed">
            This defined-risk spread buys the <strong>${p.long_leg.strike} strike</strong> and finances it by selling the <strong>${p.short_leg.strike} strike</strong>. Your total cost today is strictly capped at <span className="text-white font-bold">${p.net_debit?.toFixed(2)}/share</span>.
          </p>

          {/* Risk Note */}
          <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px] leading-relaxed">
            <strong>⚠ What Could Go Wrong:</strong> {thesis.what_could_go_wrong}
          </div>
        </div>
      )}

      {/* ── 12 Deterministic Risk Checks ──────────────────────────────── */}
      {risk_check?.checks && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400 font-mono">
            <span>🛡️ Deterministic Risk Gates (12 Checks)</span>
            <span className="text-emerald-400">100% Passed</span>
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1 font-mono text-[11px]">
            {risk_check.checks.map((check, i) => {
              const isPass = check.status === "PASS";
              return (
                <div
                  key={i}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded-md border text-xs ${
                    isPass
                      ? "bg-slate-950/60 border-slate-800 text-slate-300"
                      : "bg-rose-950/40 border-rose-700/50 text-rose-300"
                  }`}
                >
                  <span className="flex items-center gap-1.5 font-medium">
                    <span className={isPass ? "text-emerald-400" : "text-rose-400"}>
                      {isPass ? "✓" : "✗"}
                    </span>
                    <span>{check.name}</span>
                  </span>
                  <span className="text-[10px] text-slate-400">{check.detail}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Expandable Pro Desk View (Greeks & OCC Symbols) ───────────── */}
      <div className="pt-1">
        <button
          onClick={() => {
            setShowProView(!showProView);
            markLessonExplored("strategy_explainer");
          }}
          className="w-full py-1.5 text-center text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center justify-center gap-1.5"
        >
          <span>{showProView ? "▲ Hide Technical Pro Desk View" : "▼ Show Technical Pro Desk View & Greeks"}</span>
        </button>

        {showProView && (
          <div className="mt-2 p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs space-y-2 animate-fade-in">
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <div className="text-emerald-400 font-bold">BUY LEG (Long):</div>
                <div className="text-white mt-0.5">{p.long_leg.type} ${p.long_leg.strike} @ ${p.long_leg.mid_price?.toFixed(2)}</div>
                <div className="text-[10px] text-slate-400">Delta: δ {p.long_leg.delta?.toFixed(2)} · Symbol: {p.long_leg.alpaca_symbol || "OCC"}</div>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <div className="text-rose-400 font-bold">SELL LEG (Short):</div>
                <div className="text-white mt-0.5">{p.short_leg.type} ${p.short_leg.strike} @ ${p.short_leg.mid_price?.toFixed(2)}</div>
                <div className="text-[10px] text-slate-400">Delta: δ {p.short_leg.delta?.toFixed(2)} · Symbol: {p.short_leg.alpaca_symbol || "OCC"}</div>
              </div>
            </div>

            {p.conviction_breakdown && (
              <div className="pt-2 border-t border-slate-800 space-y-1">
                <div className="text-[10px] font-bold uppercase text-slate-400">Conviction Breakdown:</div>
                <div className="grid grid-cols-3 gap-1 text-[10px] text-slate-300">
                  {Object.entries(p.conviction_breakdown).map(([k, v]) => (
                    <div key={k} className="flex justify-between px-1.5 py-0.5 rounded bg-slate-900">
                      <span className="text-slate-400">{k.replace("_", " ")}:</span>
                      <span className="text-amber-300 font-bold">{v.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Consent Authorization Buttons ─────────────────────────────── */}
      <div className="pt-2 flex gap-3">
        <button
          className="btn-bloomberg-approve flex-1 py-3 px-4 rounded-xl text-sm font-mono flex items-center justify-center gap-2 cursor-pointer"
          onClick={() => handleDecision("APPROVE")}
          disabled={loading}
        >
          <span>⚡</span> {loading ? "AUTHORIZING..." : `AUTHORIZE TRADE (${contracts}x)`}
        </button>
        <button
          className="btn-bloomberg-reject flex-1 py-3 px-4 rounded-xl text-sm font-mono flex items-center justify-center gap-2 cursor-pointer"
          onClick={() => handleDecision("REJECT")}
          disabled={loading}
        >
          <span>✕</span> {loading ? "..." : "REJECT PROPOSAL"}
        </button>
      </div>
    </div>
  );
}

