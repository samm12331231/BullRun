"use client";

import { useState } from "react";
import type { TradeProposal } from "@/lib/useWebSocket";
import { submitConsent } from "@/lib/useWebSocket";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TradeCardProps {
  proposal: TradeProposal;
  onDecision?: () => void;
}

export default function TradeCard({ proposal, onDecision }: TradeCardProps) {
  const [loading, setLoading] = useState(false);
  const [decision, setDecision] = useState<string | null>(null);
  const [showWhy, setShowWhy] = useState(false);

  const { proposal: p, thesis, risk_check } = proposal;
  const structureName = p.structure?.replace(/_/g, " ") ?? "SPREAD";
  const isBull = p.structure?.includes("CALL");
  const color = isBull ? "#22c55e" : "#ef4444";

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
    void fetch(`${API_URL}/api/learning/explore/${feature}`, { method: "POST" });
  };

  if (decision) {
    return (
      <div className="card" style={{ borderColor: decision === "APPROVE" ? "#22c55e" : "#ef4444" }}>
        <div className="flex flex-col items-center py-8 gap-3">
          <div className="text-4xl">{decision === "APPROVE" ? "✅" : "❌"}</div>
          <div className="text-lg font-bold" style={{ color: decision === "APPROVE" ? "#22c55e" : "#ef4444" }}>
            {decision === "APPROVE" ? "Trade Approved" : "Trade Rejected"}
          </div>
          <div className="text-sm text-[var(--text-secondary)]">
            {decision === "APPROVE"
              ? "Submitting to Alpaca paper trading..."
              : "No order submitted. Trade logged."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ borderColor: "var(--gold)", borderWidth: "2px" }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold"
            style={{ background: `${color}22`, color }}
          >
            #{proposal.trade_number}
          </div>
          <div>
            <div className="text-sm font-bold text-white">{p.underlying} {structureName}</div>
            <div className="text-xs text-[var(--text-muted)]">
              {p.dte} DTE · {p.direction}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-[var(--text-muted)]">Conviction</div>
          <div className="text-lg font-bold font-mono" style={{ color: "var(--gold)" }}>
            {p.conviction_score?.toFixed(1)}
          </div>
        </div>
      </div>

      {/* What's Happening */}
      <div className="mb-3 p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
        <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-1">
          What&apos;s Happening
        </div>
        <div className="text-sm text-[var(--text-primary)] leading-relaxed">
          {thesis.what_happening}
        </div>
      </div>

      {/* The Trade */}
      <div className="mb-3 p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
        <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-1">
          The Trade
        </div>
        <div className="text-sm text-[var(--text-primary)] leading-relaxed">
          {thesis.the_trade}
        </div>
      </div>

      {/* Numbers */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="metric-box">
          <div className="metric-value text-green-400" style={{ fontSize: "20px" }}>
            ${p.max_profit_per_contract}
          </div>
          <div className="metric-label">Max Gain</div>
        </div>
        <div className="metric-box">
          <div className="metric-value text-red-400" style={{ fontSize: "20px" }}>
            ${p.max_loss_per_contract}
          </div>
          <div className="metric-label">Max Loss</div>
        </div>
        <div className="metric-box">
          <div className="metric-value text-white" style={{ fontSize: "20px" }}>
            1:{p.risk_reward_ratio?.toFixed(1)}
          </div>
          <div className="metric-label">Risk:Reward</div>
        </div>
      </div>

      {/* Breakeven */}
      <div className="mb-3 text-xs font-mono text-[var(--text-secondary)] text-center">
        Breakeven: <span className="text-white">${p.breakeven?.toFixed(2)}</span>
        <span className="mx-2">·</span>
        Net debit: <span className="text-white">${p.net_debit?.toFixed(2)}</span>
      </div>

      {/* Risk Engine */}
      {risk_check?.checks && (
        <div className="mb-4">
          <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-2">
            Risk Engine
          </div>
          {risk_check.checks.map((check, i) => (
            <div
              key={i}
              className={`risk-check ${check.status === "PASS" ? "pass" : "fail"}`}
            >
              <span className="flex items-center gap-2">
                <span>{check.status === "PASS" ? "✓" : "✗"}</span>
                <span>{check.name}</span>
              </span>
              <span className="text-[var(--text-muted)]">{check.detail}</span>
            </div>
          ))}
        </div>
      )}

      {/* Why Now */}
      <div className="mb-3 p-3 rounded-lg" style={{ background: "var(--bg-secondary)" }}>
        <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-1">
          Why Now
        </div>
        <div className="text-sm text-[var(--text-primary)] leading-relaxed">
          {thesis.why_now}
        </div>
      </div>

      {/* What Could Go Wrong */}
      <div className="mb-4 p-3 rounded-lg" style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.15)" }}>
        <div className="text-[10px] font-bold uppercase tracking-widest text-red-400 mb-1">
          What Could Go Wrong
        </div>
        <div className="text-sm text-[var(--text-primary)] leading-relaxed">
          {thesis.what_could_go_wrong}
        </div>
      </div>

      {/* Why button */}
      <button
        onClick={() => {
          setShowWhy(!showWhy);
          markLessonExplored("strategy_explainer");
        }}
        className="w-full mb-3 py-2 text-sm text-[var(--blue)] hover:underline"
      >
        {showWhy ? "Hide Details" : "Why this trade?"}
      </button>

      {showWhy && (
        <div className="mb-4 p-3 rounded-lg font-mono text-xs" style={{ background: "var(--bg-secondary)" }}>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-[var(--text-muted)]">Buy:</span>{" "}
              <span className="text-green-400">
                {p.long_leg.type} {p.long_leg.strike} @ ${p.long_leg.mid_price?.toFixed(2)} (δ {p.long_leg.delta?.toFixed(2)})
              </span>
            </div>
            <div>
              <span className="text-[var(--text-muted)]">Sell:</span>{" "}
              <span className="text-red-400">
                {p.short_leg.type} {p.short_leg.strike} @ ${p.short_leg.mid_price?.toFixed(2)} (δ {p.short_leg.delta?.toFixed(2)})
              </span>
            </div>
          </div>
          <div className="mt-2 text-[var(--text-muted)]">
            Spread width: ${p.spread_width?.toFixed(0)} · Expiry: {p.dte} DTE
          </div>
          {p.teaching?.strategy && (
            <div className="mt-3 pt-3 border-t border-[var(--border)] font-sans text-sm text-[var(--text-primary)] leading-relaxed">
              <div className="text-[10px] font-bold uppercase tracking-widest text-cyan-400 mb-1">
                Learn this strategy
              </div>
              {p.teaching.strategy.explanation}
            </div>
          )}
        </div>
      )}

      {/* Consent Buttons */}
      <div className="flex gap-3">
        <button
          className="btn-approve flex-1"
          onClick={() => handleDecision("APPROVE")}
          disabled={loading}
        >
          {loading ? "..." : "Approve Trade"}
        </button>
        <button
          className="btn-reject flex-1"
          onClick={() => handleDecision("REJECT")}
          disabled={loading}
        >
          {loading ? "..." : "Reject"}
        </button>
      </div>
    </div>
  );
}
