import { getModelAccuracy, getCurrentModel } from './modelService'
import { getLatestDashboard, getLatestForecast } from './persistenceService'

function settle(result) {
  if (result.status === 'fulfilled') {
    return { data: result.value.data, error: null }
  }
  const err = result.reason
  return {
    data: null,
    error: err instanceof Error ? err.message : String(err),
  }
}

/**
 * Loads the dashboard exclusively from persisted / live read APIs (Axios).
 * Sources: GET /dashboard/latest, /forecast/latest, /model/current, /model/accuracy
 * No hardcoded metrics — missing endpoints surface as null + error messages.
 */
export async function fetchDashboardData() {
  const [dashboard, forecast, accuracy, current] = await Promise.allSettled([
    getLatestDashboard(),
    getLatestForecast(),
    getModelAccuracy(),
    getCurrentModel(),
  ])

  const dashboardResult = settle(dashboard)
  const forecastResult = settle(forecast)
  const accuracyResult = settle(accuracy)
  const currentResult = settle(current)

  const d = dashboardResult.data
  const f = forecastResult.data
  const a = accuracyResult.data
  const m = currentResult.data

  const staff = d?.staff ?? null
  const inventory = d?.inventory ?? null
  const summary = d?.summary ?? null

  const staffCost = d?.staff_cost ?? summary?.staff_cost ?? null
  const inventoryCost = d?.inventory_cost ?? summary?.inventory_cost ?? null
  const totalCost =
    staffCost != null && inventoryCost != null
      ? staffCost + inventoryCost
      : d
        ? (d.staff_cost ?? 0) + (d.inventory_cost ?? 0) || null
        : null

  const todaysForecast = d?.forecast ?? f?.predicted_customers ?? null
  const confidence = d?.confidence ?? f?.confidence ?? null

  return {
    dashboard: d,
    forecast: f,
    accuracy: a,
    currentModel: m,
    staff,
    inventory,
    dashboardError: dashboardResult.error,
    forecastError: forecastResult.error,
    accuracyError: accuracyResult.error,
    currentModelError: currentResult.error,
    stats: {
      todaysForecast,
      confidence,
      modelAccuracy: a?.overall_accuracy ?? m?.accuracy ?? null,
      last30DaysAccuracy: a?.last_30_days_accuracy ?? null,
      recommendedStaff: summary?.recommended_staff ?? staff?.total_staff ?? null,
      staffCost,
      inventoryCost,
      ingredientCount: summary?.ingredients ?? inventory?.ingredient_count ?? null,
      estimatedRevenue: d?.revenue ?? null,
      estimatedProfit: d?.profit ?? summary?.estimated_profit ?? null,
      totalCost,
      modelVersion: m?.version_label ?? d?.model_version ?? f?.model_version ?? null,
      modelName: m?.model_name ?? null,
      lastRetrained: m?.training_date ?? null,
      datasetSize: m?.dataset_size ?? null,
    },
  }
}

export const DASHBOARD_QUERY_KEY = ['dashboard']
