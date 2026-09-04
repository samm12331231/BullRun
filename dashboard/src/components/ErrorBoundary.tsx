"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="card p-6 text-center">
            <p className="text-[var(--warning)] font-mono text-sm mb-2">
              Something went wrong
            </p>
            <p className="text-[var(--muted)] text-xs mb-3">
              {this.state.error?.message || "Unknown error"}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-3 py-1.5 text-xs rounded-lg bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] hover:bg-[var(--surface-hover)]"
            >
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
