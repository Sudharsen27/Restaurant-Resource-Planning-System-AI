import { Brain, CheckCircle2, Loader2, Percent, RefreshCw, TrendingUp } from 'lucide-react'
import { formatPercent } from '../../utils/format'
import { parseRetrainingStatus } from '../../utils/feedbackForm'

export default function FeedbackResultPanel({ result, submitting }) {
  if (submitting) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center gap-3 rounded-2xl border border-blue-200 bg-blue-50/50 p-8 dark:border-blue-900 dark:bg-blue-950/30">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <p className="font-medium text-slate-900 dark:text-white">Submitting feedback…</p>
        <p className="text-sm text-slate-500">Appending data and retraining the model</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 p-8 text-center dark:border-slate-700">
        <RefreshCw className="mb-3 h-8 w-8 text-slate-300" />
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
          Submission results will appear here
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Prediction error, model version, and retraining status
        </p>
      </div>
    )
  }

  const retrain = parseRetrainingStatus(result.retraining)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
        <CheckCircle2 className="h-5 w-5 shrink-0" />
        <span className="text-sm font-medium">Feedback submitted — model updated</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-500">
            <Percent className="h-3.5 w-3.5" />
            Prediction Error
          </div>
          <p className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
            {formatPercent(result.percentage_error ?? result.mape)}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            Predicted {result.predicted_customers} · Actual {result.actual_customers}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-500">
            <Brain className="h-3.5 w-3.5" />
            Model Version
          </div>
          <p className="mt-2 text-2xl font-bold text-violet-600 dark:text-violet-400">
            {result.production_model || retrain.version || '—'}
          </p>
          {retrain.modelName && (
            <p className="mt-0.5 truncate text-xs text-slate-500">{retrain.modelName}</p>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Retraining Status
          </p>
          <p className="mt-2 text-sm font-semibold leading-snug text-slate-900 dark:text-white">
            {retrain.message}
          </p>
          {result.dataset_size != null && (
            <p className="mt-1 text-xs text-slate-500">
              Dataset: {result.dataset_size.toLocaleString('en-IN')} rows
            </p>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-500">
            <TrendingUp className="h-3.5 w-3.5" />
            New Accuracy
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {formatPercent(result.new_accuracy)}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">After retraining</p>
        </div>
      </div>
    </div>
  )
}
