import { FadeInSection } from "@/components/shared/fade-in-section";

export function BriefingHeader({ dateline, greeting, lead }: { dateline: string; greeting: string; lead: string }) {
  return (
    <FadeInSection>
      <header>
        <p className="text-[11px] uppercase tracking-[0.08em] mb-5" style={{ color: "var(--text-muted)", fontFamily: "var(--font-display)" }}>
          {dateline}
        </p>
        <h1 className="font-serif-display text-4xl md:text-[52px] leading-[1.05]" style={{ color: "var(--text-primary)" }}>
          {greeting}
        </h1>
        <p className="mt-5 text-lg md:text-xl leading-relaxed max-w-[640px]" style={{ color: "var(--text-secondary)" }}>
          {lead}
        </p>
      </header>
    </FadeInSection>
  );
}
