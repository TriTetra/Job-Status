import Link from "next/link";
import { SectionLabel } from "@/components/shared/narrative-section";
import type { ChangeLine } from "@/features/briefing/types";
import { Movement } from "./movement";

export function BriefingChanges({ lines }: { lines: ChangeLine[] }) {
  if (lines.length === 0) return null;
  return (
    <Movement delay={200}>
      <SectionLabel>Since your last visit</SectionLabel>
      <ul className="space-y-3">
        {lines.map((l) => (
          <li key={l.text} className="text-lg leading-relaxed" style={{ color: "var(--text-primary)" }}>
            {l.text}
            {l.href && (
              <Link href={l.href} className="ml-2 text-sm whitespace-nowrap" style={{ color: "var(--accent)" }}>
                {l.linkLabel ?? "Open"} →
              </Link>
            )}
          </li>
        ))}
      </ul>
    </Movement>
  );
}
