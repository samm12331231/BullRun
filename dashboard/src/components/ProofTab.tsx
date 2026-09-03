"use client";

import { useEffect, useState } from "react";
import { fetchProof, fetchSafetyChallenge, type ProofData, type SafetyChallenge } from "@/lib/useWebSocket";

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
      <div className="p-4 text-center text-slate-500 text-xs font-mono">
        Loading proof data...
      </div>
    );
  }

  return (
    <div className="space-y-4 text-xs">
      {/* Account Evidence */}
      <section className="glass-card p-3 rounded-xl">
        <h3 className="text-[10px] uppercase text-slate-500 font-semibold mb-2 tracking-wider">
          🏦 Account Evidence
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-slate-500 text-[10px]">Type</div>
            <div className="text-emerald-400 font-bold font-mono">
              {proof?.account.type || "—"}
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-[10px]">Data Mode</div>
            <div className={`font-bold font-mono ${
              proof?.account.data_mode === "live" ? "text-emerald-400" : "text-amber-400"
            }`}>
              {proof?.account.data_mode?.toUpperCase() || "—"}
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-[10px]">Starting Equity</div>
            <div className="text-slate-200 font-bold font-mono">
              ${proof?.performance.starting_equity.toLocaleString() || "—"}
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-[10px]">Current Equity</div>
            <div className={`font-bold font-mono ${
              (proof?.performance.current_equity ?? 0) >= 100000 ? "text-emerald-400" : "text-rose-400"
            }`}>
              ${proof?.performance.current_equity?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "—"}
            </div>
          </div>
        </div>
      </section>

      {/* Performance */}
      <section className="glass-card p-3 rounded-xl">
        <h3 className="text-[10px] uppercase text-slate-500 font-semibold mb-2 tracking-wider">
          📊 Performance
        </h3>
        <div className="grid grid-cols-3 gap-2">
          <MetricCell label="Total P&L" value={`$${proof?.performance.combined_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "0"}`} positive={proof ? proof.performance.combined_pnl >= 0 : true} />
          <MetricCell label="Win Rate" value={`${proof?.performance.win_rate || 0}%`} />
          <MetricCell label="Open Positions" value={`${proof?.performance.open_positions || 0}`} />
          <MetricCell label="Closed Trades" value={`${proof?.performance.closed_positions || 0}`} />
          <MetricCell label="Total Return" value={`${proof?.performance.total_return_pct || 0}%`} positive={proof ? proof.performance.total_return_pct >= 0 : true} />
          <MetricCell label="Unrealized" value={`$${proof?.performance.unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "0"}`} positive={proof ? proof.performance.unrealized_pnl >= 0 : true} />
        </div>
      </section>

      {/* Risk Engine Stats */}
      <section className="glass-card p-3 rounded-xl">
        <h3 className="text-[10px] uppercase text-slate-500 font-semibold mb-2 tracking-wider">
          🛡️ Risk Engine Statistics
        </h3>
        <div className="grid grid-cols-2 gap-2 mb-2">
          <div>
            <div className="text-slate-500 text-[10px]">Proposals Checked</div>
            <div className="text-slate-200 font-bold font-mono text-lg">
              {proof?.risk_engine.total_proposals_checked || 0}
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-[10px]">Blocked by Gates</div>
            <div className="text-rose-400 font-bold font-mono text-lg">
              {proof?.risk_engine.total_blocked || 0}
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-[10px]">Pass Rate</div>
            <div className="text-slate-200 font-bold font-mono">
              {proof?.risk_engine.pass_rate_pct || 0}%
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-[10px]">Audit Chain</div>
            <div className={`font-bold font-mono ${
              proof?.risk_engine.audit_chain_valid ? "text-emerald-400" : "text-rose-400"
            }`}>
              {proof?.risk_engine.audit_chain_valid ? "✓ VALID" : "✗ INVALID"}
            </div>
          </div>
        </div>
        {proof?.risk_engine.blocked_by_gate && Object.keys(proof.risk_engine.blocked_by_gate).length > 0 && (
          <div>
            <div className="text-slate-500 text-[10px] mb-1">Blocked by Gate</div>
            <div className="space-y-1">
              {Object.entries(proof.risk_engine.blocked_by_gate).map(([gate, count]) => (
                <div key={gate} className="flex justify-between text-[10px]">
                  <span className="text-slate-400">{gate}</span>
                  <span className="text-rose-400 font-mono font-bold">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Consent & Execution */}
      <section className="glass-card p-3 rounded-xl">
        <h3 className="text-[10px] uppercase text-slate-500 font-semibold mb-2 tracking-wider">
          ✅ Consent & Execution
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <MetricCell label="Approvals" value={`${proof?.consent.approvals || 0}`} />
          <MetricCell label="Rejections" value={`${proof?.consent.rejections || 0}`} />
          <MetricCell label="Total Orders" value={`${proof?.execution.total_orders || 0}`} />
          <MetricCell label="Successful" value={`${proof?.execution.successful_orders || 0}`} />
        </div>
      </section>

      {/* Safety Challenge */}
      {challenge && (
        <section className="glass-card p-3 rounded-xl border border-amber-500/30">
          <h3 className="text-[10px] uppercase text-amber-400 font-semibold mb-2 tracking-wider">
            ⚡ Safety Challenge: 18% Risk Test
          </h3>
          <p className="text-[10px] text-slate-400 mb-2">{challenge.description}</p>
          <div className="space-y-2">
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-2">
              <div className="text-[10px] text-rose-400 font-bold mb-1">OVERSIZED PROPOSAL — {challenge.oversized.risk_pct}% RISK</div>
              <div className="text-slate-300 font-mono">
                {String(challenge.oversized.proposal.quantity)} contracts × ${Number(challenge.oversized.proposal.max_loss_per_contract)} = ${Number(challenge.oversized.proposal.total_risk_proposed)}
              </div>
              <div className={`text-xs font-bold mt-1 ${challenge.oversized.verdict === "REJECT" ? "text-rose-400" : "text-emerald-400"}`}>
                VERDICT: {challenge.oversized.verdict}
                {challenge.oversized.failed_gates.length > 0 && (
                  <span className="text-[10px] font-normal ml-2">
                    — blocked by: {challenge.oversized.failed_gates.join(", ")}
                  </span>
                )}
              </div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2">
              <div className="text-[10px] text-emerald-400 font-bold mb-1">RESIZED TO SAFE — {challenge.resized.risk_pct}% RISK</div>
              <div className="text-slate-300 font-mono">
                {String(challenge.resized.proposal.quantity)} contracts × ${Number(challenge.resized.proposal.max_loss_per_contract)} = ${Number(challenge.resized.proposal.total_risk_proposed)}
              </div>
              <div className={`text-xs font-bold mt-1 ${challenge.resized.verdict === "PASS" ? "text-emerald-400" : "text-rose-400"}`}>
                VERDICT: {challenge.resized.verdict}
              </div>
            </div>
          </div>
          <p className="text-[10px] text-amber-400 mt-2 italic">{challenge.lesson}</p>
        </section>
      )}

      {/* Footer */}
      <div className="text-center text-[10px] text-slate-600 font-mono">
        Data refreshed every 30s · Commit: {proof?.commit_hash || "HEAD"} · {proof ? new Date(proof.timestamp).toLocaleTimeString() : ""}
      </div>
    </div>
  );
}

function MetricCell({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <div>
      <div className="text-slate-500 text-[10px]">{label}</div>
      <div className={`font-bold font-mono ${
        positive === true ? "text-emerald-400" : positive === false ? "text-rose-400" : "text-slate-200"
      }`}>
        {value}
      </div>
    </div>
  );
}
