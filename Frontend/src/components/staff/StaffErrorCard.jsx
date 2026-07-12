import { AlertCircle } from 'lucide-react'

export default function StaffErrorCard({ title, message, onRetry }) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 dark:border-rose-900/50 dark:bg-rose-950/30">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600 dark:text-rose-400" />
        <div className="flex-1">
          <h3 className="font-semibold text-rose-900 dark:text-rose-100">{title}</h3>
          <p className="mt-1 text-sm text-rose-800 dark:text-rose-200">{message}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
