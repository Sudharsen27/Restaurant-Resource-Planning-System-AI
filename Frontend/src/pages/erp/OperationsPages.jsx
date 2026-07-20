import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  ArrowUpRight,
  Armchair,
  Building2,
  FileText,
  GitBranch,
  LayoutGrid,
  SlidersHorizontal,
  Store,
  Boxes,
} from 'lucide-react'
import EntityListPage from '../../components/pages/EntityListPage'
import AppModal from '../../components/modals/AppModal'
import { AddEntityButton, CodeChip, RowActions, StatusBadge } from '../../components/erp/ErpTableUi'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { Input, Select, Textarea, FileUpload } from '../../components/forms/FormControls'
import { useOrg } from '../../context/OrgContext'
import { useToast } from '../../context/ToastContext'
import {
  createBranch,
  deleteBranch,
  listBranches,
  updateBranch,
} from '../../services/branchService'
import {
  createDepartment,
  createDiningArea,
  createTable,
  deleteDepartment,
  deleteDiningArea,
  deleteDocument,
  deleteTable,
  fetchOpsDashboard,
  getBusinessSettings,
  listDepartments,
  listDiningAreas,
  listDocuments,
  listTables,
  saveBusinessSettings,
  updateDepartment,
  updateDiningArea,
  updateTable,
  uploadDocument,
} from '../../services/operationsService'
import { getRestaurant } from '../../services/restaurantService'

const TABLE_STATUSES = [
  { value: 'AVAILABLE', label: 'Available' },
  { value: 'OCCUPIED', label: 'Occupied' },
  { value: 'RESERVED', label: 'Reserved' },
  { value: 'CLEANING', label: 'Cleaning' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
]

const DOC_TYPES = [
  { value: 'BUSINESS_LICENSE', label: 'Business License' },
  { value: 'GST_CERTIFICATE', label: 'GST Certificate' },
  { value: 'FSSAI_LICENSE', label: 'FSSAI License' },
  { value: 'OTHER', label: 'Other' },
]

const DEFAULT_DEPTS = ['Kitchen', 'Cash Counter', 'Inventory', 'Management', 'HR', 'Cleaning', 'Delivery']

const OPS_MODULES = [
  {
    to: '/branches',
    title: 'Branches',
    blurb: 'Locations under this restaurant',
    icon: GitBranch,
    accent: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
  },
  {
    to: '/dining-areas',
    title: 'Dining areas',
    blurb: 'Floors, outdoor, VIP zones',
    icon: LayoutGrid,
    accent: 'bg-sky-500/15 text-sky-600 dark:text-sky-400',
  },
  {
    to: '/tables',
    title: 'Tables',
    blurb: 'Capacity, status, QR links',
    icon: Armchair,
    accent: 'bg-amber-500/15 text-amber-700 dark:text-amber-400',
  },
  {
    to: '/departments',
    title: 'Departments',
    blurb: 'Kitchen, cash, inventory…',
    icon: Boxes,
    accent: 'bg-violet-500/15 text-violet-600 dark:text-violet-400',
  },
  {
    to: '/business-settings',
    title: 'Business settings',
    blurb: 'Tax, prefixes, policies',
    icon: SlidersHorizontal,
    accent: 'bg-slate-500/15 text-slate-700 dark:text-zinc-300',
  },
  {
    to: '/documents',
    title: 'Documents',
    blurb: 'GST, FSSAI, licenses',
    icon: FileText,
    accent: 'bg-rose-500/15 text-rose-600 dark:text-rose-400',
  },
  {
    to: '/restaurants',
    title: 'Restaurants',
    blurb: 'Brands and legal entities',
    icon: Store,
    accent: 'bg-teal-500/15 text-teal-700 dark:text-teal-400',
  },
  {
    to: '/restaurant-profile',
    title: 'Restaurant profile',
    blurb: 'GST, PAN, contact details',
    icon: Building2,
    accent: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400',
  },
]

function useBranchOptions() {
  const { restaurant } = useOrg()
  const { data: branches = [] } = useQuery({
    queryKey: ['branches', restaurant?.id, 'ops'],
    queryFn: async () =>
      (await listBranches(restaurant?.id ? { restaurant_id: restaurant.id } : {})).data || [],
    enabled: Boolean(restaurant?.id),
  })
  return { restaurant, branches }
}

export function OpsOverviewPage() {
  const { restaurant } = useOrg()
  const { data, isLoading } = useQuery({
    queryKey: ['ops-dashboard', restaurant?.id],
    queryFn: async () =>
      (await fetchOpsDashboard(restaurant?.id ? { restaurant_id: restaurant.id } : {})).data,
  })
  const s = data || {}
  const cards = [
    { label: 'Restaurants', value: s.restaurant_count, hint: 'Active brands' },
    { label: 'Branches', value: s.branch_count, hint: 'Locations' },
    { label: 'Dining areas', value: s.dining_area_count, hint: 'Zones' },
    { label: 'Tables', value: s.table_count, hint: 'Floor seats' },
    { label: 'Available', value: s.available_tables, hint: 'Ready now' },
    { label: 'Occupied', value: s.occupied_tables, hint: 'In service' },
    { label: 'Departments', value: s.department_count, hint: 'Org units' },
    { label: 'Employees', value: s.employee_count, hint: 'Staff on file' },
  ]

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-50 via-white to-slate-100 p-6 dark:border-zinc-800 dark:from-zinc-950 dark:via-black dark:to-zinc-900 sm:p-8">
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">
              Live · PostgreSQL
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Operations overview
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-500 dark:text-zinc-400">
              {restaurant?.name || 'All restaurants'} — master data for branches, floor layout,
              departments, and documents.
            </p>
          </div>
          <Link
            to="/restaurant-profile"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-800 transition hover:bg-slate-50 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:hover:bg-zinc-900"
          >
            <Building2 className="h-4 w-4" />
            View profile
          </Link>
        </div>
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Snapshot</h2>
          {isLoading && <span className="text-xs text-slate-400">Refreshing…</span>}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {cards.map((c) => (
            <div
              key={c.label}
              className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{c.label}</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900 dark:text-white">
                {c.value ?? '—'}
              </p>
              <p className="mt-1 text-xs text-slate-500">{c.hint}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          Manage modules
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {OPS_MODULES.map(({ to, title, blurb, icon: Icon, accent }) => (
            <Link
              key={to}
              to={to}
              className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-4 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-600"
            >
              <div className="flex items-start justify-between gap-3">
                <span className={`inline-flex rounded-xl p-2.5 ${accent}`}>
                  <Icon className="h-5 w-5" />
                </span>
                <ArrowUpRight className="h-4 w-4 text-slate-300 transition group-hover:text-slate-600 dark:text-zinc-600 dark:group-hover:text-zinc-300" />
              </div>
              <p className="mt-4 text-sm font-semibold text-slate-900 dark:text-zinc-100">{title}</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-zinc-400">{blurb}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

export function RestaurantDetailsPage() {
  const { restaurant } = useOrg()
  const { data, isLoading } = useQuery({
    queryKey: ['restaurant-detail', restaurant?.id],
    queryFn: async () => (await getRestaurant(restaurant.id)).data,
    enabled: Boolean(restaurant?.id),
  })
  if (!restaurant) return <p className="text-sm text-slate-500">Select a restaurant</p>
  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>
  const r = data || restaurant
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{r.name}</h1>
          <p className="text-sm text-slate-500">Restaurant profile · live PostgreSQL</p>
        </div>
        <Link to="/restaurants">
          <Button variant="secondary">Manage restaurants</Button>
        </Link>
      </div>
      <Card>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-sm">
          {[
            ['Code', r.code],
            ['Legal name', r.legal_name],
            ['GST', r.gst_number],
            ['PAN', r.pan_number],
            ['Email', r.email],
            ['Phone', r.phone],
            ['Website', r.website],
            ['City', r.city],
            ['State', r.state],
            ['Country', r.country],
            ['Timezone', r.timezone],
            ['Currency', r.currency],
            ['Status', r.status],
            ['Address', r.address],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs uppercase tracking-wide text-slate-400">{k}</dt>
              <dd className="mt-1 font-medium text-slate-800 dark:text-zinc-100">{v || '—'}</dd>
            </div>
          ))}
        </dl>
      </Card>
    </div>
  )
}

export function BranchesManagePage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const { restaurant, branches } = useBranchOptions()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', code: '', phone: '', email: '', address: '' })
  const [deleting, setDeleting] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['branches', restaurant?.id],
    queryFn: async () =>
      (await listBranches(restaurant?.id ? { restaurant_id: restaurant.id } : {})).data || [],
    enabled: Boolean(restaurant?.id),
  })

  const saveMut = useMutation({
    mutationFn: async () => {
      const payload = {
        restaurant_id: restaurant.id,
        name: form.name,
        code: form.code,
        phone: form.phone || null,
        email: form.email || null,
        address: form.address || null,
      }
      if (editing) return updateBranch(editing.id, payload)
      return createBranch(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      success(editing ? 'Branch updated' : 'Branch created')
      setOpen(false)
      setEditing(null)
    },
    onError: (e) => toastError(e.message),
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteBranch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches'] })
      success('Branch deleted')
      setDeleting(null)
    },
    onError: (e) => toastError(e.message),
  })

  return (
    <>
      <EntityListPage
        title="Branches"
        description={`Locations under ${restaurant?.name || 'restaurant'}`}
        entity="branches"
        rows={data}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add branch"
            onClick={() => {
              setEditing(null)
              setForm({ name: '', code: '', phone: '', email: '', address: '' })
              setOpen(true)
            }}
          />
        }
        columns={[
          { key: 'name', label: 'Branch' },
          { key: 'code', label: 'Code', render: (c) => <CodeChip code={c} /> },
          { key: 'phone', label: 'Phone' },
          { key: 'email', label: 'Email' },
          { key: 'status', label: 'Status', render: (s) => <StatusBadge status={s === 'open' ? 'active' : 'inactive'} /> },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <RowActions
                onEdit={() => {
                  setEditing(row)
                  setForm({
                    name: row.name || '',
                    code: row.code || '',
                    phone: row.phone || '',
                    email: row.email || '',
                    address: row.address || '',
                  })
                  setOpen(true)
                }}
                onDelete={() => setDeleting(row)}
              />
            ),
          },
        ]}
      />
      <AppModal
        open={open}
        title={editing ? 'Edit branch' : 'Add branch'}
        onClose={() => setOpen(false)}
        onConfirm={() => saveMut.mutate()}
        confirmLabel={editing ? 'Save' : 'Create'}
        busy={saveMut.isPending}
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Code *" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <Input label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <Input label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <Textarea
          className="mt-3"
          label="Address"
          rows={2}
          value={form.address}
          onChange={(e) => setForm({ ...form, address: e.target.value })}
        />
      </AppModal>
      <AppModal
        open={Boolean(deleting)}
        title="Delete branch"
        danger
        confirmLabel="Delete"
        onClose={() => setDeleting(null)}
        onConfirm={() => delMut.mutate(deleting.id)}
        busy={delMut.isPending}
      >
        Delete {deleting?.name}?
      </AppModal>
      {!branches.length && null}
    </>
  )
}

export function DiningAreasPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const { restaurant, branches } = useBranchOptions()
  const [branchId, setBranchId] = useState('')
  const effectiveBranch = branchId || branches[0]?.id || ''
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', description: '' })
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['dining-areas', effectiveBranch],
    queryFn: async () =>
      (await listDiningAreas({ branch_id: effectiveBranch })).data || [],
    enabled: Boolean(effectiveBranch),
  })

  const saveMut = useMutation({
    mutationFn: async () => {
      if (editing) return updateDiningArea(editing.id, form)
      return createDiningArea({ branch_id: effectiveBranch, ...form })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dining-areas'] })
      queryClient.invalidateQueries({ queryKey: ['ops-dashboard'] })
      success('Saved')
      setOpen(false)
    },
    onError: (e) => toastError(e.message),
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteDiningArea(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dining-areas'] })
      success('Deleted')
      setDeleting(null)
    },
    onError: (e) => toastError(e.message),
  })

  return (
    <>
      <div className="mb-3 max-w-xs">
        <Select
          label="Branch"
          value={effectiveBranch}
          onChange={(e) => setBranchId(e.target.value)}
          options={branches.map((b) => ({ value: b.id, label: b.name }))}
        />
      </div>
      <EntityListPage
        title="Dining areas"
        description={`Floors / zones for ${restaurant?.name || 'branch'}`}
        entity="dining-areas"
        rows={data}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add area"
            onClick={() => {
              setEditing(null)
              setForm({ name: '', description: '' })
              setOpen(true)
            }}
          />
        }
        columns={[
          { key: 'name', label: 'Area' },
          { key: 'description', label: 'Description' },
          { key: 'status', label: 'Status', render: (s) => <StatusBadge status={s} /> },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <RowActions
                onEdit={() => {
                  setEditing(row)
                  setForm({ name: row.name, description: row.description || '' })
                  setOpen(true)
                }}
                onDelete={() => setDeleting(row)}
              />
            ),
          },
        ]}
      />
      <AppModal open={open} title={editing ? 'Edit area' : 'Add dining area'} onClose={() => setOpen(false)} onConfirm={() => saveMut.mutate()} busy={saveMut.isPending}>
        <Input label="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ground Floor" />
        <Textarea className="mt-3" label="Description" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </AppModal>
      <AppModal open={Boolean(deleting)} title="Delete area" danger confirmLabel="Delete" onClose={() => setDeleting(null)} onConfirm={() => delMut.mutate(deleting.id)}>
        Delete {deleting?.name}?
      </AppModal>
    </>
  )
}

export function TablesPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const { branches } = useBranchOptions()
  const [branchId, setBranchId] = useState('')
  const effectiveBranch = branchId || branches[0]?.id || ''
  const { data: areas = [] } = useQuery({
    queryKey: ['dining-areas', effectiveBranch, 'for-tables'],
    queryFn: async () => (await listDiningAreas({ branch_id: effectiveBranch })).data || [],
    enabled: Boolean(effectiveBranch),
  })
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    table_number: '',
    capacity: 2,
    dining_area_id: '',
    status: 'AVAILABLE',
    qr_code: '',
  })
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['tables', effectiveBranch],
    queryFn: async () => (await listTables({ branch_id: effectiveBranch })).data || [],
    enabled: Boolean(effectiveBranch),
  })

  const saveMut = useMutation({
    mutationFn: async () => {
      const payload = {
        branch_id: effectiveBranch,
        dining_area_id: form.dining_area_id,
        table_number: form.table_number,
        capacity: Number(form.capacity) || 2,
        status: form.status,
        qr_code: form.qr_code || null,
      }
      if (editing) return updateTable(editing.id, payload)
      return createTable(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tables'] })
      queryClient.invalidateQueries({ queryKey: ['ops-dashboard'] })
      success('Table saved')
      setOpen(false)
    },
    onError: (e) => toastError(e.message),
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteTable(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tables'] })
      success('Deleted')
      setDeleting(null)
    },
    onError: (e) => toastError(e.message),
  })

  return (
    <>
      <div className="mb-3 max-w-xs">
        <Select
          label="Branch"
          value={effectiveBranch}
          onChange={(e) => setBranchId(e.target.value)}
          options={branches.map((b) => ({ value: b.id, label: b.name }))}
        />
      </div>
      <EntityListPage
        title="Tables"
        description="Floor tables with status and QR"
        entity="tables"
        rows={data}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add table"
            onClick={() => {
              setEditing(null)
              setForm({
                table_number: '',
                capacity: 2,
                dining_area_id: areas[0]?.id || '',
                status: 'AVAILABLE',
                qr_code: '',
              })
              setOpen(true)
            }}
          />
        }
        columns={[
          { key: 'table_number', label: 'Table #' },
          { key: 'dining_area_name', label: 'Area' },
          { key: 'capacity', label: 'Capacity' },
          {
            key: 'status',
            label: 'Status',
            render: (s) => <StatusBadge status={s === 'AVAILABLE' ? 'active' : 'inactive'} />,
          },
          { key: 'qr_code', label: 'QR' },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <RowActions
                onEdit={() => {
                  setEditing(row)
                  setForm({
                    table_number: row.table_number,
                    capacity: row.capacity,
                    dining_area_id: row.dining_area_id,
                    status: row.status,
                    qr_code: row.qr_code || '',
                  })
                  setOpen(true)
                }}
                onDelete={() => setDeleting(row)}
              />
            ),
          },
        ]}
      />
      <AppModal open={open} size="lg" title={editing ? 'Edit table' : 'Add table'} onClose={() => setOpen(false)} onConfirm={() => saveMut.mutate()} busy={saveMut.isPending}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="Table number *" value={form.table_number} onChange={(e) => setForm({ ...form, table_number: e.target.value })} />
          <Input label="Capacity" type="number" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} />
          <Select
            label="Dining area *"
            value={form.dining_area_id}
            onChange={(e) => setForm({ ...form, dining_area_id: e.target.value })}
            options={areas.map((a) => ({ value: a.id, label: a.name }))}
          />
          <Select
            label="Status"
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            options={TABLE_STATUSES}
          />
          <Input label="QR code" value={form.qr_code} onChange={(e) => setForm({ ...form, qr_code: e.target.value })} />
        </div>
        {!areas.length && (
          <p className="mt-2 text-xs text-amber-600">Create a dining area for this branch first.</p>
        )}
      </AppModal>
      <AppModal open={Boolean(deleting)} title="Delete table" danger confirmLabel="Delete" onClose={() => setDeleting(null)} onConfirm={() => delMut.mutate(deleting.id)}>
        Delete table {deleting?.table_number}?
      </AppModal>
    </>
  )
}

export function DepartmentsPage() {
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const { branches } = useBranchOptions()
  const [branchId, setBranchId] = useState('')
  const effectiveBranch = branchId || branches[0]?.id || ''
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', code: '', description: '' })
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['departments', effectiveBranch],
    queryFn: async () => (await listDepartments({ branch_id: effectiveBranch })).data || [],
    enabled: Boolean(effectiveBranch),
  })

  const saveMut = useMutation({
    mutationFn: async () => {
      if (editing) return updateDepartment(editing.id, form)
      return createDepartment({ branch_id: effectiveBranch, ...form })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      success('Saved')
      setOpen(false)
    },
    onError: (e) => toastError(e.message),
  })

  const seedMut = useMutation({
    mutationFn: async () => {
      for (const name of DEFAULT_DEPTS) {
        try {
          await createDepartment({ branch_id: effectiveBranch, name, code: name.slice(0, 3).toUpperCase() })
        } catch {
          /* skip duplicates */
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      success('Default departments seeded')
    },
    onError: (e) => toastError(e.message),
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteDepartment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setDeleting(null)
      success('Deleted')
    },
    onError: (e) => toastError(e.message),
  })

  return (
    <>
      <div className="mb-3 flex flex-wrap items-end gap-3">
        <div className="max-w-xs flex-1">
          <Select
            label="Branch"
            value={effectiveBranch}
            onChange={(e) => setBranchId(e.target.value)}
            options={branches.map((b) => ({ value: b.id, label: b.name }))}
          />
        </div>
        <Button variant="secondary" onClick={() => seedMut.mutate()} disabled={!effectiveBranch || seedMut.isPending}>
          Seed defaults
        </Button>
      </div>
      <EntityListPage
        title="Departments"
        description="Kitchen, Cash Counter, Inventory, …"
        entity="departments"
        rows={data}
        loading={isLoading}
        headerActions={
          <AddEntityButton
            label="Add department"
            onClick={() => {
              setEditing(null)
              setForm({ name: '', code: '', description: '' })
              setOpen(true)
            }}
          />
        }
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'code', label: 'Code', render: (c) => <CodeChip code={c} /> },
          { key: 'description', label: 'Description' },
          { key: 'status', label: 'Status', render: (s) => <StatusBadge status={s} /> },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <RowActions
                onEdit={() => {
                  setEditing(row)
                  setForm({ name: row.name, code: row.code || '', description: row.description || '' })
                  setOpen(true)
                }}
                onDelete={() => setDeleting(row)}
              />
            ),
          },
        ]}
      />
      <AppModal open={open} title={editing ? 'Edit department' : 'Add department'} onClose={() => setOpen(false)} onConfirm={() => saveMut.mutate()} busy={saveMut.isPending}>
        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
        </div>
        <Textarea className="mt-3" label="Description" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </AppModal>
      <AppModal open={Boolean(deleting)} title="Delete department" danger confirmLabel="Delete" onClose={() => setDeleting(null)} onConfirm={() => delMut.mutate(deleting.id)}>
        Delete {deleting?.name}?
      </AppModal>
    </>
  )
}

export function BusinessSettingsPage() {
  const { restaurant } = useOrg()
  const { success, error: toastError } = useToast()
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['business-settings', restaurant?.id],
    queryFn: async () => (await getBusinessSettings(restaurant.id)).data,
    enabled: Boolean(restaurant?.id),
  })
  const [form, setForm] = useState(null)
  const current = form || data || {}

  const saveMut = useMutation({
    mutationFn: () =>
      saveBusinessSettings(restaurant.id, {
        tax_rate: Number(current.tax_rate) || 0,
        currency: current.currency || 'INR',
        timezone: current.timezone || 'Asia/Kolkata',
        invoice_prefix: current.invoice_prefix || 'INV',
        order_prefix: current.order_prefix || 'ORD',
        receipt_footer: current.receipt_footer || null,
        policies: current.policies || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-settings'] })
      success('Settings saved')
      setForm(null)
    },
    onError: (e) => toastError(e.message),
  })

  if (!restaurant) return <p className="text-sm text-slate-500">Select a restaurant</p>
  if (isLoading && !data) return <p className="text-sm text-slate-500">Loading…</p>

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Business settings</h1>
        <p className="text-sm text-slate-500">{restaurant.name} · tax, prefixes, policies</p>
      </div>
      <Card>
        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="Tax rate %" value={current.tax_rate ?? 0} onChange={(e) => setForm({ ...current, tax_rate: e.target.value })} />
          <Input label="Currency" value={current.currency || ''} onChange={(e) => setForm({ ...current, currency: e.target.value })} />
          <Input label="Timezone" value={current.timezone || ''} onChange={(e) => setForm({ ...current, timezone: e.target.value })} />
          <Input label="Invoice prefix" value={current.invoice_prefix || ''} onChange={(e) => setForm({ ...current, invoice_prefix: e.target.value })} />
          <Input label="Order prefix" value={current.order_prefix || ''} onChange={(e) => setForm({ ...current, order_prefix: e.target.value })} />
        </div>
        <Textarea className="mt-3" label="Receipt footer" rows={2} value={current.receipt_footer || ''} onChange={(e) => setForm({ ...current, receipt_footer: e.target.value })} />
        <Textarea className="mt-3" label="Policies" rows={4} value={current.policies || ''} onChange={(e) => setForm({ ...current, policies: e.target.value })} />
        <div className="mt-4">
          <Button onClick={() => saveMut.mutate()} disabled={saveMut.isPending}>
            Save settings
          </Button>
        </div>
      </Card>
    </div>
  )
}

export function DocumentsPage() {
  const { restaurant } = useOrg()
  const { success, error: toastError } = useToast()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [docType, setDocType] = useState('OTHER')
  const [file, setFile] = useState(null)

  const { data = [], isLoading } = useQuery({
    queryKey: ['documents', restaurant?.id],
    queryFn: async () =>
      (await listDocuments({ restaurant_id: restaurant.id })).data || [],
    enabled: Boolean(restaurant?.id),
  })

  const uploadMut = useMutation({
    mutationFn: () =>
      uploadDocument({
        restaurantId: restaurant.id,
        title,
        documentType: docType,
        file,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      success('Document uploaded')
      setTitle('')
      setFile(null)
    },
    onError: (e) => toastError(e.message),
  })

  const delMut = useMutation({
    mutationFn: (id) => deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      success('Deleted')
    },
    onError: (e) => toastError(e.message),
  })

  if (!restaurant) return <p className="text-sm text-slate-500">Select a restaurant</p>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Documents</h1>
        <p className="text-sm text-slate-500">Licenses & certificates · metadata in PostgreSQL</p>
      </div>
      <Card title="Upload">
        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="Title *" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Select label="Type" value={docType} onChange={(e) => setDocType(e.target.value)} options={DOC_TYPES} />
        </div>
        <div className="mt-3">
          <FileUpload label="File" onChange={setFile} />
        </div>
        <Button
          className="mt-4"
          disabled={!title || !file || uploadMut.isPending}
          onClick={() => uploadMut.mutate()}
        >
          Upload
        </Button>
      </Card>
      <EntityListPage
        title="Stored documents"
        description={restaurant.name}
        entity="documents"
        rows={data}
        loading={isLoading}
        columns={[
          { key: 'title', label: 'Title' },
          { key: 'document_type', label: 'Type' },
          { key: 'file_name', label: 'File' },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <Button variant="danger" size="sm" onClick={() => delMut.mutate(row.id)}>
                Delete
              </Button>
            ),
          },
        ]}
      />
    </div>
  )
}
