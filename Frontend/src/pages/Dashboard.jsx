import {
  AlertCircle,
  RefreshCw,
  Activity,
  Brain,
  DollarSign,
  Package,
  TrendingUp,
  Users,
  Wallet,
} from 'lucide-react'
import Card from '../components/ui/Card'
import StatCard from '../components/ui/StatCard'
import { CardSkeleton, ChartSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import {
  BarChartCard,
  LineChartCard,
  PieChartCard,
} from '../components/charts/ChartComponents'
import { useQuery } from '@tanstack/react-query'
import { useDashboard } from '../hooks/useDashboard'
import { getFeedbackHistory } from '../services/feedbackService'
import {
  chartColors,
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercent,
  formatModelName,
} from '../utils/format'

function ErrorBanner({ message, onRetry }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/50 dark:bg-amber-950/30">
      <div className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="flex items-center gap-1 rounded-lg bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-900 hover:bg-amber-200 dark:bg-amber-900/50 dark:text-amber-100"
        >
          <RefreshCw className="h-3 w-3" />
          Retry
        </button>
      )}
    </div>
  )
}

function hasAnyMetric(stats) {
  if (!stats) return false
  return Object.values(stats).some((v) => v != null && v !== '')
}

export default function Dashboard() {
  const { data, isLoading, isError, error, refetch, isFetching } = useDashboard()

  const { data: history, isLoading: histLoading } = useQuery({
    queryKey: ['feedback-history'],
    queryFn: async () => (await getFeedbackHistory({ limit: 100 })).data,
    staleTime: 30_000,
  })

  const stats = data?.stats
  const errors = [
    data?.dashboardError,
    data?.forecastError,
    data?.accuracyError,
    data?.currentModelError,
  ].filter(Boolean)
  const hasPartialError = errors.length > 0 && hasAnyMetric(stats)

  const forecastVsActual = (history || [])
    .filter((h) => h.actual_customers != null)
    .slice(-14)
    .map((h) => ({
      date: `${h.forecast_date} ${h.forecast_hour}:00`,
      predicted: h.predicted_customers,
      actual: h.actual_customers,
    }))

  const perCustomerRevenue =
    stats?.estimatedRevenue && stats?.todaysForecast
      ? stats.estimatedRevenue / stats.todaysForecast
      : null

  const revenueTrend =
    perCustomerRevenue != null
      ? (history || [])
          .slice(-14)
          .map((h) => ({
            date: h.forecast_date?.slice(5) || '',
            revenue: Math.round(
              (h.actual_customers ?? h.predicted_customers) * perCustomerRevenue,
            ),
          }))
          .filter((r) => r.revenue > 0)
      : []

  const inventoryChart = (data?.inventory?.ingredients || []).slice(0, 8).map((ing) => ({
    name: ing.name.length > 12 ? `${ing.name.slice(0, 12)}…` : ing.name,
    required: ing.required,
    purchase: ing.purchase,
  }))

  const staffRoles = data?.staff?.staff
    ? Object.entries(data.staff.staff)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({
          name: name.replace(/_/g, ' '),
          value,
        }))
    : []

  const accuracyTrend = (history || [])
    .filter((h) => h.mape != null)
    .slice(-20)
    .map((h, i) => ({
      idx: i + 1,
      accuracy: Math.max(0, 100 - (h.mape || 0)),
    }))

  if (isError && !data) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Dashboard
          </h2>
        </div>
        <EmptyState
          title="Unable to load dashboard"
          description={error?.message || 'Check that the backend is running on port 8001'}
          action={
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Retry
            </button>
          }
        />
      </div>
    )
  }

  const noPersistedData =
    !isLoading &&
    !hasAnyMetric(stats) &&
    Boolean(data?.dashboardError || data?.forecastError)

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Live values from PostgreSQL snapshots and model APIs
            {isFetching && !isLoading && (
              <span className="ml-2 text-blue-500">· Refreshing…</span>
            )}
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {hasPartialError && (
        <ErrorBanner
          message={`Some metrics failed to load: ${errors.join('; ')}`}
          onRetry={() => refetch()}
        />
      )}

      {noPersistedData && (
        <EmptyState
          title="No saved dashboard data yet"
          description="Generate a forecast or full plan so PostgreSQL can store a snapshot, then refresh this page."
          action={
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Retry
            </button>
          }
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <StatCard
              label="Today's Forecast"
              value={
                stats?.todaysForecast != null ? formatNumber(stats.todaysForecast) : '—'
              }
              change={
                stats?.confidence != null
                  ? `${formatPercent(stats.confidence, 0)} confidence`
                  : data?.forecastError || data?.dashboardError || 'From /forecast/latest'
              }
              icon={TrendingUp}
              accent="blue"
            />
            <StatCard
              label="Model Accuracy"
              value={formatPercent(stats?.modelAccuracy)}
              change={
                stats?.last30DaysAccuracy != null
                  ? `30d: ${formatPercent(stats.last30DaysAccuracy)}`
                  : data?.accuracyError || 'From /model/accuracy'
              }
              icon={Brain}
              accent="violet"
            />
            <StatCard
              label="Recommended Staff"
              value={
                stats?.recommendedStaff != null
                  ? formatNumber(stats.recommendedStaff)
                  : '—'
              }
              change={
                stats?.staffCost != null
                  ? `Cost: ${formatCurrency(stats.staffCost)}`
                  : data?.dashboardError || 'From /dashboard/latest'
              }
              icon={Users}
              accent="emerald"
            />
            <StatCard
              label="Inventory Cost"
              value={
                stats?.inventoryCost != null ? formatCurrency(stats.inventoryCost) : '—'
              }
              change={
                stats?.ingredientCount != null
                  ? `${stats.ingredientCount} ingredients`
                  : data?.dashboardError || 'From /dashboard/latest'
              }
              icon={Package}
              accent="amber"
            />
            <StatCard
              label="Revenue"
              value={
                stats?.estimatedRevenue != null
                  ? formatCurrency(stats.estimatedRevenue)
                  : '—'
              }
              change={
                stats?.todaysForecast != null
                  ? `Based on ${formatNumber(stats.todaysForecast)} customers`
                  : data?.dashboardError || 'From /dashboard/latest'
              }
              icon={DollarSign}
              accent="blue"
            />
            <StatCard
              label="Profit"
              value={
                stats?.estimatedProfit != null
                  ? formatCurrency(stats.estimatedProfit)
                  : '—'
              }
              change={
                stats?.totalCost != null
                  ? `Total cost: ${formatCurrency(stats.totalCost)}`
                  : data?.dashboardError || 'From /dashboard/latest'
              }
              icon={Wallet}
              accent="emerald"
            />
            <StatCard
              label="Current Model Version"
              value={stats?.modelVersion || '—'}
              change={
                formatModelName(stats?.modelName) !== '—'
                  ? formatModelName(stats?.modelName)
                  : data?.currentModelError || 'From /model/current'
              }
              icon={Activity}
              accent="violet"
            />
            <StatCard
              label="Last Retrained"
              value={formatDate(stats?.lastRetrained)}
              change={
                stats?.datasetSize != null
                  ? `Dataset: ${formatNumber(stats.datasetSize)} rows`
                  : data?.currentModelError || 'From /model/current'
              }
              icon={Brain}
              accent="rose"
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Forecast vs Actual" subtitle="From GET /feedback/history">
          {histLoading ? (
            <ChartSkeleton />
          ) : forecastVsActual.length ? (
            <LineChartCard
              data={forecastVsActual}
              xKey="date"
              lines={[
                { key: 'predicted', name: 'Predicted', color: chartColors.primary },
                { key: 'actual', name: 'Actual', color: chartColors.success },
              ]}
            />
          ) : (
            <EmptyState
              title="No feedback yet"
              description="Submit manager feedback to compare predictions vs actuals"
            />
          )}
        </Card>

        <Card title="Revenue Trend" subtitle="Derived from history × latest revenue">
          {histLoading || isLoading ? (
            <ChartSkeleton />
          ) : revenueTrend.length ? (
            <LineChartCard
              data={revenueTrend}
              xKey="date"
              lines={[{ key: 'revenue', name: 'Revenue (INR)', color: chartColors.secondary }]}
            />
          ) : (
            <EmptyState title="No revenue data" description={data?.dashboardError} />
          )}
        </Card>

        <Card title="Inventory Usage" subtitle="From GET /dashboard/latest">
          {isLoading ? (
            <ChartSkeleton />
          ) : inventoryChart.length ? (
            <BarChartCard
              data={inventoryChart}
              xKey="name"
              bars={[
                { key: 'required', name: 'Required', color: chartColors.primary },
                { key: 'purchase', name: 'Purchase', color: chartColors.warning },
              ]}
            />
          ) : (
            <EmptyState title="No inventory data" description={data?.dashboardError} />
          )}
        </Card>

        <Card title="Staff Utilization" subtitle="From GET /dashboard/latest">
          {isLoading ? (
            <ChartSkeleton />
          ) : staffRoles.length ? (
            <PieChartCard data={staffRoles} />
          ) : (
            <EmptyState title="No staff data" description={data?.dashboardError} />
          )}
        </Card>

        <Card
          title="Model Accuracy Trend"
          subtitle="From feedback loop (100 − MAPE)"
          className="lg:col-span-2"
        >
          {histLoading ? (
            <ChartSkeleton />
          ) : accuracyTrend.length ? (
            <LineChartCard
              data={accuracyTrend}
              xKey="idx"
              lines={[{ key: 'accuracy', name: 'Accuracy %', color: chartColors.success }]}
            />
          ) : (
            <EmptyState title="No accuracy history" />
          )}
        </Card>
      </div>
    </div>
  )
}
