import { Clock, Hash, Sparkles, Tag, TrendingUp } from 'lucide-react'
import { formatNumber, formatPercent } from '../../utils/format'
import { formatPredictionTimestamp, getConfidenceLabel } from '../../utils/forecastForm'

export default function PredictionCard({ result, submittedAt }) {
  if (!result) return null

  const confidence = getConfidenceLabel(result.confidence)
  const timestamp = submittedAt || formatPredictionTimestamp(result.created_at)

  return (
    <div className="relative overflow-hidden rounded-2xl border border-blue-200/80 bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 p-6 text-white shadow-xl shadow-blue-600/20 sm:p-8">
      <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
      <div className="absolute -bottom-12 -left-8 h-48 w-48 rounded-full bg-indigo-400/20 blur-3xl" />

      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-blue-100">
              <Sparkles className="h-4 w-4" />
              <span className="text-xs font-semibold uppercase tracking-widest">
                Prediction Result
              </span>
            </div>
            <p className="mt-4 text-sm text-blue-100">Predicted Customers</p>
            <p className="mt-1 text-5xl font-bold tracking-tight sm:text-6xl">
              {formatNumber(result.predicted_customers)}
            </p>
          </div>

          <div className="rounded-2xl bg-white/15 px-5 py-4 backdrop-blur-sm">
            <p className="text-xs font-medium uppercase tracking-wider text-blue-100">
              Confidence Score
            </p>
            <p className="mt-1 text-3xl font-bold">{formatPercent(result.confidence, 0)}</p>
            <p className="mt-1 text-xs font-medium text-blue-100">{confidence.label} reliability</p>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/20">
              <div
                className="h-full rounded-full bg-white transition-all"
                style={{ width: `${Math.min(100, result.confidence ?? 0)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3 border-t border-white/20 pt-5">
          {result.prediction_id != null && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <Hash className="h-3 w-3" />
              Prediction #{result.prediction_id}
            </span>
          )}
          {result.model_version && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <Tag className="h-3 w-3" />
              Model {result.model_version}
            </span>
          )}
          {timestamp && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <Clock className="h-3 w-3" />
              {timestamp}
            </span>
          )}
          {!timestamp && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <TrendingUp className="h-3 w-3" />
              Live prediction
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
