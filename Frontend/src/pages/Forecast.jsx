import { useEffect, useState } from 'react'
import { AlertCircle, Loader2, RefreshCw, TrendingUp } from 'lucide-react'
import Card from '../components/ui/Card'
import ForecastMetricCard from '../components/ui/ForecastMetricCard'
import ForecastForm from '../components/forecast/ForecastForm'
import PredictionCard from '../components/forecast/PredictionCard'
import PredictionSummary from '../components/forecast/PredictionSummary'
import { ChartSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useToast } from '../context/ToastContext'
import { predictCustomers } from '../services/forecastService'
import { getLatestForecast } from '../services/persistenceService'
import { useDashboardRefresh } from '../hooks/useDashboard'
import { formatNumber, formatPercent } from '../utils/format'
import {
  buildPredictPayload,
  createForecastFormDefaults,
  formatPredictionTimestamp,
  formatPredictionTimestampParts,
  mapLatestToResult,
  payloadToForm,
  validateForecastForm,
} from '../utils/forecastForm'

export default function Forecast() {
  const toast = useToast()
  const refreshDashboard = useDashboardRefresh()
  const [form, setForm] = useState(() => createForecastFormDefaults())
  const [result, setResult] = useState(null)
  const [lastPayload, setLastPayload] = useState(null)
  const [timestampIso, setTimestampIso] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitError, setSubmitError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [restoring, setRestoring] = useState(true)
  const [restoreError, setRestoreError] = useState(null)

  const applyLatest = (saved) => {
    const mapped = mapLatestToResult(saved)
    setResult(mapped)
    setTimestampIso(saved.created_at || null)
    const payload = saved.input_payload
    if (payload) {
      setForm(payloadToForm(payload))
      setLastPayload(payload)
    } else if (saved.date != null && saved.hour != null) {
      const minimal = {
        ...createForecastFormDefaults(),
        date: saved.date,
        hour: saved.hour,
      }
      setForm(minimal)
      setLastPayload(minimal)
    }
  }

  const loadLatest = async ({ silent = false } = {}) => {
    if (!silent) {
      setRestoring(true)
      setRestoreError(null)
    }
    try {
      const res = await getLatestForecast()
      applyLatest(res.data)
      setRestoreError(null)
      return res.data
    } catch (err) {
      const message = err?.message || 'Unable to load latest forecast'
      if (!silent) {
        setRestoreError(message)
        if (!result) setResult(null)
      }
      return null
    } finally {
      if (!silent) setRestoring(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setRestoring(true)
      try {
        const res = await getLatestForecast()
        if (cancelled) return
        applyLatest(res.data)
      } catch (err) {
        if (!cancelled) {
          setRestoreError(err?.message || 'No saved forecast yet')
        }
      } finally {
        if (!cancelled) setRestoring(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitError(null)

    const { valid, errors } = validateForecastForm(form)
    setFieldErrors(errors)
    if (!valid) {
      toast.error('Please fix the highlighted fields')
      return
    }

    setSubmitting(true)
    try {
      const payload = buildPredictPayload(form)
      const res = await predictCustomers(payload)

      const baseResult = {
        prediction_id: res.data.prediction_id,
        predicted_customers: res.data.predicted_customers,
        confidence: res.data.confidence,
      }
      setResult(baseResult)
      setLastPayload(payload)
      setTimestampIso(new Date().toISOString())

      const latest = await loadLatest({ silent: true })
      if (latest) {
        applyLatest(latest)
      }

      refreshDashboard()
      toast.success('Prediction generated successfully')
    } catch (err) {
      const message = err?.message || 'Prediction failed'
      setSubmitError(message)
      toast.error(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/10">
              <TrendingUp className="h-5 w-5 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Customer Forecast
            </h2>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            Predict demand with{' '}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">
              POST /forecast/predict
            </code>
            {' · '}
            Restore from{' '}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">
              GET /forecast/latest
            </code>
          </p>
        </div>
        <button
          type="button"
          onClick={() => loadLatest()}
          disabled={restoring || submitting}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          {restoring ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Load Latest
        </button>
      </div>

      {submitError && (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-200">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{submitError}</span>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-5">
        <Card
          title="Prediction Form"
          subtitle="All signals required by the ML model"
          className="xl:col-span-2"
        >
          <ForecastForm
            form={form}
            onChange={setForm}
            onSubmit={handleSubmit}
            submitting={submitting}
            errors={fieldErrors}
          />
        </Card>

        <div className="space-y-6 xl:col-span-3">
          {restoring && !result && (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 py-16 dark:border-slate-700">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="text-sm text-slate-500">Loading latest prediction from PostgreSQL…</p>
            </div>
          )}

          {!result && !submitting && !restoring && (
            <EmptyState
              title="No prediction yet"
              description={
                restoreError
                  ? `${restoreError}. Fill the form and click Predict.`
                  : 'Fill in the form and click Predict to generate a forecast.'
              }
            />
          )}

          {submitting && !result && (
            <div className="grid gap-4 sm:grid-cols-2">
              <ChartSkeleton />
              <ChartSkeleton />
            </div>
          )}

          {result && (
            <>
              {submitting && (
                <div className="flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-200">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating prediction…
                </div>
              )}

              <PredictionCard
                result={result}
                submittedAt={formatPredictionTimestamp(timestampIso || result.created_at)}
              />

              <div className="grid gap-4 sm:grid-cols-2">
                <ForecastMetricCard
                  label="Predicted Customers"
                  value={formatNumber(result.predicted_customers)}
                  subtext={
                    result.prediction_id != null ? `ID #${result.prediction_id}` : undefined
                  }
                  accent="blue"
                  size="lg"
                />
                <ForecastMetricCard
                  label="Confidence Score"
                  value={formatPercent(result.confidence, 0)}
                  accent="emerald"
                  size="lg"
                >
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-emerald-200 dark:bg-emerald-900">
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all"
                      style={{ width: `${Math.min(100, result.confidence ?? 0)}%` }}
                    />
                  </div>
                </ForecastMetricCard>
                <ForecastMetricCard
                  label="Model Version"
                  value={result.model_version || '—'}
                  subtext="From saved prediction"
                  accent="violet"
                  size="lg"
                />
                {(() => {
                  const stamp = formatPredictionTimestampParts(
                    timestampIso || result.created_at,
                  )
                  return (
                    <ForecastMetricCard
                      label="Prediction Timestamp"
                      value={
                        stamp.date ? (
                          <span className="flex flex-col gap-0.5">
                            <span className="whitespace-nowrap">{stamp.date}</span>
                            {stamp.time && (
                              <span className="whitespace-nowrap text-base font-semibold text-slate-600 dark:text-slate-300 sm:text-lg">
                                {stamp.time}
                              </span>
                            )}
                          </span>
                        ) : (
                          '—'
                        )
                      }
                      title={stamp.full || undefined}
                      subtext="When this forecast was stored"
                      accent="amber"
                      size="sm"
                    />
                  )
                })()}
              </div>

              <Card title="Prediction Summary" subtitle="Inputs used for this forecast">
                <PredictionSummary form={form} result={result} payload={lastPayload} />
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
