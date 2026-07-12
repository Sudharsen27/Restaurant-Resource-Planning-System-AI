import { formatDate, formatModelName, formatPercent } from '../../utils/format'

export default function ModelVersionsTable({ versions }) {
  if (!versions?.length) {
    return <p className="py-8 text-center text-sm text-slate-500">No model versions recorded</p>
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
            <th className="pb-3 pr-4 font-medium">R²</th>
            <th className="pb-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {versions.map((v) => {
            const version = v.version ?? v.version_label
            const modelName = v.modelName ?? v.model_name
            const trainedAt = v.trainedAt ?? v.training_date
            const datasetSize = v.datasetSize ?? v.dataset_size
            const isProduction = v.isProduction ?? v.is_production

            return (
              <tr
                key={v.id}
                className={`border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50 ${
                  isProduction ? 'bg-emerald-50/40 dark:bg-emerald-950/15' : ''
                }`}
              >
                <td className="py-3.5 pr-4 font-bold text-slate-900 dark:text-white">{version}</td>
                <td className="py-3.5 pr-4" title={modelName}>
                  {formatModelName(modelName)}
                </td>
                <td className="whitespace-nowrap py-3.5 pr-4 text-slate-600 dark:text-slate-400">
                  {formatDate(trainedAt)}
                </td>
                <td className="py-3.5 pr-4">{datasetSize?.toLocaleString('en-IN')}</td>
                <td className="py-3.5 pr-4 font-medium text-blue-600 dark:text-blue-400">
                  {formatPercent(v.accuracy)}
                </td>
                <td className="py-3.5 pr-4">{v.mae?.toFixed(4)}</td>
                <td className="py-3.5 pr-4">{v.rmse?.toFixed(4)}</td>
                <td className="py-3.5 pr-4">{v.r2?.toFixed(4)}</td>
                <td className="py-3.5">
                  {isProduction ? (
                    <span className="inline-flex shrink-0 whitespace-nowrap rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                      Production
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">Archived</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
