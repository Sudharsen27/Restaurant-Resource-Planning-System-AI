import { Download, Loader2, Printer, RefreshCw, Sparkles } from 'lucide-react'

export default function InventoryPlannerActions({
  customers,
  safetyRate,
  leadTime,
  onCustomersChange,
  onSafetyChange,
  onLeadTimeChange,
  onGenerate,
  onRefresh,
  onExport,
  onPrint,
  loading,
  disabled,
  errors = {},
}) {
  return (
    <div className="inventory-planner-actions rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/80">
      <div className="grid gap-4 lg:grid-cols-4 lg:items-end">
        <label>
          <span className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
            Forecasted Customers
          </span>
          <input
            type="number"
            min={1}
            value={customers}
            onChange={(e) => onCustomersChange(e.target.value)}
            className={`w-full rounded-lg border bg-white px-3 py-2.5 text-sm dark:bg-slate-800 ${
              errors.customers ? 'border-rose-400' : 'border-slate-200 dark:border-slate-700'
            }`}
          />
          {errors.customers && (
            <p className="mt-1 text-[11px] text-rose-500">{errors.customers}</p>
          )}
        </label>

        <label>
          <span className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
            Safety Stock Rate
          </span>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min={0}
              max={0.5}
              step={0.05}
              value={safetyRate}
              onChange={(e) => onSafetyChange(Number(e.target.value))}
              className="flex-1 accent-amber-500"
            />
            <span className="w-10 text-right text-sm font-medium">
              {(Number(safetyRate) * 100).toFixed(0)}%
            </span>
          </div>
        </label>

        <label>
          <span className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
            Supplier Lead Time (days)
          </span>
          <input
            type="number"
            min={0}
            step={0.5}
            value={leadTime}
            onChange={(e) => onLeadTimeChange(e.target.value)}
            className={`w-full rounded-lg border bg-white px-3 py-2.5 text-sm dark:bg-slate-800 ${
              errors.leadTime ? 'border-rose-400' : 'border-slate-200 dark:border-slate-700'
            }`}
          />
        </label>

        <div className="flex flex-wrap gap-2 lg:col-span-1 lg:justify-end">
          <button
            type="button"
            onClick={onGenerate}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 hover:from-blue-700 hover:to-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Generate Inventory Plan
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
        <button
          type="button"
          onClick={onExport}
          disabled={disabled || loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
        <button
          type="button"
          onClick={onPrint}
          disabled={disabled || loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <Printer className="h-4 w-4" />
          Print
        </button>
      </div>
    </div>
  )
}
