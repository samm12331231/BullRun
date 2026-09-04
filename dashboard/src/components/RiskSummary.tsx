"use client";

import { useState } from "react";
import { CheckCircle, XCircle, ChevronDown, ChevronUp, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/cn";

interface Gate {
  name: string;
  status: string;
  detail: string;
  critical?: boolean;
}

interface RiskSummaryProps {
  checks: Gate[];
  allPassed?: boolean;
  failedChecks?: string[];
}

export default function RiskSummary({ checks, allPassed, failedChecks }: RiskSummaryProps) {
  const [expanded, setExpanded] = useState(false);
  const passed = checks.filter(c => c.status === "PASS").length;
  const blocked = checks.length - passed;

  return (
    <div className="space-y-2">
      {/* Compact summary row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-[var(--muted)]" />
          <span className="text-[11px] font-mono font-semibold text-[var(--muted-strong)]">
            {checks.length} deterministic gates
          </span>
        </div>
        <div className="flex items-center gap-2 text-[11px] font-mono">
          <span className="text-[var(--accent)]">{passed} passed</span>
          {blocked > 0 && (
            <>
              <span className="text-[var(--border)]">·</span>
              <span className="text-[var(--danger)]">{blocked} blocked</span>
            </>
          )}
        </div>
      </div>

      {/* Accordion toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[11px] font-mono text-[var(--info)] hover:text-[var(--text)] transition-colors cursor-pointer bg-transparent border-none p-0"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? "Hide risk checks" : "View risk checks"}
      </button>

      {/* Gate detail */}
      {expanded && (
        <div className="space-y-1 mt-2">
          {checks.map((check, i) => {
            const isPass = check.status === "PASS";
            return (
              <div
                key={i}
                className={cn(
                  "flex items-center justify-between px-3 py-2 rounded-lg border text-[11px] font-mono",
                  isPass
                    ? "bg-[var(--surface)] border-[var(--border-subtle)] text-[var(--muted-strong)]"
                    : check.critical
                      ? "bg-[var(--danger-soft)] border-[rgba(241,116,122,0.2)] text-[var(--danger)]"
                      : "bg-[var(--warning-soft)] border-[rgba(240,184,90,0.2)] text-[var(--warning)]"
                )}
              >
                <span className="flex items-center gap-1.5">
                  {isPass ? (
                    <CheckCircle className="w-3.5 h-3.5 text-[var(--accent)] shrink-0" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 shrink-0" />
                  )}
                  <span className="font-medium">{check.name}</span>
                </span>
                <span className="text-[10px] text-[var(--muted)]">{check.detail}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Safety statement */}
      <p className="text-[10px] font-mono text-[var(--muted)] leading-relaxed">
        AI proposes. Deterministic controls decide. Human consent is required before paper execution.
      </p>
    </div>
  );
}
