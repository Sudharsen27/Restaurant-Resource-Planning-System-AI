import { Inbox } from 'lucide-react'

export default function EmptyState({ title = 'No data yet', description, action }) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl border border-dashed border-stone-300 bg-stone-50/60 px-6 py-16 text-center dark:border-white/15 dark:bg-white/[0.03]"
      role="status"
      aria-live="polite"
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-400/10">
        <Inbox className="h-7 w-7 text-emerald-700 dark:text-emerald-300" />
      </div>
      <h3 className="mb-1 text-base font-semibold text-stone-900 dark:text-white">{title}</h3>
      {description && (
        <p className="mb-4 max-w-sm text-sm text-stone-500 dark:text-stone-400">{description}</p>
      )}
      {action}
    </div>
  )
}
