import { formatDate, formatModelName, formatPercent } from '../../utils/format'

export default function TrainingHistoryTable({ rows }) {
  if (!rows.length) {
    return (
      <p className="py-8 text-center text-sm text-slate-500">
        No training history available yet.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[800px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500 dark:border-slate-700">
            <th className="pb-3 pr-4 font-medium">Version</th>
            <th className="pb-3 pr-4 font-medium">Model</th>
            <th className="pb-3 pr-4 font-medium">Trained</th>
            <th className="pb-3 pr-4 font-medium">Dataset</th>
            <th className="pb-3 pr-4 font-medium">Accuracy</th>
            <th className="pb-3 pr-4 font-medium">MAE</th>
            <th className="pb-3 pr-4 font-medium">RMSE</th>
            <th className="pb-3 font-medium">R²</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              className={`border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50 ${
                row.isProduction ? 'bg-emerald-50/40 dark:bg-emerald-950/15' : ''
              }`}
            >
              <td className="py-3.5 pr-4 font-bold text-slate-900 dark:text-white">
                {row.version}
              </td>
              <td className="py-3.5 pr-4 text-slate-700 dark:text-slate-300">
                {formatModelName(row.modelName)}
              </td>
              <td className="whitespace-nowrap py-3.5 pr-4 text-slate-600 dark:text-slate-400">
                {formatDate(row.trainedAt)}
              </td>
              <td className="py-3.5 pr-4">{row.datasetSize?.toLocaleString('en-IN')}</td>
              <td className="py-3.5 pr-4 font-medium text-emerald-600 dark:text-emerald-400">
                {formatPercent(row.accuracy)}
              </td>
              <td className="py-3.5 pr-4">{row.mae?.toFixed(4)}</td>
              <td className="py-3.5 pr-4">{row.rmse?.toFixed(4)}</td>
              <td className="py-3.5">{row.r2?.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
