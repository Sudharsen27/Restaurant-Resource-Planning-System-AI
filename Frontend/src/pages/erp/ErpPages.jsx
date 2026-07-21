import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import EntityListPage from '../../components/pages/EntityListPage'
import RestaurantFormModal from '../../components/erp/RestaurantFormModal'
import { AddEntityButton, CodeChip, RowActions, StatusBadge } from '../../components/erp/ErpTableUi'
import AppModal from '../../components/modals/AppModal'
import { formatCurrency } from '../../utils/format'
import {
  listRestaurants,
  createRestaurant,
  updateRestaurant,
  deleteRestaurant,
} from '../../services/restaurantService'
import { listBranches } from '../../services/branchService'
import { listCategories, createCategory } from '../../services/categoryService'
import { listProducts, createProduct, exportProductsCsv, importProductsCsv } from '../../services/productService'
import { listSuppliers, createSupplier } from '../../services/supplierService'
import { listCustomers, createCustomer, updateCustomer } from '../../services/customerService'
import { listEmployees, createEmployee } from '../../services/employeeService'
import { fetchCustomerProfile } from '../../services/crmHrmsService'
import { listOrders, updateOrder } from '../../services/orderService'
import { listInventoryItems } from '../../services/inventoryItemService'
import { adjustInventory } from '../../services/catalogService'
import { useOrg } from '../../context/OrgContext'
import { useToast } from '../../context/ToastContext'
import { Input, Select } from '../../components/forms/FormControls'
import Button from '../../components/ui/Button'

function invalidateRestaurantQueries(queryClient) {
  queryClient.invalidateQueries({ queryKey: ['restaurants'] })
  queryClient.invalidateQueries({ queryKey: ['branches'] })
}

export default function RestaurantsPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState('create')
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['restaurants'],
    queryFn: async () => {
      const res = await listRestaurants()
      return res.data || []
    },
  })

  const saveMutation = useMutation({
    mutationFn: async (payload) => {
      if (formMode === 'edit' && editing?.id) {
        return updateRestaurant(editing.id, payload)
      }
      return createRestaurant(payload)
    },
    onSuccess: () => {
      invalidateRestaurantQueries(queryClient)
      success(formMode === 'edit' ? 'Restaurant updated' : 'Restaurant created')
      setFormOpen(false)
      setEditing(null)
    },
    onError: (err) => {
      toastError(err?.message || 'Could not save restaurant')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteRestaurant(id),
    onSuccess: () => {
      invalidateRestaurantQueries(queryClient)
      success('Restaurant deleted')
      setDeleting(null)
    },
    onError: (err) => {
      toastError(err?.message || 'Could not delete restaurant')
    },
  })

  function openCreate() {
    setFormMode('create')
    setEditing(null)
    setFormOpen(true)
  }

  function openEdit(row) {
    setFormMode('edit')
    setEditing(row)
    setFormOpen(true)
  }

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load restaurants'}</p>
      )}
      <EntityListPage
        title="Restaurants"
        description="Manage restaurant brands and legal entities"
        entity="restaurants"
        rows={data || []}
        loading={isLoading}
        headerActions={<AddEntityButton label="Add restaurant" onClick={openCreate} />}
        columns={[
          {
            key: 'name',
            label: 'Restaurant',
            render: (name, row) => (
              <div className="min-w-[160px]">
                <p className="font-medium text-slate-900 dark:text-zinc-100">{name}</p>
                {row.legal_name ? (
                  <p className="mt-0.5 max-w-[220px] truncate text-xs text-slate-500">{row.legal_name}</p>
                ) : null}
              </div>
            ),
          },
          {
            key: 'code',
            label: 'Code',
            render: (code) => <CodeChip code={code} />,
          },
          {
            key: 'city',
            label: 'Location',
            render: (city, row) => (
              <div>
                <p>{city || '—'}</p>
                {row.phone ? <p className="mt-0.5 text-xs text-slate-500">{row.phone}</p> : null}
              </div>
            ),
          },
          {
            key: 'email',
            label: 'Contact',
            render: (email) => (
              <span className="text-slate-600 dark:text-zinc-400">{email || '—'}</span>
            ),
          },
          {
            key: 'status',
            label: 'Status',
            render: (status) => <StatusBadge status={status} />,
          },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <RowActions onEdit={() => openEdit(row)} onDelete={() => setDeleting(row)} />
            ),
          },
        ]}
      />

      <RestaurantFormModal
        open={formOpen}
        mode={formMode}
        initial={editing}
        busy={saveMutation.isPending}
        onClose={() => {
          if (saveMutation.isPending) return
          setFormOpen(false)
          setEditing(null)
        }}
        onSubmit={(payload) => saveMutation.mutate(payload)}
      />

      <AppModal
        open={Boolean(deleting)}
        title="Delete restaurant"
        danger
        confirmLabel="Delete"
        busy={deleteMutation.isPending}
        onClose={() => {
          if (deleteMutation.isPending) return
          setDeleting(null)
        }}
        onConfirm={() => deleting?.id && deleteMutation.mutate(deleting.id)}
      >
        <p>
          Delete <span className="font-semibold text-slate-900 dark:text-white">{deleting?.name}</span>{' '}
          <span className="font-mono text-xs text-slate-500">({deleting?.code})</span>? This removes it
          from active lists (soft delete in PostgreSQL).
        </p>
      </AppModal>
    </>
  )
}

export function BranchesPage() {
  const { restaurant } = useOrg()
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['branches', restaurant?.id],
    queryFn: async () => {
      const res = await listBranches(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load branches'}</p>
      )}
      <EntityListPage
        title="Branches"
        description="Locations under the selected restaurant"
        entity="branches"
        rows={data || []}
        loading={isLoading}
        columns={[
          { key: 'name', label: 'Branch' },
          { key: 'code', label: 'Code' },
          { key: 'status', label: 'Status' },
        ]}
      />
    </>
  )
}

export function CategoriesPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['categories', restaurant?.id],
    queryFn: async () => {
      const res = await listCategories(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createCategory({
        restaurant_id: restaurant.id,
        name: name.trim(),
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      success('Category created')
      setOpen(false)
      setName('')
    },
    onError: (err) => toastError(err?.message || 'Could not create category'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load categories'}</p>
      )}
      <EntityListPage
        title="Categories"
        description="Product / inventory categories (create your own for live demos)"
        entity="categories"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add category"
            onClick={() => setOpen(true)}
            disabled={!restaurant?.id}
          />
        }
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'slug', label: 'Slug' },
          { key: 'status', label: 'Status' },
        ]}
      />
      <AppModal open={open} onClose={() => setOpen(false)} title="Add category">
        <div className="space-y-3">
          <Input label="Name *" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Seafood" />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!name.trim() || createMutation.isPending}
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

export function ProductsPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    sku: '',
    unit: 'kg',
    unit_cost: '50',
    unit_price: '80',
    category_id: '',
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['categories', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => {
      const res = await listCategories({ restaurant_id: restaurant.id, limit: 200 })
      return res.data || []
    },
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['products', restaurant?.id],
    queryFn: async () => {
      const res = await listProducts(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createProduct({
        restaurant_id: restaurant.id,
        name: form.name.trim(),
        sku: form.sku.trim(),
        unit: form.unit || 'kg',
        unit_cost: Number(form.unit_cost),
        unit_price: Number(form.unit_price),
        category_id: form.category_id || null,
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      success('Product created')
      setOpen(false)
      setForm({ name: '', sku: '', unit: 'kg', unit_cost: '50', unit_price: '80', category_id: '' })
    },
    onError: (err) => toastError(err?.message || 'Could not create product'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load products'}</p>
      )}
      <EntityListPage
        title="Products"
        description="Create real SKUs — used by PO, stock, and recipes"
        entity="products"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              disabled={!restaurant?.id}
              onClick={async () => {
                try {
                  const blob = await exportProductsCsv(
                    restaurant?.id ? { restaurant_id: restaurant.id } : {},
                  )
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = 'products.csv'
                  a.click()
                  URL.revokeObjectURL(url)
                  success('Products exported')
                } catch (err) {
                  toastError(err?.message || 'Export failed')
                }
              }}
            >
              Export CSV
            </Button>
            <label className="inline-flex cursor-pointer items-center">
              <input
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                disabled={!restaurant?.id}
                onChange={async (e) => {
                  const file = e.target.files?.[0]
                  e.target.value = ''
                  if (!file || !restaurant?.id) return
                  try {
                    const res = await importProductsCsv(restaurant.id, file)
                    queryClient.invalidateQueries({ queryKey: ['products'] })
                    const d = res?.data || {}
                    success(`Import: ${d.created || 0} created, ${d.updated || 0} updated`)
                    if (d.errors?.length) toastError(d.errors.slice(0, 3).join('; '))
                  } catch (err) {
                    toastError(err?.message || 'Import failed')
                  }
                }}
              />
              <span className="inline-flex h-9 items-center rounded-lg border border-slate-200 px-3 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900">
                Import CSV
              </span>
            </label>
            <AddEntityButton
              label="Add product"
              onClick={() => setOpen(true)}
              disabled={!restaurant?.id}
            />
          </div>
        }
        columns={[
          { key: 'name', label: 'Product' },
          { key: 'sku', label: 'SKU' },
          { key: 'category', label: 'Category' },
          { key: 'unit_cost', label: 'Cost', render: (v) => formatCurrency(Number(v || 0)) },
          { key: 'price', label: 'Price', render: (v) => formatCurrency(Number(v)) },
          { key: 'status', label: 'Status' },
        ]}
      />
      <AppModal open={open} onClose={() => setOpen(false)} title="Add product">
        <div className="space-y-3">
          <Input
            label="Name *"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Interview Demo Chicken"
          />
          <Input
            label="SKU *"
            value={form.sku}
            onChange={(e) => setForm({ ...form, sku: e.target.value })}
            placeholder="DEMO-CHICKEN-01"
          />
          <Select
            label="Category"
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            options={[
              { value: '', label: 'Optional…' },
              ...categories.map((c) => ({ value: c.id, label: c.name })),
            ]}
          />
          <div className="grid grid-cols-3 gap-3">
            <Input label="Unit" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
            <Input
              label="Cost"
              value={form.unit_cost}
              onChange={(e) => setForm({ ...form, unit_cost: e.target.value })}
            />
            <Input
              label="Sell price"
              value={form.unit_price}
              onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!form.name.trim() || !form.sku.trim() || createMutation.isPending}
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

export function SuppliersPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    phone: '',
    category: 'Produce',
    gst_number: '',
    payment_terms: 'Net 15',
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['suppliers', restaurant?.id],
    queryFn: async () => {
      const res = await listSuppliers(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createSupplier({
        restaurant_id: restaurant.id,
        name: form.name.trim(),
        phone: form.phone || null,
        category: form.category || null,
        gst_number: form.gst_number || null,
        payment_terms: form.payment_terms || null,
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      success('Supplier created')
      setOpen(false)
      setForm({ name: '', phone: '', category: 'Produce', gst_number: '', payment_terms: 'Net 15' })
    },
    onError: (err) => toastError(err?.message || 'Could not create supplier'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load suppliers'}</p>
      )}
      <EntityListPage
        title="Suppliers"
        description="Vendor directory — create real suppliers for PO demos"
        entity="suppliers"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add supplier"
            onClick={() => setOpen(true)}
            disabled={!restaurant?.id}
          />
        }
        columns={[
          { key: 'name', label: 'Supplier' },
          { key: 'category', label: 'Category' },
          { key: 'gst_number', label: 'GST' },
          { key: 'leadDays', label: 'Lead days' },
          { key: 'status', label: 'Status' },
        ]}
      />
      <AppModal open={open} onClose={() => setOpen(false)} title="Add supplier">
        <div className="space-y-3">
          <Input
            label="Name *"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Interview Fresh Farms"
          />
          <Input label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <Input
            label="GST number"
            value={form.gst_number}
            onChange={(e) => setForm({ ...form, gst_number: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Category"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
            <Input
              label="Payment terms"
              value={form.payment_terms}
              onChange={(e) => setForm({ ...form, payment_terms: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!form.name.trim() || createMutation.isPending}
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

export function OrdersPage() {
  const { restaurant, branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['orders', restaurant?.id, branch?.id, statusFilter],
    queryFn: async () => {
      const res = await listOrders({
        ...(restaurant?.id ? { restaurant_id: restaurant.id } : {}),
        ...(branch?.id ? { branch_id: branch.id } : {}),
        ...(statusFilter ? { status: statusFilter } : {}),
      })
      return res.data || []
    },
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }) => updateOrder(id, { status }),
    onSuccess: () => {
      success('Order updated')
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
    onError: (e) => toastError(e.message),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load orders'}</p>
      )}
      <EntityListPage
        title="Orders"
        description="POS order ledger · dine-in / takeaway / delivery"
        entity="orders"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <div className="flex flex-wrap gap-2">
            <select
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All statuses</option>
              {['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'COMPLETED', 'CANCELLED'].map(
                (s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ),
              )}
            </select>
            <Link to="/pos">
              <Button>Open POS</Button>
            </Link>
            <Link to="/kitchen">
              <Button variant="secondary">Kitchen</Button>
            </Link>
          </div>
        }
        columns={[
          { key: 'id', label: 'Order' },
          { key: 'order_type', label: 'Type' },
          { key: 'table_number', label: 'Table', render: (v) => v || '—' },
          { key: 'customer', label: 'Customer' },
          { key: 'branch', label: 'Branch' },
          { key: 'total', label: 'Total', render: (v) => formatCurrency(Number(v)) },
          { key: 'status', label: 'Status' },
          {
            key: 'actions',
            label: '',
            render: (_, row) =>
              row.status_code !== 'COMPLETED' && row.status_code !== 'CANCELLED' ? (
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => statusMutation.mutate({ id: row.uuid, status: 'CANCELLED' })}
                >
                  Cancel
                </Button>
              ) : null,
          },
        ]}
      />
    </>
  )
}

export function StockPage() {
  const { restaurant, branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [adjustForm, setAdjustForm] = useState({
    product_id: '',
    quantity_delta: '1',
    transaction_type: 'ADJUSTMENT',
    notes: '',
  })

  const { data: products = [] } = useQuery({
    queryKey: ['products', restaurant?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => {
      const res = await listProducts({ restaurant_id: restaurant.id, limit: 200 })
      return res.data || []
    },
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['inventory-items', restaurant?.id],
    queryFn: async () => {
      const res = await listInventoryItems(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  const adjustMutation = useMutation({
    mutationFn: () =>
      adjustInventory({
        branch_id: branch.id,
        product_id: adjustForm.product_id,
        quantity_delta: Number(adjustForm.quantity_delta),
        transaction_type: adjustForm.transaction_type,
        notes: adjustForm.notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory-items'] })
      queryClient.invalidateQueries({ queryKey: ['inventory-transactions'] })
      queryClient.invalidateQueries({ queryKey: ['catalog-dashboard'] })
      success('Stock adjusted')
      setAdjustOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Adjust failed'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load stock'}</p>
      )}
      <EntityListPage
        title="Stock levels"
        description="On-hand, reserved, damaged, and available quantity by branch"
        entity="inventory-items"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Adjust stock"
            onClick={() => setAdjustOpen(true)}
            disabled={!branch?.id}
          />
        }
        columns={[
          { key: 'product', label: 'Product' },
          { key: 'branch', label: 'Branch' },
          { key: 'quantity_on_hand', label: 'On hand' },
          { key: 'reserved_quantity', label: 'Reserved' },
          { key: 'damaged_quantity', label: 'Damaged' },
          { key: 'available_stock', label: 'Available' },
          { key: 'reorder_level', label: 'Reorder' },
          { key: 'status', label: 'Status' },
        ]}
      />
      <AppModal open={adjustOpen} onClose={() => setAdjustOpen(false)} title="Adjust stock">
        <div className="space-y-3">
          <Select
            label="Product *"
            value={adjustForm.product_id}
            onChange={(e) => setAdjustForm({ ...adjustForm, product_id: e.target.value })}
            options={[
              { value: '', label: 'Select…' },
              ...products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` })),
            ]}
          />
          <Input
            label="Quantity delta (+/-) *"
            value={adjustForm.quantity_delta}
            onChange={(e) => setAdjustForm({ ...adjustForm, quantity_delta: e.target.value })}
          />
          <Select
            label="Type"
            value={adjustForm.transaction_type}
            onChange={(e) => setAdjustForm({ ...adjustForm, transaction_type: e.target.value })}
            options={[
              { value: 'ADJUSTMENT', label: 'Adjustment' },
              { value: 'WASTE', label: 'Waste' },
              { value: 'DAMAGE', label: 'Damage' },
              { value: 'PRODUCTION', label: 'Production' },
              { value: 'RETURN', label: 'Return' },
              { value: 'OPENING', label: 'Opening' },
            ]}
          />
          <Input
            label="Notes"
            value={adjustForm.notes}
            onChange={(e) => setAdjustForm({ ...adjustForm, notes: e.target.value })}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdjustOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!adjustForm.product_id || !adjustForm.quantity_delta || adjustMutation.isPending}
              onClick={() => adjustMutation.mutate()}
            >
              Post
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

const MEMBERSHIP_OPTIONS = [
  { value: 'BRONZE', label: 'Bronze' },
  { value: 'SILVER', label: 'Silver' },
  { value: 'GOLD', label: 'Gold' },
  { value: 'PLATINUM', label: 'Platinum' },
]

const EMPTY_CUSTOMER_FORM = {
  full_name: '',
  email: '',
  phone: '',
  birthday: '',
  address: '',
  allergies: '',
  notes: '',
  is_vip: false,
  membership_level: 'BRONZE',
  loyalty_points: '0',
}

export function CustomersPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState('create')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_CUSTOMER_FORM)
  const [profileId, setProfileId] = useState(null)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['customers', restaurant?.id],
    queryFn: async () => {
      const res = await listCustomers(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  const { data: profileRes, isLoading: profileLoading } = useQuery({
    queryKey: ['customer-profile', profileId],
    queryFn: async () => {
      const res = await fetchCustomerProfile(profileId)
      return res.data || res
    },
    enabled: Boolean(profileId),
  })

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        restaurant_id: restaurant.id,
        full_name: form.full_name.trim(),
        email: form.email || null,
        phone: form.phone || null,
        birthday: form.birthday || null,
        address: form.address || null,
        allergies: form.allergies || null,
        notes: form.notes || null,
        is_vip: form.is_vip,
        membership_level: form.membership_level,
        loyalty_points: Number(form.loyalty_points) || 0,
        is_active: true,
      }
      if (formMode === 'edit' && editing?.id) {
        return updateCustomer(editing.id, payload)
      }
      return createCustomer(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard'] })
      success(formMode === 'edit' ? 'Customer updated' : 'Customer created')
      setFormOpen(false)
      setEditing(null)
      setForm(EMPTY_CUSTOMER_FORM)
    },
    onError: (err) => toastError(err?.message || 'Could not save customer'),
  })

  function openCreate() {
    setFormMode('create')
    setEditing(null)
    setForm(EMPTY_CUSTOMER_FORM)
    setFormOpen(true)
  }

  function openEdit(row) {
    setFormMode('edit')
    setEditing(row)
    setForm({
      full_name: row.full_name || row.name || '',
      email: row.email || '',
      phone: row.phone || '',
      birthday: row.birthday || '',
      address: row.address || '',
      allergies: row.allergies || '',
      notes: row.notes || '',
      is_vip: Boolean(row.is_vip),
      membership_level: row.membership_level || 'BRONZE',
      loyalty_points: String(row.loyalty_points ?? 0),
    })
    setFormOpen(true)
  }

  const profile = profileRes?.customer ? profileRes : profileRes
  const profileCustomer = profile?.customer || profile

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load customers'}</p>
      )}
      <EntityListPage
        title="Customers"
        description="Guest profiles, VIP tags, and loyalty"
        entity="customers"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton label="Add customer" onClick={openCreate} disabled={!restaurant?.id} />
        }
        columns={[
          { key: 'name', label: 'Customer' },
          {
            key: 'is_vip',
            label: 'VIP',
            render: (v) => (v ? <StatusBadge status="VIP" /> : '—'),
          },
          {
            key: 'membership_level',
            label: 'Tier',
            render: (v) => (v ? <StatusBadge status={v} /> : '—'),
          },
          { key: 'visits', label: 'Visits' },
          { key: 'spend', label: 'Spend', render: (v) => formatCurrency(Number(v)) },
          { key: 'loyalty_points', label: 'Points' },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <div className="flex gap-1">
                <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => setProfileId(row.id)}>
                  Profile
                </Button>
                <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => openEdit(row)}>
                  Edit
                </Button>
              </div>
            ),
          },
        ]}
      />

      <AppModal open={formOpen} title={formMode === 'edit' ? 'Edit customer' : 'New customer'} onClose={() => setFormOpen(false)} hideFooter size="lg">
        <div className="space-y-4">
          <Input label="Full name" value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Email" type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            <Input label="Phone" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Birthday" type="date" value={form.birthday} onChange={(e) => setForm((f) => ({ ...f, birthday: e.target.value }))} />
            <Select label="Membership" value={form.membership_level} onChange={(e) => setForm((f) => ({ ...f, membership_level: e.target.value }))} options={MEMBERSHIP_OPTIONS} />
          </div>
          <Input label="Loyalty points" type="number" min="0" value={form.loyalty_points} onChange={(e) => setForm((f) => ({ ...f, loyalty_points: e.target.value }))} />
          <Input label="Address" value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
          <Input label="Allergies" value={form.allergies} onChange={(e) => setForm((f) => ({ ...f, allergies: e.target.value }))} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_vip} onChange={(e) => setForm((f) => ({ ...f, is_vip: e.target.checked }))} />
            VIP customer
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button disabled={!form.full_name.trim() || saveMutation.isPending} onClick={() => saveMutation.mutate()}>Save</Button>
          </div>
        </div>
      </AppModal>

      <AppModal open={Boolean(profileId)} title="Customer profile" onClose={() => setProfileId(null)} hideFooter size="xl">
        {profileLoading ? (
          <p className="text-sm text-slate-500">Loading profile…</p>
        ) : profileCustomer ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <p className="text-xs text-slate-500">Name</p>
                <p className="font-medium">{profileCustomer.full_name || profileCustomer.name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Tier / VIP</p>
                <p className="font-medium">
                  {profileCustomer.membership_level || '—'}
                  {profileCustomer.is_vip ? ' · VIP' : ''}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Points</p>
                <p className="font-medium">{profileCustomer.loyalty_points ?? 0}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Lifetime spend</p>
                <p className="font-medium">{formatCurrency(Number(profileCustomer.spend ?? 0))}</p>
              </div>
            </div>
            {profile?.order_timeline?.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-semibold">Recent orders</p>
                <ul className="divide-y divide-slate-100 dark:divide-zinc-800 rounded-lg border border-slate-200 dark:border-zinc-800">
                  {profile.order_timeline.slice(0, 5).map((o) => (
                    <li key={o.order_id} className="flex justify-between px-3 py-2 text-sm">
                      <span>{o.order_number}</span>
                      <span>{formatCurrency(Number(o.total))}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex justify-end">
              <Link to="/loyalty" className="text-sm text-emerald-600 hover:underline" onClick={() => setProfileId(null)}>
                View loyalty program →
              </Link>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Profile not available.</p>
        )}
      </AppModal>
    </>
  )
}

const EMPLOYEE_ROLES = [
  { value: 'CHEF', label: 'Chef' },
  { value: 'WAITER', label: 'Waiter' },
  { value: 'CASHIER', label: 'Cashier' },
  { value: 'MANAGER', label: 'Manager' },
  { value: 'SUPERVISOR', label: 'Supervisor' },
  { value: 'HR', label: 'HR' },
  { value: 'ACCOUNTANT', label: 'Accountant' },
]

const EMPLOYMENT_TYPES = [
  { value: 'FULL_TIME', label: 'Full time' },
  { value: 'PART_TIME', label: 'Part time' },
  { value: 'CONTRACT', label: 'Contract' },
]

export function EmployeesPage() {
  const { restaurant, branch, branches } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    branch_id: '',
    employee_code: '',
    full_name: '',
    role: 'WAITER',
    designation: '',
    monthly_salary: '',
    employment_type: 'FULL_TIME',
    email: '',
    phone: '',
  })

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['employees', restaurant?.id],
    queryFn: async () => {
      const res = await listEmployees(
        restaurant?.id ? { restaurant_id: restaurant.id } : {},
      )
      return res.data || []
    },
  })

  const branchOptions = (branches || []).map((b) => ({ value: b.id, label: b.name }))

  const createMutation = useMutation({
    mutationFn: () =>
      createEmployee({
        branch_id: form.branch_id || branch?.id,
        employee_code: form.employee_code.trim(),
        full_name: form.full_name.trim(),
        role: form.role,
        designation: form.designation || null,
        monthly_salary: Number(form.monthly_salary) || 0,
        employment_type: form.employment_type,
        email: form.email || null,
        phone: form.phone || null,
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      queryClient.invalidateQueries({ queryKey: ['hrms-dashboard'] })
      success('Employee created')
      setOpen(false)
      setForm({
        branch_id: '',
        employee_code: '',
        full_name: '',
        role: 'WAITER',
        designation: '',
        monthly_salary: '',
        employment_type: 'FULL_TIME',
        email: '',
        phone: '',
      })
    },
    onError: (err) => toastError(err?.message || 'Could not create employee'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load employees'}</p>
      )}
      <EntityListPage
        title="Employees"
        description="Workforce directory — designation, salary, employment type"
        entity="employees"
        rows={data || []}
        loading={isLoading}
        headerActions={
          <AddEntityButton label="Add employee" onClick={() => setOpen(true)} disabled={!branch?.id && !branches?.length} />
        }
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'role', label: 'Role', render: (v) => <StatusBadge status={v} /> },
          { key: 'designation', label: 'Designation' },
          {
            key: 'monthly_salary',
            label: 'Salary',
            render: (v) => formatCurrency(Number(v ?? 0)),
          },
          {
            key: 'employment_type',
            label: 'Type',
            render: (v) => <StatusBadge status={v} />,
          },
          { key: 'branch', label: 'Branch' },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
        ]}
      />

      <AppModal open={open} title="New employee" onClose={() => setOpen(false)} hideFooter size="lg">
        <div className="space-y-4">
          <Select
            label="Branch"
            value={form.branch_id || branch?.id || ''}
            onChange={(e) => setForm((f) => ({ ...f, branch_id: e.target.value }))}
            options={[{ value: '', label: 'Select branch' }, ...branchOptions]}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Employee code" value={form.employee_code} onChange={(e) => setForm((f) => ({ ...f, employee_code: e.target.value }))} />
            <Input label="Full name" value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Select label="Role" value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))} options={EMPLOYEE_ROLES} />
            <Select label="Employment type" value={form.employment_type} onChange={(e) => setForm((f) => ({ ...f, employment_type: e.target.value }))} options={EMPLOYMENT_TYPES} />
          </div>
          <Input label="Designation" value={form.designation} onChange={(e) => setForm((f) => ({ ...f, designation: e.target.value }))} />
          <Input label="Monthly salary (₹)" type="number" min="0" value={form.monthly_salary} onChange={(e) => setForm((f) => ({ ...f, monthly_salary: e.target.value }))} />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Email" type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            <Input label="Phone" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
            <Button
              disabled={!form.full_name.trim() || !form.employee_code.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Create
            </Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}
