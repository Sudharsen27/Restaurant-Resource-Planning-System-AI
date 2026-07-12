import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

export default function HistoryPagination({ safePage, totalPages, start, end, total, onPageChange }) {
  if (total === 0) return null

  return (
    <div className="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
      <p className="text-xs text-slate-500">
        Page {safePage + 1} of {totalPages} · {start}–{end} of {total}
      </p>
      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled={safePage === 0}
          onClick={() => onPageChange(0)}
          className="rounded-lg border border-slate-200 p-2 disabled:opacity-40 dark:border-slate-700"
          aria-label="First page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </button>
        <button
          type="button"
          disabled={safePage === 0}
          onClick={() => onPageChange(safePage - 1)}
          className="rounded-lg border border-slate-200 p-2 disabled:opacity-40 dark:border-slate-700"
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="min-w-[4rem] text-center text-sm text-slate-600 dark:text-slate-400">
          {safePage + 1} / {totalPages}
        </span>
        <button
          type="button"
          disabled={safePage >= totalPages - 1}
          onClick={() => onPageChange(safePage + 1)}
          className="rounded-lg border border-slate-200 p-2 disabled:opacity-40 dark:border-slate-700"
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          disabled={safePage >= totalPages - 1}
          onClick={() => onPageChange(totalPages - 1)}
          className="rounded-lg border border-slate-200 p-2 disabled:opacity-40 dark:border-slate-700"
          aria-label="Last page"
        >
          <ChevronsRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
