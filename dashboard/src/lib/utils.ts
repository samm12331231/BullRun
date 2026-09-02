import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function money(n: number, decimals = 2): string {
  return "$" + n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function signedMoney(n: number): string {
  const prefix = n >= 0 ? "+" : "";
  return prefix + money(n);
}

export function pct(n: number): string {
  const prefix = n >= 0 ? "+" : "";
  return prefix + n.toFixed(2) + "%";
}

export function titleCase(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function sentenceCase(s: string): string {
  const clean = s.replace(/_/g, " ").toLowerCase();
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

export function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}
