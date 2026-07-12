import { History } from 'lucide-react'

export default function PredictionHistoryHeader() {
  return (
    <div>
      <div className="flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/10">
          <History className="h-5 w-5 text-indigo-600" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Prediction History
        </h2>
      </div>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">
        Browse forecast records, manager feedback, and model version snapshots.
      </p>
    </div>
  )
}
