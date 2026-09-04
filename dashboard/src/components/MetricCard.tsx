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
    <div className="metric-card">
      <div className="flex items-center gap-2 mb-2">
        {icon && <span className="text-[var(--muted)]">{icon}</span>}
        <span className="text-[11px] font-mono uppercase tracking-wide text-[var(--muted)]">{label}</span>
      </div>
      <div className={cn("text-2xl font-bold font-mono leading-none", valueColors[variant])}>
        {value}
      </div>
      {sub && (
        <div className="text-[11px] font-mono text-[var(--muted)] mt-1.5">{sub}</div>
      )}
    </div>
  );
}
