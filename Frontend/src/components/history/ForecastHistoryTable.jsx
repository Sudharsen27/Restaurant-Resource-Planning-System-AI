import { formatDateTime, formatHour } from '../../utils/predictionHistory'
import { formatNumber, formatPercent } from '../../utils/format'

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

function StatusBadge({ status }) {
  const reviewed = status === 'Reviewed'
  return (
    <span
      className={`inline-flex shrink-0 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${
        reviewed
          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
          : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'
      }`}
    >
      {status}
    </span>
  )
}

export default function ForecastHistoryTable({ rows, sortKey, sortDir, onSort }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[960px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="pb-3 pr-4">
              <SortHeader label="Prediction ID" field="predictionId" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Forecast Date" field="forecastDate" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Forecast Hour" field="forecastHour" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Predicted Customers" field="predictedCustomers" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Confidence" field="confidence" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Model Version" field="modelVersion" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Created At" field="createdAt" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3">
              <SortHeader label="Status" field="status" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
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
              <td className="py-3.5 pr-4 text-slate-700 dark:text-slate-300">{row.forecastDate}</td>
              <td className="py-3.5 pr-4 text-slate-600 dark:text-slate-400">{formatHour(row.forecastHour)}</td>
              <td className="py-3.5 pr-4 font-semibold text-slate-900 dark:text-white">
                {formatNumber(row.predictedCustomers)}
              </td>
              <td className="py-3.5 pr-4 font-medium text-blue-600 dark:text-blue-400">
                {row.confidence != null ? formatPercent(row.confidence) : '—'}
              </td>
              <td className="py-3.5 pr-4">
                {row.modelVersion ? (
                  <span className="rounded-md bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">
                    {row.modelVersion}
                  </span>
                ) : (
                  '—'
                )}
              </td>
              <td className="whitespace-nowrap py-3.5 pr-4 text-slate-500">
                {formatDateTime(row.createdAt)}
              </td>
              <td className="py-3.5">
                <StatusBadge status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
