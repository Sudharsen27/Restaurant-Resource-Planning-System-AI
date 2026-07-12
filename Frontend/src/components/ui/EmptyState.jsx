import { Inbox } from 'lucide-react'

export default function EmptyState({ title = 'No data yet', description, action }) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/50 px-6 py-16 text-center dark:border-slate-700 dark:bg-slate-900/30"
      role="status"
      aria-live="polite"
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 dark:bg-slate-800">
        <Inbox className="h-7 w-7 text-slate-400" />
      </div>
      <h3 className="mb-1 text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
      {description && (
        <p className="mb-4 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>
      )}
      {action}
    </div>
  )
}
