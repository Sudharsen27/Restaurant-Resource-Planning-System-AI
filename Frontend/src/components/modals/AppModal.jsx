import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import Button from '../ui/Button'

/**
 * Responsive modal — centered card on desktop, bottom sheet on mobile.
 * Set hideFooter when children render their own action buttons.
 */
const SIZE_CLASS = {
  sm: 'sm:max-w-md',
  md: 'sm:max-w-lg',
  lg: 'sm:max-w-2xl',
  xl: 'sm:max-w-3xl',
}

export default function AppModal({
  open,
  title,
  description,
  children,
  onClose,
  onConfirm,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  busy = false,
  size = 'md',
  hideFooter = false,
}) {
  useEffect(() => {
    if (!open) return undefined
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.()
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      document.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center sm:p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/55 backdrop-blur-[1px]"
        aria-label="Close dialog"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="app-modal-title"
        className={`relative z-10 flex max-h-[92vh] w-full flex-col rounded-t-2xl border border-slate-200 bg-white shadow-2xl dark:border-zinc-700 dark:bg-zinc-950 sm:max-h-[88vh] sm:rounded-2xl ${SIZE_CLASS[size] || SIZE_CLASS.md}`}
      >
        <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-100 px-4 py-3 dark:border-zinc-800 sm:px-6 sm:py-4">
          <div className="min-w-0">
            {title && (
              <h2
                id="app-modal-title"
                className="text-base font-semibold tracking-tight text-slate-900 dark:text-white sm:text-lg"
              >
                {title}
              </h2>
            )}
            {description && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-zinc-400 sm:text-sm">{description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            aria-label="Close"
          >
            <span className="text-xl leading-none">×</span>
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 text-sm text-slate-700 dark:text-zinc-200 sm:px-6">
          {children}
        </div>

        {!hideFooter && (
          <div className="flex shrink-0 flex-col-reverse gap-2 border-t border-slate-100 px-4 py-3 dark:border-zinc-800 sm:flex-row sm:justify-end sm:px-6 sm:py-4">
            <Button variant="secondary" onClick={onClose} disabled={busy} className="w-full sm:w-auto">
              {cancelLabel}
            </Button>
            {onConfirm && (
              <Button
                variant={danger ? 'danger' : 'primary'}
                onClick={onConfirm}
                disabled={busy}
                className="w-full sm:w-auto"
              >
                {confirmLabel}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}
