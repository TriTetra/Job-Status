/** Aplio wordmark used on the signed-out pages (sign-in, invite). */
export function Brand() {
  return (
    <div className="flex flex-col items-center mb-10">
      <div
        className="text-[42px] tracking-[0.14em] font-extralight leading-none mb-3"
        style={{
          fontFamily: "'Outfit', 'Inter Variable', Inter, system-ui, sans-serif",
          color: "var(--text-primary)",
          textIndent: "0.14em",
        }}
      >
        Aplio
      </div>
      <div className="w-8 mb-3" style={{ height: 1.5, background: "var(--accent)" }} />
      <p className="text-sm font-editorial italic" style={{ color: "var(--text-muted)" }}>
        Your career, understood.
      </p>
    </div>
  );
}
