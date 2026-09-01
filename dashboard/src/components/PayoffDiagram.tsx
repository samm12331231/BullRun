"use client";

import { useState, useMemo } from "react";

interface PayoffDiagramProps {
  structure: string; // "BULL_CALL_SPREAD" or "BEAR_PUT_SPREAD"
  longStrike: number;
  shortStrike: number;
  netDebit: number;
  currentPrice: number;
  underlying?: string;
}

interface PayoffPoint {
  price: number;
  pnl: number;
  isProfit: boolean;
}

export default function PayoffDiagram({
  structure,
  longStrike,
  shortStrike,
  netDebit,
  currentPrice,
  underlying = "SPY",
}: PayoffDiagramProps) {
  const [sliderPrice, setSliderPrice] = useState(currentPrice);

  // Calculate payoff at each price point
  const payoffData = useMemo((): PayoffPoint[] => {
    const points: PayoffPoint[] = [];
    const isCallSpread = structure === "BULL_CALL_SPREAD";

    // Range: 10% below long strike to 10% above short strike
    const minPrice = Math.min(longStrike, shortStrike) - 5;
    const maxPrice = Math.max(longStrike, shortStrike) + 5;
    const step = 0.25;

    for (let price = minPrice; price <= maxPrice; price += step) {
      let pnl: number;

      if (isCallSpread) {
        // Bull Call Spread
        const longValue = Math.max(0, price - longStrike);
        const shortValue = Math.max(0, price - shortStrike);
        pnl = (longValue - shortValue - netDebit) * 100; // × 100 for contracts
      } else {
        // Bear Put Spread
        const longValue = Math.max(0, longStrike - price);
        const shortValue = Math.max(0, shortStrike - price);
        pnl = (longValue - shortValue - netDebit) * 100;
      }

      points.push({ price, pnl, isProfit: pnl > 0 });
    }

    return points;
  }, [structure, longStrike, shortStrike, netDebit]);

  // Calculate P&L at slider position
  const sliderPnL = useMemo(() => {
    const isCallSpread = structure === "BULL_CALL_SPREAD";
    let pnl: number;

    if (isCallSpread) {
      const longValue = Math.max(0, sliderPrice - longStrike);
      const shortValue = Math.max(0, sliderPrice - shortStrike);
      pnl = (longValue - shortValue - netDebit) * 100;
    } else {
      const longValue = Math.max(0, longStrike - sliderPrice);
      const shortValue = Math.max(0, shortStrike - sliderPrice);
      pnl = (longValue - shortValue - netDebit) * 100;
    }

    return pnl;
  }, [structure, longStrike, shortStrike, netDebit, sliderPrice]);

  // SVG dimensions
  const width = 560;
  const height = 280;
  const padding = { top: 30, right: 30, bottom: 50, left: 70 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Price range
  const prices = payoffData.map((p) => p.price);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);

  // P&L range
  const pnls = payoffData.map((p) => p.pnl);
  const minPnL = Math.min(...pnls, 0);
  const maxPnL = Math.max(...pnls, 0);
  const pnlRange = Math.max(Math.abs(minPnL), Math.abs(maxPnL));

  // Scale functions
  const scaleX = (price: number) =>
    padding.left + ((price - minP) / (maxP - minP)) * chartWidth;
  const scaleY = (pnl: number) =>
    padding.top + chartHeight / 2 - (pnl / pnlRange) * (chartHeight / 2);

  // Build SVG path
  const pathD = payoffData
    .map((p, i) => `${i === 0 ? "M" : "L"} ${scaleX(p.price).toFixed(1)} ${scaleY(p.pnl).toFixed(1)}`)
    .join(" ");

  // Zero line Y position
  const zeroY = scaleY(0);

  // Slider position
  const sliderX = scaleX(sliderPrice);

  // Breakeven calculation
  const isCallSpread = structure === "BULL_CALL_SPREAD";
  const breakeven = isCallSpread ? longStrike + netDebit : longStrike - netDebit;

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Payoff Diagram</span>
        <span className="text-xs text-[var(--text-muted)] font-mono">
          {structure.replace(/_/g, " ")}
        </span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map((frac) => (
          <line
            key={frac}
            x1={padding.left}
            y1={padding.top + chartHeight * frac}
            x2={width - padding.right}
            y2={padding.top + chartHeight * frac}
            stroke="var(--border)"
            strokeWidth="0.5"
            strokeDasharray="4,4"
          />
        ))}

        {/* Zero line */}
        <line
          x1={padding.left}
          y1={zeroY}
          x2={width - padding.right}
          y2={zeroY}
          stroke="var(--text-muted)"
          strokeWidth="1"
        />

        {/* Profit zone fill */}
        <path
          d={`${pathD} L ${scaleX(payoffData[payoffData.length - 1]?.price || 0).toFixed(1)} ${zeroY.toFixed(1)} L ${scaleX(payoffData[0]?.price || 0).toFixed(1)} ${zeroY.toFixed(1)} Z`}
          fill="rgba(34, 197, 94, 0.1)"
        />

        {/* Payoff line */}
        <path d={pathD} fill="none" stroke="var(--gold)" strokeWidth="2.5" strokeLinejoin="round" />

        {/* Long strike marker */}
        <line
          x1={scaleX(longStrike)}
          y1={padding.top}
          x2={scaleX(longStrike)}
          y2={padding.top + chartHeight}
          stroke="var(--green)"
          strokeWidth="1"
          strokeDasharray="4,4"
        />
        <text
          x={scaleX(longStrike)}
          y={padding.top - 8}
          textAnchor="middle"
          fill="var(--green)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          BUY ${longStrike}
        </text>

        {/* Short strike marker */}
        <line
          x1={scaleX(shortStrike)}
          y1={padding.top}
          x2={scaleX(shortStrike)}
          y2={padding.top + chartHeight}
          stroke="var(--red)"
          strokeWidth="1"
          strokeDasharray="4,4"
        />
        <text
          x={scaleX(shortStrike)}
          y={padding.top - 8}
          textAnchor="middle"
          fill="var(--red)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          SELL ${shortStrike}
        </text>

        {/* Breakeven marker */}
        <circle cx={scaleX(breakeven)} cy={zeroY} r="4" fill="var(--yellow)" />
        <text
          x={scaleX(breakeven)}
          y={zeroY + 16}
          textAnchor="middle"
          fill="var(--yellow)"
          fontSize="9"
          fontFamily="var(--font-mono)"
        >
          BE ${breakeven.toFixed(2)}
        </text>

        {/* Slider line */}
        <line
          x1={sliderX}
          y1={padding.top}
          x2={sliderX}
          y2={padding.top + chartHeight}
          stroke="white"
          strokeWidth="1.5"
          strokeOpacity="0.6"
        />

        {/* Slider dot */}
        <circle
          cx={sliderX}
          cy={scaleY(sliderPnL)}
          r="6"
          fill={sliderPnL >= 0 ? "var(--green)" : "var(--red)"}
          stroke="white"
          strokeWidth="2"
        />

        {/* Slider P&L label */}
        <rect
          x={sliderX - 40}
          y={scaleY(sliderPnL) - 28}
          width="80"
          height="20"
          rx="4"
          fill={sliderPnL >= 0 ? "var(--green)" : "var(--red)"}
        />
        <text
          x={sliderX}
          y={scaleY(sliderPnL) - 14}
          textAnchor="middle"
          fill="white"
          fontSize="11"
          fontWeight="bold"
          fontFamily="var(--font-mono)"
        >
          {sliderPnL >= 0 ? "+" : ""}${sliderPnL.toFixed(0)}
        </text>

        {/* Y-axis labels */}
        <text
          x={padding.left - 10}
          y={zeroY + 4}
          textAnchor="end"
          fill="var(--text-muted)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          $0
        </text>
        <text
          x={padding.left - 10}
          y={padding.top + 10}
          textAnchor="end"
          fill="var(--green)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          +${maxPnL.toFixed(0)}
        </text>
        <text
          x={padding.left - 10}
          y={padding.top + chartHeight - 5}
          textAnchor="end"
          fill="var(--red)"
          fontSize="10"
          fontFamily="var(--font-mono)"
        >
          {minPnL.toFixed(0)}
        </text>

        {/* X-axis labels */}
        {[minP, (minP + maxP) / 2, maxP].map((price, i) => (
          <text
            key={i}
            x={scaleX(price)}
            y={height - 10}
            textAnchor="middle"
            fill="var(--text-muted)"
            fontSize="10"
            fontFamily="var(--font-mono)"
          >
            ${price.toFixed(0)}
          </text>
        ))}

        {/* Axis labels */}
        <text
          x={width / 2}
          y={height}
          textAnchor="middle"
          fill="var(--text-muted)"
          fontSize="11"
          fontFamily="var(--font-sans)"
        >
          {underlying} Price at Expiration
        </text>
        <text
          x={12}
          y={height / 2}
          textAnchor="middle"
          fill="var(--text-muted)"
          fontSize="11"
          fontFamily="var(--font-sans)"
          transform={`rotate(-90, 12, ${height / 2})`}
        >
          Profit / Loss
        </text>
      </svg>

      {/* Interactive slider */}
      <div className="mt-4 px-2">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[var(--text-muted)] font-mono">
            Drag to simulate: What if {underlying} is at...
          </span>
          <span
            className="text-sm font-bold font-mono"
            style={{ color: sliderPnL >= 0 ? "var(--green)" : "var(--red)" }}
          >
            ${sliderPrice.toFixed(2)} → {sliderPnL >= 0 ? "+" : ""}${sliderPnL.toFixed(0)}
          </span>
        </div>
        <input
          type="range"
          min={minP * 100}
          max={maxP * 100}
          value={sliderPrice * 100}
          onChange={(e) => setSliderPrice(Number(e.target.value) / 100)}
          className="w-full h-2 rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, var(--red) 0%, var(--yellow) 50%, var(--green) 100%)`,
          }}
        />
        <div className="flex justify-between mt-1">
          <span className="text-xs text-[var(--text-muted)] font-mono">
            ${minP.toFixed(0)}
          </span>
          <span className="text-xs text-[var(--text-muted)] font-mono">
            Current: ${currentPrice.toFixed(2)}
          </span>
          <span className="text-xs text-[var(--text-muted)] font-mono">
            ${maxP.toFixed(0)}
          </span>
        </div>
      </div>

      {/* Scenario cards */}
      <div className="grid grid-cols-3 gap-2 mt-4">
        <div className="text-center p-2 rounded-lg" style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
          <div className="text-xs text-[var(--text-muted)] mb-1">If wrong</div>
          <div className="text-sm font-bold font-mono" style={{ color: "var(--red)" }}>
            -${(netDebit * 100).toFixed(0)}
          </div>
          <div className="text-[10px] text-[var(--text-muted)]">
            {isCallSpread ? `Below $${longStrike}` : `Above $${longStrike}`}
          </div>
        </div>
        <div className="text-center p-2 rounded-lg" style={{ background: "rgba(234, 179, 8, 0.1)", border: "1px solid rgba(234, 179, 8, 0.2)" }}>
          <div className="text-xs text-[var(--text-muted)] mb-1">Breakeven</div>
          <div className="text-sm font-bold font-mono" style={{ color: "var(--yellow)" }}>
            ${breakeven.toFixed(2)}
          </div>
          <div className="text-[10px] text-[var(--text-muted)]">
            Need {underlying} at ${breakeven.toFixed(2)}
          </div>
        </div>
        <div className="text-center p-2 rounded-lg" style={{ background: "rgba(34, 197, 94, 0.1)", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
          <div className="text-xs text-[var(--text-muted)] mb-1">Max profit</div>
          <div className="text-sm font-bold font-mono" style={{ color: "var(--green)" }}>
            +${((Math.abs(shortStrike - longStrike) - netDebit) * 100).toFixed(0)}
          </div>
          <div className="text-[10px] text-[var(--text-muted)]">
            {isCallSpread ? `Above $${shortStrike}` : `Below $${shortStrike}`}
          </div>
        </div>
      </div>
    </div>
  );
}
