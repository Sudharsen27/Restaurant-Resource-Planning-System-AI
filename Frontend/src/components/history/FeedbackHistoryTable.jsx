import { formatDateTime, formatErrorPct } from '../../utils/predictionHistory'
import { formatNumber } from '../../utils/format'

function SortHeader({ label, field, sortKey, sortDir, onSort }) {
  const active = sortKey === field
  return (
    <button
      type="button"
      onClick={() => onSort(field)}
      className={`text-left text-xs font-semibold uppercase tracking-wider transition ${
        active ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
      }`}
    >
      {label}
      {active && <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>}
    </button>
  )
}

function ErrorCell({ value }) {
  if (value == null) return <span className="text-slate-400">—</span>
  const color =
    value > 20
      ? 'text-red-600 dark:text-red-400'
      : value > 10
        ? 'text-amber-600 dark:text-amber-400'
        : 'text-emerald-600 dark:text-emerald-400'
  return <span className={`font-medium ${color}`}>{formatErrorPct(value)}</span>
}

export default function FeedbackHistoryTable({ rows, sortKey, sortDir, onSort }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[880px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="pb-3 pr-4">
              <SortHeader label="Prediction ID" field="predictionId" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Predicted" field="predicted" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Actual" field="actual" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Error %" field="errorPct" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Comments" field="comments" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Submitted By" field="submittedBy" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3">
              <SortHeader label="Created At" field="createdAt" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.predictionId}
              className="border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-3.5 pr-4 font-mono text-xs font-medium">#{row.predictionId}</td>
              <td className="py-3.5 pr-4 font-semibold text-slate-900 dark:text-white">
                {formatNumber(row.predicted)}
              </td>
              <td className="py-3.5 pr-4 font-semibold text-slate-900 dark:text-white">
                {formatNumber(row.actual)}
              </td>
              <td className="py-3.5 pr-4">
                <ErrorCell value={row.errorPct} />
              </td>
              <td
                className="max-w-[200px] truncate py-3.5 pr-4 text-slate-600 dark:text-slate-400"
                title={row.comments || ''}
              >
                {row.comments || '—'}
              </td>
              <td className="py-3.5 pr-4 text-slate-600 dark:text-slate-400">
                {row.submittedBy || '—'}
              </td>
              <td className="whitespace-nowrap py-3.5 text-slate-500">
                {formatDateTime(row.createdAt)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
