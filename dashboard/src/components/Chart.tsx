"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  CandlestickSeries,
  HistogramSeries,
} from "lightweight-charts";
import type { CandlestickData, HistogramData } from "lightweight-charts";

interface ChartProps {
  data: {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }[];
  symbol?: string;
}

export default function PriceChart({ data, symbol = "SPY" }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: "#111827" },
        textColor: "#94a3b8",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(42, 48, 66, 0.5)" },
        horzLines: { color: "rgba(42, 48, 66, 0.5)" },
      },
      crosshair: {
        mode: 0,
        vertLine: { color: "rgba(59, 130, 246, 0.4)", width: 1, style: 2, labelBackgroundColor: "#3b82f6" },
        horzLine: { color: "rgba(59, 130, 246, 0.4)", width: 1, style: 2, labelBackgroundColor: "#3b82f6" },
      },
      rightPriceScale: {
        borderColor: "#2a3042",
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: "#2a3042",
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#3b82f6",
      priceFormat: { type: "volume" as const },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    chartRef.current = chart;
    candlestickRef.current = candlestickSeries as unknown as ISeriesApi<"Candlestick">;
    volumeRef.current = volumeSeries as unknown as ISeriesApi<"Histogram">;

    // Resize observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chart.applyOptions({ width, height });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, []);

  useEffect(() => {
    if (!data.length || !candlestickRef.current || !volumeRef.current) return;

    const candleData: CandlestickData[] = data.map((d) => ({
      time: d.time as string,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    const volumeData: HistogramData[] = data.map((d) => ({
      time: d.time as string,
      value: d.volume,
      color: d.close >= d.open ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)",
    }));

    candlestickRef.current.setData(candleData);
    volumeRef.current.setData(volumeData);

    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return (
    <div className="relative w-full h-full">
      {/* Symbol label */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-3">
        <span className="text-lg font-bold text-white font-mono">{symbol}</span>
        {data.length > 0 && (
          <span className={`text-sm font-mono ${data[data.length - 1].close >= data[data.length - 1].open ? "text-green-400" : "text-red-400"}`}>
            ${data[data.length - 1].close.toFixed(2)}
            <span className="ml-1 text-xs">
              {data[data.length - 1].close >= data[data.length - 1].open ? "▲" : "▼"}
              {Math.abs(((data[data.length - 1].close - data[data.length - 1].open) / data[data.length - 1].open * 100)).toFixed(2)}%
            </span>
          </span>
        )}
      </div>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}
