import { formatCurrency, formatNumber } from '../../utils/format'

function StatusBadge({ status }) {
  const staffed = status === 'Staffed'
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
        staffed
          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300'
          : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
      }`}
    >
      {status}
    </span>
  )
}

export default function StaffRecommendationTable({ rows, totalStaff, totalCost }) {
  if (!rows.length) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500 dark:border-slate-700">
            <th className="pb-3 pr-4 font-medium">Role</th>
            <th className="pb-3 pr-4 font-medium">Recommended Count</th>
            <th className="pb-3 pr-4 font-medium">Shift</th>
            <th className="pb-3 pr-4 font-medium text-right">Hourly Cost</th>
            <th className="pb-3 pr-4 font-medium text-right">Daily Cost</th>
            <th className="pb-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.role}
              className="border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-3.5 pr-4 font-medium text-slate-900 dark:text-white">
                {row.roleLabel}
              </td>
              <td className="py-3.5 pr-4">
                <span
                  className={`inline-flex h-7 min-w-[2rem] items-center justify-center rounded-lg px-2 font-semibold ${
                    row.count > 0
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300'
                      : 'bg-slate-100 text-slate-500 dark:bg-slate-800'
                  }`}
                >
                  {row.count}
                </span>
              </td>
              <td className="py-3.5 pr-4 text-slate-600 dark:text-slate-400">{row.shift}</td>
              <td className="py-3.5 pr-4 text-right font-medium text-slate-900 dark:text-white">
                {row.count > 0 ? formatCurrency(row.hourlyCost) : '—'}
              </td>
              <td className="py-3.5 pr-4 text-right font-medium text-slate-900 dark:text-white">
                {row.count > 0 ? formatCurrency(row.dailyCost) : '—'}
              </td>
              <td className="py-3.5">
                <StatusBadge status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t-2 border-slate-200 dark:border-slate-700">
            <td className="pt-4 pr-4 font-semibold text-slate-900 dark:text-white">Total</td>
            <td className="pt-4 pr-4 font-bold text-slate-900 dark:text-white">
              {formatNumber(totalStaff)}
            </td>
            <td className="pt-4 pr-4 text-xs text-slate-500">—</td>
            <td className="pt-4 pr-4" />
            <td className="pt-4 pr-4 text-right font-bold text-emerald-600 dark:text-emerald-400">
              {formatCurrency(totalCost)}
            </td>
            <td className="pt-4" />
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
