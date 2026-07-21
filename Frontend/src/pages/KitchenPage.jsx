import { useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChefHat, RotateCcw } from 'lucide-react'
import Button from '../components/ui/Button'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import { useOrg } from '../context/OrgContext'
import { useToast } from '../context/ToastContext'
import {
  connectPosSocket,
  fetchKitchenQueue,
  updateKitchenItem,
  updateOrder,
} from '../services/orderService'

const COLUMNS = [
  { key: 'new', title: 'New orders', tone: 'border-sky-400 bg-sky-50 dark:bg-sky-950/30' },
  { key: 'preparing', title: 'Preparing', tone: 'border-amber-400 bg-amber-50 dark:bg-amber-950/30' },
  { key: 'ready', title: 'Ready', tone: 'border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30' },
  { key: 'completed', title: 'Completed', tone: 'border-slate-300 bg-slate-50 dark:bg-slate-900/40' },
]

function priorityClass(minutes) {
  if (minutes >= 20) return 'text-rose-600 font-bold'
  if (minutes >= 12) return 'text-amber-600 font-semibold'
  return 'text-slate-500'
}

export default function KitchenPage() {
  const { restaurant, branch } = useOrg()
  const { success, error: toastError } = useToast()
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['kitchen', restaurant?.id, branch?.id],
    enabled: !!restaurant?.id,
    refetchInterval: 8000,
    queryFn: async () => {
      const res = await fetchKitchenQueue({
        restaurant_id: restaurant.id,
        branch_id: branch?.id,
      })
      return res.data || res
    },
  })

  useEffect(() => {
    return connectPosSocket((msg) => {
      if (String(msg?.event || '').startsWith('order') || String(msg?.event || '').startsWith('kitchen')) {
        queryClient.invalidateQueries({ queryKey: ['kitchen'] })
      }
    })
  }, [queryClient])

  const itemMutation = useMutation({
    mutationFn: ({ orderId, itemId, status }) => updateKitchenItem(orderId, itemId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kitchen'] })
      success('Kitchen updated')
    },
    onError: (e) => toastError(e.message),
  })

  const orderMutation = useMutation({
    mutationFn: ({ orderId, status }) => updateOrder(orderId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kitchen'] })
      success('Order updated')
    },
    onError: (e) => toastError(e.message),
  })

  const counts = useMemo(() => {
    if (!data) return {}
    return Object.fromEntries(COLUMNS.map((c) => [c.key, (data[c.key] || []).length]))
  }, [data])

  if (!restaurant) {
    return <EmptyState title="Select a restaurant" description="Kitchen board needs org context." />
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900 dark:text-white">
            <ChefHat className="h-7 w-7" /> Kitchen display
          </h1>
          <p className="text-sm text-slate-500">
            Live tickets · auto-refresh · {branch?.name || 'all branches'}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/pos">
            <Button variant="secondary">POS</Button>
          </Link>
          <Button
            variant="ghost"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['kitchen'] })}
          >
            <RotateCcw className="h-4 w-4" /> Refresh
          </Button>
        </div>
      </div>

      {isError && <p className="text-sm text-rose-600">{error?.message}</p>}
      {isLoading ? (
        <LoadingSpinner label="Loading kitchen queue…" />
      ) : (
        <div className="grid gap-3 lg:grid-cols-4">
          {COLUMNS.map((col) => (
            <div key={col.key} className={`rounded-2xl border-t-4 p-3 ${col.tone}`}>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-semibold text-slate-900 dark:text-white">{col.title}</h2>
                <span className="rounded-full bg-white/80 px-2 py-0.5 text-xs font-bold dark:bg-slate-900">
                  {counts[col.key] || 0}
                </span>
              </div>
              <div className="space-y-3">
                {(data?.[col.key] || []).length === 0 ? (
                  <p className="py-8 text-center text-xs text-slate-400">Empty</p>
                ) : (
                  (data[col.key] || []).map((ticket) => (
                    <article
                      key={ticket.uuid}
                      className="rounded-xl border border-slate-200/80 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-950"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-bold text-slate-900 dark:text-white">
                            {ticket.order_number}
                          </p>
                          <p className="text-xs text-slate-500">
                            {ticket.order_type?.replace('_', ' ')}
                            {ticket.table_number ? ` · T${ticket.table_number}` : ''}
                            {ticket.customer ? ` · ${ticket.customer}` : ''}
                          </p>
                        </div>
                        <span className={`text-sm ${priorityClass(ticket.elapsed_minutes || 0)}`}>
                          {ticket.elapsed_minutes || 0}m
                        </span>
                      </div>
                      <ul className="mt-2 space-y-1.5">
                        {(ticket.items || []).map((item) => (
                          <li
                            key={item.id}
                            className="rounded-lg bg-slate-50 px-2 py-1.5 text-sm dark:bg-slate-900"
                          >
                            <div className="flex justify-between gap-2">
                              <span className="font-medium">
                                {Number(item.quantity)}× {item.item_name}
                              </span>
                              <span className="text-[10px] uppercase text-slate-400">
                                {item.kitchen_status}
                              </span>
                            </div>
                            {item.notes && (
                              <p className="mt-0.5 text-xs text-amber-700 dark:text-amber-400">
                                Note: {item.notes}
                              </p>
                            )}
                            <div className="mt-1 flex flex-wrap gap-1">
                              {item.kitchen_status !== 'PREPARING' && col.key === 'new' && (
                                <button
                                  type="button"
                                  className="rounded bg-amber-600 px-2 py-0.5 text-[11px] font-semibold text-white"
                                  onClick={() =>
                                    itemMutation.mutate({
                                      orderId: ticket.uuid,
                                      itemId: item.id,
                                      status: 'PREPARING',
                                    })
                                  }
                                >
                                  Start
                                </button>
                              )}
                              {item.kitchen_status !== 'READY' && col.key !== 'ready' && (
                                <button
                                  type="button"
                                  className="rounded bg-emerald-600 px-2 py-0.5 text-[11px] font-semibold text-white"
                                  onClick={() =>
                                    itemMutation.mutate({
                                      orderId: ticket.uuid,
                                      itemId: item.id,
                                      status: 'READY',
                                    })
                                  }
                                >
                                  Ready
                                </button>
                              )}
                              {item.kitchen_status === 'READY' && (
                                <button
                                  type="button"
                                  className="rounded bg-slate-700 px-2 py-0.5 text-[11px] font-semibold text-white"
                                  onClick={() =>
                                    itemMutation.mutate({
                                      orderId: ticket.uuid,
                                      itemId: item.id,
                                      status: 'PREPARING',
                                    })
                                  }
                                >
                                  Recall
                                </button>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {col.key === 'new' && (
                          <Button
                            size="sm"
                            onClick={() =>
                              orderMutation.mutate({ orderId: ticket.uuid, status: 'PREPARING' })
                            }
                          >
                            Accept all
                          </Button>
                        )}
                        {col.key === 'preparing' && (
                          <Button
                            size="sm"
                            onClick={() =>
                              orderMutation.mutate({ orderId: ticket.uuid, status: 'READY' })
                            }
                          >
                            Mark ready
                          </Button>
                        )}
                        {col.key === 'ready' && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() =>
                              orderMutation.mutate({ orderId: ticket.uuid, status: 'SERVED' })
                            }
                          >
                            Served
                          </Button>
                        )}
                      </div>
                    </article>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
