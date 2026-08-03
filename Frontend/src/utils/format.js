export const formatCurrency = (value, currency = 'INR') =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value ?? 0)

export const formatNumber = (value, decimals = 0) =>
  new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: decimals,
  }).format(value ?? 0)

export const formatPercent = (value, decimals = 1) =>
  value == null ? '—' : `${Number(value).toFixed(decimals)}%`

/** Human-readable ML model name for compact UI slots */
export const formatModelName = (name) => {
  if (!name) return '—'
  return name
    .replace(/Regressor$/, '')
    .replace(/Classifier$/, '')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .trim()
}

export const formatDate = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export const formatDateTime = (value) => {
  if (!value) return '—'
  return new Date(value).toLocaleString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const defaultForecastInput = () => {
  const now = new Date()
  return {
    date: now.toISOString().slice(0, 10),
    hour: now.getHours(),
    temperature: 28,
    rainfall: 0,
    promotion: false,
    is_holiday: false,
    previous_hour_customers: 45,
    previous_day_customers: 320,
    walk_in_customers: 30,
    online_reservations: 15,
    takeaway_orders: 20,
    delivery_orders: 25,
    kitchen_load: 0.6,
    table_utilization: 0.65,
    supplier_delay_days: 0,
    local_event: null,
    average_order_value: 450,
    is_weekend: [0, 6].includes(now.getDay()),
  }
}

export const AOV = 450

export const chartColors = {
  primary: '#059669',
  secondary: '#0f766e',
  success: '#34a853',
  warning: '#f59e0b',
  danger: '#ef4444',
  muted: '#a29d91',
  grid: '#e5e2da',
  gridDark: '#3f4a43',
}

export const getChartTheme = (dark) => ({
  grid: dark ? chartColors.gridDark : chartColors.grid,
  text: dark ? '#bdb9ae' : '#747067',
  tooltip: dark ? '#1b2520' : '#ffffff',
})
