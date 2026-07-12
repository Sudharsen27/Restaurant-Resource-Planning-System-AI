export default function ForecastMetricCard({
  label,
  value,
  subtext,
  accent = 'blue',
  children,
  title,
  size = 'md',
}) {
  const styles = {
    blue: {
      border: 'border-blue-200 dark:border-blue-900',
      bg: 'from-blue-50 to-indigo-50 dark:from-blue-950/50 dark:to-indigo-950/50',
      label: 'text-blue-600 dark:text-blue-400',
    },
    emerald: {
      border: 'border-emerald-200 dark:border-emerald-900',
      bg: 'from-emerald-50 to-teal-50 dark:from-emerald-950/50 dark:to-teal-950/50',
      label: 'text-emerald-600 dark:text-emerald-400',
    },
    violet: {
      border: 'border-violet-200 dark:border-violet-900',
      bg: 'from-violet-50 to-purple-50 dark:from-violet-950/50 dark:to-purple-950/50',
      label: 'text-violet-600 dark:text-violet-400',
    },
    amber: {
      border: 'border-amber-200 dark:border-amber-900',
      bg: 'from-amber-50 to-orange-50 dark:from-amber-950/50 dark:to-orange-950/50',
      label: 'text-amber-600 dark:text-amber-400',
    },
  }

  const theme = styles[accent] || styles.blue
  const valueClass =
    size === 'sm'
      ? 'text-base leading-snug sm:text-lg'
      : size === 'lg'
        ? 'text-3xl sm:text-4xl'
        : 'text-2xl sm:text-3xl'

  return (
    <div
      className={`flex min-h-[120px] min-w-0 flex-col rounded-2xl border bg-gradient-to-br p-4 sm:p-5 ${theme.border} ${theme.bg}`}
    >
      <p className={`text-[11px] font-medium uppercase tracking-wider ${theme.label}`}>{label}</p>
      <p
        className={`mt-2 min-w-0 font-bold tracking-tight text-slate-900 dark:text-white ${valueClass}`}
        title={title || (typeof value === 'string' ? value : undefined)}
      >
        {value}
      </p>
      {children}
      {subtext && (
        <p className="mt-auto pt-2 text-xs leading-snug text-slate-500 dark:text-slate-400">
          {subtext}
        </p>
      )}
    </div>
  )
}
