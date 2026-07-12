import { formatCurrency, formatNumber } from '../../utils/format'

export default function RecentStaffPlansTable({ rows }) {
  if (!rows.length) {
    return (
      <p className="py-6 text-center text-sm text-slate-500">
        No saved staff plans yet. Generate a plan to persist it via the API.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500 dark:border-slate-700">
            <th className="pb-3 pr-4 font-medium">Date</th>
            <th className="pb-3 pr-4 font-medium">Forecast</th>
            <th className="pb-3 pr-4 font-medium">Total Staff</th>
            <th className="pb-3 pr-4 font-medium">Staff Cost</th>
            <th className="pb-3 font-medium">Created Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id ?? row.created_at}
              className="border-b border-slate-100 dark:border-slate-800"
            >
              <td className="py-3 pr-4 text-slate-900 dark:text-white">{row.date}</td>
              <td className="py-3 pr-4 font-medium">{formatNumber(row.forecast)}</td>
              <td className="py-3 pr-4">{formatNumber(row.totalStaff)}</td>
              <td className="py-3 pr-4 font-medium text-emerald-600 dark:text-emerald-400">
                {formatCurrency(row.staffCost)}
              </td>
              <td className="py-3 text-slate-500">{row.createdTime}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
