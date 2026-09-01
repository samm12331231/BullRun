"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TradeProposal {
  trade_number: number;
  proposal: {
    structure: string;
    underlying: string;
    direction: string;
    long_leg: { type: string; strike: number; delta: number; mid_price: number };
    short_leg: { type: string; strike: number; delta: number; mid_price: number };
    net_debit: number;
    spread_width: number;
    max_loss_per_contract: number;
    max_profit_per_contract: number;
    breakeven: number;
    risk_reward_ratio: number;
    dte: number;
    conviction_score: number;
    teaching?: {
      regime?: { title: string; explanation: string };
      strategy?: { title: string; explanation: string; legs?: { action: string; strike: number; meaning: string }[] };
      rejection?: { title: string; explanation: string };
    };
  };
  thesis: {
    what_happening: string;
    the_trade: string;
    the_numbers: string;
    why_now: string;
    what_could_go_wrong: string;
  };
  risk_check: {
    status: string;
    checks: { name: string; status: string; detail: string }[];
  };
  timestamp: string;
}

export interface PortfolioData {
  equity: number;
  cash: number;
  total_pnl: number;
  return_pct: number;
  open_positions: number;
  total_trades: number;
  win_rate: number;
  risk_used: number;
  risk_limit: number;
}

export interface LearningProgress {
  score: number;
  level: "Beginner" | "Intermediate" | "Advanced";
  explored_features: string[];
  next_feature: string | null;
}

export interface RegimeData {
  regime: string;
  confidence: number;
  reason: string;
  metrics: {
    adx: number;
    atr: number;
    rsi: number;
    current_price: number;
    ema_fast: number;
    ema_slow: number;
    macd: number;
    macd_histogram: number;
    macd_bullish: boolean;
    price_above_ema: boolean;
    ema_bullish: boolean;
  };
}

export interface AuditEntry {
  timestamp: string;
  event: string;
  trade_number: number;
  decision?: string;
  structure?: string;
  regime?: string;
  status?: string;
  pnl?: number;
  reason?: string;
}

export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [pendingProposal, setPendingProposal] = useState<TradeProposal | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnected(true);
        console.log("[WS] Connected to BullRun");
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          setLastMessage(msg);

          if (msg.type === "trade_proposal") {
            setPendingProposal(msg as unknown as TradeProposal);
          }
          if (msg.type === "consent_decision") {
            setPendingProposal(null);
          }
        } catch {}
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimeout.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      reconnectTimeout.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { connected, lastMessage, pendingProposal, setPendingProposal, sendMessage };
}

// ── REST API helpers ──────────────────────────────────────────────────────

export async function fetchPortfolio(): Promise<PortfolioData> {
  const res = await fetch(`${API_URL}/api/portfolio`);
  return res.json();
}

export async function fetchTrades(): Promise<{ trades: AuditEntry[] }> {
  const res = await fetch(`${API_URL}/api/trades`);
  return res.json();
}

export async function fetchRegime(): Promise<RegimeData> {
  const res = await fetch(`${API_URL}/api/regime`);
  return res.json();
}

export async function fetchRiskLimits() {
  const res = await fetch(`${API_URL}/api/risk-limits`);
  return res.json();
}

export async function submitConsent(
  tradeNumber: number,
  decision: string,
  reason = ""
) {
  const res = await fetch(`${API_URL}/api/consent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      trade_number: tradeNumber,
      decision,
      reason,
    }),
  });
  return res.json();
}

export async function fetchAuditSummary() {
  const res = await fetch(`${API_URL}/api/audit-summary`);
  return res.json();
}

export async function fetchLearningProgress(): Promise<LearningProgress> {
  const res = await fetch(`${API_URL}/api/learning/progress`);
  return res.json();
}
