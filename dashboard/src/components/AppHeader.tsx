"use client";

import { ShieldCheck, Activity, Database, CircleAlert } from "lucide-react";
import type { TickerQuote, RegimeData } from "@/lib/useWebSocket";

interface AppHeaderProps {
  connected: boolean;
  scanning: boolean;
  dataMode?: string;
  auditValid?: boolean;
  regime?: RegimeData | null;
  tickers: TickerQuote[];
  onScan: () => void;
  regimeBadge: (r: string) => React.ReactNode;
}

export default function AppHeader({
  connected,
  scanning,
  dataMode,
  auditValid,
  regime,
  tickers,
  onScan,
  regimeBadge,
}: AppHeaderProps) {
  return (
    <header className="border-b border-[var(--border)] bg-[var(--surface)] sticky top-0 z-50">
      {/* Main header row */}
      <div className="flex items-center justify-between px-4 md:px-6 py-3">
        {/* Left: brand */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-soft)] border border-[rgba(80,213,168,0.2)] flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4 h-4 text-[var(--accent)]" />
          </div>
          <div className="min-w-0">
            <div className="flex items-baseline gap-2">
              <span className="text-base font-black tracking-tight text-[var(--text)] font-mono">
                BullRun
              </span>
              <span className="text-[10px] font-mono text-[var(--muted)] hidden sm:inline">
                Governed AI options paper trading
              </span>
            </div>
          </div>
        </div>

        {/* Center: scan button */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={onScan}
            disabled={scanning}
            className="px-3 py-1.5 rounded-lg bg-[var(--surface-raised)] border border-[var(--border)] text-xs font-mono font-semibold text-[var(--muted-strong)] hover:text-[var(--text)] hover:border-[var(--muted)] transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <span>{scanning ? "Scanning..." : "Trigger Scan"}</span>
          </button>
          {regime && regimeBadge(
            (regime.metrics?.adx != null && regime.metrics.adx > 25)
              ? regime.regime
              : "WATCHING"
          )}
        </div>

        {/* Right: status cluster */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[var(--accent-soft)] border border-[rgba(80,213,168,0.2)]">
            <Database className="w-3 h-3 text-[var(--accent)]" />
            <span className="text-[10px] font-mono font-bold text-[var(--accent)] uppercase">
              Alpaca Paper
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[var(--surface-raised)] border border-[var(--border)]">
            {connected ? (
              <Activity className="w-3 h-3 text-[var(--accent)] pulse" />
            ) : (
              <CircleAlert className="w-3 h-3 text-[var(--warning)]" />
            )}
            <span className="text-[10px] font-mono font-semibold text-[var(--muted-strong)]">
              {dataMode?.toUpperCase() || (connected ? "LIVE" : "OFFLINE")}
            </span>
          </div>

          {auditValid !== undefined && (
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded-md bg-[var(--surface-raised)] border border-[var(--border)]">
              <ShieldCheck className="w-3 h-3 text-[var(--accent)]" />
              <span className="text-[10px] font-mono font-semibold text-[var(--muted-strong)]">
                {auditValid ? "AUDIT VALID" : "AUDIT UNAVAILABLE"}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Ticker tape */}
      {tickers.length > 0 && (
        <div className="flex items-center gap-5 px-4 md:px-6 py-1.5 bg-[var(--bg)] border-t border-[var(--border-subtle)] text-[11px] font-mono overflow-x-auto">
          <span className="text-[10px] text-[var(--muted)] uppercase tracking-widest font-bold shrink-0">
            Live
          </span>
          {tickers.filter(q => q.price != null).map((quote) => {
            const isPos = (quote.change_pct ?? 0) >= 0;
            return (
              <div key={quote.symbol} className="flex items-center gap-1.5 shrink-0">
                <span className="font-semibold text-[var(--text)]">{quote.symbol}</span>
                <span className="text-[var(--muted-strong)]">${(quote.price ?? 0).toFixed(2)}</span>
                <span className={`text-[10px] font-bold ${isPos ? "text-[var(--accent)]" : "text-[var(--danger)]"}`}>
                  {isPos ? "+" : ""}{(quote.change_pct ?? 0).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      )}
    </header>
  );
}
