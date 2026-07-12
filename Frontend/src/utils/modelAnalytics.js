import { chartColors } from './format'

export function buildTrainingHistoryChart(versions) {
  return [...(versions || [])]
    .sort((a, b) => new Date(a.training_date) - new Date(b.training_date))
    .map((v) => ({
      version: v.version_label,
      accuracy: v.accuracy,
      mae: v.mae,
      rmse: v.rmse,
      r2: v.r2,
      dataset: v.dataset_size,
      date: v.training_date,
    }))
}

export function buildVersionComparisonChart(versions) {
  return [...(versions || [])]
    .sort((a, b) => a.id - b.id)
    .map((v) => ({
      name: v.version_label,
      accuracy: v.accuracy,
      mae: v.mae,
      rmse: v.rmse,
    }))
}

/** Visual profile from production model metrics (GET /model/current). */
export function buildFeatureImportanceChart(current) {
  if (!current) return []
  return [
    { feature: 'Accuracy', importance: current.accuracy ?? 0, fill: chartColors.success },
    { feature: 'R² Score', importance: (current.r2 ?? 0) * 100, fill: chartColors.secondary },
    {
      feature: 'MAE (inverted)',
      importance: current.mae != null ? Math.max(0, 100 - current.mae * 50) : 0,
      fill: chartColors.warning,
    },
    {
      feature: 'RMSE (inverted)',
      importance: current.rmse != null ? Math.max(0, 100 - current.rmse * 20) : 0,
      fill: chartColors.danger,
    },
  ]
}

export function buildAccuracyDashboardChart(accuracy) {
  if (!accuracy) return []
  return [
    { label: 'Today', value: accuracy.todays_accuracy },
    { label: '30 Days', value: accuracy.last_30_days_accuracy },
    { label: 'Overall', value: accuracy.overall_accuracy },
  ].filter((d) => d.value != null)
}

export function buildTrainingHistoryRows(versions) {
  return [...(versions || [])]
    .sort((a, b) => new Date(a.training_date) - new Date(b.training_date))
    .map((v) => ({
      id: v.id,
      version: v.version_label,
      modelName: v.model_name,
      trainedAt: v.training_date,
      datasetSize: v.dataset_size,
      accuracy: v.accuracy,
      mae: v.mae,
      rmse: v.rmse,
      r2: v.r2,
      isProduction: v.is_production,
    }))
}

export function buildVersionHistoryRows(versions) {
  return [...(versions || [])]
    .sort((a, b) => b.id - a.id)
    .map((v) => ({
      id: v.id,
      version: v.version_label,
      modelName: v.model_name,
      trainedAt: v.training_date,
      datasetSize: v.dataset_size,
      accuracy: v.accuracy,
      mae: v.mae,
      rmse: v.rmse,
      r2: v.r2,
      isProduction: v.is_production,
    }))
}
