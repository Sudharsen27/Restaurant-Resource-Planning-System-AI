import { Calendar, History, ShoppingBag, Sliders, Thermometer } from 'lucide-react'

function FieldLabel({ children, hint, error }) {
  return (
    <span className="mb-1.5 block">
      <span className="text-xs font-medium text-slate-600 dark:text-slate-400">{children}</span>
      {hint && !error && <span className="mt-0.5 block text-[10px] text-slate-400">{hint}</span>}
      {error && <span className="mt-0.5 block text-[10px] text-rose-500">{error}</span>}
    </span>
  )
}

function TextInput({ error, className = '', ...props }) {
  return (
    <input
      {...props}
      className={`w-full rounded-lg border bg-white px-3 py-2 text-sm transition focus:outline-none focus:ring-2 dark:bg-slate-800 dark:text-white ${
        error
          ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20'
          : 'border-slate-200 focus:border-blue-500 focus:ring-blue-500/20 dark:border-slate-700'
      } ${className}`}
    />
  )
}

function Toggle({ checked, onChange, label, description }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800/50">
      <div>
        <p className="text-sm font-medium text-slate-900 dark:text-white">{label}</p>
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${
          checked ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-600'
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
      <span className="sr-only">{checked ? 'Yes' : 'No'}</span>
    </label>
  )
}

function Section({ icon: Icon, title, children }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
        <Icon className="h-4 w-4 text-blue-600" />
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
          {title}
        </h4>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">{children}</div>
    </div>
  )
}

export default function ForecastForm({ form, onChange, onSubmit, submitting, errors = {} }) {
  const set = (key, value) => onChange((prev) => ({ ...prev, [key]: value }))

  return (
    <form onSubmit={onSubmit} className="space-y-6" noValidate>
      <Section icon={Calendar} title="Schedule">
        <label className="sm:col-span-1">
          <FieldLabel error={errors.date}>Forecast Date</FieldLabel>
          <TextInput
            type="date"
            required
            value={form.date}
            error={errors.date}
            onChange={(e) => set('date', e.target.value)}
          />
        </label>
        <label className="sm:col-span-1">
          <FieldLabel error={errors.hour}>Forecast Hour</FieldLabel>
          <select
            value={form.hour}
            onChange={(e) => set('hour', Number(e.target.value))}
            className={`w-full rounded-lg border bg-white px-3 py-2 text-sm dark:bg-slate-800 ${
              errors.hour ? 'border-rose-400' : 'border-slate-200 dark:border-slate-700'
            }`}
          >
            {Array.from({ length: 24 }, (_, h) => (
              <option key={h} value={h}>
                {String(h).padStart(2, '0')}:00
              </option>
            ))}
          </select>
        </label>
      </Section>

      <Section icon={Thermometer} title="Weather">
        <label>
          <FieldLabel error={errors.temperature}>Temperature (°C)</FieldLabel>
          <TextInput
            type="number"
            step="0.1"
            required
            value={form.temperature}
            error={errors.temperature}
            onChange={(e) => set('temperature', e.target.value)}
          />
        </label>
        <label>
          <FieldLabel error={errors.rainfall}>Rainfall (mm)</FieldLabel>
          <TextInput
            type="number"
            min={0}
            step="0.1"
            required
            value={form.rainfall}
            error={errors.rainfall}
            onChange={(e) => set('rainfall', e.target.value)}
          />
        </label>
      </Section>

      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
          <Calendar className="h-4 w-4 text-blue-600" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Events
          </h4>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Toggle
            label="Promotion"
            description={form.promotion ? 'Yes' : 'No'}
            checked={form.promotion}
            onChange={(v) => set('promotion', v)}
          />
          <Toggle
            label="Holiday"
            description={form.is_holiday ? 'Yes' : 'No'}
            checked={form.is_holiday}
            onChange={(v) => set('is_holiday', v)}
          />
        </div>
      </div>

      <Section icon={History} title="Historical Demand">
        <label>
          <FieldLabel error={errors.previous_hour_customers}>Previous Hour Customers</FieldLabel>
          <TextInput
            type="number"
            min={0}
            required
            value={form.previous_hour_customers}
            error={errors.previous_hour_customers}
            onChange={(e) => set('previous_hour_customers', e.target.value)}
          />
        </label>
        <label>
          <FieldLabel error={errors.previous_day_customers}>Previous Day Customers</FieldLabel>
          <TextInput
            type="number"
            min={0}
            required
            value={form.previous_day_customers}
            error={errors.previous_day_customers}
            onChange={(e) => set('previous_day_customers', e.target.value)}
          />
        </label>
      </Section>

      <Section icon={ShoppingBag} title="Order Channels">
        <label>
          <FieldLabel error={errors.walk_in_customers}>Walk-in Customers</FieldLabel>
          <TextInput
            type="number"
            min={0}
            required
            value={form.walk_in_customers}
            error={errors.walk_in_customers}
            onChange={(e) => set('walk_in_customers', e.target.value)}
          />
        </label>
        <label>
          <FieldLabel error={errors.online_reservations}>Online Reservations</FieldLabel>
          <TextInput
            type="number"
            min={0}
            required
            value={form.online_reservations}
            error={errors.online_reservations}
            onChange={(e) => set('online_reservations', e.target.value)}
          />
        </label>
        <label>
          <FieldLabel error={errors.takeaway_orders}>Takeaway Orders</FieldLabel>
          <TextInput
            type="number"
            min={0}
            required
            value={form.takeaway_orders}
            error={errors.takeaway_orders}
            onChange={(e) => set('takeaway_orders', e.target.value)}
          />
        </label>
        <label>
          <FieldLabel error={errors.delivery_orders}>Delivery Orders</FieldLabel>
          <TextInput
            type="number"
            min={0}
            required
            value={form.delivery_orders}
            error={errors.delivery_orders}
            onChange={(e) => set('delivery_orders', e.target.value)}
          />
        </label>
      </Section>

      <Section icon={Sliders} title="Operations">
        <label className="sm:col-span-2">
          <FieldLabel
            hint={`${Math.round(Number(form.kitchen_load) * 100)}%`}
            error={errors.kitchen_load}
          >
            Kitchen Load
          </FieldLabel>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={form.kitchen_load}
            onChange={(e) => set('kitchen_load', Number(e.target.value))}
            className="w-full accent-blue-600"
          />
        </label>
        <label className="sm:col-span-2">
          <FieldLabel
            hint={`${Math.round(Number(form.table_utilization) * 100)}%`}
            error={errors.table_utilization}
          >
            Table Utilization
          </FieldLabel>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={form.table_utilization}
            onChange={(e) => set('table_utilization', Number(e.target.value))}
            className="w-full accent-blue-600"
          />
        </label>
        <label>
          <FieldLabel error={errors.supplier_delay_days}>Supplier Delay Days</FieldLabel>
          <TextInput
            type="number"
            min={0}
            step={0.5}
            required
            value={form.supplier_delay_days}
            error={errors.supplier_delay_days}
            onChange={(e) => set('supplier_delay_days', e.target.value)}
          />
        </label>
      </Section>

      <button
        type="submit"
        disabled={submitting}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:from-blue-700 hover:to-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Predicting…
          </>
        ) : (
          'Predict'
        )}
      </button>
    </form>
  )
}
