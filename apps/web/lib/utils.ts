import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** An outbound link from scraped data, or null — only http(s), never javascript: or data:. */
export function safeHttpUrl(value: unknown): string | null {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

/** Scores are stored as floats (62.7468…); people read whole numbers. */
export function formatScore(score: number | null | undefined): number {
  return Math.round(score ?? 0);
}

/** "ABDULLOKH" or "abdullokh" (as typed / read from a CV) → "Abdullokh"; mixed case is kept. */
export function displayName(name: string | null | undefined): string {
  const n = (name ?? "").trim();
  if (!n || (n !== n.toUpperCase() && n !== n.toLowerCase())) return n;
  return n.toLowerCase().replace(/(^|[\s\-'])(\p{L})/gu, (_, sep: string, ch: string) => sep + ch.toUpperCase());
}
