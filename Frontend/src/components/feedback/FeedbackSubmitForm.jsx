import { MessageSquare, Send, Users } from 'lucide-react'
import { formatNumber } from '../../utils/format'

export default function FeedbackSubmitForm({
  predictions,
  form,
  fieldErrors,
  onChange,
  onSubmit,
  submitting,
  selectedPrediction,
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <label className="block">
        <span className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Prediction ID
        </span>
        <select
          required
          value={form.prediction_id}
          onChange={(e) => onChange({ ...form, prediction_id: e.target.value })}
          className={`w-full rounded-lg border bg-white px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:bg-slate-800 ${
            fieldErrors.prediction_id
              ? 'border-rose-400 focus:border-rose-500'
              : 'border-slate-200 focus:border-blue-500 dark:border-slate-700'
          }`}
        >
          <option value="">Select prediction ID…</option>
          {predictions.map((p) => (
            <option key={p.id} value={p.id}>
              #{p.id} — {p.forecast_date} {String(p.forecast_hour).padStart(2, '0')}:00 —{' '}
              {p.predicted_customers} predicted
              {p.actual_customers != null ? ' (reviewed)' : ''}
            </option>
          ))}
        </select>
        {fieldErrors.prediction_id && (
          <p className="mt-1 text-xs text-rose-600">{fieldErrors.prediction_id}</p>
        )}
        {predictions.length === 0 && (
          <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
            No predictions available. Generate a forecast first.
          </p>
        )}
      </label>

      {selectedPrediction && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/80 px-4 py-3 dark:border-indigo-900 dark:bg-indigo-950/30">
          <p className="text-xs font-medium uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
            Predicted Customers
          </p>
          <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
            {formatNumber(selectedPrediction.predicted_customers)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Forecast {selectedPrediction.forecast_date} at {selectedPrediction.forecast_hour}:00
            {selectedPrediction.confidence != null &&
              ` · ${selectedPrediction.confidence.toFixed(1)}% confidence`}
          </p>
        </div>
      )}

      <label className="block">
        <span className="mb-1.5 flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-400">
          <Users className="h-3.5 w-3.5" />
          Actual Customers
        </span>
        <input
          type="number"
          min={0}
          required
          value={form.actual_customers}
          onChange={(e) => onChange({ ...form, actual_customers: e.target.value })}
          className={`w-full rounded-lg border bg-white px-3 py-2.5 text-sm dark:bg-slate-800 ${
            fieldErrors.actual_customers
              ? 'border-rose-400 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20'
              : 'border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700'
          }`}
          placeholder="Enter actual customer count"
        />
        {fieldErrors.actual_customers && (
          <p className="mt-1 text-xs text-rose-600">{fieldErrors.actual_customers}</p>
        )}
      </label>

      <label className="block">
        <span className="mb-1.5 flex items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-400">
          <MessageSquare className="h-3.5 w-3.5" />
          Comments
        </span>
        <textarea
          rows={4}
          maxLength={2000}
          value={form.comments}
          onChange={(e) => onChange({ ...form, comments: e.target.value })}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-slate-800"
          placeholder="Weather, events, staffing issues, promotions…"
        />
        <p className="mt-1 text-right text-[10px] text-slate-400">{form.comments.length}/2000</p>
      </label>

      <button
        type="submit"
        disabled={submitting || !form.prediction_id}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 hover:from-indigo-700 hover:to-violet-700 disabled:opacity-60"
      >
        {submitting ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Submitting…
          </>
        ) : (
          <>
            <Send className="h-4 w-4" />
            Submit Feedback
          </>
        )}
      </button>
    </form>
  )
}
