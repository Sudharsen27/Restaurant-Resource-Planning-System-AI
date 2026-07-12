import { Brain, CheckCircle2 } from 'lucide-react'
import { formatDate, formatModelName, formatNumber, formatPercent } from '../../utils/format'

export default function CurrentModelBanner({ current, accuracy }) {
  if (!current) return null

  return (
    <div className="rounded-2xl border border-violet-200 bg-gradient-to-r from-violet-50 via-indigo-50 to-blue-50 px-6 py-5 dark:border-violet-900 dark:from-violet-950/40 dark:via-indigo-950/30 dark:to-blue-950/20">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-600/15">
            <Brain className="h-6 w-6 text-violet-600" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-violet-600 dark:text-violet-400">
              Current Model
            </p>
            <p className="mt-1 text-xl font-bold text-slate-900 dark:text-white">
              {current.version_label ?? '—'} — {formatModelName(current.model_name)}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Trained {formatDate(current.training_date)} ·{' '}
              {formatNumber(current.dataset_size)} training rows
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {current.is_production && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Production
            </span>
          )}
          {accuracy?.current_production_model && (
            <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-700 dark:bg-violet-900/50 dark:text-violet-300">
              Serving: {accuracy.current_production_model}
            </span>
          )}
          <div className="rounded-xl border border-white/60 bg-white/70 px-4 py-2 dark:border-slate-700 dark:bg-slate-900/60">
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Model Version
            </p>
            <p className="text-lg font-bold text-violet-600 dark:text-violet-400">
              {current.version_label ?? '—'}
            </p>
          </div>
          <div className="rounded-xl border border-white/60 bg-white/70 px-4 py-2 dark:border-slate-700 dark:bg-slate-900/60">
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Accuracy
            </p>
            <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              {formatPercent(current.accuracy)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
