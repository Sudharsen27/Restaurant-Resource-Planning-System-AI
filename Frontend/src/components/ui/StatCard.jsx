export default function StatCard({ label, value, change, icon: Icon, accent = 'blue' }) {
  const accents = {
    blue: 'from-blue-500/10 to-indigo-500/10 text-blue-600 dark:text-blue-400',
    emerald: 'from-emerald-500/10 to-teal-500/10 text-emerald-600 dark:text-emerald-400',
    amber: 'from-amber-500/10 to-orange-500/10 text-amber-600 dark:text-amber-400',
    violet: 'from-violet-500/10 to-purple-500/10 text-violet-600 dark:text-violet-400',
    rose: 'from-rose-500/10 to-pink-500/10 text-rose-600 dark:text-rose-400',
  }

  return (
    <div className="min-w-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-slate-800 dark:bg-slate-900/80">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {label}
          </p>
          <p className="mt-2 break-words text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {value}
          </p>
          {change && (
            <p className="mt-1 line-clamp-2 text-xs text-slate-500 dark:text-slate-400" title={change}>
              {change}
            </p>
          )}
        </div>
        {Icon && (
          <div className={`rounded-xl bg-gradient-to-br p-2.5 ${accents[accent]}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  )
}
