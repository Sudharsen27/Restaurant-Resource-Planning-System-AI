import { formatNumber, formatPercent } from '../../utils/format'
import { formatHourLabel } from '../../utils/forecastForm'

const SUMMARY_FIELDS = [
  { key: 'date', label: 'Date' },
  { key: 'hour', label: 'Hour', format: (v) => formatHourLabel(v) },
  { key: 'temperature', label: 'Temperature', format: (v) => `${v}°C` },
  { key: 'rainfall', label: 'Rainfall', format: (v) => `${v} mm` },
  { key: 'is_holiday', label: 'Holiday', format: (v) => (v ? 'Yes' : 'No') },
  { key: 'promotion', label: 'Promotion', format: (v) => (v ? 'Yes' : 'No') },
  { key: 'previous_hour_customers', label: 'Prev. Hour Customers', format: formatNumber },
  { key: 'previous_day_customers', label: 'Prev. Day Customers', format: formatNumber },
  { key: 'walk_in_customers', label: 'Walk-in', format: formatNumber },
  { key: 'online_reservations', label: 'Reservations', format: formatNumber },
  { key: 'takeaway_orders', label: 'Takeaway', format: formatNumber },
  { key: 'delivery_orders', label: 'Delivery', format: formatNumber },
  { key: 'kitchen_load', label: 'Kitchen Load', format: (v) => `${Math.round(v * 100)}%` },
  { key: 'table_utilization', label: 'Table Utilization', format: (v) => `${Math.round(v * 100)}%` },
  { key: 'supplier_delay_days', label: 'Supplier Delay', format: (v) => `${v} day(s)` },
]

export default function PredictionSummary({ form, result, payload }) {
  if (!result || !form) return null

  const channelTotal =
    Number(form.walk_in_customers) +
    Number(form.online_reservations) +
    Number(form.takeaway_orders) +
    Number(form.delivery_orders)

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h4 className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">Input Summary</h4>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          {SUMMARY_FIELDS.map(({ key, label, format }) => (
            <div key={key} className="contents">
              <dt className="text-slate-500">{label}</dt>
              <dd className="font-medium text-slate-900 dark:text-white">
                {format ? format(form[key]) : form[key]}
              </dd>
            </div>
          ))}
        </dl>
      </div>

      <div>
        <h4 className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">
          Prediction Insights
        </h4>
        <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-700 dark:bg-slate-800/50">
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">Predicted Customers</span>
            <span className="font-bold text-blue-600 dark:text-blue-400">
              {formatNumber(result.predicted_customers)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">Confidence Score</span>
            <span className="font-semibold">{formatPercent(result.confidence)}</span>
          </div>
          {result.model_version && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Model Version</span>
              <span className="font-semibold">{result.model_version}</span>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">Channel Signals Total</span>
            <span className="font-semibold">{formatNumber(channelTotal)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">vs Previous Hour</span>
            <span className="font-semibold">
              {result.predicted_customers > Number(form.previous_hour_customers) ? '+' : ''}
              {formatNumber(result.predicted_customers - Number(form.previous_hour_customers))}
            </span>
          </div>
          {payload?.is_weekend && (
            <p className="border-t border-slate-200 pt-3 text-xs text-amber-600 dark:border-slate-700 dark:text-amber-400">
              Weekend demand pattern applied automatically.
            </p>
          )}
          {result.prediction_id && (
            <p className="border-t border-slate-200 pt-3 text-xs text-slate-500 dark:border-slate-700">
              Use Prediction #{result.prediction_id} on the Feedback page to improve the model.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
