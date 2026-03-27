export function CardSkeleton({ count = 3 }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="panel animate-pulse p-6">
          <div className="h-4 w-24 rounded-full bg-white/10" />
          <div className="mt-4 h-8 w-40 rounded-xl bg-white/12" />
          <div className="mt-4 h-24 rounded-2xl bg-white/[0.04]" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="h-14 rounded-2xl bg-white/[0.04]" />
            <div className="h-14 rounded-2xl bg-white/[0.04]" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="table-shell animate-pulse p-4">
      <div className="h-10 rounded-2xl bg-white/[0.06]" />
      <div className="mt-3 space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="h-14 rounded-2xl bg-white/[0.04]" />
        ))}
      </div>
    </div>
  );
}
