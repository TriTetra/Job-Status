"use client";

import { useRouter } from "next/navigation";
import { DecisionList } from "@/components/patterns/decision-list";
import { SectionLabel } from "@/components/shared/narrative-section";
import { Movement } from "./movement";
import type { FocusItem } from "@/features/briefing/types";

export function BriefingFocus({ items }: { items: FocusItem[] }) {
  const router = useRouter();
  return (
    <Movement delay={80}>
      <SectionLabel>Today&apos;s Focus</SectionLabel>
      <div className="mt-8">
        <DecisionList
          layout="columns"
          items={items.map((item) => ({
            number: item.number,
            action: item.action,
            reason: item.reason,
            ctaLabel: item.ctaLabel,
            ctaOnClick: item.ctaHref
              ? () => router.push(item.ctaHref!)
              : undefined,
          }))}
        />
      </div>
    </Movement>
  );
}
