import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  variant?: "default" | "accent" | "danger" | "warning" | "info";
  icon?: ReactNode;
}

const valueColors = {
  default: "text-[var(--text)]",
  accent: "text-[var(--accent)]",
  danger: "text-[var(--danger)]",
  warning: "text-[var(--warning)]",
  info: "text-[var(--info)]",
};

export default function MetricCard({ label, value, sub, variant = "default", icon }: MetricCardProps) {
  return (
    <div className="metric-card flex items-center justify-between gap-3">
      <div className="min-w-0">
        <div className="text-[10px] font-mono uppercase tracking-wide text-[var(--muted)] truncate">{label}</div>
        <div className={cn("text-lg font-bold font-mono leading-none mt-2", valueColors[variant])}>{value}</div>
        {sub && <div className="text-[10px] font-mono text-[var(--muted)] mt-1 truncate">{sub}</div>}
      </div>
      {icon && <span className="text-[var(--muted)] shrink-0">{icon}</span>}
    </div>
  );
}
