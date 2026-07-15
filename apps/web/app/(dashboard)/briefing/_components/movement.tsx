import { FadeInSection } from "@/components/shared/fade-in-section";

/** A narrative movement separated from the one before it by a hairline, not a box. */
export function Movement({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <FadeInSection delay={delay}>
      <section className="pt-14 mt-14" style={{ borderTop: "1px solid var(--border)" }}>
        {children}
      </section>
    </FadeInSection>
  );
}
