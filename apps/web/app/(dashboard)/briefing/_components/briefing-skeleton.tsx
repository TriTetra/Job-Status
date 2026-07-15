export function BriefingSkeleton() {
  return (
    <div className="max-w-[1000px] mx-auto px-6 lg:px-8 py-14">
      {/* Greeting + brief */}
      <div className="max-w-[640px] space-y-4">
        <div className="h-9 w-64 skeleton-shimmer rounded" />
        <div className="space-y-3 pt-4">
          <div className="h-5 w-full skeleton-shimmer rounded" />
          <div className="h-5 w-11/12 skeleton-shimmer rounded" />
          <div className="h-5 w-10/12 skeleton-shimmer rounded" />
          <div className="h-5 w-9/12 skeleton-shimmer rounded" />
          <div className="h-5 w-7/12 skeleton-shimmer rounded opacity-60" />
        </div>
      </div>

      {/* Today's Focus — 3 columns */}
      <div className="pt-14 mt-14" style={{ borderTop: "1px solid var(--border)" }}>
        <div className="h-3 w-24 skeleton-shimmer rounded mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-x-10 gap-y-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-3 w-6 skeleton-shimmer rounded" />
              <div className="h-5 w-2/3 skeleton-shimmer rounded" />
              <div className="h-4 w-full skeleton-shimmer rounded opacity-60" />
              <div className="h-3 w-20 skeleton-shimmer rounded mt-3" />
            </div>
          ))}
        </div>
      </div>

      {/* Opportunities — 2 columns, no box */}
      <div className="pt-14 mt-14" style={{ borderTop: "1px solid var(--border)" }}>
        <div className="h-3 w-32 skeleton-shimmer rounded mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {[1, 2].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-6 w-40 skeleton-shimmer rounded" />
              <div className="h-4 w-56 skeleton-shimmer rounded opacity-60" />
              <div className="h-4 w-full skeleton-shimmer rounded opacity-60 mt-2" />
            </div>
          ))}
        </div>
      </div>

      {/* Evidence + Progress — 2 columns */}
      <div className="pt-14 mt-14" style={{ borderTop: "1px solid var(--border)" }}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {[1, 2].map((i) => (
            <div key={i} className="space-y-3">
              <div className="h-3 w-36 skeleton-shimmer rounded mb-4" />
              <div className="h-5 w-48 skeleton-shimmer rounded" />
              <div className="h-4 w-full skeleton-shimmer rounded opacity-60" />
              <div className="h-4 w-3/4 skeleton-shimmer rounded opacity-60" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
