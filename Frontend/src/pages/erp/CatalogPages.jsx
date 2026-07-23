import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertTriangle,
  ArrowLeftRight,
  ChefHat,
  ClipboardList,
  Package,
  UtensilsCrossed,
} from 'lucide-react'
import EntityListPage from '../../components/pages/EntityListPage'
import AppModal from '../../components/modals/AppModal'
import { AddEntityButton, CodeChip, StatusBadge } from '../../components/erp/ErpTableUi'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { Input, Select, Textarea } from '../../components/forms/FormControls'
import { useOrg } from '../../context/OrgContext'
import { useToast } from '../../context/ToastContext'
import { formatCurrency, formatNumber } from '../../utils/format'
import { listProducts } from '../../services/productService'
import { listSuppliers } from '../../services/supplierService'
import { listBranches } from '../../services/branchService'
import {
  approvePurchaseOrder,
  cancelPurchaseOrder,
  completeStockTransfer,
  createGoodsReceipt,
  createMenuCategory,
  createMenuItem,
  createPurchaseOrder,
  createRecipe,
  createStockTransfer,
  fetchCatalogDashboard,
  listGoodsReceipts,
  listInventoryTransactions,
  listMenuItems,
  listPurchaseOrders,
  listRecipes,
  listStockAlerts,
  listStockTransfers,
  seedDefaultUnits,
  submitPurchaseOrder,
  submitStockTransfer,
  approveStockTransfer,
  listUnits,
  createUnit,
  listUnitConversions,
  createUnitConversion,
} from '../../services/catalogService'
import { listWarehouses, createWarehouse } from '../../services/warehouseService'

const MODULES = [
  { to: '/purchase-orders', title: 'Purchase orders', blurb: 'Draft → approve → order', icon: ClipboardList },
  { to: '/goods-receipts', title: 'Goods receipts', blurb: 'Receive PO into stock', icon: Package },
  { to: '/recipes', title: 'Recipes', blurb: 'BOM + food cost', icon: ChefHat },
  { to: '/menu', title: 'Menu', blurb: 'Items, variants, availability', icon: UtensilsCrossed },
  { to: '/stock-alerts', title: 'Stock alerts', blurb: 'Low / expiry warnings', icon: AlertTriangle },
  { to: '/stock-transfers', title: 'Transfers', blurb: 'Branch-to-branch stock', icon: ArrowLeftRight },
]

function asList(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.data)) return res.data
  if (Array.isArray(res?.data?.data)) return res.data.data
  return []
}

function asData(res) {
  if (res && typeof res === 'object' && !Array.isArray(res) && res.data && !Array.isArray(res.data)) {
    return res.data
  }
  if (res?.data && typeof res.data === 'object' && !Array.isArray(res.data)) return res.data
  return res
}

function daysFromNow(days) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

const EMPTY_PO_FORM = {
  supplier_id: '',
  product_id: '',
  quantity: '10',
  unit_cost: '',
  expected_date: '',
  notes: '',
}

export function CatalogOverviewPage() {
  const { restaurant } = useOrg()
  const { success, error: toastError } = useToast()

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['catalog-dashboard', restaurant?.id],
    queryFn: async () => {
      const res = await fetchCatalogDashboard(
        restaurant?.id ? { restaurant_id: restaurant.id } : {}
      )
      return asData(res)
    },
  })

  const seedMutation = useMutation({
    mutationFn: () =>
      seedDefaultUnits(restaurant?.id ? { restaurant_id: restaurant.id } : {}),
    onSuccess: (res) => success(`Units seeded (${asData(res)?.created ?? 0} rows)`),
    onError: (err) => toastError(err?.message || 'Seed failed'),
  })

  const metrics = [
    { label: 'Products', value: data?.total_products ?? '—' },
    { label: 'Inventory value', value: data ? formatCurrency(data.inventory_value) : '—' },
    { label: 'Low stock', value: data?.low_stock ?? '—' },
    { label: 'Out of stock', value: data?.out_of_stock ?? '—' },
    { label: 'Pending POs', value: data?.pending_purchase_orders ?? '—' },
    { label: 'Suppliers', value: data?.supplier_count ?? '—' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
            Catalog & procurement
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Supplier → PO → GRN → inventory → recipe → menu → sale
          </p>
        </div>
        <Button variant="secondary" onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
          Seed units of measure
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 text-sm">
        <Link
          to="/products"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-700 transition hover:border-emerald-400/50 hover:text-emerald-700 dark:border-zinc-700 dark:text-zinc-200 dark:hover:text-emerald-300"
        >
          Products
        </Link>
        <Link
          to="/purchase-orders"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-700 transition hover:border-emerald-400/50 hover:text-emerald-700 dark:border-zinc-700 dark:text-zinc-200 dark:hover:text-emerald-300"
        >
          Purchase orders
        </Link>
        <Link
          to="/goods-receipts"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-700 transition hover:border-emerald-400/50 hover:text-emerald-700 dark:border-zinc-700 dark:text-zinc-200 dark:hover:text-emerald-300"
        >
          Goods receipts
        </Link>
        <Link
          to="/stock"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-slate-700 transition hover:border-emerald-400/50 hover:text-emerald-700 dark:border-zinc-700 dark:text-zinc-200 dark:hover:text-emerald-300"
        >
          Stock
        </Link>
      </div>

      {isError && (
        <p className="text-sm text-rose-600">
          {error?.message || 'Failed to load catalog dashboard'}{' '}
          <button type="button" className="underline" onClick={() => refetch()}>
            Retry
          </button>
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {metrics.map((m) => (
          <Card key={m.label} className="p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">{m.label}</p>
            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-white">
              {isLoading ? '…' : m.value}
            </p>
          </Card>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {MODULES.map((m) => {
          const Icon = m.icon
          return (
            <Link
              key={m.to}
              to={m.to}
              className="group rounded-xl border border-slate-200 bg-white p-4 transition hover:border-emerald-400/60 dark:border-slate-700 dark:bg-slate-900"
            >
              <div className="flex items-start gap-3">
                <span className="rounded-lg bg-emerald-500/10 p-2 text-emerald-600">
                  <Icon size={18} />
                </span>
                <div>
                  <p className="font-medium text-slate-900 group-hover:text-emerald-700 dark:text-white">
                    {m.title}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">{m.blurb}</p>
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-800 dark:text-slate-100">
            Top selling (stock ledger)
          </h2>
          <ul className="space-y-2 text-sm">
            {(data?.top_selling_products || []).length === 0 && (
              <li className="text-slate-500">No sale movements yet</li>
            )}
            {(data?.top_selling_products || []).map((row) => (
              <li key={row.product_id} className="flex justify-between gap-2">
                <span>{row.product}</span>
                <span className="tabular-nums text-slate-500">{formatNumber(row.quantity_sold)}</span>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-800 dark:text-slate-100">
            Stock movement by type
          </h2>
          <ul className="space-y-2 text-sm">
            {(data?.stock_movement || []).length === 0 && (
              <li className="text-slate-500">No transactions yet</li>
            )}
            {(data?.stock_movement || []).map((row) => (
              <li key={row.type} className="flex justify-between gap-2">
                <span>{row.type}</span>
                <span className="tabular-nums text-slate-500">
                  {row.count} txn · {formatNumber(row.quantity)}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  )
}

export function PurchaseOrdersPage() {
  const { restaurant, branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(EMPTY_PO_FORM)

  const {
    data: suppliers = [],
    isLoading: suppliersLoading,
    isError: suppliersError,
  } = useQuery({
    queryKey: ['suppliers', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listSuppliers({ restaurant_id: restaurant.id, limit: 200 })),
  })
  const { data: products = [], isLoading: productsLoading } = useQuery({
    queryKey: ['products', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listProducts({ restaurant_id: restaurant.id, limit: 200 })),
  })
  const { data: branches = [] } = useQuery({
    queryKey: ['branches', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listBranches({ restaurant_id: restaurant.id })),
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['purchase-orders', restaurant?.id],
    queryFn: async () =>
      asList(await listPurchaseOrders(restaurant?.id ? { restaurant_id: restaurant.id } : {})),
  })

  const selectedProduct = useMemo(
    () => products.find((p) => String(p.id) === String(form.product_id)),
    [products, form.product_id],
  )

  function openCreate() {
    setForm({
      ...EMPTY_PO_FORM,
      expected_date: daysFromNow(3),
      supplier_id: suppliers[0]?.id ? String(suppliers[0].id) : '',
    })
    setOpen(true)
  }

  function onProductChange(productId) {
    const product = products.find((p) => String(p.id) === String(productId))
    setForm((prev) => ({
      ...prev,
      product_id: productId,
      unit_cost:
        product?.unit_cost != null && product.unit_cost !== ''
          ? String(product.unit_cost)
          : prev.unit_cost || '0',
      supplier_id: product?.supplier_id
        ? String(product.supplier_id)
        : prev.supplier_id || (suppliers[0]?.id ? String(suppliers[0].id) : ''),
    }))
  }

  const createMutation = useMutation({
    mutationFn: async () => {
      const branchId = branch?.id || branches[0]?.id
      if (!branchId) throw new Error('Select a branch in the top bar first')
      if (!form.supplier_id) throw new Error('Select a supplier')
      if (!form.product_id) throw new Error('Select a product')
      return createPurchaseOrder({
        branch_id: branchId,
        supplier_id: form.supplier_id,
        expected_date: form.expected_date || null,
        notes: form.notes || null,
        items: [
          {
            product_id: form.product_id,
            quantity: Number(form.quantity),
            unit_cost: Number(form.unit_cost),
          },
        ],
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      success('Purchase order created as DRAFT')
      setOpen(false)
      setForm(EMPTY_PO_FORM)
    },
    onError: (err) => toastError(err?.message || 'Create failed'),
  })

  const actionMutation = useMutation({
    mutationFn: async ({ id, action }) => {
      if (action === 'submit') return submitPurchaseOrder(id)
      if (action === 'approve') return approvePurchaseOrder(id)
      return cancelPurchaseOrder(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      success('Purchase order updated')
    },
    onError: (err) => toastError(err?.message || 'Action failed'),
  })

  const supplierOptions = [
    { value: '', label: suppliersLoading ? 'Loading suppliers…' : 'Select supplier…' },
    ...suppliers.map((s) => ({ value: String(s.id), label: s.name })),
  ]
  const productOptions = [
    { value: '', label: productsLoading ? 'Loading products…' : 'Select product…' },
    ...products.map((p) => ({
      value: String(p.id),
      label: `${p.name}${p.sku ? ` (${p.sku})` : ''}`,
    })),
  ]

  const createDisabled =
    createMutation.isPending ||
    !form.supplier_id ||
    !form.product_id ||
    !(Number(form.quantity) > 0) ||
    form.unit_cost === '' ||
    Number.isNaN(Number(form.unit_cost))

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Purchase orders"
        description="Draft → Submitted → Approved → Ordered → Received"
        entity="purchase-orders"
        rows={data || []}
        loading={isLoading}
        headerActions={<AddEntityButton label="New PO" onClick={openCreate} disabled={!restaurant?.id} />}
        columns={[
          {
            key: 'po_number',
            label: 'PO #',
            render: (_v, r) => <CodeChip>{r.po_number}</CodeChip>,
          },
          { key: 'supplier_name', label: 'Supplier' },
          { key: 'branch_name', label: 'Branch' },
          {
            key: 'status',
            label: 'Status',
            render: (v) => <StatusBadge status={v} />,
          },
          {
            key: 'total_amount',
            label: 'Total',
            render: (v) => formatCurrency(v),
          },
          {
            key: 'actions',
            label: '',
            render: (_v, r) => (
              <div className="flex flex-wrap justify-end gap-1">
                {r.status === 'DRAFT' && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => actionMutation.mutate({ id: r.id, action: 'submit' })}
                  >
                    Submit
                  </Button>
                )}
                {r.status === 'SUBMITTED' && (
                  <Button size="sm" onClick={() => actionMutation.mutate({ id: r.id, action: 'approve' })}>
                    Approve
                  </Button>
                )}
                {!['RECEIVED', 'CANCELLED'].includes(r.status) && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => actionMutation.mutate({ id: r.id, action: 'cancel' })}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            ),
          },
        ]}
      />

      <AppModal
        open={open}
        onClose={() => setOpen(false)}
        title="Create purchase order"
        description="Draft PO — submit & approve next, then receive goods"
        size="lg"
        hideFooter
      >
        <div className="space-y-4">
          {!restaurant?.id && (
            <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2.5 text-sm text-amber-800 dark:text-amber-200">
              Select a restaurant in the top bar first.
            </p>
          )}
          {(suppliersError || (!suppliersLoading && suppliers.length === 0)) && (
            <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2.5 text-sm text-rose-800 dark:text-rose-200">
              No suppliers found.{' '}
              <Link className="font-medium underline" to="/suppliers">
                Add a supplier
              </Link>{' '}
              then open this form again.
            </p>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Supplier *"
              value={form.supplier_id}
              onChange={(e) => setForm({ ...form, supplier_id: e.target.value })}
              options={supplierOptions}
              error={!form.supplier_id && !suppliersLoading ? 'Required' : undefined}
            />
            <Select
              label="Product *"
              value={form.product_id}
              onChange={(e) => onProductChange(e.target.value)}
              options={productOptions}
              error={!form.product_id && products.length > 0 ? 'Required to create draft' : undefined}
              hint={
                !productsLoading && products.length === 0
                  ? 'No products — add one under Products first'
                  : undefined
              }
            />
          </div>

          {selectedProduct && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs text-slate-600 dark:border-zinc-700 dark:bg-zinc-900/80 dark:text-zinc-300 sm:text-sm">
              <span className="font-medium text-slate-800 dark:text-zinc-100">{selectedProduct.name}</span>
              <span className="mx-1.5 text-slate-400">·</span>
              Cost {formatCurrency(selectedProduct.unit_cost || 0)}
              {selectedProduct.sku ? (
                <>
                  <span className="mx-1.5 text-slate-400">·</span>
                  SKU {selectedProduct.sku}
                </>
              ) : null}
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Qty *"
              type="number"
              inputMode="decimal"
              min="0.001"
              step="any"
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: e.target.value })}
            />
            <Input
              label="Unit cost (₹) *"
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              value={form.unit_cost}
              onChange={(e) => setForm({ ...form, unit_cost: e.target.value })}
              hint={!form.unit_cost ? 'Filled automatically when you pick a product' : undefined}
            />
          </div>

          {form.product_id && form.quantity && form.unit_cost !== '' && (
            <div className="flex items-center justify-between rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-3 py-2.5 text-sm">
              <span className="text-slate-600 dark:text-zinc-300">Line total</span>
              <span className="font-semibold tabular-nums text-emerald-700 dark:text-emerald-300">
                {formatCurrency(Number(form.quantity) * Number(form.unit_cost || 0))}
              </span>
            </div>
          )}

          <Input
            label="Expected delivery"
            type="date"
            value={form.expected_date}
            onChange={(e) => setForm({ ...form, expected_date: e.target.value })}
          />
          <Textarea
            label="Notes"
            rows={3}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Optional delivery or quality notes"
          />

          <div className="sticky bottom-0 -mx-4 mt-2 border-t border-slate-100 bg-white px-4 pt-3 dark:border-zinc-800 dark:bg-zinc-950 sm:-mx-6 sm:px-6">
            {createDisabled && !createMutation.isPending && (
              <p className="mb-3 rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium text-slate-700 dark:bg-zinc-800 dark:text-zinc-200 sm:text-sm">
                {!form.supplier_id
                  ? 'Select a supplier to continue.'
                  : !form.product_id
                    ? 'Select a product to continue.'
                    : 'Enter quantity and unit cost.'}
              </p>
            )}
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button variant="secondary" onClick={() => setOpen(false)} className="w-full sm:w-auto">
                Cancel
              </Button>
              <Button
                disabled={createDisabled}
                onClick={() => createMutation.mutate()}
                className="w-full sm:w-auto"
              >
                {createMutation.isPending ? 'Creating…' : 'Create draft'}
              </Button>
            </div>
          </div>
        </div>
      </AppModal>
    </>
  )
}
export function GoodsReceiptsPage() {
  const { restaurant, branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ po_id: '', received_quantity: '' })

  const { data: pos = [] } = useQuery({
    queryKey: ['purchase-orders-receivable', restaurant?.id],
    queryFn: async () => {
      const all = asList(
        await listPurchaseOrders(restaurant?.id ? { restaurant_id: restaurant.id, limit: 200 } : {})
      )
      return all.filter((p) => ['APPROVED', 'ORDERED'].includes(p.status))
    },
  })

  const selectedPo = useMemo(() => pos.find((p) => p.id === form.po_id), [pos, form.po_id])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['goods-receipts', restaurant?.id],
    queryFn: async () =>
      asList(await listGoodsReceipts(restaurant?.id ? { restaurant_id: restaurant.id } : {})),
  })

  const createMutation = useMutation({
    mutationFn: async () => {
      const line = selectedPo?.items?.[0]
      if (!line) throw new Error('PO has no lines')
      return createGoodsReceipt({
        purchase_order_id: form.po_id,
        branch_id: branch?.id || selectedPo.branch_id,
        items: [
          {
            purchase_item_id: line.id,
            product_id: line.product_id,
            received_quantity: Number(form.received_quantity || line.quantity),
            rejected_quantity: 0,
            damaged_quantity: 0,
            unit_cost: Number(line.unit_cost),
          },
        ],
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goods-receipts'] })
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
      queryClient.invalidateQueries({ queryKey: ['inventory-items'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['stock-alerts'] })
      success('Goods received — stock increased')
      setOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Receive failed'),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Goods receipts"
        description="Receive purchase orders into branch inventory"
        entity="goods-receipts"
        rows={data || []}
        loading={isLoading}
        headerActions={<AddEntityButton label="Receive goods" onClick={() => setOpen(true)} />}
        columns={[
          { key: 'grn_number', label: 'GRN #', render: (v) => <CodeChip>{v}</CodeChip> },
          { key: 'po_number', label: 'PO #' },
          { key: 'receipt_date', label: 'Date' },
          {
            key: 'items',
            label: 'Lines',
            render: (v) => (Array.isArray(v) ? v.length : 0),
          },
        ]}
      />

      <AppModal open={open} onClose={() => setOpen(false)} title="Receive goods" hideFooter>
        <div className="space-y-4">
          <Select
            label="Approved PO *"
            value={form.po_id}
            onChange={(e) => setForm({ ...form, po_id: e.target.value })}
            options={[
              { value: '', label: pos.length ? 'Select…' : 'No receivable POs' },
              ...pos.map((p) => ({
                value: p.id,
                label: `${p.po_number} · ${p.supplier_name || 'Supplier'}`,
              })),
            ]}
          />
          {selectedPo?.items?.[0] && (
            <p className="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:bg-zinc-900 dark:text-zinc-300">
              Line: {selectedPo.items[0].item_name} · ordered {selectedPo.items[0].quantity}
            </p>
          )}
          <Input
            label="Received qty"
            type="number"
            inputMode="decimal"
            value={form.received_quantity}
            onChange={(e) => setForm({ ...form, received_quantity: e.target.value })}
            placeholder={selectedPo?.items?.[0]?.quantity?.toString() || ''}
          />
          <div className="flex flex-col-reverse gap-2 pt-1 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={() => setOpen(false)} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button
              disabled={!form.po_id || createMutation.isPending}
              onClick={() => createMutation.mutate()}
              className="w-full sm:w-auto"
            >
              Post GRN
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function RecipesPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    menu_item_id: '',
    name: '',
    product_id: '',
    quantity: '1',
    yield_portions: '1',
  })

  const { data: menuItems = [] } = useQuery({
    queryKey: ['menu-items', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listMenuItems({ restaurant_id: restaurant.id })),
  })
  const { data: products = [] } = useQuery({
    queryKey: ['products', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listProducts({ restaurant_id: restaurant.id, limit: 200 })),
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['recipes', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listRecipes({ restaurant_id: restaurant.id })),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createRecipe({
        restaurant_id: restaurant.id,
        menu_item_id: form.menu_item_id,
        name: form.name,
        yield_portions: Number(form.yield_portions),
        ingredients: [{ product_id: form.product_id, quantity: Number(form.quantity) }],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] })
      success('Recipe created with food cost')
      setOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Create failed'),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Recipes"
        description="Bill of materials with automatic food / portion cost"
        entity="recipes"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton label="Add recipe" onClick={() => setOpen(true)} disabled={!restaurant?.id} />
        }
        columns={[
          { key: 'name', label: 'Recipe' },
          { key: 'menu_item_name', label: 'Menu item' },
          {
            key: 'food_cost',
            label: 'Food cost',
            render: (v) => formatCurrency(v),
          },
          {
            key: 'portion_cost',
            label: 'Portion cost',
            render: (v) => formatCurrency(v),
          },
          {
            key: 'ingredients',
            label: 'Ingredients',
            render: (v) => (Array.isArray(v) ? v.length : 0),
          },
        ]}
      />

      <AppModal open={open} onClose={() => setOpen(false)} title="Create recipe" hideFooter>
        <div className="space-y-4">
          <Input label="Recipe name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Select
            label="Menu item *"
            value={form.menu_item_id}
            onChange={(e) => setForm({ ...form, menu_item_id: e.target.value })}
            options={[
              { value: '', label: menuItems.length ? 'Select…' : 'Create a menu item first' },
              ...menuItems.map((m) => ({ value: m.id, label: m.name })),
            ]}
          />
          <Select
            label="Ingredient product *"
            value={form.product_id}
            onChange={(e) => setForm({ ...form, product_id: e.target.value })}
            options={[{ value: '', label: 'Select…' }, ...products.map((p) => ({ value: p.id, label: p.name }))]}
          />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Qty" type="number" inputMode="decimal" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
            <Input
              label="Yield portions"
              type="number"
              inputMode="decimal"
              value={form.yield_portions}
              onChange={(e) => setForm({ ...form, yield_portions: e.target.value })}
            />
          </div>
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={() => setOpen(false)} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button
              disabled={!form.name || !form.menu_item_id || !form.product_id || createMutation.isPending}
              onClick={() => createMutation.mutate()}
              className="w-full sm:w-auto"
            >
              Save
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function MenuManagePage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [catOpen, setCatOpen] = useState(false)
  const [form, setForm] = useState({ name: '', price: '199', prep_time_minutes: '20', description: '' })
  const [catName, setCatName] = useState('')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['menu-items', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listMenuItems({ restaurant_id: restaurant.id })),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createMenuItem({
        restaurant_id: restaurant.id,
        name: form.name,
        price: Number(form.price),
        prep_time_minutes: Number(form.prep_time_minutes),
        description: form.description || null,
        is_available: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu-items'] })
      success('Menu item created')
      setOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Create failed'),
  })

  const catMutation = useMutation({
    mutationFn: () => createMenuCategory({ restaurant_id: restaurant.id, name: catName }),
    onSuccess: () => {
      success('Menu category created')
      setCatOpen(false)
      setCatName('')
    },
    onError: (err) => toastError(err?.message || 'Create failed'),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Menu"
        description="Menu items with prep time, availability, and recipe cost"
        entity="menu"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setCatOpen(true)} disabled={!restaurant?.id}>
              Add category
            </Button>
            <AddEntityButton label="Add menu item" onClick={() => setOpen(true)} disabled={!restaurant?.id} />
          </div>
        }
        columns={[
          { key: 'name', label: 'Item' },
          { key: 'menu_category', label: 'Category', render: (v) => v || '—' },
          { key: 'price', label: 'Price', render: (v) => formatCurrency(v) },
          {
            key: 'portion_cost',
            label: 'Food cost',
            render: (v) => (v != null ? formatCurrency(v) : '—'),
          },
          { key: 'prep_time_minutes', label: 'Prep (min)' },
          {
            key: 'is_available',
            label: 'Available',
            render: (v) => <StatusBadge status={v ? 'Active' : 'Inactive'} />,
          },
        ]}
      />

      <AppModal open={open} onClose={() => setOpen(false)} title="Add menu item" hideFooter>
        <div className="space-y-4">
          <Input label="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Price" type="number" inputMode="decimal" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            <Input
              label="Prep minutes"
              type="number"
              inputMode="numeric"
              value={form.prep_time_minutes}
              onChange={(e) => setForm({ ...form, prep_time_minutes: e.target.value })}
            />
          </div>
          <Textarea
            label="Description"
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={() => setOpen(false)} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button disabled={!form.name || createMutation.isPending} onClick={() => createMutation.mutate()} className="w-full sm:w-auto">
              Save
            </Button>
          </div>
        </div>
      </AppModal>

      <AppModal open={catOpen} onClose={() => setCatOpen(false)} title="Add menu category" hideFooter>
        <div className="space-y-4">
          <Input label="Name *" value={catName} onChange={(e) => setCatName(e.target.value)} />
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={() => setCatOpen(false)} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button disabled={!catName || catMutation.isPending} onClick={() => catMutation.mutate()} className="w-full sm:w-auto">
              Save
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function StockAlertsPage() {
  const { restaurant } = useOrg()
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['stock-alerts', restaurant?.id],
    queryFn: async () =>
      asList(await listStockAlerts(restaurant?.id ? { restaurant_id: restaurant.id } : {})),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Stock alerts"
        description="Low stock, out of stock, expiring, and expired"
        entity="stock-alerts"
        rows={data || []}
        loading={isLoading}
        columns={[
          {
            key: 'type',
            label: 'Type',
            render: (v) => <StatusBadge status={v} />,
          },
          { key: 'product', label: 'Product' },
          { key: 'branch', label: 'Branch' },
          { key: 'message', label: 'Message' },
          {
            key: 'quantity',
            label: 'Qty',
            render: (v) => (v != null ? formatNumber(v) : '—'),
          },
        ]}
      />
    </>
  )
}

export function StockTransfersPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ from_branch_id: '', to_branch_id: '', product_id: '', quantity: '5' })

  const { data: branches = [] } = useQuery({
    queryKey: ['branches', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listBranches({ restaurant_id: restaurant.id })),
  })
  const { data: products = [] } = useQuery({
    queryKey: ['products', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => asList(await listProducts({ restaurant_id: restaurant.id, limit: 200 })),
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['stock-transfers', restaurant?.id],
    queryFn: async () =>
      asList(await listStockTransfers(restaurant?.id ? { restaurant_id: restaurant.id } : {})),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createStockTransfer({
        from_branch_id: form.from_branch_id,
        to_branch_id: form.to_branch_id,
        items: [{ product_id: form.product_id, quantity: Number(form.quantity) }],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-transfers'] })
      success('Transfer draft created')
      setOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Create failed'),
  })

  const actionMutation = useMutation({
    mutationFn: async ({ id, action }) => {
      if (action === 'submit') return submitStockTransfer(id)
      if (action === 'approve') return approveStockTransfer(id)
      return completeStockTransfer(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-transfers'] })
      queryClient.invalidateQueries({ queryKey: ['inventory-items'] })
      success('Transfer updated')
    },
    onError: (err) => toastError(err?.message || 'Action failed'),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Stock transfers"
        description="Branch-to-branch transfer with approval workflow"
        entity="stock-transfers"
        rows={data || []}
        loading={isLoading}
        headerActions={<AddEntityButton label="New transfer" onClick={() => setOpen(true)} />}
        columns={[
          {
            key: 'transfer_number',
            label: 'Transfer #',
            render: (v) => <CodeChip>{v}</CodeChip>,
          },
          { key: 'from_branch', label: 'From' },
          { key: 'to_branch', label: 'To' },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
          {
            key: 'actions',
            label: '',
            render: (_v, r) => (
              <div className="flex flex-wrap gap-1">
                {r.status === 'DRAFT' && (
                  <Button size="sm" variant="secondary" onClick={() => actionMutation.mutate({ id: r.id, action: 'submit' })}>
                    Submit
                  </Button>
                )}
                {r.status === 'PENDING' && (
                  <Button size="sm" onClick={() => actionMutation.mutate({ id: r.id, action: 'approve' })}>
                    Approve
                  </Button>
                )}
                {r.status === 'APPROVED' && (
                  <Button size="sm" onClick={() => actionMutation.mutate({ id: r.id, action: 'complete' })}>
                    Complete
                  </Button>
                )}
              </div>
            ),
          },
        ]}
      />

      <AppModal open={open} onClose={() => setOpen(false)} title="Create transfer" hideFooter>
        <div className="space-y-4">
          <Select
            label="From branch *"
            value={form.from_branch_id}
            onChange={(e) => setForm({ ...form, from_branch_id: e.target.value })}
            options={[{ value: '', label: 'Select…' }, ...branches.map((b) => ({ value: b.id, label: b.name }))]}
          />
          <Select
            label="To branch *"
            value={form.to_branch_id}
            onChange={(e) => setForm({ ...form, to_branch_id: e.target.value })}
            options={[{ value: '', label: 'Select…' }, ...branches.map((b) => ({ value: b.id, label: b.name }))]}
          />
          <Select
            label="Product *"
            value={form.product_id}
            onChange={(e) => setForm({ ...form, product_id: e.target.value })}
            options={[{ value: '', label: 'Select…' }, ...products.map((p) => ({ value: p.id, label: p.name }))]}
          />
          <Input label="Quantity" type="number" inputMode="decimal" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={() => setOpen(false)} className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button
              disabled={
                !form.from_branch_id ||
                !form.to_branch_id ||
                !form.product_id ||
                createMutation.isPending
              }
              onClick={() => createMutation.mutate()}
              className="w-full sm:w-auto"
            >
              Create draft
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function InventoryTransactionsPage() {
  const { branch } = useOrg()
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['inventory-transactions', branch?.id],
    queryFn: async () =>
      asList(
        await listInventoryTransactions(branch?.id ? { branch_id: branch.id, limit: 200 } : { limit: 200 })
      ),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Inventory transactions"
        description="Purchase, sale, waste, damage, production, adjustment, transfer, return"
        entity="inventory-transactions"
        rows={data || []}
        loading={isLoading}
        columns={[
          { key: 'created_at', label: 'When', render: (v) => new Date(v).toLocaleString() },
          { key: 'transaction_type', label: 'Type', render: (v) => <StatusBadge status={v} /> },
          { key: 'product_name', label: 'Product' },
          { key: 'quantity', label: 'Qty', render: (v) => formatNumber(v) },
          { key: 'reference', label: 'Reference', render: (v) => v || '—' },
        ]}
      />
    </>
  )
}

export function WarehousesPage() {
  const { restaurant, branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    code: '',
    name: '',
    location: '',
    manager_name: '',
    capacity: '1000',
    branch_id: '',
  })

  const { data: branches = [] } = useQuery({
    queryKey: ['branches', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => {
      const res = await listBranches({ restaurant_id: restaurant.id })
      return res.data || []
    },
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['warehouses', restaurant?.id],
    queryFn: async () =>
      asList(await listWarehouses(restaurant?.id ? { restaurant_id: restaurant.id } : {})),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createWarehouse({
        restaurant_id: restaurant.id,
        branch_id: form.branch_id || branch?.id,
        code: form.code.trim(),
        name: form.name.trim(),
        location: form.location || null,
        manager_name: form.manager_name || null,
        capacity: Number(form.capacity || 0),
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warehouses'] })
      success('Warehouse created')
      setOpen(false)
      setForm({ code: '', name: '', location: '', manager_name: '', capacity: '1000', branch_id: '' })
    },
    onError: (err) => toastError(err?.message || 'Could not create warehouse'),
  })

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Warehouses"
        description="Branch storage locations with capacity and live stock"
        entity="warehouses"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add warehouse"
            onClick={() => {
              setForm((f) => ({ ...f, branch_id: branch?.id || branches[0]?.id || '' }))
              setOpen(true)
            }}
            disabled={!restaurant?.id}
          />
        }
        columns={[
          { key: 'code', label: 'Code', render: (v) => <CodeChip>{v}</CodeChip> },
          { key: 'name', label: 'Name' },
          { key: 'branch_name', label: 'Branch' },
          { key: 'location', label: 'Location', render: (v) => v || '—' },
          { key: 'manager_name', label: 'Manager', render: (v) => v || '—' },
          { key: 'current_stock', label: 'Stock', render: (v) => formatNumber(v) },
          { key: 'capacity', label: 'Capacity', render: (v) => formatNumber(v) },
          {
            key: 'utilization_percent',
            label: 'Util %',
            render: (v) => `${Number(v || 0).toFixed(0)}%`,
          },
          { key: 'status', label: 'Status' },
        ]}
      />
      <AppModal open={open} onClose={() => setOpen(false)} title="Add warehouse">
        <div className="space-y-3">
          <Select
            label="Branch *"
            value={form.branch_id || ''}
            onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
            options={[
              { value: '', label: 'Select…' },
              ...branches.map((b) => ({ value: b.id, label: b.name })),
            ]}
          />
          <Input
            label="Code *"
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value })}
            placeholder="MAIN"
          />
          <Input
            label="Name *"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Main cold storage"
          />
          <Input
            label="Location"
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
          />
          <Input
            label="Manager"
            value={form.manager_name}
            onChange={(e) => setForm({ ...form, manager_name: e.target.value })}
          />
          <Input
            label="Capacity"
            value={form.capacity}
            onChange={(e) => setForm({ ...form, capacity: e.target.value })}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={
                !form.code.trim() ||
                !form.name.trim() ||
                !(form.branch_id || branch?.id) ||
                createMutation.isPending
              }
              onClick={() => createMutation.mutate()}
            >
              Save
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function UnitsManagePage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [convOpen, setConvOpen] = useState(false)
  const [form, setForm] = useState({ code: '', name: '', symbol: '' })
  const [conv, setConv] = useState({ from_uom_id: '', to_uom_id: '', factor: '1000' })

  const { data: units = [], isLoading } = useQuery({
    queryKey: ['units', restaurant?.id],
    queryFn: async () => asList(await listUnits(restaurant?.id ? { restaurant_id: restaurant.id } : {})),
  })

  const { data: conversions = [] } = useQuery({
    queryKey: ['unit-conversions'],
    queryFn: async () => asList(await listUnitConversions()),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createUnit({
        restaurant_id: restaurant?.id || null,
        code: form.code.trim().toUpperCase(),
        name: form.name.trim(),
        symbol: form.symbol || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['units'] })
      success('Unit created')
      setOpen(false)
      setForm({ code: '', name: '', symbol: '' })
    },
    onError: (err) => toastError(err?.message || 'Could not create unit'),
  })

  const convMutation = useMutation({
    mutationFn: () =>
      createUnitConversion({
        from_uom_id: conv.from_uom_id,
        to_uom_id: conv.to_uom_id,
        factor: Number(conv.factor),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unit-conversions'] })
      success('Conversion created')
      setConvOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Could not create conversion'),
  })

  const seedMutation = useMutation({
    mutationFn: () => seedDefaultUnits(restaurant?.id ? { restaurant_id: restaurant.id } : {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['units'] })
      success('Default units seeded')
    },
    onError: (err) => toastError(err?.message || 'Seed failed'),
  })

  return (
    <>
      <EntityListPage
        title="Units of measure"
        description="Base units and conversion factors for recipes and procurement"
        entity="units"
        rows={units}
        loading={isLoading}
        headerActions={
          <div className="flex flex-wrap gap-2">
            <Button variant="ghost" onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
              Seed defaults
            </Button>
            <Button variant="ghost" onClick={() => setConvOpen(true)}>
              Add conversion
            </Button>
            <AddEntityButton label="Add unit" onClick={() => setOpen(true)} />
          </div>
        }
        columns={[
          { key: 'code', label: 'Code', render: (v) => <CodeChip>{v}</CodeChip> },
          { key: 'name', label: 'Name' },
          { key: 'symbol', label: 'Symbol', render: (v) => v || '—' },
          { key: 'is_active', label: 'Active', render: (v) => (v ? 'Yes' : 'No') },
        ]}
      />
      <div className="mt-6">
        <EntityListPage
          title="Unit conversions"
          description="1 from-unit = factor × to-unit"
          entity="unit-conversions"
          rows={conversions}
          loading={false}
          columns={[
            { key: 'from_code', label: 'From' },
            { key: 'to_code', label: 'To' },
            { key: 'factor', label: 'Factor', render: (v) => formatNumber(v) },
          ]}
        />
      </div>
      <AppModal open={open} onClose={() => setOpen(false)} title="Add unit">
        <div className="space-y-3">
          <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <Input label="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Symbol" value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!form.code.trim() || !form.name.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Save
            </Button>
          </div>
        </div>
      </AppModal>
      <AppModal open={convOpen} onClose={() => setConvOpen(false)} title="Add conversion">
        <div className="space-y-3">
          <Select
            label="From unit *"
            value={conv.from_uom_id}
            onChange={(e) => setConv({ ...conv, from_uom_id: e.target.value })}
            options={[
              { value: '', label: 'Select…' },
              ...units.map((u) => ({ value: u.id, label: `${u.code} — ${u.name}` })),
            ]}
          />
          <Select
            label="To unit *"
            value={conv.to_uom_id}
            onChange={(e) => setConv({ ...conv, to_uom_id: e.target.value })}
            options={[
              { value: '', label: 'Select…' },
              ...units.map((u) => ({ value: u.id, label: `${u.code} — ${u.name}` })),
            ]}
          />
          <Input
            label="Factor *"
            value={conv.factor}
            onChange={(e) => setConv({ ...conv, factor: e.target.value })}
          />
          <p className="text-xs text-slate-500">e.g. 1 KG = 1000 G → factor 1000</p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setConvOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!conv.from_uom_id || !conv.to_uom_id || !conv.factor || convMutation.isPending}
              onClick={() => convMutation.mutate()}
            >
              Save
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}
