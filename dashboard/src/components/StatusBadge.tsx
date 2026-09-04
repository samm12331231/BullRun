import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

interface StatusBadgeProps {
  variant: "accent" | "warning" | "danger" | "info" | "muted";
  children: ReactNode;
  icon?: ReactNode;
}

export default function StatusBadge({ variant, children, icon }: StatusBadgeProps) {
  return (
    <span className={cn("badge", `badge-${variant}`)}>
      {icon}
      {children}
    </span>
  );
}
