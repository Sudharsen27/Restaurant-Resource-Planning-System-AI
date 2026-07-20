import { Plus, Pencil, Trash2 } from 'lucide-react'
import Button from '../ui/Button'

export function StatusBadge({ status }) {
  const active = String(status || '').toLowerCase() === 'active'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
        active
          ? 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-400/30'
          : 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/10 dark:bg-zinc-800 dark:text-zinc-400'
      }`}
    >
      <span
        className={`mr-1.5 h-1.5 w-1.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-slate-400'}`}
      />
      {status || '—'}
    </span>
  )
}

export function CodeChip({ code }) {
  if (!code) return <span className="text-slate-400">—</span>
  return (
    <span className="inline-flex rounded-md bg-slate-100 px-2 py-0.5 font-mono text-xs font-medium text-slate-700 dark:bg-zinc-800 dark:text-zinc-300">
      {code}
    </span>
  )
}

export function RowActions({ onEdit, onDelete }) {
  return (
    <div className="flex items-center justify-end gap-1">
      <button
        type="button"
        onClick={onEdit}
        title="Edit"
        className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
      >
        <Pencil className="h-3.5 w-3.5" />
        <span className="sr-only">Edit</span>
      </button>
      <button
        type="button"
        onClick={onDelete}
        title="Delete"
        className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400"
      >
        <Trash2 className="h-3.5 w-3.5" />
        <span className="sr-only">Delete</span>
      </button>
    </div>
  )
}

export function AddEntityButton({ label = 'Add', onClick, disabled = false }) {
  return (
    <Button onClick={onClick} disabled={disabled}>
      <Plus className="h-4 w-4" />
      {label}
    </Button>
  )
}
