"use client";

import { useEffect, useRef, useCallback, useState } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TickerQuote {
  symbol: string;
  price: number;
  change_pct: number;
}

export interface TradeProposal {
  trade_number: number;
  proposal: {
    structure: string;
    underlying: string;
    direction: string;
    long_leg: { type: string; strike: number; delta: number; mid_price: number; alpaca_symbol?: string };
    short_leg: { type: string; strike: number; delta: number; mid_price: number; alpaca_symbol?: string };
    net_debit: number;
    spread_width: number;
    max_loss_per_contract: number;
    max_profit_per_contract: number;
    breakeven: number;
    risk_reward_ratio: number;
    dte: number;
    conviction_score: number;
    conviction_breakdown?: Record<string, number>;
    quantity?: number;
    recommended_contracts?: number;
    total_risk_proposed?: number;
    total_profit_potential?: number;
    teaching?: {
      regime?: { title: string; explanation: string; facts?: string[] };
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
    checks: { name: string; status: string; detail: string; critical?: boolean }[];
    all_passed?: boolean;
    failed_checks?: string[];
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
    atr_20avg?: number;
    atr_ratio?: number;
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

export async function fetchTickers(): Promise<TickerQuote[]> {
  try {
    const res = await fetch(`${API_URL}/api/market/tickers`);
    const data = await res.json();
    return data.tickers || [];
  } catch {
    return [
      { symbol: "SPY", price: 565.40, change_pct: 0.42 },
      { symbol: "QQQ", price: 482.15, change_pct: 0.68 },
      { symbol: "IWM", price: 218.90, change_pct: -0.15 },
      { symbol: "VIX", price: 14.85, change_pct: -3.20 },
      { symbol: "NVDA", price: 128.50, change_pct: 1.80 },
      { symbol: "AAPL", price: 224.30, change_pct: 0.50 },
      { symbol: "MSFT", price: 448.20, change_pct: 0.35 },
      { symbol: "TSLA", price: 214.80, change_pct: -0.85 },
    ];
  }
}

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

export async function exploreFeature(feature: string): Promise<LearningProgress> {
  const res = await fetch(`${API_URL}/api/learning/explore/${feature}`, { method: "POST" });
  return res.json();
}

export interface BacktestTrade {
  entry_date: string;
  exit_date: string;
  underlying: string;
  strategy: string;
  entry_price: number;
  exit_price: number;
  qty: number;
  pnl: number;
  exit_reason: string;
  regime_at_entry: string;
}

export interface BacktestSummary {
  initial_capital: number;
  final_capital: number;
  total_pnl: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  avg_win: number;
  avg_loss: number;
  risk_gate_rejections: number;
  regime_distribution: Record<string, number>;
  backtest_period: string;
  data_points: number;
}

export interface BacktestResult {
  summary: BacktestSummary;
  trades: BacktestTrade[];
  equity_curve: { date: string; equity: number; regime: string; adx: number; price: number; has_position: boolean }[];
}

export async function fetchBacktest(): Promise<BacktestResult | null> {
  try {
    const res = await fetch(`${API_URL}/api/backtest`);
    return res.json();
  } catch {
    return null;
  }
}

