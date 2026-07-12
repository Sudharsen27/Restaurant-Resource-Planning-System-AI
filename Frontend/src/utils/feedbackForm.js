import { formatNumber } from './format'
import { formatHourLabel } from './forecastForm'

export function formatPredictionOption(item) {
  const date = item.forecast_date
  const hour = formatHourLabel(item.forecast_hour)
  const predicted = formatNumber(item.predicted_customers)
  const status = item.actual_customers != null ? ' (reviewed)' : ''
  return `#${item.id} — ${date} ${hour} — ${predicted} customers${status}`
}

export function getPendingPredictions(history) {
  return (history || []).filter((h) => h.actual_customers == null)
}

export function buildRecentFeedbackRows(history) {
  return (history || [])
    .filter((row) => row.actual_customers != null)
    .sort((a, b) => {
      const ta = new Date(a.feedback_received_at || a.created_at).getTime()
      const tb = new Date(b.feedback_received_at || b.created_at).getTime()
      return tb - ta
    })
    .map((row) => ({
      predictionId: row.id,
      predicted: row.predicted_customers,
      actual: row.actual_customers,
      error: row.percentage_error ?? row.mape,
      comments: row.comments,
      createdDate: row.feedback_received_at || row.created_at,
    }))
}

export function validateFeedbackForm(form) {
  const errors = {}
  const predictionId = Number(form.prediction_id)
  if (!form.prediction_id || !Number.isFinite(predictionId) || predictionId < 1) {
    errors.prediction_id = 'Select a prediction ID'
  }

  const actual = Number(form.actual_customers)
  if (!Number.isFinite(actual) || actual < 0) {
    errors.actual_customers = 'Actual customers must be 0 or greater'
  }

  return { valid: Object.keys(errors).length === 0, errors }
}

export function parseRetrainingStatus(retraining) {
  if (!retraining) return { status: 'unknown', message: 'No retraining data' }

  if (retraining.version_label) {
    return {
      status: 'success',
      message: `Model retrained and promoted to ${retraining.version_label}`,
      version: retraining.version_label,
      modelName: retraining.model_name,
      datasetSize: retraining.dataset_size,
      metrics: retraining.metrics,
    }
  }

  return { status: 'completed', message: 'Retraining completed', raw: retraining }
}
