import { useMemo, useState } from 'react'
import { Download, Search } from 'lucide-react'
import Button from '../ui/Button'
import EmptyState from '../ui/EmptyState'
import LoadingSpinner from '../ui/LoadingSpinner'

/**
 * Reusable data table — pagination, sort, search, export stub.
 * @param {{ columns: Array<{key:string,label:string,sortable?:boolean,render?:Function}>, rows: Array, loading?:boolean, emptyTitle?:string, onExport?:Function }} props
 */
export default function DataTable({
  columns = [],
  rows = [],
  loading = false,
  emptyTitle = 'No data',
  emptyDescription = 'Nothing to show yet.',
  pageSize = 8,
  onExport,
}) {
  const [query, setQuery] = useState('')
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const [page, setPage] = useState(1)
  const [visibleKeys, setVisibleKeys] = useState(() => columns.map((c) => c.key))

  const filtered = useMemo(() => {
    let data = [...rows]
    if (query.trim()) {
      const q = query.toLowerCase()
      data = data.filter((row) =>
        columns.some((col) => String(row[col.key] ?? '').toLowerCase().includes(q)),
      )
    }
    if (sortKey) {
      data.sort((a, b) => {
        const av = a[sortKey]
        const bv = b[sortKey]
        if (av === bv) return 0
        const cmp = av > bv ? 1 : -1
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return data
  }, [rows, query, sortKey, sortDir, columns])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const pageRows = filtered.slice((page - 1) * pageSize, page * pageSize)
  const visibleCols = columns.filter((c) => visibleKeys.includes(c.key))

  function toggleSort(key) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  if (loading) return <LoadingSpinner label="Loading table…" />

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setPage(1)
            }}
            placeholder="Filter rows…"
            className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <details className="relative">
          <summary className="cursor-pointer list-none rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-zinc-700">
            Columns
          </summary>
          <div className="absolute right-0 z-20 mt-1 w-48 rounded-xl border border-slate-200 bg-white p-2 shadow-lg dark:border-zinc-700 dark:bg-zinc-950">
            {columns.map((col) => (
              <label key={col.key} className="flex items-center gap-2 px-2 py-1 text-sm">
                <input
                  type="checkbox"
                  checked={visibleKeys.includes(col.key)}
                  onChange={(e) => {
                    setVisibleKeys((prev) =>
                      e.target.checked ? [...prev, col.key] : prev.filter((k) => k !== col.key),
                    )
                  }}
                />
                {col.label}
              </label>
            ))}
          </div>
        </details>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onExport?.(filtered)}
          disabled={!onExport}
        >
          <Download className="h-4 w-4" /> Export
        </Button>
      </div>

      {pageRows.length === 0 ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-zinc-800">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-zinc-800">
            <thead className="bg-slate-50 dark:bg-zinc-900/80">
              <tr>
                {visibleCols.map((col) => (
                  <th
                    key={col.key}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500"
                  >
                    {col.sortable !== false ? (
                      <button type="button" onClick={() => toggleSort(col.key)} className="hover:text-slate-800">
                        {col.label}
                        {sortKey === col.key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
                      </button>
                    ) : (
                      col.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white dark:divide-zinc-900 dark:bg-black/40">
              {pageRows.map((row, idx) => (
                <tr key={row.id || idx} className="hover:bg-slate-50/80 dark:hover:bg-zinc-900/50">
                  {visibleCols.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-slate-700 dark:text-zinc-300 ${
                        col.key === 'actions' ? 'text-right' : 'whitespace-nowrap'
                      }`}
                    >
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>
          {filtered.length} row{filtered.length === 1 ? '' : 's'} · page {page}/{totalPages}
        </span>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
