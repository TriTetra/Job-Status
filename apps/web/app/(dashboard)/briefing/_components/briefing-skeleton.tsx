/** Mirrors the briefing: header, top pick, changes, to-dos, the week. */
export function BriefingSkeleton() {
  const rule = { borderTop: "1px solid var(--border)" };
  return (
    <div className="max-w-[880px] mx-auto px-6 lg:px-10 py-14" aria-busy="true">
      <div className="h-3 w-72 skeleton-shimmer rounded mb-6" />
      <div className="h-12 w-96 max-w-full skeleton-shimmer rounded" />
      <div className="h-5 w-[34rem] max-w-full skeleton-shimmer rounded mt-6 opacity-70" />

      <div className="pt-14 mt-14" style={rule}>
        <div className="h-3 w-20 skeleton-shimmer rounded mb-8" />
        <div className="h-9 w-56 skeleton-shimmer rounded" />
        <div className="h-5 w-80 max-w-full skeleton-shimmer rounded mt-3 opacity-70" />
        <div className="h-5 w-full skeleton-shimmer rounded mt-6 opacity-60" />
        <div className="h-5 w-10/12 skeleton-shimmer rounded mt-2 opacity-60" />
      </div>

      <div className="pt-14 mt-14" style={rule}>
        <div className="h-3 w-36 skeleton-shimmer rounded mb-8" />
        {[1, 2].map((i) => (
          <div key={i} className="h-5 w-9/12 skeleton-shimmer rounded mb-3 opacity-70" />
        ))}
      </div>

      <div className="pt-14 mt-14" style={rule}>
        <div className="h-3 w-16 skeleton-shimmer rounded mb-8" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="grid grid-cols-[2.5rem_1fr] gap-3 mb-6">
            <div className="h-4 w-6 skeleton-shimmer rounded" />
            <div>
              <div className="h-5 w-2/3 skeleton-shimmer rounded" />
              <div className="h-4 w-full skeleton-shimmer rounded mt-2 opacity-60" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
