import { FadeInSection } from "@/components/shared/fade-in-section";

export function BriefingClosing({ lines }: { lines: string[] }) {
  return (
    <FadeInSection delay={320}>
      <div className="text-center pt-14 mt-14" style={{ borderTop: "1px solid var(--border)" }}>
        {lines.map((line, i) => (
          <p
            key={i}
            className="font-editorial text-2xl leading-relaxed"
            style={{ color: i === 0 ? "var(--text-secondary)" : "var(--text-muted)", marginTop: i > 0 ? "0.25rem" : 0 }}
          >
            {line}
          </p>
        ))}
      </div>
    </FadeInSection>
  );
}
