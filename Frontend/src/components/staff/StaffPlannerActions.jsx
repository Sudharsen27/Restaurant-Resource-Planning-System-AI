import { Download, Loader2, Printer, RefreshCw, Sparkles } from 'lucide-react'

export default function StaffPlannerActions({
  customers,
  onCustomersChange,
  onGenerate,
  onRefresh,
  onExport,
  onPrint,
  loading,
  disabled,
}) {
  return (
    <div className="staff-planner-actions flex flex-col gap-4 rounded-xl border border-stone-200 bg-white p-5 shadow-[0_1px_2px_rgba(28,35,30,0.04)] dark:border-white/10 dark:bg-[#1b2520] lg:flex-row lg:items-end lg:justify-between">
      <label className="flex-1 lg:max-w-xs">
        <span className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Forecasted Customers
        </span>
        <input
          type="number"
          min={1}
          value={customers}
          onChange={(e) => onCustomersChange(e.target.value)}
          className="w-full rounded-lg border border-stone-200 bg-white px-3 py-2.5 text-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-white/10 dark:bg-[#1b2520]"
          placeholder="e.g. 120"
        />
      </label>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onGenerate}
          disabled={loading || disabled}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-950/15 hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          Generate Staff Plan
        </button>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
        <button
          type="button"
          onClick={onExport}
          disabled={disabled || loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
        <button
          type="button"
          onClick={onPrint}
          disabled={disabled || loading}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900"
        >
          <Printer className="h-4 w-4" />
          Print
        </button>
      </div>
    </div>
  )
}
