export default function StatCard({ label, value, change, icon: Icon, accent = 'blue' }) {
  const accents = {
    blue: 'bg-sky-50 text-sky-700 dark:bg-sky-400/10 dark:text-sky-300',
    emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300',
    violet: 'bg-violet-50 text-violet-700 dark:bg-violet-400/10 dark:text-violet-300',
    rose: 'bg-rose-50 text-rose-700 dark:bg-rose-400/10 dark:text-rose-300',
  }

  return (
    <div className="min-w-0 rounded-xl border border-stone-200/80 bg-white p-5 shadow-[0_1px_2px_rgba(28,35,30,0.04)] transition hover:-translate-y-0.5 hover:shadow-md dark:border-white/10 dark:bg-[#1b2520]">
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
          <div className={`rounded-lg p-2.5 ${accents[accent]}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  )
}
