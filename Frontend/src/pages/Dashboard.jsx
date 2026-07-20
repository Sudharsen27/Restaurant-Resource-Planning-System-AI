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
  ShoppingCart,
  UserCheck,
  Trash2,
  Percent,
  AlertTriangle,
  ClipboardList,
  Truck,
} from 'lucide-react'
import Card from '../components/ui/Card'
import StatCard from '../components/ui/StatCard'
import { CardSkeleton, ChartSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { BarChartCard, LineChartCard } from '../components/charts/ChartComponents'
import QuickActions from '../components/dashboard/QuickActions'
import ActivityTimeline from '../components/dashboard/ActivityTimeline'
import { useQuery } from '@tanstack/react-query'
import { useDashboard } from '../hooks/useDashboard'
import { getFeedbackHistory } from '../services/feedbackService'
import { fetchExecutiveDashboard } from '../services/erpDashboardService'
import {
  chartColors,
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercent,
  formatModelName,
} from '../utils/format'
import { useOrg } from '../context/OrgContext'

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
  const { restaurant, branch } = useOrg()
  const { data, isLoading, isError, error, refetch, isFetching } = useDashboard()

  const { data: history, isLoading: histLoading } = useQuery({
    queryKey: ['feedback-history'],
    queryFn: async () => (await getFeedbackHistory({ limit: 100 })).data,
    staleTime: 30_000,
  })

  const { data: erpPayload, refetch: refetchErp } = useQuery({
    queryKey: ['erp-dashboard', restaurant?.id],
    queryFn: async () => {
      const res = await fetchExecutiveDashboard(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data
    },
    staleTime: 30_000,
  })

  const exec = erpPayload?.stats || {}
  const salesTrend = erpPayload?.salesTrend || []
  const ordersByHour = erpPayload?.ordersByHour || []
  const topProducts = erpPayload?.topProducts || []
  const activity = erpPayload?.recentActivity || []
  const deltas = exec.deltas || {}

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
      label: formatDate(h.created_at || h.date),
      forecast: h.predicted_customers,
      actual: h.actual_customers,
    }))

  const accuracyTrend = (history || [])
    .filter((h) => h.accuracy != null)
    .slice(-14)
    .map((h) => ({
      label: formatDate(h.created_at || h.date),
      accuracy: Number(h.accuracy),
    }))

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Executive dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {restaurant?.name}
            {branch ? ` · ${branch.name}` : ''} — live ops overview
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            refetch()
            refetchErp()
          }}
          disabled={isFetching}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {isError && <ErrorBanner message={error?.message || 'Failed to load dashboard'} onRetry={refetch} />}
      {hasPartialError && (
        <ErrorBanner message={`Some metrics unavailable: ${errors.join(' · ')}`} onRetry={refetch} />
      )}

      {/* ERP KPI row — mock until finance APIs exist */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Today</h2>
          <span className="text-[10px] uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
            Live data · PostgreSQL
          </span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard
            label="Today's Revenue"
            value={formatCurrency(exec.todaysRevenue || 0)}
            change={deltas.todaysRevenue}
            icon={DollarSign}
            accent="emerald"
          />
          <StatCard
            label="Today's Orders"
            value={formatNumber(exec.todaysOrders || 0)}
            change={deltas.todaysOrders}
            icon={ShoppingCart}
            accent="blue"
          />
          <StatCard
            label="Today's Customers"
            value={formatNumber(exec.todaysCustomers || 0)}
            change={deltas.todaysCustomers}
            icon={Users}
            accent="violet"
          />
          <StatCard
            label="Pending Orders"
            value={formatNumber(exec.pendingOrders || 0)}
            icon={ClipboardList}
            accent="amber"
          />
          <StatCard
            label="Low Stock Items"
            value={formatNumber(exec.lowStockItems || 0)}
            icon={AlertTriangle}
            accent="rose"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard
            label="Inventory Value"
            value={formatCurrency(exec.inventoryValue || 0)}
            change={deltas.inventoryValue}
            icon={Package}
            accent="blue"
          />
          <StatCard
            label="Total Products"
            value={formatNumber(exec.totalProducts || 0)}
            icon={Package}
            accent="violet"
          />
          <StatCard
            label="Out of Stock"
            value={formatNumber(exec.outOfStockItems || 0)}
            icon={AlertTriangle}
            accent="rose"
          />
          <StatCard
            label="Pending POs"
            value={formatNumber(exec.pendingPurchaseOrders || 0)}
            icon={ClipboardList}
            accent="amber"
          />
          <StatCard
            label="Suppliers"
            value={formatNumber(exec.supplierCount || 0)}
            icon={Truck}
            accent="emerald"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Food Waste"
            value={`${exec.foodWaste ?? 0}%`}
            change={deltas.foodWaste}
            icon={Trash2}
            accent="rose"
          />
          <StatCard
            label="Attendance"
            value={`${exec.employeeAttendance ?? 0}%`}
            change={deltas.employeeAttendance}
            icon={UserCheck}
            accent="emerald"
          />
          <StatCard
            label="Profit"
            value={formatCurrency(exec.profit || 0)}
            change={deltas.profit}
            icon={Wallet}
            accent="emerald"
          />
          <StatCard
            label="Forecast Accuracy"
            value={`${exec.forecastAccuracy ?? 0}%`}
            change={deltas.forecastAccuracy}
            icon={Percent}
            accent="violet"
          />
        </div>
      </section>

      {/* Live ML metrics when API available */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          Forecasting engine
        </h2>
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Today's Forecast"
              value={stats?.todaysForecast != null ? formatNumber(stats.todaysForecast) : '—'}
              icon={TrendingUp}
              accent="blue"
            />
            <StatCard
              label="Model Accuracy"
              value={stats?.modelAccuracy != null ? formatPercent(stats.modelAccuracy) : '—'}
              icon={Activity}
              accent="emerald"
            />
            <StatCard
              label="Staff Needed"
              value={stats?.staffNeeded != null ? formatNumber(stats.staffNeeded) : '—'}
              icon={Users}
              accent="amber"
            />
            <StatCard
              label="Model Version"
              value={stats?.modelVersion ? formatModelName(stats.modelVersion) : '—'}
              icon={Brain}
              accent="violet"
            />
          </div>
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card title="Sales & revenue trend" className="xl:col-span-2">
          <LineChartCard
            data={salesTrend}
            xKey="day"
            lines={[
              { key: 'sales', name: 'Sales', color: chartColors.primary },
              { key: 'revenue', name: 'Revenue', color: chartColors.success },
            ]}
          />
        </Card>
        <Card title="Orders by hour">
          <BarChartCard
            data={ordersByHour}
            xKey="hour"
            bars={[{ key: 'orders', name: 'Orders', color: chartColors.secondary }]}
          />
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card title="Top selling products" className="xl:col-span-2">
          <BarChartCard
            data={topProducts}
            xKey="name"
            bars={[{ key: 'units', name: 'Units', color: chartColors.primary }]}
          />
        </Card>
        <Card title="Recent activity">
          <ActivityTimeline items={activity} />
        </Card>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Quick actions</h2>
        <QuickActions />
      </section>

      {/* Existing forecast vs actual when history exists */}
      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Forecast vs actual">
          {histLoading ? (
            <ChartSkeleton />
          ) : forecastVsActual.length === 0 ? (
            <EmptyState title="No feedback history" description="Submit actuals to unlock this chart." />
          ) : (
            <LineChartCard
              data={forecastVsActual}
              xKey="label"
              lines={[
                { key: 'forecast', name: 'Forecast', color: chartColors.primary },
                { key: 'actual', name: 'Actual', color: chartColors.success },
              ]}
            />
          )}
        </Card>
        <Card title="Accuracy trend">
          {histLoading ? (
            <ChartSkeleton />
          ) : accuracyTrend.length === 0 ? (
            <EmptyState title="No accuracy points" description="Accuracy appears after feedback." />
          ) : (
            <LineChartCard
              data={accuracyTrend}
              xKey="label"
              lines={[{ key: 'accuracy', name: 'Accuracy %', color: chartColors.secondary }]}
            />
          )}
        </Card>
      </div>

    </div>
  )
}
