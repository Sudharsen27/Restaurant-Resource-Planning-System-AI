import { formatDateTime } from './format'

export const PAGE_SIZE_OPTIONS = [10, 25, 50]
export const HISTORY_TABS = [
  { id: 'forecast', label: 'Forecast History' },
  { id: 'feedback', label: 'Feedback History' },
  { id: 'model', label: 'Model History' },
]

export function downloadCsv(filename, content) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function matchesDateRange(value, dateFrom, dateTo) {
  if (!dateFrom && !dateTo) return true
  if (!value) return false
  const day = String(value).slice(0, 10)
  if (dateFrom && day < dateFrom) return false
  if (dateTo && day > dateTo) return false
  return true
}

function matchesSearch(row, search, fields) {
  if (!search.trim()) return true
  const q = search.trim().toLowerCase()
  return fields.some((field) => {
    const val = row[field]
    return val != null && String(val).toLowerCase().includes(q)
  })
}

export function buildForecastHistoryRows(feedbackHistory, latestForecast) {
  const rows = (feedbackHistory || []).map((row) => ({
    predictionId: row.id,
    forecastDate: row.forecast_date,
    forecastHour: row.forecast_hour,
    predictedCustomers: row.predicted_customers,
    confidence: row.confidence,
    modelVersion: row.model_version_label,
    createdAt: row.created_at,
    status: row.actual_customers != null ? 'Reviewed' : 'Pending',
  }))

  if (latestForecast?.prediction_id) {
    const exists = rows.some((r) => r.predictionId === latestForecast.prediction_id)
    if (!exists) {
      rows.unshift({
        predictionId: latestForecast.prediction_id,
        forecastDate: latestForecast.date,
        forecastHour: latestForecast.hour,
        predictedCustomers: latestForecast.predicted_customers,
        confidence: latestForecast.confidence,
        modelVersion: latestForecast.model_version,
        createdAt: latestForecast.created_at,
        status: 'Pending',
      })
    }
  }

  return rows
}

export function buildFeedbackHistoryRows(feedbackHistory) {
  return (feedbackHistory || [])
    .filter((row) => row.actual_customers != null)
    .map((row) => ({
      predictionId: row.id,
      predicted: row.predicted_customers,
      actual: row.actual_customers,
      errorPct: row.percentage_error ?? row.mape,
      comments: row.comments,
      submittedBy: row.submitted_by ?? null,
      createdAt: row.feedback_received_at ?? row.created_at,
    }))
}

export function buildModelHistoryRows(feedbackHistory, latestDashboard, latestForecast) {
  const productionVersion =
    latestDashboard?.model_version ?? latestForecast?.model_version ?? null
  const aggregates = new Map()

  for (const row of feedbackHistory || []) {
    const version = row.model_version_label
    if (!version) continue

    if (!aggregates.has(version)) {
      aggregates.set(version, {
        version,
        trainingDate: row.created_at,
        percentageErrors: [],
        absoluteErrors: [],
        confidences: [],
        predictionCount: 0,
      })
    }

    const agg = aggregates.get(version)
    agg.predictionCount += 1
    if (row.confidence != null) agg.confidences.push(row.confidence)
    if (row.percentage_error != null) agg.percentageErrors.push(row.percentage_error)
    if (row.mape != null && row.percentage_error == null) agg.percentageErrors.push(row.mape)
    if (row.absolute_error != null) agg.absoluteErrors.push(row.absolute_error)
    if (new Date(row.created_at) < new Date(agg.trainingDate)) {
      agg.trainingDate = row.created_at
    }
  }

  const rows = [...aggregates.values()].map((agg) => {
    const avgError =
      agg.percentageErrors.length > 0
        ? agg.percentageErrors.reduce((sum, v) => sum + v, 0) / agg.percentageErrors.length
        : null
    const avgMae =
      agg.absoluteErrors.length > 0
        ? agg.absoluteErrors.reduce((sum, v) => sum + v, 0) / agg.absoluteErrors.length
        : null
    const avgConfidence =
      agg.confidences.length > 0
        ? agg.confidences.reduce((sum, v) => sum + v, 0) / agg.confidences.length
        : null

    return {
      version: agg.version,
      trainingDate: agg.trainingDate,
      accuracy: avgError != null ? Math.max(0, 100 - avgError) : avgConfidence,
      mae: avgMae,
      rmse: null,
      r2: null,
      datasetSize: null,
      isProduction: productionVersion != null && agg.version === productionVersion,
      predictionCount: agg.predictionCount,
    }
  })

  return rows.sort((a, b) => new Date(b.trainingDate) - new Date(a.trainingDate))
}

export function filterRows(rows, { search, dateFrom, dateTo, searchFields, dateField }) {
  return rows.filter((row) => {
    if (!matchesDateRange(row[dateField], dateFrom, dateTo)) return false
    return matchesSearch(row, search, searchFields)
  })
}

export function sortRows(rows, sortKey, sortDir) {
  const dir = sortDir === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    const av = a[sortKey]
    const bv = b[sortKey]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (av < bv) return -1 * dir
    if (av > bv) return 1 * dir
    return 0
  })
}

export function paginateRows(rows, page, pageSize) {
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize))
  const safePage = Math.min(page, totalPages - 1)
  const start = safePage * pageSize
  return {
    rows: rows.slice(start, start + pageSize),
    totalPages,
    safePage,
    total: rows.length,
    start: rows.length ? start + 1 : 0,
    end: Math.min(start + pageSize, rows.length),
  }
}

export function forecastHistoryToCsv(rows) {
  const header = [
    'Prediction ID',
    'Forecast Date',
    'Forecast Hour',
    'Predicted Customers',
    'Confidence',
    'Model Version',
    'Created At',
    'Status',
  ]
  const lines = rows.map((r) =>
    [
      r.predictionId,
      r.forecastDate,
      r.forecastHour,
      r.predictedCustomers,
      r.confidence ?? '',
      r.modelVersion ?? '',
      r.createdAt,
      r.status,
    ].join(','),
  )
  return [header.join(','), ...lines].join('\n')
}

export function feedbackHistoryToCsv(rows) {
  const header = [
    'Prediction ID',
    'Predicted Customers',
    'Actual Customers',
    'Error %',
    'Comments',
    'Submitted By',
    'Created At',
  ]
  const lines = rows.map((r) =>
    [
      r.predictionId,
      r.predicted,
      r.actual,
      r.errorPct ?? '',
      `"${(r.comments || '').replace(/"/g, '""')}"`,
      r.submittedBy ?? '',
      r.createdAt,
    ].join(','),
  )
  return [header.join(','), ...lines].join('\n')
}

export function modelHistoryToCsv(rows) {
  const header = [
    'Version',
    'Training Date',
    'Accuracy',
    'MAE',
    'RMSE',
    'R²',
    'Dataset Size',
    'Production Status',
  ]
  const lines = rows.map((r) =>
    [
      r.version,
      r.trainingDate,
      r.accuracy ?? '',
      r.mae ?? '',
      r.rmse ?? '',
      r.r2 ?? '',
      r.datasetSize ?? '',
      r.isProduction ? 'Production' : 'Archived',
    ].join(','),
  )
  return [header.join(','), ...lines].join('\n')
}

export function formatErrorPct(pct) {
  if (pct == null) return '—'
  return `${Number(pct).toFixed(1)}%`
}

export function formatDifference(diff) {
  if (diff == null) return '—'
  const sign = diff > 0 ? '+' : ''
  return `${sign}${diff}`
}

export function formatHour(hour) {
  return `${String(hour).padStart(2, '0')}:00`
}

export { formatDateTime }
