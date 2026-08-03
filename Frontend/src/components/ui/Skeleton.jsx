export function Skeleton({ className = '' }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-stone-200 dark:bg-white/10 ${className}`}
    />
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5 dark:border-white/10 dark:bg-[#1b2520]">
      <Skeleton className="mb-3 h-4 w-24" />
      <Skeleton className="h-8 w-32" />
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5 dark:border-white/10 dark:bg-[#1b2520]">
      <Skeleton className="mb-4 h-5 w-40" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}
