export default function ForecastMetricCard({
  label,
  value,
  subtext,
  accent = 'emerald',
  children,
  title,
  size = 'md',
}) {
  const styles = {
    blue: {
      border: 'border-sky-200 dark:border-sky-900',
      bg: 'bg-sky-50 dark:bg-sky-950/30',
      label: 'text-sky-700 dark:text-sky-300',
    },
    emerald: {
      border: 'border-emerald-200 dark:border-emerald-900',
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
      label: 'text-emerald-600 dark:text-emerald-400',
    },
    violet: {
      border: 'border-violet-200 dark:border-violet-900',
      bg: 'bg-violet-50 dark:bg-violet-950/30',
      label: 'text-violet-600 dark:text-violet-400',
    },
    amber: {
      border: 'border-amber-200 dark:border-amber-900',
      bg: 'bg-amber-50 dark:bg-amber-950/30',
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
      className={`flex min-h-[120px] min-w-0 flex-col rounded-xl border p-4 shadow-[0_1px_2px_rgba(28,35,30,0.04)] sm:p-5 ${theme.border} ${theme.bg}`}
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
