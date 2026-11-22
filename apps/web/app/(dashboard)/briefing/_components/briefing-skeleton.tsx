/** Mirrors the one-screen briefing: masthead + numbers, the pick | to do, closing. */
export function BriefingSkeleton() {
  return (
    <div className="lg:h-full w-full max-w-[1360px] mx-auto px-6 lg:px-12 py-8 lg:py-9 flex flex-col overflow-hidden" aria-busy="true">
      <div className="grid lg:grid-cols-[minmax(0,1fr)_auto] items-end gap-12">
        <div>
          <div className="h-3 w-56 skeleton-shimmer rounded" />
          <div className="h-11 w-96 max-w-full skeleton-shimmer rounded mt-4" />
          <div className="h-5 w-[30rem] max-w-full skeleton-shimmer rounded mt-4 opacity-70" />
        </div>
        <div className="hidden lg:grid grid-cols-3 gap-10">
          {[1, 2, 3].map((i) => <div key={i} className="h-14 w-24 skeleton-shimmer rounded" />)}
        </div>
      </div>
      <div className="mt-8 pt-8 border-t lg:flex-1 grid lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] gap-14" style={{ borderColor: "var(--border)" }}>
        <div>
          <div className="flex gap-5">
            <div className="h-[60px] w-[60px] skeleton-shimmer rounded-2xl" />
            <div className="flex-1">
              <div className="h-4 w-32 skeleton-shimmer rounded" />
              <div className="h-8 w-80 max-w-full skeleton-shimmer rounded mt-2" />
            </div>
          </div>
          <div className="h-5 w-full skeleton-shimmer rounded mt-6 opacity-60" />
          <div className="h-5 w-10/12 skeleton-shimmer rounded mt-2 opacity-60" />
        </div>
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-5 w-2/3 skeleton-shimmer rounded" />
              <div className="h-4 w-full skeleton-shimmer rounded mt-2 opacity-60" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
