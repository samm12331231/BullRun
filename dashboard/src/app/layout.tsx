import type { Metadata } from "next";
import "./globals.css";
import { ClientErrorBoundary } from "@/components/ClientErrorBoundary";

export const metadata: Metadata = {
  title: "BullRun — Governed AI Options Paper Trading",
  description:
    "AI proposes. Evidence decides. Humans authorize. Governed options paper trading on Alpaca with deterministic risk gates.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col font-sans bg-[var(--bg)] text-[var(--text)] selection:bg-[var(--accent-soft)] selection:text-[var(--accent)]">
        <ClientErrorBoundary>{children}</ClientErrorBoundary>
      </body>
    </html>
  );
}

