import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  Bot,
  CheckCircle2,
  Download,
  Lightbulb,
  MessageSquare,
  Package,
  RefreshCw,
  Send,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Users,
  Wallet,
} from 'lucide-react'
import EntityListPage from '../../components/pages/EntityListPage'
import {
  AreaChartCard,
  BarChartCard,
  LineChartCard,
  PieChartCard,
} from '../../components/charts/ChartComponents'
import { Input, Select } from '../../components/forms/FormControls'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import LoadingSpinner from '../../components/ui/LoadingSpinner'
import { useOrg } from '../../context/OrgContext'
import { useToast } from '../../context/ToastContext'
import {
  acknowledgeInsight,
  askAssistant,
  exportReport,
  fetchAlerts,
  fetchCustomerAnalytics,
  fetchDemandForecast,
  fetchEmployeeAnalytics,
  fetchExecutive,
  fetchInsights,
  fetchMenuAnalytics,
  fetchRevenueTrend,
  fetchSalesForecast,
  resolveAlert,
} from '../../services/biService'
import {
  chartColors,
  formatCurrency,
  formatDate,
  formatNumber,
  formatPercent,
} from '../../utils/format'

function asData(res) {
  if (res && typeof res === 'object' && !Array.isArray(res) && res.data != null && !Array.isArray(res.data)) {
    return res.data
  }
  if (res?.data != null) return res.data
  return res
}

function asList(res) {
  const d = asData(res)
  if (Array.isArray(d)) return d
  if (Array.isArray(res)) return res
  return []
}

function defaultDateRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
  }
}

function orgQueryParams(restaurant, branch, extra = {}) {
  return {
    restaurant_id: restaurant?.id,
    branch_id: branch?.id,
    ...extra,
  }
}

function ErrorBanner({ message, onRetry }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/50 dark:bg-amber-950/30">
      <div className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <span>{message}</span>
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="flex items-center gap-1 rounded-lg bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-900 hover:bg-amber-200 dark:bg-amber-900/50 dark:text-amber-100"
        >
          <RefreshCw className="h-3 w-3" />
          Retry
        </button>
      ) : null}
    </div>
  )
}

function SeverityBadge({ severity }) {
  const s = String(severity || 'INFO').toUpperCase()
  const styles = {
    ALERT: 'bg-rose-50 text-rose-700 ring-rose-600/20 dark:bg-rose-950/40 dark:text-rose-300',
    WARNING: 'bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-950/40 dark:text-amber-300',
    INFO: 'bg-sky-50 text-sky-700 ring-sky-600/20 dark:bg-sky-950/40 dark:text-sky-300',
  }
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${styles[s] || styles.INFO}`}
    >
      {s}
    </span>
  )
}

function KpiGrid({ cards, loading }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {cards.map((c) => (
        <Card key={c.label} className="!p-0">
          <div className="p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{c.label}</p>
            <p className="mt-2 text-2xl font-bold tabular-nums text-slate-900 dark:text-white">
              {loading ? '…' : c.value ?? '—'}
            </p>
            {c.hint ? <p className="mt-1 text-xs text-slate-500">{c.hint}</p> : null}
            {c.delta != null ? (
              <p
                className={`mt-1 flex items-center gap-0.5 text-xs font-medium ${
                  c.delta >= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {c.delta >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {formatPercent(Math.abs(c.delta), 1)} vs prior
              </p>
            ) : null}
          </div>
        </Card>
      ))}
    </div>
  )
}

function BiPageShell({ title, description, filters, children }) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
          <p className="mt-1 text-[11px] uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
            Live BI · PostgreSQL
          </p>
        </div>
        {filters}
      </div>
      {children}
    </div>
  )
}

function DateRangeFilters({ range, onChange, restaurant, branch }) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <Input
        label="From"
        type="date"
        value={range.start_date}
        onChange={(e) => onChange({ ...range, start_date: e.target.value })}
        className="w-40"
      />
      <Input
        label="To"
        type="date"
        value={range.end_date}
        onChange={(e) => onChange({ ...range, end_date: e.target.value })}
        className="w-40"
      />
      <p className="pb-2 text-xs text-slate-500">
        {restaurant?.name}
        {branch ? ` · ${branch.name}` : ''}
      </p>
    </div>
  )
}

function InsightStrip({ insights, loading, onAcknowledge, acknowledgingId }) {
  if (loading) return <LoadingSpinner label="Loading insights…" />
  if (!insights.length) {
    return (
      <Card title="Insights" subtitle="Auto-generated business signals">
        <EmptyState title="No open insights" description="Generate insights from the Insights page." />
      </Card>
    )
  }
  return (
    <Card title="Insight strip" subtitle="Top unacknowledged signals">
      <div className="space-y-3">
        {insights.slice(0, 4).map((ins) => (
          <div
            key={ins.id}
            className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/50"
          >
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <SeverityBadge severity={ins.severity} />
                <span className="font-semibold text-slate-900 dark:text-white">{ins.title}</span>
              </div>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{ins.body}</p>
            </div>
            <Button
              size="sm"
              variant="secondary"
              disabled={acknowledgingId === ins.id}
              onClick={() => onAcknowledge(ins.id)}
            >
              Acknowledge
            </Button>
          </div>
        ))}
      </div>
    </Card>
  )
}

export function ExecutiveDashboardPage() {
  const { restaurant, branch } = useOrg()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [range, setRange] = useState(defaultDateRange)
  const params = orgQueryParams(restaurant, branch, range)

  const execQuery = useQuery({
    queryKey: ['bi-executive', params],
    queryFn: async () => asData(await fetchExecutive(params)),
    enabled: Boolean(restaurant?.id),
  })

  const trendQuery = useQuery({
    queryKey: ['bi-revenue-trend', params],
    queryFn: async () => asData(await fetchRevenueTrend(params)),
    enabled: Boolean(restaurant?.id),
  })

  const insightsQuery = useQuery({
    queryKey: ['bi-insights-strip', restaurant?.id, branch?.id],
    queryFn: async () => asList(await fetchInsights(orgQueryParams(restaurant, branch))),
    enabled: Boolean(restaurant?.id),
  })

  const ackMutation = useMutation({
    mutationFn: acknowledgeInsight,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bi-insights-strip'] })
      toast.success('Insight acknowledged')
    },
    onError: (err) => toast.error(err.message),
  })

  const kpis = execQuery.data
  const trend = trendQuery.data
  const isLoading = execQuery.isLoading || trendQuery.isLoading
  const isError = execQuery.isError || trendQuery.isError
  const error = execQuery.error || trendQuery.error

  const kpiCards = [
    { label: 'Revenue', value: formatCurrency(kpis?.revenue), hint: 'Period total' },
    { label: 'Profit', value: formatCurrency(kpis?.profit), hint: 'After food & labor' },
    { label: 'Orders', value: formatNumber(kpis?.orders_count), hint: 'Completed pipeline' },
    { label: 'AOV', value: formatCurrency(kpis?.aov), hint: 'Avg order value' },
    { label: 'Food cost', value: formatPercent(kpis?.food_cost_pct), hint: formatCurrency(kpis?.food_cost) },
    { label: 'Labor', value: formatCurrency(kpis?.labor_cost), hint: 'Payroll & attendance' },
    { label: 'Inventory', value: formatCurrency(kpis?.inventory_value), hint: 'On-hand value' },
    {
      label: 'Retention',
      value: kpis?.customer_retention != null ? formatPercent(kpis.customer_retention * 100) : '—',
      hint: `${kpis?.repeat_customers ?? 0} returning`,
    },
    {
      label: 'Growth',
      value: formatPercent(kpis?.growth_pct),
      hint: 'vs prior period',
      delta: kpis?.growth_pct,
    },
  ]

  const chartSeries = (trend?.series || []).map((row) => ({
    ...row,
    label: formatDate(row.date),
  }))

  const paymentPie = (trend?.payment_distribution || []).map((p) => ({
    name: p.method,
    value: p.amount,
  }))

  return (
    <BiPageShell
      title="Executive BI"
      description="Enterprise KPIs, revenue trends, and payment mix for leadership."
      filters={<DateRangeFilters range={range} onChange={setRange} restaurant={restaurant} branch={branch} />}
    >
      {isError ? <ErrorBanner message={error?.message} onRetry={() => { execQuery.refetch(); trendQuery.refetch() }} /> : null}

      <KpiGrid cards={kpiCards} loading={isLoading} />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Revenue trend" subtitle="Daily revenue & orders" className="lg:col-span-2">
          {trendQuery.isLoading ? (
            <LoadingSpinner />
          ) : chartSeries.length ? (
            <AreaChartCard
              data={chartSeries}
              xKey="label"
              areas={[
                { key: 'revenue', name: 'Revenue', color: chartColors.primary },
                { key: 'orders', name: 'Orders', color: chartColors.secondary },
              ]}
            />
          ) : (
            <EmptyState title="No revenue data" description="Adjust the date range or record orders." />
          )}
        </Card>

        <Card title="Payment mix" subtitle="Methods by amount">
          {trendQuery.isLoading ? (
            <LoadingSpinner />
          ) : paymentPie.length ? (
            <PieChartCard data={paymentPie} />
          ) : (
            <EmptyState title="No payments" description="Payments appear after checkout." />
          )}
        </Card>
      </div>

      <InsightStrip
        insights={insightsQuery.data || []}
        loading={insightsQuery.isLoading}
        acknowledgingId={ackMutation.variables}
        onAcknowledge={(id) => ackMutation.mutate(id)}
      />
    </BiPageShell>
  )
}

const ANALYTICS_TABS = [
  { id: 'menu', label: 'Menu' },
  { id: 'customers', label: 'Customers' },
  { id: 'employees', label: 'Employees' },
]

export function AnalyticsCenterPage() {
  const { restaurant, branch } = useOrg()
  const [tab, setTab] = useState('menu')
  const [range, setRange] = useState(defaultDateRange)
  const params = orgQueryParams(restaurant, branch, range)

  const menuQuery = useQuery({
    queryKey: ['bi-menu', params],
    queryFn: async () => asData(await fetchMenuAnalytics(params)),
    enabled: Boolean(restaurant?.id) && tab === 'menu',
  })

  const customerQuery = useQuery({
    queryKey: ['bi-customers', params],
    queryFn: async () => asData(await fetchCustomerAnalytics(params)),
    enabled: Boolean(restaurant?.id) && tab === 'customers',
  })

  const employeeQuery = useQuery({
    queryKey: ['bi-employees', params],
    queryFn: async () => asData(await fetchEmployeeAnalytics(params)),
    enabled: Boolean(restaurant?.id) && tab === 'employees',
  })

  const activeQuery = tab === 'menu' ? menuQuery : tab === 'customers' ? customerQuery : employeeQuery

  const menuChart = (menuQuery.data?.best_sellers_qty || []).slice(0, 8).map((r) => ({
    name: r.name?.length > 18 ? `${r.name.slice(0, 16)}…` : r.name,
    qty: r.quantity_sold,
    revenue: r.revenue,
  }))

  const segmentPie = Object.entries(customerQuery.data?.segments_by_membership || {}).map(
    ([name, value]) => ({ name, value }),
  )

  const waiterChart = (employeeQuery.data?.sales_per_waiter || []).slice(0, 8).map((r) => ({
    name: r.waiter?.length > 14 ? `${r.waiter.slice(0, 12)}…` : r.waiter,
    revenue: r.revenue,
  }))

  return (
    <BiPageShell
      title="Analytics Center"
      description="Menu performance, customer segments, and workforce analytics."
      filters={<DateRangeFilters range={range} onChange={setRange} restaurant={restaurant} branch={branch} />}
    >
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2 dark:border-zinc-800">
        {ANALYTICS_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              tab === t.id
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
                : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-zinc-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeQuery.isError ? (
        <ErrorBanner message={activeQuery.error?.message} onRetry={() => activeQuery.refetch()} />
      ) : null}

      {tab === 'menu' ? (
        <div className="space-y-6">
          <Card title="Best sellers" subtitle="By quantity sold">
            {menuQuery.isLoading ? (
              <LoadingSpinner />
            ) : menuChart.length ? (
              <BarChartCard
                data={menuChart}
                xKey="name"
                bars={[{ key: 'qty', name: 'Qty sold', color: chartColors.primary }]}
                height={320}
              />
            ) : (
              <EmptyState title="No menu sales" description="Orders with menu items will populate this view." />
            )}
          </Card>
          <EntityListPage
            title="Menu performance"
            description="Margin and revenue by item"
            entity="menu-analytics"
            loading={menuQuery.isLoading}
            rows={menuQuery.data?.best_sellers_revenue || []}
            columns={[
              { key: 'name', label: 'Item' },
              { key: 'quantity_sold', label: 'Qty', render: (v) => formatNumber(v, 1) },
              { key: 'revenue', label: 'Revenue', render: (v) => formatCurrency(v) },
              { key: 'margin_pct', label: 'Margin', render: (v) => formatPercent(v) },
            ]}
          />
        </div>
      ) : null}

      {tab === 'customers' ? (
        <div className="space-y-6">
          <KpiGrid
            loading={customerQuery.isLoading}
            cards={[
              { label: 'Total customers', value: formatNumber(customerQuery.data?.total_customers) },
              { label: 'New (period)', value: formatNumber(customerQuery.data?.new_customers) },
              { label: 'Returning', value: formatNumber(customerQuery.data?.returning_customers) },
              {
                label: 'Retention',
                value: customerQuery.data?.retention_rate != null
                  ? formatPercent(customerQuery.data.retention_rate * 100)
                  : '—',
              },
              { label: 'VIP', value: formatNumber(customerQuery.data?.vip_count) },
              { label: 'Avg CLV', value: formatCurrency(customerQuery.data?.avg_clv) },
              { label: 'Avg visits', value: formatNumber(customerQuery.data?.avg_visit_count, 1) },
              { label: 'Loyalty avg', value: formatNumber(customerQuery.data?.loyalty_points_avg, 0) },
            ]}
          />
          <Card title="Membership segments" subtitle="Customer distribution">
            {customerQuery.isLoading ? (
              <LoadingSpinner />
            ) : segmentPie.length ? (
              <PieChartCard data={segmentPie} />
            ) : (
              <EmptyState title="No segments" description="Add customers with membership levels." />
            )}
          </Card>
        </div>
      ) : null}

      {tab === 'employees' ? (
        <div className="space-y-6">
          <KpiGrid
            loading={employeeQuery.isLoading}
            cards={[
              { label: 'Headcount', value: formatNumber(employeeQuery.data?.employee_count) },
              { label: 'Attendance', value: formatPercent(employeeQuery.data?.attendance_pct) },
              { label: 'Overtime (min)', value: formatNumber(employeeQuery.data?.overtime_minutes_total) },
            ]}
          />
          <Card title="Sales by waiter" subtitle="Table-assigned revenue">
            {employeeQuery.isLoading ? (
              <LoadingSpinner />
            ) : waiterChart.length ? (
              <BarChartCard
                data={waiterChart}
                xKey="name"
                bars={[{ key: 'revenue', name: 'Revenue', color: chartColors.success }]}
                layout="vertical"
                height={320}
              />
            ) : (
              <EmptyState title="No waiter sales" description="Assign waiters to tables to track attribution." />
            )}
          </Card>
          <EntityListPage
            title="Hours ranking"
            description="Top employees by hours worked"
            entity="employee-hours"
            loading={employeeQuery.isLoading}
            rows={employeeQuery.data?.hours_ranking || []}
            columns={[
              { key: 'name', label: 'Employee' },
              { key: 'role', label: 'Role' },
              { key: 'hours_worked', label: 'Hours', render: (v) => formatNumber(v, 1) },
              { key: 'overtime_minutes', label: 'OT (min)', render: (v) => formatNumber(v) },
            ]}
          />
        </div>
      ) : null}
    </BiPageShell>
  )
}

const HORIZON_OPTIONS = [
  { value: 'tomorrow', label: 'Tomorrow' },
  { value: 'week', label: 'Next 7 days' },
  { value: 'month', label: 'Next 30 days' },
]

export function ForecastDashboardPage() {
  const { restaurant, branch } = useOrg()
  const [horizon, setHorizon] = useState('week')
  const params = orgQueryParams(restaurant, branch, { horizon })

  const salesQuery = useQuery({
    queryKey: ['bi-sales-forecast', params],
    queryFn: async () => asData(await fetchSalesForecast(params)),
    enabled: Boolean(restaurant?.id),
  })

  const demandQuery = useQuery({
    queryKey: ['bi-demand-forecast', restaurant?.id, branch?.id],
    queryFn: async () => asData(await fetchDemandForecast(orgQueryParams(restaurant, branch))),
    enabled: Boolean(restaurant?.id),
  })

  const salesChart = (salesQuery.data?.predictions || []).map((p) => ({
    label: formatDate(p.date),
    predicted_revenue: p.predicted_revenue,
  }))

  const peakHours = (demandQuery.data?.peak_hours || []).map((h) => ({
    hour: `${String(h.hour).padStart(2, '0')}:00`,
    orders: h.orders,
  }))

  return (
    <BiPageShell
      title="BI Forecasts"
      description="Sales projections, peak-hour demand, and ingredient predictions."
      filters={
        <Select
          label="Sales horizon"
          value={horizon}
          onChange={(e) => setHorizon(e.target.value)}
          options={HORIZON_OPTIONS}
          className="w-44"
        />
      }
    >
      {(salesQuery.isError || demandQuery.isError) ? (
        <ErrorBanner
          message={(salesQuery.error || demandQuery.error)?.message}
          onRetry={() => {
            salesQuery.refetch()
            demandQuery.refetch()
          }}
        />
      ) : null}

      <KpiGrid
        loading={salesQuery.isLoading}
        cards={[
          {
            label: 'Predicted total',
            value: formatCurrency(salesQuery.data?.predicted_total_revenue),
            hint: HORIZON_OPTIONS.find((o) => o.value === horizon)?.label,
          },
          {
            label: 'Baseline daily',
            value: formatCurrency(salesQuery.data?.baseline_daily_revenue),
            hint: salesQuery.data?.method,
          },
          {
            label: 'Avg footfall',
            value: formatNumber(demandQuery.data?.avg_daily_footfall, 1),
            hint: 'Guests / day (28d avg)',
          },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Sales forecast" subtitle="Predicted daily revenue">
          {salesQuery.isLoading ? (
            <LoadingSpinner />
          ) : salesChart.length ? (
            <LineChartCard
              data={salesChart}
              xKey="label"
              lines={[{ key: 'predicted_revenue', name: 'Predicted revenue', color: chartColors.primary }]}
            />
          ) : (
            <EmptyState title="Insufficient history" description="Need order history to generate forecasts." />
          )}
        </Card>

        <Card title="Peak hours" subtitle="Order volume by hour (28d)">
          {demandQuery.isLoading ? (
            <LoadingSpinner />
          ) : peakHours.length ? (
            <BarChartCard
              data={peakHours}
              xKey="hour"
              bars={[{ key: 'orders', name: 'Orders', color: chartColors.warning }]}
            />
          ) : (
            <EmptyState title="No hourly data" />
          )}
        </Card>
      </div>

      <EntityListPage
        title="Ingredient predictions"
        description="Daily qty from recipe-linked demand forecast"
        entity="ingredient-forecast"
        loading={demandQuery.isLoading}
        rows={demandQuery.data?.top_ingredients || []}
        columns={[
          { key: 'ingredient', label: 'Ingredient' },
          { key: 'predicted_daily_qty', label: 'Predicted qty / day', render: (v) => formatNumber(v, 2) },
        ]}
      />

      {salesQuery.data?.top_item_demand?.length ? (
        <EntityListPage
          title="Top item demand"
          description="Predicted daily menu item quantities"
          entity="item-demand"
          loading={salesQuery.isLoading}
          rows={salesQuery.data.top_item_demand}
          columns={[
            { key: 'name', label: 'Menu item' },
            { key: 'predicted_daily_qty', label: 'Predicted qty / day', render: (v) => formatNumber(v, 1) },
          ]}
        />
      ) : null}
    </BiPageShell>
  )
}

export function InsightsAlertsPage() {
  const { restaurant, branch } = useOrg()
  const toast = useToast()
  const queryClient = useQueryClient()
  const orgParams = orgQueryParams(restaurant, branch)

  const insightsQuery = useQuery({
    queryKey: ['bi-insights', orgParams],
    queryFn: async () => asList(await fetchInsights({ ...orgParams, include_acknowledged: true })),
    enabled: Boolean(restaurant?.id),
  })

  const alertsQuery = useQuery({
    queryKey: ['bi-alerts', orgParams],
    queryFn: async () => asData(await fetchAlerts(orgParams)),
    enabled: Boolean(restaurant?.id),
  })

  const generateMutation = useMutation({
    mutationFn: () => fetchInsights({ ...orgParams, generate: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bi-insights'] })
      toast.success('Insights generated')
    },
    onError: (err) => toast.error(err.message),
  })

  const ackMutation = useMutation({
    mutationFn: acknowledgeInsight,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bi-insights'] })
      toast.success('Insight acknowledged')
    },
    onError: (err) => toast.error(err.message),
  })

  const resolveMutation = useMutation({
    mutationFn: resolveAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bi-alerts'] })
      toast.success('Alert resolved')
    },
    onError: (err) => toast.error(err.message),
  })

  const openAlerts = alertsQuery.data?.open_alerts || []

  return (
    <BiPageShell
      title="Insights & Alerts"
      description="Rule-based insights and operational alert center."
      filters={
        <Button
          variant="secondary"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending || !restaurant?.id}
        >
          <Sparkles className="h-4 w-4" />
          Generate insights
        </Button>
      }
    >
      {(insightsQuery.isError || alertsQuery.isError) ? (
        <ErrorBanner
          message={(insightsQuery.error || alertsQuery.error)?.message}
          onRetry={() => {
            insightsQuery.refetch()
            alertsQuery.refetch()
          }}
        />
      ) : null}

      <Card
        title="Insights"
        subtitle={`${insightsQuery.data?.length || 0} records`}
        action={
          <Button size="sm" variant="ghost" onClick={() => insightsQuery.refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        }
      >
        {insightsQuery.isLoading ? (
          <LoadingSpinner />
        ) : insightsQuery.data?.length ? (
          <div className="space-y-3">
            {insightsQuery.data.map((ins) => (
              <div
                key={ins.id}
                className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-200 p-4 dark:border-zinc-800"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <SeverityBadge severity={ins.severity} />
                    <span className="font-semibold">{ins.title}</span>
                    {ins.acknowledged ? (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Acknowledged
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{ins.body}</p>
                  <p className="mt-1 text-xs text-slate-400">{formatDate(ins.created_at)}</p>
                </div>
                {!ins.acknowledged ? (
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={ackMutation.isPending}
                    onClick={() => ackMutation.mutate(ins.id)}
                  >
                    Acknowledge
                  </Button>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No insights yet"
            description="Generate insights from current KPIs and inventory signals."
            action={
              <Button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
                Generate now
              </Button>
            }
          />
        )}
      </Card>

      <Card title="Alert center" subtitle={`${openAlerts.length} open alerts`}>
        {alertsQuery.isLoading ? (
          <LoadingSpinner />
        ) : openAlerts.length ? (
          <div className="space-y-3">
            {openAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-amber-200/80 bg-amber-50/50 p-4 dark:border-amber-900/40 dark:bg-amber-950/20"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <SeverityBadge severity={alert.severity} />
                    <span className="text-xs font-mono text-slate-500">{alert.alert_type}</span>
                  </div>
                  <p className="mt-1 font-semibold text-slate-900 dark:text-white">{alert.title}</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">{alert.body}</p>
                </div>
                <Button
                  size="sm"
                  onClick={() => resolveMutation.mutate(alert.id)}
                  disabled={resolveMutation.isPending}
                >
                  Resolve
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No open alerts" description="Alerts are created from live operational thresholds." />
        )}
      </Card>
    </BiPageShell>
  )
}

const REPORT_KINDS = [
  { kind: 'daily', label: 'Daily report', blurb: 'Today’s KPIs, trend, and payments' },
  { kind: 'weekly', label: 'Weekly report', blurb: 'Last 7 days consolidated' },
  { kind: 'monthly', label: 'Monthly report', blurb: 'Last 30 days consolidated' },
]

export function ReportsCenterPage() {
  const { restaurant, branch } = useOrg()
  const toast = useToast()
  const [exporting, setExporting] = useState(null)

  const handleExport = async (kind) => {
    setExporting(kind)
    try {
      const { filename } = await exportReport(kind, orgQueryParams(restaurant, branch))
      toast.success(`Downloaded ${filename}`)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setExporting(null)
    }
  }

  return (
    <BiPageShell
      title="Reports Center"
      description="Export executive BI summaries as CSV for finance and ops."
    >
      <div className="grid gap-4 sm:grid-cols-3">
        {REPORT_KINDS.map(({ kind, label, blurb }) => (
          <Card key={kind} className="!p-0">
            <div className="flex h-full flex-col p-6">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">{label}</h3>
              <p className="mt-2 flex-1 text-sm text-slate-500">{blurb}</p>
              <Button
                className="mt-6 w-full"
                onClick={() => handleExport(kind)}
                disabled={!restaurant?.id || exporting === kind}
              >
                <Download className="h-4 w-4" />
                {exporting === kind ? 'Exporting…' : 'Download CSV'}
              </Button>
            </div>
          </Card>
        ))}
      </div>
      <p className="text-xs text-slate-500">
        Scope: {restaurant?.name || '—'}
        {branch ? ` · ${branch.name}` : ''}
      </p>
    </BiPageShell>
  )
}

const ASSISTANT_PROMPTS = [
  {
    label: 'Revenue & profit',
    prompt: 'What is our revenue and profit this month?',
    icon: Wallet,
  },
  {
    label: 'Low stock',
    prompt: 'Which items are low on stock?',
    icon: Package,
  },
  {
    label: 'Staff & labor',
    prompt: 'How is staff attendance and labor?',
    icon: Users,
  },
  {
    label: 'Customers',
    prompt: 'Show customer retention and VIP count',
    icon: MessageSquare,
  },
  {
    label: 'Next week forecast',
    prompt: 'Forecast sales for next week',
    icon: TrendingUp,
  },
]

const CARD_ACCENT = {
  sales: 'from-emerald-500/15 to-transparent text-emerald-600 dark:text-emerald-400',
  overview: 'from-sky-500/15 to-transparent text-sky-600 dark:text-sky-400',
  inventory: 'from-amber-500/15 to-transparent text-amber-600 dark:text-amber-400',
  hr: 'from-cyan-500/15 to-transparent text-cyan-600 dark:text-cyan-400',
  customers: 'from-rose-500/15 to-transparent text-rose-600 dark:text-rose-400',
  menu: 'from-orange-500/15 to-transparent text-orange-600 dark:text-orange-400',
  forecast: 'from-blue-500/15 to-transparent text-blue-600 dark:text-blue-400',
}

function RecommendationCard({ card }) {
  const metrics = useMemo(() => {
    const d = card.data
    if (!d || typeof d !== 'object') return []
    if (card.type === 'sales' || card.type === 'overview') {
      return [
        { label: 'Revenue', value: formatCurrency(d.revenue), emphasize: true },
        { label: 'Profit', value: formatCurrency(d.profit), emphasize: true },
        { label: 'Orders', value: formatNumber(d.orders_count) },
        {
          label: 'Growth',
          value:
            d.growth_pct != null
              ? `${d.growth_pct > 0 ? '+' : ''}${formatPercent(d.growth_pct)}`
              : '—',
          tone: d.growth_pct > 0 ? 'up' : d.growth_pct < 0 ? 'down' : null,
        },
      ]
    }
    if (card.type === 'inventory') {
      return [
        { label: 'Inventory value', value: formatCurrency(d.inventory_value), emphasize: true },
        { label: 'Low stock', value: formatNumber(d.low_stock?.length || 0), emphasize: true },
        { label: 'Fast movers', value: formatNumber(d.fast_movers?.length || 0) },
      ]
    }
    if (card.type === 'hr') {
      return [
        { label: 'Attendance', value: formatPercent(d.attendance_pct), emphasize: true },
        { label: 'Employees', value: formatNumber(d.employee_count), emphasize: true },
        { label: 'Overtime (min)', value: formatNumber(d.overtime_minutes_total) },
      ]
    }
    if (card.type === 'customers') {
      return [
        { label: 'Customers', value: formatNumber(d.total_customers), emphasize: true },
        {
          label: 'Retention',
          value: d.retention_rate != null ? formatPercent(d.retention_rate * 100) : '—',
          emphasize: true,
        },
        { label: 'VIP', value: formatNumber(d.vip_count) },
      ]
    }
    if (card.type === 'forecast') {
      return [
        {
          label: 'Predicted total',
          value: formatCurrency(d.predicted_total_revenue),
          emphasize: true,
        },
        { label: 'Horizon', value: String(d.horizon || '—') },
        { label: 'Baseline / day', value: formatCurrency(d.baseline_daily_revenue) },
      ]
    }
    if (card.type === 'menu') {
      return [
        { label: 'Items tracked', value: formatNumber(d.total_items_tracked), emphasize: true },
        {
          label: 'Top seller',
          value: d.best_sellers_qty?.[0]?.name || '—',
        },
      ]
    }
    return Object.entries(d)
      .filter(([, v]) => typeof v !== 'object')
      .slice(0, 4)
      .map(([k, v]) => ({ label: k.replace(/_/g, ' '), value: String(v) }))
  }, [card])

  const accent = CARD_ACCENT[card.type] || CARD_ACCENT.overview

  return (
    <div
      className={`overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950/80 animate-in`}
    >
      <div className={`bg-gradient-to-br ${accent} px-4 pb-1 pt-4`}>
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] opacity-90">
            {card.type}
          </p>
          {card.period ? (
            <span className="rounded-md bg-white/70 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:bg-zinc-900/70 dark:text-zinc-300">
              {card.period}
            </span>
          ) : null}
        </div>
        <p className="mt-1 text-base font-semibold text-slate-900 dark:text-white">{card.title}</p>
      </div>
      {metrics.length ? (
        <div className="grid grid-cols-2 gap-px bg-slate-100 dark:bg-zinc-800/80">
          {metrics.map((m) => (
            <div
              key={m.label}
              className={`bg-white px-4 py-3 dark:bg-zinc-950 ${m.emphasize ? 'sm:col-span-1' : ''}`}
            >
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
                {m.label}
              </p>
              <p
                className={`mt-1 flex items-center gap-1 text-sm font-semibold tabular-nums text-slate-900 dark:text-white ${
                  m.emphasize ? 'text-lg' : ''
                }`}
              >
                {m.tone === 'up' ? <TrendingUp className="h-3.5 w-3.5 text-emerald-500" /> : null}
                {m.tone === 'down' ? <TrendingDown className="h-3.5 w-3.5 text-rose-500" /> : null}
                {m.value}
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function AssistantTyping() {
  return (
    <div className="flex items-end gap-3 animate-in">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
        <Bot className="h-4 w-4" />
      </div>
      <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:0ms]" />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
          <span className="ml-2 text-xs text-slate-500">Querying live BI…</span>
        </div>
      </div>
    </div>
  )
}

export function AiAssistantPage() {
  const { restaurant, branch } = useOrg()
  const toast = useToast()
  const scrollRef = useRef(null)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'I read live sales, inventory, workforce, and customer data from PostgreSQL. Ask in plain language — try a prompt below or type your own.',
      welcome: true,
    },
  ])

  const askMutation = useMutation({
    mutationFn: (question) =>
      askAssistant({
        question,
        restaurant_id: restaurant?.id,
        branch_id: branch?.id,
      }),
    onSuccess: (res) => {
      const data = asData(res)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.answer_summary || 'Here are the relevant insights.',
          period: data.period,
          cards: data.cards || [],
        },
      ])
    },
    onError: (err) => toast.error(err.message),
  })

  const conversationStarted = messages.some((m) => m.role === 'user')

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, askMutation.isPending])

  const ask = (raw) => {
    const q = String(raw || '').trim()
    if (!q || askMutation.isPending || !restaurant?.id) return
    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setInput('')
    askMutation.mutate(q)
  }

  const send = () => ask(input)

  return (
    <div className="space-y-5 animate-in">
      <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 text-white dark:border-zinc-800">
        <div
          className="pointer-events-none absolute inset-0 opacity-80"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 10% 0%, rgba(16,185,129,0.22), transparent 55%), radial-gradient(ellipse 60% 50% at 90% 20%, rgba(14,165,233,0.18), transparent 50%), linear-gradient(180deg, #0a0a0a 0%, #111113 100%)',
          }}
        />
        <div className="relative flex flex-wrap items-end justify-between gap-4 px-6 py-6 sm:px-8 sm:py-7">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-emerald-300/90">
              <Sparkles className="h-3.5 w-3.5" />
              Intelligence
            </div>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">AI Assistant</h1>
            <p className="mt-2 max-w-xl text-sm text-zinc-400 sm:text-base">
              Natural-language questions over live restaurant BI — sales, stock, staff, and forecasts.
            </p>
          </div>
          <div className="flex flex-col items-start gap-1 sm:items-end">
            <span className="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300 ring-1 ring-emerald-500/30">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              LIVE BI · POSTGRESQL
            </span>
            <p className="text-xs text-zinc-500">
              {restaurant?.name || 'Select a restaurant'}
              {branch ? ` · ${branch.name}` : ''}
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="flex min-h-[620px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-5 py-6 sm:px-7">
            {!conversationStarted ? (
              <div className="flex min-h-[280px] flex-col items-center justify-center px-4 text-center animate-in">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <Bot className="h-7 w-7" />
                </div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                  Ask anything about the business
                </h2>
                <p className="mt-2 max-w-md text-sm text-slate-500">
                  {messages[0]?.text}
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {ASSISTANT_PROMPTS.map(({ label, prompt, icon: Icon }) => (
                    <button
                      key={prompt}
                      type="button"
                      disabled={!restaurant?.id || askMutation.isPending}
                      onClick={() => ask(prompt)}
                      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-800 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-emerald-700 dark:hover:bg-emerald-950/40 dark:hover:text-emerald-200"
                    >
                      <Icon className="h-3.5 w-3.5 opacity-70" />
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => {
                if (msg.welcome && conversationStarted) return null
                const isUser = msg.role === 'user'
                return (
                  <div
                    key={i}
                    className={`flex gap-3 animate-in ${isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    {!isUser ? (
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                        <Bot className="h-4 w-4" />
                      </div>
                    ) : null}
                    <div
                      className={`max-w-[min(100%,42rem)] ${
                        isUser
                          ? 'rounded-2xl rounded-br-md bg-blue-600 px-4 py-3 text-sm text-white shadow-sm'
                          : 'min-w-0 flex-1 space-y-3'
                      }`}
                    >
                      {isUser ? (
                        <p>{msg.text}</p>
                      ) : (
                        <>
                          <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-800 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100">
                            {msg.period ? (
                              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
                                Period · {msg.period}
                              </p>
                            ) : null}
                            <p>{msg.text}</p>
                          </div>
                          {msg.cards?.length ? (
                            <div className="grid gap-3 sm:grid-cols-2">
                              {msg.cards.map((card, j) => (
                                <RecommendationCard key={`${i}-${j}`} card={card} />
                              ))}
                            </div>
                          ) : null}
                        </>
                      )}
                    </div>
                  </div>
                )
              })
            )}
            {askMutation.isPending ? <AssistantTyping /> : null}
          </div>

          <div className="border-t border-slate-200 bg-slate-50/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/50 sm:p-5">
            <div className="flex gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-emerald-400 focus-within:ring-2 focus-within:ring-emerald-500/20 dark:border-zinc-700 dark:bg-zinc-950">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
                placeholder={
                  restaurant?.id
                    ? 'Ask about revenue, stock, staff, customers…'
                    : 'Select a restaurant to start'
                }
                className="min-h-11 flex-1 bg-transparent px-3 text-sm outline-none placeholder:text-slate-400 dark:text-white"
                disabled={!restaurant?.id}
              />
              <Button
                onClick={send}
                disabled={!input.trim() || askMutation.isPending || !restaurant?.id}
                className="!rounded-xl"
              >
                <Send className="h-4 w-4" />
                Ask
              </Button>
            </div>
            <p className="mt-2 text-center text-[11px] text-slate-400">
              Answers use keyword routing against live aggregations — not a generative LLM.
            </p>
          </div>
        </div>

        <aside className="flex flex-col gap-4">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Suggested</h2>
            <p className="mt-1 text-xs text-slate-500">One click runs the query.</p>
            <ul className="mt-4 space-y-2">
              {ASSISTANT_PROMPTS.map(({ label, prompt, icon: Icon }) => (
                <li key={prompt}>
                  <button
                    type="button"
                    disabled={!restaurant?.id || askMutation.isPending}
                    className="group flex w-full items-start gap-3 rounded-2xl border border-transparent bg-slate-50 px-3 py-3 text-left transition hover:border-slate-200 hover:bg-white hover:shadow-sm disabled:opacity-50 dark:bg-zinc-900 dark:hover:border-zinc-700 dark:hover:bg-zinc-900"
                    onClick={() => ask(prompt)}
                  >
                    <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white text-slate-500 shadow-sm ring-1 ring-slate-200/80 group-hover:text-emerald-600 dark:bg-zinc-950 dark:ring-zinc-800 dark:group-hover:text-emerald-400">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span>
                      <span className="block text-sm font-medium text-slate-800 dark:text-zinc-100">
                        {label}
                      </span>
                      <span className="mt-0.5 block text-xs leading-snug text-slate-500">
                        {prompt}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-3xl border border-dashed border-slate-200 px-5 py-4 text-xs leading-relaxed text-slate-500 dark:border-zinc-800 dark:text-zinc-400">
            Tip: include a period — <span className="text-slate-700 dark:text-zinc-200">this month</span>,{' '}
            <span className="text-slate-700 dark:text-zinc-200">this week</span>, or{' '}
            <span className="text-slate-700 dark:text-zinc-200">today</span> — for accurate windows.
          </div>
        </aside>
      </div>
    </div>
  )
}
