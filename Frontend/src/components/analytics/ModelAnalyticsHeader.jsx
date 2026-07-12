import { BarChart3 } from 'lucide-react'

export default function ModelAnalyticsHeader() {
  return (
    <div>
      <div className="flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600/10">
          <BarChart3 className="h-5 w-5 text-violet-600" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Model Analytics
        </h2>
      </div>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">
        Monitor production model performance, training history, and version comparisons.
      </p>
    </div>
  )
}
