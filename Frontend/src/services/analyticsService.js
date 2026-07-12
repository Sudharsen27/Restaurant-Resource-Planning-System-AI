import { getCurrentModel, getModelVersions, getModelAccuracy } from './modelService'

export {
  buildAccuracyDashboardChart,
  buildFeatureImportanceChart,
  buildTrainingHistoryChart,
  buildTrainingHistoryRows,
  buildVersionComparisonChart,
  buildVersionHistoryRows,
} from '../utils/modelAnalytics'

export const ANALYTICS_QUERY_KEY = ['model-analytics']

export async function fetchAnalyticsData() {
  const [current, versions, accuracy] = await Promise.allSettled([
    getCurrentModel(),
    getModelVersions(),
    getModelAccuracy(),
  ])

  const unwrap = (result) =>
    result.status === 'fulfilled' ? result.value.data : null

  return {
    current: unwrap(current),
    versions: unwrap(versions) || [],
    accuracy: unwrap(accuracy),
    errors: [current, versions, accuracy]
      .filter((r) => r.status === 'rejected')
      .map((r) => r.reason?.message || 'Request failed'),
  }
}
