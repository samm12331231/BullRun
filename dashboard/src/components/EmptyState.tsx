import { type ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="card p-8 text-center space-y-3">
      {icon && (
        <div className="flex justify-center text-[var(--muted)]">{icon}</div>
      )}
      <div className="text-sm font-semibold text-[var(--text)]">{title}</div>
      <div className="text-xs text-[var(--muted)] font-mono max-w-sm mx-auto leading-relaxed">
        {description}
      </div>
      {action && <div className="pt-1">{action}</div>}
    </div>
  );
}
