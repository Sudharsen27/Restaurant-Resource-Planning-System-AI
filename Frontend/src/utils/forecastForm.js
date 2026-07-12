export function createForecastFormDefaults() {
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
  }
}

/** @deprecated Prefer createForecastFormDefaults() */
export const FORECAST_FORM_DEFAULTS = createForecastFormDefaults

export function buildPredictPayload(form) {
  const date = new Date(`${form.date}T12:00:00`)
  return {
    date: form.date,
    hour: Number(form.hour),
    temperature: Number(form.temperature),
    rainfall: Number(form.rainfall) || 0,
    promotion: Boolean(form.promotion),
    is_holiday: Boolean(form.is_holiday),
    previous_hour_customers: Number(form.previous_hour_customers),
    previous_day_customers: Number(form.previous_day_customers),
    walk_in_customers: Number(form.walk_in_customers),
    online_reservations: Number(form.online_reservations),
    takeaway_orders: Number(form.takeaway_orders),
    delivery_orders: Number(form.delivery_orders),
    kitchen_load: Number(form.kitchen_load),
    table_utilization: Number(form.table_utilization),
    supplier_delay_days: Number(form.supplier_delay_days) || 0,
    is_weekend: [0, 6].includes(date.getDay()),
  }
}

export function validateForecastForm(form) {
  const errors = {}

  if (!form.date) {
    errors.date = 'Forecast date is required'
  } else if (Number.isNaN(Date.parse(form.date))) {
    errors.date = 'Enter a valid date'
  }

  const hour = Number(form.hour)
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) {
    errors.hour = 'Hour must be between 0 and 23'
  }

  if (form.temperature === '' || form.temperature == null || Number.isNaN(Number(form.temperature))) {
    errors.temperature = 'Temperature is required'
  }

  if (Number(form.rainfall) < 0 || Number.isNaN(Number(form.rainfall))) {
    errors.rainfall = 'Rainfall must be 0 or greater'
  }

  const nonNegInt = [
    ['previous_hour_customers', 'Previous hour customers'],
    ['previous_day_customers', 'Previous day customers'],
    ['walk_in_customers', 'Walk-in customers'],
    ['online_reservations', 'Online reservations'],
    ['takeaway_orders', 'Takeaway orders'],
    ['delivery_orders', 'Delivery orders'],
  ]
  for (const [key, label] of nonNegInt) {
    const n = Number(form[key])
    if (!Number.isFinite(n) || n < 0 || !Number.isInteger(n)) {
      errors[key] = `${label} must be a whole number ≥ 0`
    }
  }

  const kitchen = Number(form.kitchen_load)
  if (!Number.isFinite(kitchen) || kitchen < 0 || kitchen > 1) {
    errors.kitchen_load = 'Kitchen load must be between 0 and 1'
  }

  const tables = Number(form.table_utilization)
  if (!Number.isFinite(tables) || tables < 0 || tables > 1) {
    errors.table_utilization = 'Table utilization must be between 0 and 1'
  }

  if (Number(form.supplier_delay_days) < 0 || Number.isNaN(Number(form.supplier_delay_days))) {
    errors.supplier_delay_days = 'Supplier delay must be 0 or greater'
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  }
}

export function mapLatestToResult(saved) {
  if (!saved) return null
  return {
    prediction_id: saved.prediction_id,
    predicted_customers: saved.predicted_customers,
    confidence: saved.confidence,
    model_version: saved.model_version,
    created_at: saved.created_at,
    date: saved.date,
    hour: saved.hour,
  }
}

export function payloadToForm(payload, fallback = createForecastFormDefaults()) {
  if (!payload) return { ...fallback }
  return {
    ...fallback,
    date: payload.date ?? fallback.date,
    hour: payload.hour ?? fallback.hour,
    temperature: payload.temperature ?? fallback.temperature,
    rainfall: payload.rainfall ?? fallback.rainfall,
    promotion: payload.promotion ?? fallback.promotion,
    is_holiday: payload.is_holiday ?? fallback.is_holiday,
    previous_hour_customers:
      payload.previous_hour_customers ?? fallback.previous_hour_customers,
    previous_day_customers:
      payload.previous_day_customers ?? fallback.previous_day_customers,
    walk_in_customers: payload.walk_in_customers ?? fallback.walk_in_customers,
    online_reservations: payload.online_reservations ?? fallback.online_reservations,
    takeaway_orders: payload.takeaway_orders ?? fallback.takeaway_orders,
    delivery_orders: payload.delivery_orders ?? fallback.delivery_orders,
    kitchen_load: payload.kitchen_load ?? fallback.kitchen_load,
    table_utilization: payload.table_utilization ?? fallback.table_utilization,
    supplier_delay_days: payload.supplier_delay_days ?? fallback.supplier_delay_days,
  }
}

export function formatPredictionTimestamp(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Compact two-line-friendly stamp for narrow metric cards. */
export function formatPredictionTimestampParts(iso) {
  if (!iso) return { date: null, time: null, full: null }
  const d = new Date(iso)
  const date = d.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
  const time = d.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  })
  return { date, time, full: `${date} · ${time}` }
}

export function getConfidenceLabel(confidence) {
  if (confidence >= 90) return { label: 'Very High', color: 'text-emerald-600' }
  if (confidence >= 75) return { label: 'High', color: 'text-blue-600' }
  if (confidence >= 60) return { label: 'Moderate', color: 'text-amber-600' }
  return { label: 'Low', color: 'text-red-600' }
}

export const TIMELINE_HOURS = Array.from({ length: 15 }, (_, i) => i + 8)

export function formatHourLabel(hour) {
  const h = Number(hour)
  if (h === 0) return '12 AM'
  if (h < 12) return `${h} AM`
  if (h === 12) return '12 PM'
  return `${h - 12} PM`
}
