import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LayoutGrid, ZoomIn, ZoomOut } from 'lucide-react'
import Button from '../components/ui/Button'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import { useOrg } from '../context/OrgContext'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/format'
import {
  connectPosSocket,
  fetchFloorPlan,
  mergeTables,
  splitTables,
  updateTablePosition,
} from '../services/orderService'

const STATUS_STYLE = {
  AVAILABLE: 'bg-emerald-500 border-emerald-700',
  OCCUPIED: 'bg-rose-500 border-rose-800',
  RESERVED: 'bg-amber-400 border-amber-700',
  CLEANING: 'bg-sky-400 border-sky-700',
  MAINTENANCE: 'bg-slate-400 border-slate-600',
}

export default function FloorPlanPage() {
  const { branch } = useOrg()
  const { success, error: toastError } = useToast()
  const queryClient = useQueryClient()
  const [zoom, setZoom] = useState(1)
  const [selected, setSelected] = useState([])
  const dragRef = useRef(null)

  const { data: tables = [], isLoading } = useQuery({
    queryKey: ['floor', branch?.id],
    enabled: !!branch?.id,
    refetchInterval: 10000,
    queryFn: async () => {
      const res = await fetchFloorPlan(branch.id)
      return res.data || []
    },
  })

  useEffect(() => {
    return connectPosSocket(() => queryClient.invalidateQueries({ queryKey: ['floor'] }))
  }, [queryClient])

  const moveMutation = useMutation({
    mutationFn: ({ id, pos_x, pos_y }) => updateTablePosition(id, pos_x, pos_y),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['floor'] }),
    onError: (e) => toastError(e.message),
  })

  const mergeMutation = useMutation({
    mutationFn: () => {
      if (selected.length < 2) throw new Error('Select primary + at least one secondary')
      const [primary, ...rest] = selected
      return mergeTables(primary, rest)
    },
    onSuccess: () => {
      success('Tables merged')
      setSelected([])
      queryClient.invalidateQueries({ queryKey: ['floor'] })
    },
    onError: (e) => toastError(e.message),
  })

  const splitMutation = useMutation({
    mutationFn: () => {
      if (selected.length !== 1) throw new Error('Select one primary table to split')
      return splitTables(selected[0])
    },
    onSuccess: () => {
      success('Tables split')
      setSelected([])
      queryClient.invalidateQueries({ queryKey: ['floor'] })
    },
    onError: (e) => toastError(e.message),
  })

  const toggleSelect = (id) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const onPointerDown = (e, table) => {
    e.preventDefault()
    const startX = e.clientX
    const startY = e.clientY
    const origX = table.pos_x || 0
    const origY = table.pos_y || 0
    dragRef.current = { id: table.id, startX, startY, origX, origY }

    const onMove = (ev) => {
      if (!dragRef.current || dragRef.current.id !== table.id) return
      const dx = (ev.clientX - dragRef.current.startX) / zoom
      const dy = (ev.clientY - dragRef.current.startY) / zoom
      const el = document.getElementById(`floor-table-${table.id}`)
      if (el) {
        el.style.left = `${Math.max(0, dragRef.current.origX + dx)}px`
        el.style.top = `${Math.max(0, dragRef.current.origY + dy)}px`
      }
    }
    const onUp = (ev) => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      if (!dragRef.current) return
      const dx = (ev.clientX - dragRef.current.startX) / zoom
      const dy = (ev.clientY - dragRef.current.startY) / zoom
      const moved = Math.abs(dx) + Math.abs(dy) > 4
      const pos_x = Math.round(Math.max(0, dragRef.current.origX + dx))
      const pos_y = Math.round(Math.max(0, dragRef.current.origY + dy))
      const id = dragRef.current.id
      dragRef.current = null
      if (moved) moveMutation.mutate({ id, pos_x, pos_y })
      else toggleSelect(id)
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  if (!branch) {
    return <EmptyState title="Select a branch" description="Floor plan is branch-scoped." />
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900 dark:text-white">
            <LayoutGrid className="h-7 w-7" /> Floor plan
          </h1>
          <p className="text-sm text-slate-500">{branch.name} · drag to position · click to select</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setZoom((z) => Math.min(z + 0.1, 1.6))}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="secondary" onClick={() => setZoom((z) => Math.max(z - 0.1, 0.6))}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button disabled={selected.length < 2} onClick={() => mergeMutation.mutate()}>
            Merge
          </Button>
          <Button variant="secondary" disabled={selected.length !== 1} onClick={() => splitMutation.mutate()}>
            Split
          </Button>
          <Link to="/pos">
            <Button variant="ghost">POS</Button>
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 text-xs">
        {Object.entries(STATUS_STYLE).map(([status, cls]) => (
          <span key={status} className="inline-flex items-center gap-1.5">
            <span className={`h-3 w-3 rounded-full border ${cls}`} />
            {status}
          </span>
        ))}
      </div>

      {isLoading ? (
        <LoadingSpinner label="Loading floor…" />
      ) : tables.length === 0 ? (
        <EmptyState title="No tables" description="Create tables under Master data → Tables." />
      ) : (
        <div className="overflow-auto rounded-2xl border border-slate-200 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] bg-[size:16px_16px] dark:border-slate-700 dark:bg-[radial-gradient(#334155_1px,transparent_1px)]">
          <div
            className="relative min-h-[520px] min-w-[720px] origin-top-left p-4"
            style={{ transform: `scale(${zoom})` }}
          >
            {tables.map((t, idx) => {
              const x = t.pos_x || (idx % 6) * 110 + 20
              const y = t.pos_y || Math.floor(idx / 6) * 110 + 20
              const selectedRing = selected.includes(t.id) ? 'ring-4 ring-blue-400' : ''
              return (
                <button
                  key={t.id}
                  id={`floor-table-${t.id}`}
                  type="button"
                  onPointerDown={(e) => onPointerDown(e, { ...t, pos_x: x, pos_y: y })}
                  className={`absolute flex h-24 w-24 cursor-grab flex-col items-center justify-center rounded-2xl border-2 text-white shadow-md active:cursor-grabbing ${STATUS_STYLE[t.status] || STATUS_STYLE.AVAILABLE} ${selectedRing}`}
                  style={{ left: x, top: y }}
                >
                  <span className="text-lg font-bold">{t.table_number}</span>
                  <span className="text-[10px] opacity-90">{t.capacity} seats</span>
                  {t.guest_count != null && (
                    <span className="text-[10px]">{t.guest_count} guests · {t.elapsed_minutes || 0}m</span>
                  )}
                  {t.current_bill != null && (
                    <span className="text-[10px] font-semibold">{formatCurrency(t.current_bill)}</span>
                  )}
                  {t.assigned_waiter && (
                    <span className="max-w-[90%] truncate text-[9px] opacity-90">{t.assigned_waiter}</span>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
