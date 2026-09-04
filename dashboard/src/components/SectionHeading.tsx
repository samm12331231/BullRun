import { type ReactNode } from "react";

interface SectionHeadingProps {
  children: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
}

export default function SectionHeading({ children, icon, action }: SectionHeadingProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        {icon && <span className="text-[var(--muted)]">{icon}</span>}
        <h3 className="text-xs font-bold uppercase tracking-wide text-[var(--muted-strong)] font-mono">
          {children}
        </h3>
      </div>
      {action}
    </div>
  );
}
