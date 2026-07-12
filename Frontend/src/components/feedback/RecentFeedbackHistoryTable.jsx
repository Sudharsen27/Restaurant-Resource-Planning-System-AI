import { formatDateTime, formatNumber, formatPercent } from '../../utils/format'

export default function RecentFeedbackHistoryTable({ rows }) {
  if (!rows.length) {
    return (
      <p className="py-8 text-center text-sm text-slate-500">
        No feedback submitted yet. Submit your first correction above.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500 dark:border-slate-700">
            <th className="pb-3 pr-4 font-medium">Prediction ID</th>
            <th className="pb-3 pr-4 font-medium">Predicted</th>
            <th className="pb-3 pr-4 font-medium">Actual</th>
            <th className="pb-3 pr-4 font-medium">Error</th>
            <th className="pb-3 pr-4 font-medium">Comments</th>
            <th className="pb-3 font-medium">Created Date</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.predictionId}
              className="border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-3.5 pr-4 font-mono text-xs font-medium text-slate-900 dark:text-white">
                #{row.predictionId}
              </td>
              <td className="py-3.5 pr-4 font-medium text-slate-900 dark:text-white">
                {formatNumber(row.predicted)}
              </td>
              <td className="py-3.5 pr-4 font-medium text-slate-900 dark:text-white">
                {formatNumber(row.actual)}
              </td>
              <td className="py-3.5 pr-4">
                <span
                  className={
                    row.error != null && row.error > 10
                      ? 'font-medium text-amber-600 dark:text-amber-400'
                      : 'font-medium text-emerald-600 dark:text-emerald-400'
                  }
                >
                  {formatPercent(row.error)}
                </span>
              </td>
              <td
                className="max-w-[200px] truncate py-3.5 pr-4 text-slate-600 dark:text-slate-400"
                title={row.comments || ''}
              >
                {row.comments || '—'}
              </td>
              <td className="whitespace-nowrap py-3.5 text-slate-500">
                {formatDateTime(row.createdDate)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
