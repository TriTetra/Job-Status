"use client";

import { useRouter } from "next/navigation";
import { EvidenceBlock } from "@/components/patterns/evidence-block";
import { ProgressBlock } from "@/components/patterns/progress-block";
import { SectionLabel } from "@/components/shared/narrative-section";
import { Movement } from "./movement";
import type { EvidenceSummary, ProgressSummary } from "@/features/briefing/types";

interface BriefingEvidenceProgressProps {
  evidence: EvidenceSummary;
  progress: ProgressSummary;
}

export function BriefingEvidenceProgress({ evidence, progress }: BriefingEvidenceProgressProps) {
  const router = useRouter();
  return (
    <Movement delay={240}>
      <div className="grid grid-cols-1 md:grid-cols-2">
        <div className="md:pr-12 pb-10 md:pb-0">
          <SectionLabel>Why We Recommend This</SectionLabel>
          <div className="mt-6">
            <EvidenceBlock
              signalCount={evidence.signalCount}
              signals={evidence.signals}
              confidence={evidence.confidence}
            />
          </div>
        </div>
        <div className="md:pl-12 pt-10 md:pt-0 md:border-l" style={{ borderColor: "var(--border)" }}>
          <SectionLabel>This Month</SectionLabel>
          <div className="mt-6">
            <ProgressBlock
              headline={progress.headline}
              attribution={progress.attribution}
              promise={progress.promise}
              ctaLabel={progress.ctaLabel}
              ctaOnClick={() => progress.ctaHref && router.push(progress.ctaHref)}
            />
          </div>
        </div>
      </div>
    </Movement>
  );
}
