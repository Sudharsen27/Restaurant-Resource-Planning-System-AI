import { Loader2, RefreshCw } from 'lucide-react'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import { CardSkeleton } from '../components/ui/Skeleton'
import ModelAnalyticsHeader from '../components/analytics/ModelAnalyticsHeader'
import CurrentModelBanner from '../components/analytics/CurrentModelBanner'
import ModelMetricsCards from '../components/analytics/ModelMetricsCards'
import FeatureImportanceVisual from '../components/analytics/FeatureImportanceVisual'
import ModelVersionsTable from '../components/analytics/ModelVersionsTable'
import TrainingHistoryTable from '../components/analytics/TrainingHistoryTable'
import AnalyticsErrorCard from '../components/analytics/AnalyticsErrorCard'
import { AreaChartCard, BarChartCard, LineChartCard } from '../components/charts/ChartComponents'
import { ANALYTICS_QUERY_KEY, fetchAnalyticsData } from '../services/analyticsService'
import {
  buildAccuracyDashboardChart,
  buildFeatureImportanceChart,
  buildTrainingHistoryChart,
  buildTrainingHistoryRows,
  buildVersionComparisonChart,
  buildVersionHistoryRows,
} from '../utils/modelAnalytics'
import { chartColors, formatModelName } from '../utils/format'

export default function ModelAnalytics() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ANALYTICS_QUERY_KEY,
    queryFn: fetchAnalyticsData,
    staleTime: 60_000,
    retry: 1,
  })

  const current = data?.current
  const accuracy = data?.accuracy
  const versions = useMemo(() => data?.versions ?? [], [data?.versions])

  const featureImportance = useMemo(() => buildFeatureImportanceChart(current), [current])
  const trainingHistory = useMemo(() => buildTrainingHistoryChart(versions), [versions])
  const versionComparison = useMemo(() => buildVersionComparisonChart(versions), [versions])
  const accuracyChart = useMemo(() => buildAccuracyDashboardChart(accuracy), [accuracy])
  const trainingRows = useMemo(() => buildTrainingHistoryRows(versions), [versions])
  const versionRows = useMemo(() => buildVersionHistoryRows(versions), [versions])

  if (isLoading) {
    return (
      <div className="space-y-8">
        <ModelAnalyticsHeader />
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-violet-600" />
        </div>
      </div>
    )
  }

  if (isError && !data) {
    return (
      <div className="space-y-8">
        <ModelAnalyticsHeader />
        <AnalyticsErrorCard
          title="Unable to load model analytics"
          message={error?.message || 'Could not reach the model APIs.'}
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ModelAnalyticsHeader />
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex shrink-0 items-center gap-2 self-start rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {data?.errors?.length > 0 && (
        <AnalyticsErrorCard
          title="Partial data loaded"
          message={data.errors.join(' · ')}
          onRetry={() => refetch()}
        />
      )}

      <CurrentModelBanner current={current} accuracy={accuracy} />

      {isFetching && !isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <ModelMetricsCards current={current} accuracy={accuracy} />
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card
          title="Feature Importance"
          subtitle="Production model metrics profile"
        >
          {current ? (
            <FeatureImportanceVisual
              data={featureImportance}
              modelName={formatModelName(current.model_name)}
            />
          ) : (
            <EmptyState title="No production model" description="Model metrics are unavailable." />
          )}
        </Card>

        <Card title="Feedback Accuracy" subtitle="Accuracy trends from manager feedback">
          {accuracyChart.length ? (
            <BarChartCard
              data={accuracyChart}
              xKey="label"
              bars={[{ key: 'value', name: 'Accuracy %', color: chartColors.success }]}
            />
          ) : (
            <EmptyState
              title="No feedback accuracy yet"
              description="Submit manager feedback to populate accuracy trends."
            />
          )}
        </Card>

        <Card title="Training Metrics Trend" subtitle="Accuracy, MAE, and RMSE across versions" className="lg:col-span-2">
          {trainingHistory.length ? (
            <LineChartCard
              data={trainingHistory}
              xKey="version"
              lines={[
                { key: 'accuracy', name: 'Accuracy %', color: chartColors.success },
                { key: 'mae', name: 'MAE', color: chartColors.danger },
                { key: 'rmse', name: 'RMSE', color: chartColors.warning },
              ]}
            />
          ) : (
            <EmptyState title="No training history" />
          )}
        </Card>

        <Card title="Version Comparison" subtitle="Accuracy and error by version">
          {versionComparison.length ? (
            <BarChartCard
              data={versionComparison}
              xKey="name"
              bars={[
                { key: 'accuracy', name: 'Accuracy %', color: chartColors.primary },
                { key: 'mae', name: 'MAE', color: chartColors.secondary },
              ]}
            />
          ) : (
            <EmptyState title="No versions to compare" />
          )}
        </Card>

        <Card title="Dataset Growth" subtitle="Training data size per version">
          {trainingHistory.length ? (
            <AreaChartCard
              data={trainingHistory}
              xKey="version"
              areas={[{ key: 'dataset', name: 'Rows', color: chartColors.primary }]}
            />
          ) : (
            <EmptyState title="No dataset history" />
          )}
        </Card>
      </div>

      <Card title="Training History" subtitle="Chronological model training records">
        <TrainingHistoryTable rows={trainingRows} />
      </Card>

      <Card title="Version History" subtitle="All registered model versions">
        <ModelVersionsTable versions={versionRows} />
      </Card>
    </div>
  )
}
