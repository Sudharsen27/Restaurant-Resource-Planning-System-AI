import { Link } from 'react-router-dom'
import Card from '../ui/Card'
import DataTable from '../tables/DataTable'
import Button from '../ui/Button'

/**
 * Generic ERP list page — expects live `rows` from parent (TanStack Query).
 * Prefer `headerActions` for create/edit CTAs; `ctaTo` remains for simple links.
 */
export default function EntityListPage({
  title,
  description,
  entity,
  columns,
  ctaLabel,
  ctaTo,
  headerActions,
  rows = [],
  loading = false,
  sourceLabel = 'Live data · PostgreSQL',
}) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{title}</h1>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
          <p className="mt-1 text-[11px] uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
            {sourceLabel}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {headerActions}
          {!headerActions && ctaTo && (
            <Link to={ctaTo}>
              <Button>{ctaLabel || 'Create'}</Button>
            </Link>
          )}
        </div>
      </div>
      <Card>
        <DataTable
          columns={columns}
          rows={rows}
          loading={loading}
          emptyTitle={`No ${title.toLowerCase()}`}
          emptyDescription="Create a record or adjust filters."
          onExport={() => {
            const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${entity}-export.json`
            a.click()
            URL.revokeObjectURL(url)
          }}
        />
      </Card>
    </div>
  )
}
