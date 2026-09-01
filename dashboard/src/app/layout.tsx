import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BullRun — AI Options Trading Terminal",
  description:
    "AI proposes. Evidence decides. Humans authorize. A Bloomberg-grade options trading desk with deterministic risk gates and plain-English educational transparency.",
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
      <body className="min-h-full flex flex-col font-sans bg-[#080b11] text-[#e2e8f0] selection:bg-amber-500/30 selection:text-amber-200">
        {children}
      </body>
    </html>
  );
}

