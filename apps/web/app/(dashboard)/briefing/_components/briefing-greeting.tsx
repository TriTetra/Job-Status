import { NarrativeText } from "@/components/shared/narrative-text";
import { FadeInSection } from "@/components/shared/fade-in-section";
import type { BriefLine } from "@/features/briefing/types";

const emphasisColor: Record<NonNullable<BriefLine["segments"][number]["emphasis"]>, string> = {
  primary: "var(--text-primary)",
  accent: "var(--accent)",
  success: "var(--success)",
};

interface BriefingGreetingProps {
  name: string;
  brief: BriefLine[];
}

export function BriefingGreeting({ name, brief }: BriefingGreetingProps) {
  return (
    <FadeInSection delay={0}>
      <div className="max-w-[640px]">
        <NarrativeText as="h1" size="3xl" weight="semibold" className="mb-8">
          Good evening, {name}.
        </NarrativeText>
        <div className="space-y-[var(--rhythm-thought)]">
          {brief.map((line, i) => (
            <NarrativeText
              key={i}
              size="lg"
              style={line.muted ? { color: "var(--text-muted)" } : undefined}
            >
              {line.segments.map((segment, j) =>
                segment.emphasis ? (
                  <span key={j} className="font-medium" style={{ color: emphasisColor[segment.emphasis] }}>
                    {segment.text}
                  </span>
                ) : (
                  <span key={j}>{segment.text}</span>
                )
              )}
            </NarrativeText>
          ))}
        </div>
      </div>
    </FadeInSection>
  );
}
