import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ChefHat,
  LayoutGrid,
  Minus,
  Plus,
  Search,
  Trash2,
  MonitorSmartphone,
} from 'lucide-react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import EmptyState from '../components/ui/EmptyState'
import { Input, Select, Textarea } from '../components/forms/FormControls'
import { useOrg } from '../context/OrgContext'
import { useToast } from '../context/ToastContext'
import { formatCurrency } from '../utils/format'
import { listMenuItems } from '../services/catalogService'
import { listCustomers } from '../services/customerService'
import { listTables } from '../services/operationsService'
import {
  connectPosSocket,
  createOrder,
  fetchPosDashboard,
  payOrder,
} from '../services/orderService'

const ORDER_TYPES = [
  { value: 'DINE_IN', label: 'Dine in' },
  { value: 'TAKEAWAY', label: 'Takeaway' },
  { value: 'DELIVERY', label: 'Delivery' },
  { value: 'ONLINE', label: 'Online' },
]

const PAY_METHODS = [
  { value: 'CASH', label: 'Cash' },
  { value: 'CARD', label: 'Card' },
  { value: 'UPI', label: 'UPI' },
  { value: 'WALLET', label: 'Wallet' },
]

function asList(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.data)) return res.data
  return []
}

export default function PosPage() {
  const { restaurant, branch } = useOrg()
  const { success, error: toastError } = useToast()
  const queryClient = useQueryClient()
  const barcodeRef = useRef(null)

  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('ALL')
  const [cart, setCart] = useState([])
  const [orderType, setOrderType] = useState('DINE_IN')
  const [tableId, setTableId] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [guestCount, setGuestCount] = useState(2)
  const [discount, setDiscount] = useState(0)
  const [coupon, setCoupon] = useState('')
  const [notes, setNotes] = useState('')
  const [payMethod, setPayMethod] = useState('CASH')
  const [tip, setTip] = useState(0)
  const [lastOrder, setLastOrder] = useState(null)

  const { data: menu = [], isLoading: menuLoading } = useQuery({
    queryKey: ['pos-menu', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listMenuItems({ restaurant_id: restaurant.id })),
  })

  const { data: tables = [] } = useQuery({
    queryKey: ['pos-tables', branch?.id],
    enabled: !!branch?.id,
    queryFn: async () => asList(await listTables({ branch_id: branch.id, active_only: true })),
  })

  const { data: customers = [] } = useQuery({
    queryKey: ['pos-customers', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listCustomers({ restaurant_id: restaurant.id, limit: 200 })),
  })

  const { data: dash } = useQuery({
    queryKey: ['pos-dashboard', restaurant?.id, branch?.id],
    enabled: !!restaurant?.id,
    refetchInterval: 15000,
    queryFn: async () => {
      const res = await fetchPosDashboard({
        restaurant_id: restaurant.id,
        branch_id: branch?.id,
      })
      return res.data || res
    },
  })

  useEffect(() => {
    if (!restaurant?.id) return undefined
    return connectPosSocket(() => {
      queryClient.invalidateQueries({ queryKey: ['pos-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['pos-tables'] })
    })
  }, [restaurant?.id, queryClient])

  const categories = useMemo(() => {
    const set = new Set(menu.map((m) => m.menu_category || 'Uncategorized'))
    return ['ALL', ...Array.from(set).sort()]
  }, [menu])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return menu.filter((m) => {
      if (!m.is_available) return false
      if (category !== 'ALL' && (m.menu_category || 'Uncategorized') !== category) return false
      if (!q) return true
      return (
        m.name?.toLowerCase().includes(q) ||
        String(m.id).toLowerCase().includes(q) ||
        m.description?.toLowerCase().includes(q)
      )
    })
  }, [menu, search, category])

  const popular = useMemo(() => filtered.slice(0, 8), [filtered])

  const cartTotals = useMemo(() => {
    const sub = cart.reduce((s, l) => s + l.quantity * l.unit_price - (l.discount_amount || 0), 0)
    const disc = Number(discount) || 0
    const couponDisc = coupon.trim().toUpperCase() === 'WELCOME10' ? sub * 0.1 : 0
    const taxable = Math.max(sub - disc - couponDisc, 0)
    const tax = taxable * 0.05
    return {
      subtotal: sub,
      discount: disc + couponDisc,
      tax,
      total: taxable + tax,
    }
  }, [cart, discount, coupon])

  const addItem = (item, modifiers = null) => {
    setCart((prev) => {
      const key = `${item.id}:${JSON.stringify(modifiers || [])}`
      const idx = prev.findIndex((p) => p._key === key)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = { ...next[idx], quantity: next[idx].quantity + 1 }
        return next
      }
      return [
        ...prev,
        {
          _key: key,
          menu_item_id: item.id,
          item_name: item.name,
          unit_price: Number(item.price),
          quantity: 1,
          discount_amount: 0,
          notes: '',
          modifiers: modifiers || item.variants?.filter((v) => v.is_default).map((v) => v.name) || [],
        },
      ]
    })
  }

  const updateQty = (key, delta) => {
    setCart((prev) =>
      prev
        .map((l) => (l._key === key ? { ...l, quantity: l.quantity + delta } : l))
        .filter((l) => l.quantity > 0),
    )
  }

  // Prefer an available table so dine-in is one click less (derive; no effect setState)
  const resolvedTableId = useMemo(() => {
    if (orderType !== 'DINE_IN') return tableId
    if (tableId) return tableId
    return tables.find((t) => t.status === 'AVAILABLE')?.id || ''
  }, [orderType, tableId, tables])

  const placeMutation = useMutation({
    mutationFn: async ({ andPay }) => {
      if (!branch?.id) throw new Error('Select a branch')
      if (!cart.length) throw new Error('Add at least one item to the ticket')
      if (orderType === 'DINE_IN' && !resolvedTableId) throw new Error('Select a table for dine-in')
      const payload = {
        branch_id: branch.id,
        customer_id: customerId || null,
        table_id: orderType === 'DINE_IN' ? resolvedTableId || null : null,
        order_type: orderType,
        status: 'CONFIRMED',
        guest_count: Number(guestCount) || 1,
        discount_amount: cartTotals.discount,
        notes: notes || null,
        deduct_stock: true,
        items: cart.map((l) => ({
          menu_item_id: l.menu_item_id,
          item_name: l.item_name,
          quantity: l.quantity,
          unit_price: l.unit_price,
          discount_amount: l.discount_amount || 0,
          notes: l.notes || null,
          modifiers: l.modifiers || null,
        })),
      }
      const created = await createOrder(payload)
      const order = created.data || created
      if (andPay) {
        const paid = await payOrder(order.uuid, {
          method: payMethod,
          tip_amount: Number(tip) || 0,
        })
        return paid.data || paid
      }
      return order
    },
    onSuccess: (order) => {
      setLastOrder(order)
      setCart([])
      setNotes('')
      setDiscount(0)
      setCoupon('')
      if (order.status_code === 'COMPLETED') {
        setTip(0)
        setTableId('')
        success(`Paid ${order.order_number} · ${order.invoice_number || 'closed'}`)
      } else {
        success(`${order.order_number} sent to kitchen — collect payment when ready`)
      }
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['pos-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['pos-tables'] })
      queryClient.invalidateQueries({ queryKey: ['kitchen'] })
      queryClient.invalidateQueries({ queryKey: ['floor'] })
      queryClient.invalidateQueries({ queryKey: ['payments-orders'] })
    },
    onError: (err) => toastError(err.message || 'Order failed'),
  })

  const collectPaymentMutation = useMutation({
    mutationFn: async () => {
      if (!lastOrder?.uuid) throw new Error('No open ticket to pay')
      if (Number(lastOrder.balance_due) <= 0) throw new Error('Order is already paid')
      const paid = await payOrder(lastOrder.uuid, {
        method: payMethod,
        tip_amount: Number(tip) || 0,
      })
      return paid.data || paid
    },
    onSuccess: (order) => {
      setLastOrder(order)
      setTip(0)
      setTableId('')
      success(`Payment collected · ${order.invoice_number || order.order_number}`)
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['pos-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['pos-tables'] })
      queryClient.invalidateQueries({ queryKey: ['floor'] })
      queryClient.invalidateQueries({ queryKey: ['payments-orders'] })
    },
    onError: (err) => toastError(err.message || 'Payment failed'),
  })

  const canPlace =
    cart.length > 0 &&
    Boolean(branch?.id) &&
    (orderType !== 'DINE_IN' || Boolean(resolvedTableId)) &&
    !placeMutation.isPending

  const blockReason = !cart.length
    ? 'Add menu items to the ticket first'
    : orderType === 'DINE_IN' && !resolvedTableId
      ? 'Select a table for dine-in'
      : null

  const openTicketUnpaid =
    lastOrder &&
    lastOrder.status_code !== 'COMPLETED' &&
    lastOrder.status_code !== 'CANCELLED' &&
    Number(lastOrder.balance_due) > 0

  const onBarcode = (e) => {
    if (e.key !== 'Enter') return
    const code = e.target.value.trim().toLowerCase()
    if (!code) return
    const hit = menu.find(
      (m) => String(m.id).toLowerCase() === code || m.name?.toLowerCase() === code,
    )
    if (hit) addItem(hit)
    else toastError('Item not found')
    e.target.value = ''
  }

  if (!restaurant || !branch) {
    return (
      <EmptyState
        title="Select restaurant & branch"
        description="Use the org switcher to choose a location before opening POS."
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">POS Terminal</h1>
          <p className="text-sm text-slate-500">
            {restaurant.name} · {branch.name}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/kitchen">
            <Button variant="secondary" className="gap-2">
              <ChefHat className="h-4 w-4" /> Kitchen
            </Button>
          </Link>
          <Link to="/floor">
            <Button variant="secondary" className="gap-2">
              <LayoutGrid className="h-4 w-4" /> Floor
            </Button>
          </Link>
          <Link to="/payments">
            <Button variant="secondary">Payments</Button>
          </Link>
        </div>
      </div>

      {dash && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {[
            ['Today sales', formatCurrency(dash.today_sales)],
            ['Orders', dash.orders_today],
            ['AOV', formatCurrency(dash.average_order_value)],
            ['Open tables', dash.open_tables],
            ['Kitchen queue', dash.kitchen_queue],
          ].map(([label, value]) => (
            <Card key={label} className="!p-0">
              <div className="px-4 py-3">
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">{value}</p>
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          <Card>
            <div className="flex flex-wrap gap-3">
              <div className="relative min-w-[200px] flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                  placeholder="Search menu…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <input
                ref={barcodeRef}
                className="w-40 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Barcode / ID"
                onKeyDown={onBarcode}
              />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {categories.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCategory(c)}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                    category === c
                      ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
                      : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </Card>

          {menuLoading ? (
            <LoadingSpinner label="Loading menu…" />
          ) : filtered.length === 0 ? (
            <EmptyState title="No menu items" description="Add available items under Menu." />
          ) : (
            <>
              <div>
                <h2 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                  Popular
                </h2>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {popular.map((item) => (
                    <button
                      key={`pop-${item.id}`}
                      type="button"
                      onClick={() => addItem(item)}
                      className="rounded-xl border border-slate-200 bg-white p-3 text-left transition hover:border-emerald-400 dark:border-slate-700 dark:bg-slate-900"
                    >
                      <p className="line-clamp-2 text-sm font-semibold text-slate-900 dark:text-white">
                        {item.name}
                      </p>
                      <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-400">
                        {formatCurrency(item.price)}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                {filtered.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => addItem(item)}
                    className="min-h-[88px] rounded-xl border border-slate-200 bg-white p-3 text-left transition hover:border-slate-400 active:scale-[0.99] dark:border-slate-700 dark:bg-slate-900"
                  >
                    <p className="text-xs text-slate-400">{item.menu_category || '—'}</p>
                    <p className="mt-0.5 line-clamp-2 text-sm font-semibold text-slate-900 dark:text-white">
                      {item.name}
                    </p>
                    <p className="mt-2 text-sm font-medium">{formatCurrency(item.price)}</p>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        <Card className="h-fit xl:sticky xl:top-4">
          <div className="mb-3 flex items-center gap-2">
            <MonitorSmartphone className="h-5 w-5" />
            <h2 className="font-semibold text-slate-900 dark:text-white">Ticket</h2>
          </div>

          <div className="space-y-3">
            <Select
              label="Order type"
              value={orderType}
              onChange={(e) => setOrderType(e.target.value)}
              options={ORDER_TYPES}
            />
            {orderType === 'DINE_IN' && (
              <Select
                label="Table"
                value={resolvedTableId}
                onChange={(e) => setTableId(e.target.value)}
                options={[
                  { value: '', label: 'Select table…' },
                  ...tables
                    .filter((t) => t.status === 'AVAILABLE' || t.id === resolvedTableId)
                    .map((t) => ({
                      value: t.id,
                      label: `${t.table_number} · ${t.status} · ${t.capacity}p`,
                    })),
                ]}
              />
            )}
            <Select
              label="Customer"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              options={[
                { value: '', label: 'Walk-in' },
                ...customers.map((c) => ({
                  value: c.id,
                  label: `${c.full_name || c.name}${c.loyalty_points ? ` · ${c.loyalty_points} pts` : ''}`,
                })),
              ]}
            />
            <div className="grid grid-cols-2 gap-2">
              <Input
                label="Guests"
                type="number"
                min={1}
                value={guestCount}
                onChange={(e) => setGuestCount(e.target.value)}
              />
              <Input
                label="Discount ₹"
                type="number"
                min={0}
                value={discount}
                onChange={(e) => setDiscount(e.target.value)}
              />
            </div>
            <Input
              label="Coupon"
              placeholder="e.g. WELCOME10"
              value={coupon}
              onChange={(e) => setCoupon(e.target.value)}
            />

            <div className="max-h-56 space-y-2 overflow-y-auto">
              {cart.length === 0 ? (
                <p className="py-6 text-center text-sm text-slate-400">Tap menu items to add</p>
              ) : (
                cart.map((line) => (
                  <div
                    key={line._key}
                    className="rounded-lg border border-slate-100 p-2 dark:border-slate-800"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium">{line.item_name}</p>
                        <p className="text-xs text-slate-500">
                          {formatCurrency(line.unit_price)} each
                        </p>
                      </div>
                      <button type="button" onClick={() => updateQty(line._key, -line.quantity)}>
                        <Trash2 className="h-4 w-4 text-rose-500" />
                      </button>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <button
                        type="button"
                        className="rounded-lg bg-slate-100 p-1.5 dark:bg-slate-800"
                        onClick={() => updateQty(line._key, -1)}
                      >
                        <Minus className="h-4 w-4" />
                      </button>
                      <span className="min-w-[1.5rem] text-center text-sm font-semibold">
                        {line.quantity}
                      </span>
                      <button
                        type="button"
                        className="rounded-lg bg-slate-100 p-1.5 dark:bg-slate-800"
                        onClick={() => updateQty(line._key, 1)}
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                      <span className="ml-auto text-sm font-semibold">
                        {formatCurrency(line.quantity * line.unit_price)}
                      </span>
                    </div>
                    <input
                      className="mt-2 w-full rounded-md border border-slate-200 bg-transparent px-2 py-1 text-xs dark:border-slate-700"
                      placeholder="Special instructions…"
                      value={line.notes}
                      onChange={(e) =>
                        setCart((prev) =>
                          prev.map((l) =>
                            l._key === line._key ? { ...l, notes: e.target.value } : l,
                          ),
                        )
                      }
                    />
                  </div>
                ))
              )}
            </div>

            <Textarea
              label="Order notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
            />

            <div className="space-y-1 border-t border-slate-100 pt-3 text-sm dark:border-slate-800">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>{formatCurrency(cartTotals.subtotal)}</span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Discount</span>
                <span>-{formatCurrency(cartTotals.discount)}</span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Tax (5%)</span>
                <span>{formatCurrency(cartTotals.tax)}</span>
              </div>
              <div className="flex justify-between text-base font-bold">
                <span>Total</span>
                <span>{formatCurrency(cartTotals.total)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Select
                label="Pay method"
                value={payMethod}
                onChange={(e) => setPayMethod(e.target.value)}
                options={PAY_METHODS}
              />
              <Input
                label="Tip ₹"
                type="number"
                min={0}
                value={tip}
                onChange={(e) => setTip(e.target.value)}
              />
            </div>

            {blockReason && (
              <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
                {blockReason}
              </p>
            )}

            <div className="grid gap-2">
              <Button
                className="min-h-12 w-full text-base"
                disabled={!canPlace}
                onClick={() => placeMutation.mutate({ andPay: false })}
              >
                {placeMutation.isPending && !placeMutation.variables?.andPay
                  ? 'Sending…'
                  : 'Send to kitchen'}
              </Button>
              <Button
                className="min-h-12 w-full bg-emerald-600 text-base text-white hover:bg-emerald-700 disabled:bg-emerald-300"
                disabled={!canPlace}
                onClick={() => placeMutation.mutate({ andPay: true })}
              >
                {placeMutation.isPending && placeMutation.variables?.andPay
                  ? 'Processing…'
                  : `Pay & close · ${formatCurrency(cartTotals.total + (Number(tip) || 0))}`}
              </Button>
            </div>

            {lastOrder && (
              <div className="space-y-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm dark:border-emerald-900 dark:bg-emerald-950/40">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-white">
                      {lastOrder.order_number}
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-300">
                      {lastOrder.status}
                      {lastOrder.table_number ? ` · Table ${lastOrder.table_number}` : ''}
                      {lastOrder.invoice_number ? ` · ${lastOrder.invoice_number}` : ''}
                    </p>
                    <p className="mt-1 font-medium">
                      Total {formatCurrency(lastOrder.total)}
                      {Number(lastOrder.balance_due) > 0
                        ? ` · Due ${formatCurrency(lastOrder.balance_due)}`
                        : ' · Paid'}
                    </p>
                  </div>
                  <Link className="text-xs text-emerald-700 underline" to="/payments">
                    Receipts
                  </Link>
                </div>
                {openTicketUnpaid && (
                  <Button
                    className="w-full bg-emerald-700 hover:bg-emerald-800"
                    disabled={collectPaymentMutation.isPending}
                    onClick={() => collectPaymentMutation.mutate()}
                  >
                    {collectPaymentMutation.isPending
                      ? 'Collecting…'
                      : `Collect payment (${payMethod}) · ${formatCurrency(lastOrder.balance_due)}`}
                  </Button>
                )}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
