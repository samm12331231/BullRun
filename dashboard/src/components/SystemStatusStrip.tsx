"use client";

import { CircleAlert, CheckCircle, Clock } from "lucide-react";

interface SystemStatusStripProps {
  dataMode?: string;
  accountDataAvailable?: boolean;
  retrievedAt?: string | null;
}

export default function SystemStatusStrip({
  dataMode,
  accountDataAvailable,
  retrievedAt,
}: SystemStatusStripProps) {
  const isUnavailable = dataMode === "unavailable" || accountDataAvailable === false;

  return (
    <div className={`flex flex-wrap items-center gap-x-4 gap-y-1 px-4 md:px-6 py-2 text-[11px] font-mono border-b ${
      isUnavailable
        ? "bg-[var(--danger-soft)] border-[rgba(241,116,122,0.2)] text-[var(--danger)]"
        : "bg-[var(--surface)] border-[var(--border-subtle)] text-[var(--muted)]"
    }`}>
      {isUnavailable ? (
        <>
          <CircleAlert className="w-3.5 h-3.5 shrink-0" />
          <span className="font-semibold">Account data unavailable — execution blocked</span>
        </>
      ) : (
        <>
          <CheckCircle className="w-3.5 h-3.5 text-[var(--accent)] shrink-0" />
          <span>Paper account</span>
          <span className="text-[var(--border)]">|</span>
          <span>Verified account data</span>
          <span className="text-[var(--border)]">|</span>
          <span>Risk engine online</span>
          {retrievedAt && (
            <>
              <span className="text-[var(--border)]">|</span>
              <Clock className="w-3 h-3 shrink-0" />
              <span suppressHydrationWarning>Last retrieved: {new Date(retrievedAt).toLocaleTimeString()}</span>
            </>
          )}
        </>
      )}
    </div>
  );
}
