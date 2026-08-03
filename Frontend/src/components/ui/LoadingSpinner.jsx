import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ label = 'Loading…', className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-12 ${className}`} role="status" aria-live="polite">
      <Loader2 className="h-8 w-8 animate-spin text-emerald-600 dark:text-emerald-400" aria-hidden />
      {label && <p className="text-sm text-stone-500 dark:text-stone-400">{label}</p>}
    </div>
  )
}
