"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck,
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowRight,
  FileCheck,
} from "lucide-react";
import { fetchProof, fetchSafetyChallenge, type ProofData, type SafetyChallenge } from "@/lib/useWebSocket";
import StatusBadge from "./StatusBadge";
import { cn } from "@/lib/cn";

export default function ProofTab() {
  const [proof, setProof] = useState<ProofData | null>(null);
  const [challenge, setChallenge] = useState<SafetyChallenge | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const [p, c] = await Promise.all([fetchProof(), fetchSafetyChallenge()]);
      setProof(p);
      setChallenge(c);
      setLoading(false);
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !proof) {
    return (
      <div className="card p-8 text-center">
        <div className="text-xs font-mono text-[var(--muted)]">Retrieving verified account data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4 text-xs">
      {/* ── Proof Header ─────────────────────────────────────────── */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-1">
          <FileCheck className="w-4 h-4 text-[var(--accent)]" />
          <h3 className="text-sm font-bold text-[var(--text)]">Proof & Safety</h3>
        </div>
        <p className="text-[11px] text-[var(--muted)] mb-3">
          Verified controls, account evidence, and execution trace.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge variant="accent">
            <ShieldCheck className="w-3 h-3" />
            {proof?.account.type || "Alpaca Paper Trading"}
          </StatusBadge>
          <StatusBadge variant={proof?.account.data_mode === "live" ? "accent" : "warning"}>
            <Activity className="w-3 h-3" />
            {proof?.account.data_mode?.toUpperCase() || "UNKNOWN"} account data
          </StatusBadge>
          {proof?.account.retrieved_at && (
            <span className="text-[10px] font-mono text-[var(--muted)]">
              Retrieved: {new Date(proof.account.retrieved_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* ── Verification Metrics (2x2) ──────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <MetricBox
          label="Starting Equity"
          value={`$${proof?.performance.starting_equity.toLocaleString() || "—"}`}
          icon={<DollarSign className="w-3.5 h-3.5" />}
        />
        <MetricBox
          label="Current Equity"
          value={`$${proof?.performance.current_equity?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "—"}`}
          variant={(proof?.performance.current_equity ?? 0) >= 100000 ? "accent" : "danger"}
          icon={<TrendingUp className="w-3.5 h-3.5" />}
        />
        <MetricBox
          label="Total P&L"
          value={`$${proof?.performance.combined_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "0"}`}
          variant={proof?.performance.combined_pnl != null ? (proof.performance.combined_pnl >= 0 ? "accent" : "danger") : ("default" as const)}
          icon={proof?.performance.combined_pnl != null && proof.performance.combined_pnl >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
        />
        <MetricBox
          label="Audit Chain"
          value={proof?.risk_engine.audit_chain_valid ? "VALID" : "UNAVAILABLE"}
          variant={proof?.risk_engine.audit_chain_valid ? "accent" : "danger"}
          icon={<ShieldCheck className="w-3.5 h-3.5" />}
        />
      </div>

      {/* ── Risk Enforcement ─────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <span className="card-title flex items-center gap-1.5">
            <BarChart3 className="w-3.5 h-3.5" />
            Risk Enforcement
          </span>
          <span className="text-[10px] font-mono text-[var(--muted)]">Current server session</span>
        </div>
        <div className="card-body space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <StatCell label="Proposals checked" value={proof?.risk_engine.total_proposals_checked || 0} />
            <StatCell label="Blocked by gates" value={proof?.risk_engine.total_blocked || 0} variant="danger" />
            <StatCell label="Pass rate" value={`${proof?.risk_engine.pass_rate_pct || 0}%`} />
          </div>
          {proof?.risk_engine.blocked_by_gate && Object.keys(proof.risk_engine.blocked_by_gate).length > 0 && (
            <div>
              <div className="text-[10px] font-mono text-[var(--muted)] mb-1.5 uppercase tracking-wide">Blocked by gate</div>
              <div className="space-y-1">
                {Object.entries(proof.risk_engine.blocked_by_gate).map(([gate, count]) => (
                  <div key={gate} className="flex justify-between items-center text-[11px] font-mono px-2 py-1 rounded bg-[var(--surface-raised)]">
                    <span className="text-[var(--muted-strong)]">{gate}</span>
                    <span className="text-[var(--danger)] font-bold">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Consent & Execution ──────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <span className="card-title flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5" />
            Consent &amp; Execution
          </span>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCell label="Approvals" value={proof?.consent.approvals || 0} />
            <StatCell label="Rejections" value={proof?.consent.rejections || 0} variant="danger" />
            <StatCell label="Total orders" value={proof?.execution.total_orders || 0} />
            <StatCell label="Successful" value={proof?.execution.successful_orders || 0} variant="accent" />
          </div>
        </div>
      </div>

      {/* ── Safety Challenge ─────────────────────────────────────── */}
      {challenge && (
        <div className="card border-[rgba(240,184,90,0.3)]">
          <div className="card-header">
            <span className="card-title flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
              Oversized Position Risk Test
            </span>
          </div>
          <div className="card-body space-y-3">
            <p className="text-[11px] text-[var(--muted)] leading-relaxed">{challenge.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-3 items-start">
              {/* Left: Oversized proposal */}
              <div className="rounded-xl p-3 border bg-[var(--danger-soft)] border-[rgba(241,116,122,0.2)]">
                <div className="text-[10px] font-mono font-bold text-[var(--danger)] uppercase tracking-wide mb-2">
                  AI Proposal
                </div>
                <div className="text-[11px] font-mono font-bold text-[var(--text)] mb-1">
                  Oversized options position
                </div>
                <div className="text-[11px] font-mono text-[var(--muted-strong)]">
                  {String(challenge.oversized.proposal.quantity)} contracts · ${Number(challenge.oversized.proposal.total_risk_proposed)} risk
                </div>
                <div className="text-[11px] font-mono text-[var(--danger)] mt-1">
                  {challenge.oversized.risk_pct}% of account equity
                </div>
                <div className={cn(
                  "mt-2 text-[11px] font-mono font-bold",
                  challenge.oversized.verdict === "REJECT" ? "text-[var(--danger)]" : "text-[var(--accent)]"
                )}>
                  Verdict: {challenge.oversized.verdict}
                  {challenge.oversized.failed_gates.length > 0 && (
                    <span className="text-[10px] font-normal text-[var(--muted)] ml-1">
                      — {challenge.oversized.failed_gates.join(", ")}
                    </span>
                  )}
                </div>
              </div>

              {/* Arrow */}
              <div className="hidden md:flex items-center justify-center pt-8">
                <ArrowRight className="w-5 h-5 text-[var(--muted)]" />
              </div>
              <div className="flex md:hidden items-center justify-center py-1">
                <ArrowRight className="w-5 h-5 text-[var(--muted)] rotate-90" />
              </div>

              {/* Right: Resized */}
              <div className="rounded-xl p-3 border bg-[var(--accent-soft)] border-[rgba(80,213,168,0.2)]">
                <div className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase tracking-wide mb-2">
                  System Enforcement
                </div>
                <div className="text-[11px] font-mono font-bold text-[var(--text)] mb-1">
                  Risk-limited alternative
                </div>
                <div className="text-[11px] font-mono text-[var(--muted-strong)]">
                  {String(challenge.resized.proposal.quantity)} contracts · ${Number(challenge.resized.proposal.total_risk_proposed)} risk
                </div>
                <div className="text-[11px] font-mono text-[var(--accent)] mt-1">
                  {challenge.resized.risk_pct}% of account equity
                </div>
                <div className={cn(
                  "mt-2 text-[11px] font-mono font-bold",
                  challenge.resized.verdict === "PASS" ? "text-[var(--accent)]" : "text-[var(--danger)]"
                )}>
                  Verdict: {challenge.resized.verdict}
                </div>
              </div>
            </div>

            {/* Conclusion callout */}
            <div className="p-3 rounded-lg bg-[var(--surface-raised)] border border-[var(--border)]">
              <p className="text-[11px] text-[var(--muted-strong)] leading-relaxed font-mono">
                BullRun does not rely on a model prompt to enforce risk. Unsafe sizing is rejected by deterministic controls before execution.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-[10px] text-[var(--muted)] font-mono">
        Commit: {proof?.commit_hash || "HEAD"} · {proof ? new Date(proof.timestamp).toLocaleTimeString() : ""}
      </div>
    </div>
  );
}

/* ── Internal helpers ──────────────────────────────────────────────── */

function MetricBox({ label, value, variant = "default", icon }: {
  label: string;
  value: string;
  variant?: "default" | "accent" | "danger" | "warning";
  icon?: React.ReactNode;
}) {
  const colors = {
    default: "text-[var(--text)]",
    accent: "text-[var(--accent)]",
    danger: "text-[var(--danger)]",
    warning: "text-[var(--warning)]",
  };
  return (
    <div className="card p-3">
      <div className="flex items-center gap-1.5 mb-2">
        {icon && <span className="text-[var(--muted)]">{icon}</span>}
        <span className="text-[10px] font-mono uppercase tracking-wide text-[var(--muted)]">{label}</span>
      </div>
      <div className={cn("text-lg font-bold font-mono", colors[variant])}>{value}</div>
    </div>
  );
}

function StatCell({ label, value, variant = "default" }: {
  label: string;
  value: number | string;
  variant?: "default" | "accent" | "danger";
}) {
  const colors = {
    default: "text-[var(--text)]",
    accent: "text-[var(--accent)]",
    danger: "text-[var(--danger)]",
  };
  return (
    <div>
      <div className="text-[10px] font-mono text-[var(--muted)] uppercase">{label}</div>
      <div className={cn("text-base font-bold font-mono mt-0.5", colors[variant])}>{value}</div>
    </div>
  );
}
