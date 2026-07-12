import { getFeedbackHistory } from './feedbackService'
import { getLatestDashboard, getLatestForecast } from './persistenceService'

export const PREDICTION_HISTORY_QUERY_KEY = ['prediction-history-page']

function unwrap(result) {
  if (result.status === 'fulfilled') return { data: result.value.data, error: null }
  const err = result.reason
  return {
    data: null,
    error: err?.response?.data?.detail || err?.message || 'Request failed',
  }
}

export async function fetchPredictionHistoryData() {
  const [history, forecast, dashboard] = await Promise.allSettled([
    getFeedbackHistory({ skip: 0, limit: 500 }),
    getLatestForecast(),
    getLatestDashboard(),
  ])

  const historyResult = unwrap(history)
  const forecastResult = unwrap(forecast)
  const dashboardResult = unwrap(dashboard)

  return {
    feedbackHistory: historyResult.data || [],
    latestForecast: forecastResult.data,
    latestDashboard: dashboardResult.data,
    errors: [historyResult, forecastResult, dashboardResult]
      .filter((r) => r.error)
      .map((r) => r.error),
  }
}
