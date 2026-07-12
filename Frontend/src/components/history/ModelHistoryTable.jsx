import { formatDateTime } from '../../utils/predictionHistory'
import { formatPercent } from '../../utils/format'

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

export default function ModelHistoryTable({ rows, sortKey, sortDir, onSort }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[900px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 dark:border-slate-700">
            <th className="pb-3 pr-4">
              <SortHeader label="Version" field="version" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Training Date" field="trainingDate" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Accuracy" field="accuracy" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="MAE" field="mae" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="RMSE" field="rmse" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="R²" field="r2" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3 pr-4">
              <SortHeader label="Dataset Size" field="datasetSize" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
            <th className="pb-3">
              <SortHeader label="Production Status" field="isProduction" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.version}
              className={`border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50 ${
                row.isProduction ? 'bg-emerald-50/40 dark:bg-emerald-950/15' : ''
              }`}
            >
              <td className="py-3.5 pr-4 font-bold text-slate-900 dark:text-white">{row.version}</td>
              <td className="whitespace-nowrap py-3.5 pr-4 text-slate-600 dark:text-slate-400">
                {formatDateTime(row.trainingDate)}
              </td>
              <td className="py-3.5 pr-4 font-medium text-emerald-600 dark:text-emerald-400">
                {row.accuracy != null ? formatPercent(row.accuracy) : '—'}
              </td>
              <td className="py-3.5 pr-4">{row.mae != null ? row.mae.toFixed(4) : '—'}</td>
              <td className="py-3.5 pr-4">{row.rmse != null ? row.rmse.toFixed(4) : '—'}</td>
              <td className="py-3.5 pr-4">{row.r2 != null ? row.r2.toFixed(4) : '—'}</td>
              <td className="py-3.5 pr-4">
                {row.datasetSize != null ? row.datasetSize.toLocaleString('en-IN') : '—'}
              </td>
              <td className="py-3.5">
                {row.isProduction ? (
                  <span className="inline-flex shrink-0 whitespace-nowrap rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                    Production
                  </span>
                ) : (
                  <span className="text-xs text-slate-400">Archived</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
