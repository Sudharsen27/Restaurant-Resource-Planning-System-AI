import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CalendarDays,
  Clock,
  Gift,
  UserCheck,
  Users,
  Wallet,
} from 'lucide-react'
import EntityListPage from '../../components/pages/EntityListPage'
import AppModal from '../../components/modals/AppModal'
import { AddEntityButton, CodeChip, StatusBadge } from '../../components/erp/ErpTableUi'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { Input, Select, Textarea } from '../../components/forms/FormControls'
import { useOrg } from '../../context/OrgContext'
import { useToast } from '../../context/ToastContext'
import { formatCurrency } from '../../utils/format'
import { listCustomers } from '../../services/customerService'
import { listEmployees } from '../../services/employeeService'
import {
  assignShift,
  attendanceBreak,
  awardBirthdayBonus,
  clockIn,
  clockOut,
  createCoupon,
  createLeaveRequest,
  createReservation,
  createShiftTemplate,
  fetchCrmDashboard,
  fetchHrmsDashboard,
  fetchLoyaltyDashboard,
  fetchPayslipPrint,
  generatePayroll,
  getLoyaltyRules,
  listAttendance,
  listCoupons,
  listLeaveRequests,
  listLoyaltyTransactions,
  listPayrollRuns,
  listPayslips,
  listReservations,
  listShiftAssignments,
  listShiftTemplates,
  listWaitlist,
  lockPayrollRun,
  promoteWaitlistReservation,
  redeemLoyaltyPoints,
  reviewLeaveRequest,
  updateReservationStatus,
} from '../../services/crmHrmsService'

const CRM_MODULES = [
  { to: '/loyalty', title: 'Loyalty', blurb: 'Points, coupons, rewards', icon: Gift },
  { to: '/reservations', title: 'Reservations', blurb: 'Bookings & waitlist', icon: CalendarDays },
  { to: '/customers', title: 'Customers', blurb: 'Profiles & VIP tags', icon: Users },
]

const HRMS_MODULES = [
  { to: '/shifts', title: 'Shifts', blurb: 'Templates & rosters', icon: Clock },
  { to: '/attendance', title: 'Attendance', blurb: 'Clock in / out', icon: UserCheck },
  { to: '/leaves', title: 'Leave', blurb: 'Requests & approvals', icon: CalendarDays },
  { to: '/payroll', title: 'Payroll', blurb: 'Runs & payslips', icon: Wallet },
  { to: '/employees', title: 'Employees', blurb: 'Workforce directory', icon: Users },
]

const RESERVATION_STATUSES = [
  { value: 'CONFIRMED', label: 'Confirm' },
  { value: 'CHECKED_IN', label: 'Check in' },
  { value: 'COMPLETED', label: 'Complete' },
  { value: 'CANCELLED', label: 'Cancel' },
]

const SHIFT_TYPES = [
  { value: 'MORNING', label: 'Morning' },
  { value: 'AFTERNOON', label: 'Afternoon' },
  { value: 'NIGHT', label: 'Night' },
  { value: 'CUSTOM', label: 'Custom' },
]

const LEAVE_TYPES = [
  { value: 'ANNUAL', label: 'Annual' },
  { value: 'SICK', label: 'Sick' },
  { value: 'CASUAL', label: 'Casual' },
]

function asList(res) {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.data)) return res.data
  return []
}

function asData(res) {
  if (res && typeof res === 'object' && !Array.isArray(res) && res.data && !Array.isArray(res.data)) {
    return res.data
  }
  if (res?.data && typeof res.data === 'object' && !Array.isArray(res.data)) return res.data
  return res
}

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

function monthYearNow() {
  const d = new Date()
  return { year: d.getFullYear(), month: d.getMonth() + 1 }
}

function KpiGrid({ cards, loading }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => (
        <Card key={c.label} className="p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{c.label}</p>
          <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900 dark:text-white">
            {loading ? '…' : c.value ?? '—'}
          </p>
          {c.hint ? <p className="mt-1 text-xs text-slate-500">{c.hint}</p> : null}
        </Card>
      ))}
    </div>
  )
}

function ModuleGrid({ modules }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {modules.map(({ to, title, blurb, icon: Icon }) => (
        <Link
          key={to}
          to={to}
          className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-4 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-600"
        >
          <span className="inline-flex w-fit rounded-xl bg-rose-500/15 p-2.5 text-rose-600 dark:text-rose-400">
            <Icon className="h-5 w-5" />
          </span>
          <p className="mt-3 font-semibold text-slate-900 dark:text-white">{title}</p>
          <p className="mt-1 text-sm text-slate-500">{blurb}</p>
        </Link>
      ))}
    </div>
  )
}

function openPayslipPrintWindow(printData) {
  const d = asData(printData) || printData
  const html = `<!DOCTYPE html><html><head><title>Payslip</title>
<style>body{font-family:system-ui,sans-serif;padding:32px;max-width:640px;margin:0 auto}
h1{font-size:1.25rem;margin:0 0 8px}table{width:100%;border-collapse:collapse;margin-top:16px}
td{padding:6px 0;border-bottom:1px solid #eee}.label{color:#666}.total{font-weight:700;font-size:1.1rem}
@media print{body{padding:0}}</style></head><body>
<h1>${d.restaurant || 'Restaurant'} — Payslip</h1>
<p>${d.period || ''} · ${d.branch || ''}</p>
<p><strong>${d.employee?.name || ''}</strong> (${d.employee?.code || ''})</p>
<p>${d.employee?.designation || ''}</p>
<table>
<tr><td class="label">Basic salary</td><td>${formatCurrency(d.earnings?.basic_salary ?? 0)}</td></tr>
<tr><td class="label">Allowances</td><td>${formatCurrency(d.earnings?.allowances ?? 0)}</td></tr>
<tr><td class="label">Overtime</td><td>${formatCurrency(d.earnings?.overtime_pay ?? 0)}</td></tr>
<tr><td class="label">Bonus</td><td>${formatCurrency(d.earnings?.bonus ?? 0)}</td></tr>
<tr><td class="label">Deductions</td><td>${formatCurrency(d.deductions?.deductions ?? 0)}</td></tr>
<tr><td class="label">Tax</td><td>${formatCurrency(d.deductions?.tax ?? 0)}</td></tr>
<tr><td class="total">Net salary</td><td class="total">${formatCurrency(d.net_salary ?? 0)}</td></tr>
</table>
<p style="margin-top:24px;font-size:12px;color:#888">Days present: ${d.days_present ?? '—'} · OT minutes: ${d.overtime_minutes ?? '—'}</p>
<script>window.onload=function(){window.print()}</script>
</body></html>`
  const w = window.open('', '_blank', 'width=720,height=900')
  if (w) {
    w.document.write(html)
    w.document.close()
  }
}

export function CrmDashboardPage() {
  const { restaurant } = useOrg()
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['crm-dashboard', restaurant?.id],
    queryFn: async () => {
      const res = await fetchCrmDashboard({ restaurant_id: restaurant.id })
      return asData(res)
    },
    enabled: Boolean(restaurant?.id),
  })

  const cards = [
    { label: 'Total customers', value: data?.total_customers, hint: 'Active members' },
    { label: 'VIP customers', value: data?.vip_customers, hint: 'High-value guests' },
    { label: 'Reservations today', value: data?.reservations_today, hint: 'Booked for today' },
    { label: 'Waitlist', value: data?.waitlist_count, hint: 'Awaiting tables' },
    { label: 'Points outstanding', value: data?.loyalty_points_outstanding, hint: 'Unredeemed' },
  ]

  const upcoming = data?.upcoming_reservations || []

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-rose-50 via-white to-slate-100 p-6 dark:border-zinc-800 dark:from-zinc-950 dark:via-black dark:to-zinc-900 sm:p-8">
        <div className="relative">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-rose-600 dark:text-rose-400">
            Customer CRM
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            CRM overview
          </h1>
          <p className="mt-2 max-w-xl text-sm text-slate-500 dark:text-zinc-400">
            {restaurant?.name || 'Select a restaurant'} — loyalty, reservations, and guest insights.
          </p>
        </div>
      </div>

      {isError && (
        <p className="text-sm text-rose-600">
          {error?.message || 'Failed to load CRM dashboard'}{' '}
          <button type="button" className="underline" onClick={() => refetch()}>
            Retry
          </button>
        </p>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Snapshot</h2>
        <KpiGrid cards={cards} loading={isLoading} />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Modules</h2>
        <ModuleGrid modules={CRM_MODULES} />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          Today&apos;s reservations
        </h2>
        <Card>
          {isLoading ? (
            <p className="p-4 text-sm text-slate-500">Loading…</p>
          ) : upcoming.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">No reservations scheduled for today.</p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-zinc-800">
              {upcoming.map((r) => (
                <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">{r.guest_name}</p>
                    <p className="text-xs text-slate-500">
                      {r.reserved_time?.slice(0, 5)} · {r.guest_count} guests · {r.branch_name || '—'}
                    </p>
                  </div>
                  <StatusBadge status={r.status} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>
    </div>
  )
}

export function LoyaltyPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [couponOpen, setCouponOpen] = useState(false)
  const [couponForm, setCouponForm] = useState({
    code: '',
    description: '',
    discount_percent: '',
    discount_flat: '',
    min_order_amount: '0',
  })
  const [redeemForm, setRedeemForm] = useState({ customer_id: '', points: '', notes: '' })
  const [birthdayCustomerId, setBirthdayCustomerId] = useState('')

  const enabled = Boolean(restaurant?.id)

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['loyalty-rules', restaurant?.id],
    queryFn: async () => asData(await getLoyaltyRules(restaurant.id)),
    enabled,
  })

  const { data: dashboard } = useQuery({
    queryKey: ['loyalty-dashboard', restaurant?.id],
    queryFn: async () => asData(await fetchLoyaltyDashboard({ restaurant_id: restaurant.id })),
    enabled,
  })

  const { data: coupons = [], isLoading: couponsLoading } = useQuery({
    queryKey: ['coupons', restaurant?.id],
    queryFn: async () => asList(await listCoupons({ restaurant_id: restaurant.id })),
    enabled,
  })

  const { data: transactions = [], isLoading: txLoading } = useQuery({
    queryKey: ['loyalty-transactions', restaurant?.id],
    queryFn: async () => asList(await listLoyaltyTransactions({ restaurant_id: restaurant.id, limit: 50 })),
    enabled,
  })

  const { data: customers = [] } = useQuery({
    queryKey: ['customers', restaurant?.id, 'loyalty'],
    queryFn: async () => asList(await listCustomers({ restaurant_id: restaurant.id })),
    enabled,
  })

  const customerOptions = useMemo(
    () => customers.map((c) => ({ value: c.id, label: c.name || c.full_name })),
    [customers],
  )

  const couponMutation = useMutation({
    mutationFn: () =>
      createCoupon({
        restaurant_id: restaurant.id,
        code: couponForm.code.trim().toUpperCase(),
        description: couponForm.description || null,
        discount_percent: couponForm.discount_percent ? Number(couponForm.discount_percent) : null,
        discount_flat: couponForm.discount_flat ? Number(couponForm.discount_flat) : null,
        min_order_amount: Number(couponForm.min_order_amount) || 0,
        is_active: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['coupons'] })
      success('Coupon created')
      setCouponOpen(false)
      setCouponForm({ code: '', description: '', discount_percent: '', discount_flat: '', min_order_amount: '0' })
    },
    onError: (err) => toastError(err?.message || 'Could not create coupon'),
  })

  const redeemMutation = useMutation({
    mutationFn: () =>
      redeemLoyaltyPoints({
        customer_id: redeemForm.customer_id,
        points: Number(redeemForm.points),
        notes: redeemForm.notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loyalty-transactions'] })
      queryClient.invalidateQueries({ queryKey: ['loyalty-dashboard'] })
      success('Points redeemed')
      setRedeemForm({ customer_id: '', points: '', notes: '' })
    },
    onError: (err) => toastError(err?.message || 'Redeem failed'),
  })

  const birthdayMutation = useMutation({
    mutationFn: () => awardBirthdayBonus({ customer_id: birthdayCustomerId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loyalty-transactions'] })
      success('Birthday bonus awarded')
      setBirthdayCustomerId('')
    },
    onError: (err) => toastError(err?.message || 'Birthday bonus failed'),
  })

  const ruleCards = rules
    ? [
        { label: 'Points / ₹100', value: rules.points_per_100 },
        { label: 'Redeem value / pt', value: formatCurrency(rules.redeem_value_per_point) },
        { label: 'Birthday bonus', value: rules.birthday_bonus },
        { label: 'Min redeem', value: rules.min_redeem_points },
      ]
    : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Loyalty program</h1>
        <p className="mt-1 text-sm text-slate-500">Rules, coupons, redemptions, and transaction history</p>
      </div>

      <KpiGrid
        loading={!dashboard}
        cards={[
          { label: 'Members', value: dashboard?.total_members },
          { label: 'VIP', value: dashboard?.vip_count },
          { label: 'Points issued', value: dashboard?.points_issued },
          { label: 'Active coupons', value: dashboard?.active_coupons },
        ]}
      />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Program rules</h2>
        {rulesLoading ? (
          <p className="text-sm text-slate-500">Loading rules…</p>
        ) : rules ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {ruleCards.map((c) => (
              <Card key={c.label} className="p-4">
                <p className="text-xs text-slate-500">{c.label}</p>
                <p className="mt-1 text-lg font-semibold">{c.value}</p>
              </Card>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">No loyalty rules configured.</p>
        )}
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4 p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white">Redeem points</h3>
          <Select
            label="Customer"
            value={redeemForm.customer_id}
            onChange={(e) => setRedeemForm((f) => ({ ...f, customer_id: e.target.value }))}
            options={[{ value: '', label: 'Select customer' }, ...customerOptions]}
          />
          <Input
            label="Points"
            type="number"
            min="1"
            value={redeemForm.points}
            onChange={(e) => setRedeemForm((f) => ({ ...f, points: e.target.value }))}
          />
          <Input
            label="Notes"
            value={redeemForm.notes}
            onChange={(e) => setRedeemForm((f) => ({ ...f, notes: e.target.value }))}
          />
          <Button
            disabled={!redeemForm.customer_id || !redeemForm.points || redeemMutation.isPending}
            onClick={() => redeemMutation.mutate()}
          >
            Redeem
          </Button>
        </Card>

        <Card className="space-y-4 p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white">Birthday bonus</h3>
          <Select
            label="Customer"
            value={birthdayCustomerId}
            onChange={(e) => setBirthdayCustomerId(e.target.value)}
            options={[{ value: '', label: 'Select customer' }, ...customerOptions]}
          />
          <Button
            variant="secondary"
            disabled={!birthdayCustomerId || birthdayMutation.isPending}
            onClick={() => birthdayMutation.mutate()}
          >
            Award birthday bonus
          </Button>
        </Card>
      </div>

      <EntityListPage
        title="Coupons"
        description="Discount codes for members"
        entity="coupons"
        rows={coupons}
        loading={couponsLoading}
        headerActions={
          <AddEntityButton label="Create coupon" onClick={() => setCouponOpen(true)} disabled={!restaurant?.id} />
        }
        columns={[
          { key: 'code', label: 'Code', render: (v) => <CodeChip code={v} /> },
          { key: 'description', label: 'Description' },
          {
            key: 'discount_percent',
            label: 'Discount',
            render: (_v, row) =>
              row.discount_percent
                ? `${row.discount_percent}%`
                : row.discount_flat
                  ? formatCurrency(row.discount_flat)
                  : '—',
          },
          { key: 'redemption_count', label: 'Used' },
          {
            key: 'is_active',
            label: 'Status',
            render: (v) => <StatusBadge status={v ? 'ACTIVE' : 'INACTIVE'} />,
          },
        ]}
      />

      <EntityListPage
        title="Transactions"
        description="Recent loyalty activity"
        entity="loyalty-transactions"
        rows={transactions}
        loading={txLoading}
        columns={[
          { key: 'txn_type', label: 'Type', render: (v) => <StatusBadge status={v} /> },
          { key: 'points', label: 'Points' },
          { key: 'balance_after', label: 'Balance' },
          { key: 'notes', label: 'Notes' },
          {
            key: 'created_at',
            label: 'When',
            render: (v) => (v ? new Date(v).toLocaleString() : '—'),
          },
        ]}
      />

      <AppModal open={couponOpen} title="Create coupon" onClose={() => setCouponOpen(false)} hideFooter>
        <div className="space-y-4">
          <Input label="Code" value={couponForm.code} onChange={(e) => setCouponForm((f) => ({ ...f, code: e.target.value }))} />
          <Input label="Description" value={couponForm.description} onChange={(e) => setCouponForm((f) => ({ ...f, description: e.target.value }))} />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Discount %" type="number" value={couponForm.discount_percent} onChange={(e) => setCouponForm((f) => ({ ...f, discount_percent: e.target.value }))} />
            <Input label="Flat discount (₹)" type="number" value={couponForm.discount_flat} onChange={(e) => setCouponForm((f) => ({ ...f, discount_flat: e.target.value }))} />
          </div>
          <Input label="Min order (₹)" type="number" value={couponForm.min_order_amount} onChange={(e) => setCouponForm((f) => ({ ...f, min_order_amount: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCouponOpen(false)}>Cancel</Button>
            <Button disabled={!couponForm.code.trim() || couponMutation.isPending} onClick={() => couponMutation.mutate()}>Create</Button>
          </div>
        </div>
      </AppModal>
    </div>
  )
}

export function ReservationsPage() {
  const { restaurant, branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [createOpen, setCreateOpen] = useState(false)
  const [dateFilter, setDateFilter] = useState(todayISO())
  const [form, setForm] = useState({
    guest_name: '',
    guest_phone: '',
    guest_count: '2',
    reserved_date: todayISO(),
    reserved_time: '19:00',
    special_requests: '',
  })

  const branchId = branch?.id

  const { data: reservations = [], isLoading, isError, error } = useQuery({
    queryKey: ['reservations', restaurant?.id, branchId, dateFilter],
    queryFn: async () =>
      asList(
        await listReservations({
          restaurant_id: restaurant.id,
          branch_id: branchId,
          reserved_date: dateFilter,
        }),
      ),
    enabled: Boolean(restaurant?.id),
  })

  const { data: waitlist = [] } = useQuery({
    queryKey: ['waitlist', branchId, dateFilter],
    queryFn: async () => asList(await listWaitlist({ branch_id: branchId, reserved_date: dateFilter })),
    enabled: Boolean(branchId),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createReservation({
        restaurant_id: restaurant.id,
        branch_id: branchId,
        guest_name: form.guest_name.trim(),
        guest_phone: form.guest_phone || null,
        guest_count: Number(form.guest_count) || 2,
        reserved_date: form.reserved_date,
        reserved_time: `${form.reserved_time}:00`.slice(0, 8),
        special_requests: form.special_requests || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
      queryClient.invalidateQueries({ queryKey: ['waitlist'] })
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard'] })
      success('Reservation created')
      setCreateOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Could not create reservation'),
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, status }) => updateReservationStatus(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
      success('Status updated')
    },
    onError: (err) => toastError(err?.message || 'Status update failed'),
  })

  const promoteMutation = useMutation({
    mutationFn: (id) => promoteWaitlistReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
      queryClient.invalidateQueries({ queryKey: ['waitlist'] })
      success('Promoted from waitlist')
    },
    onError: (err) => toastError(err?.message || 'Promote failed'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load reservations'}</p>
      )}
      <EntityListPage
        title="Reservations"
        description={`${branch?.name || 'Branch'} — bookings and status`}
        entity="reservations"
        rows={reservations}
        loading={isLoading}
        headerActions={
          <div className="flex flex-wrap items-center gap-2">
            <Input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="w-auto" />
            <AddEntityButton label="New reservation" onClick={() => setCreateOpen(true)} disabled={!branchId} />
          </div>
        }
        columns={[
          { key: 'reservation_number', label: '#', render: (v) => <CodeChip code={v} /> },
          { key: 'guest_name', label: 'Guest' },
          { key: 'guest_count', label: 'Guests' },
          { key: 'reserved_time', label: 'Time', render: (v) => v?.slice(0, 5) || '—' },
          { key: 'table_number', label: 'Table' },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <div className="flex flex-wrap gap-1">
                {RESERVATION_STATUSES.filter((s) => s.value !== row.status).slice(0, 2).map((s) => (
                  <Button
                    key={s.value}
                    variant="ghost"
                    className="h-7 px-2 text-xs"
                    onClick={() => statusMutation.mutate({ id: row.id, status: s.value })}
                  >
                    {s.label}
                  </Button>
                ))}
              </div>
            ),
          },
        ]}
      />

      {waitlist.length > 0 && (
        <div className="mt-6">
          <EntityListPage
            title="Waitlist"
            description="Guests waiting for a table"
            entity="waitlist"
            rows={waitlist}
            columns={[
              { key: 'guest_name', label: 'Guest' },
              { key: 'guest_count', label: 'Guests' },
              { key: 'reserved_time', label: 'Time', render: (v) => v?.slice(0, 5) || '—' },
              {
                key: 'actions',
                label: '',
                sortable: false,
                render: (_v, row) => (
                  <Button
                    variant="secondary"
                    className="h-7 px-2 text-xs"
                    disabled={promoteMutation.isPending}
                    onClick={() => promoteMutation.mutate(row.id)}
                  >
                    Promote
                  </Button>
                ),
              },
            ]}
          />
        </div>
      )}

      <AppModal open={createOpen} title="New reservation" onClose={() => setCreateOpen(false)} hideFooter size="lg">
        <div className="space-y-4">
          <Input label="Guest name" value={form.guest_name} onChange={(e) => setForm((f) => ({ ...f, guest_name: e.target.value }))} />
          <Input label="Phone" value={form.guest_phone} onChange={(e) => setForm((f) => ({ ...f, guest_phone: e.target.value }))} />
          <div className="grid gap-3 sm:grid-cols-3">
            <Input label="Guests" type="number" min="1" value={form.guest_count} onChange={(e) => setForm((f) => ({ ...f, guest_count: e.target.value }))} />
            <Input label="Date" type="date" value={form.reserved_date} onChange={(e) => setForm((f) => ({ ...f, reserved_date: e.target.value }))} />
            <Input label="Time" type="time" value={form.reserved_time} onChange={(e) => setForm((f) => ({ ...f, reserved_time: e.target.value }))} />
          </div>
          <Textarea label="Special requests" value={form.special_requests} onChange={(e) => setForm((f) => ({ ...f, special_requests: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button disabled={!form.guest_name.trim() || !branchId || createMutation.isPending} onClick={() => createMutation.mutate()}>Create</Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function HrmsDashboardPage() {
  const { restaurant, branch } = useOrg()
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['hrms-dashboard', restaurant?.id, branch?.id],
    queryFn: async () =>
      asData(
        await fetchHrmsDashboard({
          restaurant_id: restaurant?.id,
          branch_id: branch?.id,
        }),
      ),
    enabled: Boolean(restaurant?.id),
  })

  const cards = [
    { label: 'Employees', value: data?.total_employees, hint: 'On file' },
    { label: 'On duty today', value: data?.on_duty_today, hint: 'Clocked in' },
    { label: 'Pending leave', value: data?.pending_leave_requests, hint: 'Awaiting review' },
    { label: 'Open payroll', value: data?.open_payroll_runs, hint: 'Draft runs' },
  ]

  const recentLeave = data?.recent_leave_requests || []

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-indigo-50 via-white to-slate-100 p-6 dark:border-zinc-800 dark:from-zinc-950 dark:via-black dark:to-zinc-900 sm:p-8">
        <div className="relative">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-indigo-600 dark:text-indigo-400">
            Human resources
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            HRMS overview
          </h1>
          <p className="mt-2 max-w-xl text-sm text-slate-500 dark:text-zinc-400">
            {restaurant?.name || 'Select a restaurant'} — shifts, attendance, leave, and payroll.
          </p>
        </div>
      </div>

      {isError && (
        <p className="text-sm text-rose-600">
          {error?.message || 'Failed to load HRMS dashboard'}{' '}
          <button type="button" className="underline" onClick={() => refetch()}>Retry</button>
        </p>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Snapshot</h2>
        <KpiGrid cards={cards} loading={isLoading} />
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Modules</h2>
        <ModuleGrid modules={HRMS_MODULES} />
      </section>

      {recentLeave.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Recent leave requests</h2>
          <Card>
            <ul className="divide-y divide-slate-100 dark:divide-zinc-800">
              {recentLeave.map((r) => (
                <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                  <div>
                    <p className="font-medium">{r.employee_name || 'Employee'}</p>
                    <p className="text-xs text-slate-500">
                      {r.leave_type} · {r.start_date} → {r.end_date}
                    </p>
                  </div>
                  <StatusBadge status={r.status} />
                </li>
              ))}
            </ul>
          </Card>
        </section>
      )}
    </div>
  )
}

export function ShiftsPage() {
  const { branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [templateOpen, setTemplateOpen] = useState(false)
  const [assignOpen, setAssignOpen] = useState(false)
  const [weekStart, setWeekStart] = useState(todayISO())
  const [templateForm, setTemplateForm] = useState({
    code: '',
    name: '',
    shift_type: 'MORNING',
    start_time: '09:00',
    end_time: '17:00',
    break_minutes: '30',
  })
  const [assignForm, setAssignForm] = useState({
    employee_id: '',
    shift_template_id: '',
    work_date: todayISO(),
  })

  const branchId = branch?.id

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['shift-templates', branchId],
    queryFn: async () => asList(await listShiftTemplates({ branch_id: branchId })),
    enabled: Boolean(branchId),
  })

  const { data: assignments = [], isLoading: assignLoading } = useQuery({
    queryKey: ['shift-assignments', branchId, weekStart],
    queryFn: async () => asList(await listShiftAssignments({ branch_id: branchId, week_start: weekStart })),
    enabled: Boolean(branchId),
  })

  const { data: employees = [] } = useQuery({
    queryKey: ['employees', branch?.restaurant_id, 'shifts'],
    queryFn: async () => {
      const res = await listEmployees(branch?.restaurant_id ? { restaurant_id: branch.restaurant_id } : {})
      return res.data || []
    },
    enabled: Boolean(branch?.restaurant_id),
  })

  const employeeOptions = employees.map((e) => ({ value: e.id, label: e.name || e.full_name }))
  const templateOptions = templates.map((t) => ({ value: t.id, label: `${t.name} (${t.start_time?.slice(0, 5)}–${t.end_time?.slice(0, 5)})` }))

  const templateMutation = useMutation({
    mutationFn: () =>
      createShiftTemplate({
        branch_id: branchId,
        code: templateForm.code.trim(),
        name: templateForm.name.trim(),
        shift_type: templateForm.shift_type,
        start_time: `${templateForm.start_time}:00`.slice(0, 8),
        end_time: `${templateForm.end_time}:00`.slice(0, 8),
        break_minutes: Number(templateForm.break_minutes) || 30,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shift-templates'] })
      success('Shift template created')
      setTemplateOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Could not create template'),
  })

  const assignMutation = useMutation({
    mutationFn: () =>
      assignShift({
        branch_id: branchId,
        employee_id: assignForm.employee_id,
        shift_template_id: assignForm.shift_template_id,
        work_date: assignForm.work_date,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shift-assignments'] })
      success('Shift assigned')
      setAssignOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Could not assign shift'),
  })

  return (
    <div className="space-y-6">
      <EntityListPage
        title="Shift templates"
        description={`${branch?.name || 'Branch'} — recurring shift definitions`}
        entity="shift-templates"
        rows={templates}
        loading={templatesLoading}
        headerActions={
          <AddEntityButton label="Add template" onClick={() => setTemplateOpen(true)} disabled={!branchId} />
        }
        columns={[
          { key: 'code', label: 'Code', render: (v) => <CodeChip code={v} /> },
          { key: 'name', label: 'Name' },
          { key: 'shift_type', label: 'Type', render: (v) => <StatusBadge status={v} /> },
          {
            key: 'start_time',
            label: 'Hours',
            render: (_v, row) => `${row.start_time?.slice(0, 5) || '—'} – ${row.end_time?.slice(0, 5) || '—'}`,
          },
          { key: 'break_minutes', label: 'Break (min)' },
        ]}
      />

      <EntityListPage
        title="Assignments"
        description="Weekly roster"
        entity="shift-assignments"
        rows={assignments}
        loading={assignLoading}
        headerActions={
          <div className="flex flex-wrap items-center gap-2">
            <Input type="date" value={weekStart} onChange={(e) => setWeekStart(e.target.value)} className="w-auto" />
            <AddEntityButton label="Assign shift" onClick={() => setAssignOpen(true)} disabled={!branchId} />
          </div>
        }
        columns={[
          { key: 'work_date', label: 'Date' },
          { key: 'employee_name', label: 'Employee' },
          { key: 'shift_name', label: 'Shift' },
          { key: 'notes', label: 'Notes' },
        ]}
      />

      <AppModal open={templateOpen} title="New shift template" onClose={() => setTemplateOpen(false)} hideFooter>
        <div className="space-y-4">
          <Input label="Code" value={templateForm.code} onChange={(e) => setTemplateForm((f) => ({ ...f, code: e.target.value }))} />
          <Input label="Name" value={templateForm.name} onChange={(e) => setTemplateForm((f) => ({ ...f, name: e.target.value }))} />
          <Select label="Type" value={templateForm.shift_type} onChange={(e) => setTemplateForm((f) => ({ ...f, shift_type: e.target.value }))} options={SHIFT_TYPES} />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Start" type="time" value={templateForm.start_time} onChange={(e) => setTemplateForm((f) => ({ ...f, start_time: e.target.value }))} />
            <Input label="End" type="time" value={templateForm.end_time} onChange={(e) => setTemplateForm((f) => ({ ...f, end_time: e.target.value }))} />
          </div>
          <Input label="Break (minutes)" type="number" value={templateForm.break_minutes} onChange={(e) => setTemplateForm((f) => ({ ...f, break_minutes: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setTemplateOpen(false)}>Cancel</Button>
            <Button disabled={!templateForm.code || !templateForm.name || templateMutation.isPending} onClick={() => templateMutation.mutate()}>Create</Button>
          </div>
        </div>
      </AppModal>

      <AppModal open={assignOpen} title="Assign shift" onClose={() => setAssignOpen(false)} hideFooter>
        <div className="space-y-4">
          <Select label="Employee" value={assignForm.employee_id} onChange={(e) => setAssignForm((f) => ({ ...f, employee_id: e.target.value }))} options={[{ value: '', label: 'Select' }, ...employeeOptions]} />
          <Select label="Template" value={assignForm.shift_template_id} onChange={(e) => setAssignForm((f) => ({ ...f, shift_template_id: e.target.value }))} options={[{ value: '', label: 'Select' }, ...templateOptions]} />
          <Input label="Work date" type="date" value={assignForm.work_date} onChange={(e) => setAssignForm((f) => ({ ...f, work_date: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAssignOpen(false)}>Cancel</Button>
            <Button disabled={!assignForm.employee_id || !assignForm.shift_template_id || assignMutation.isPending} onClick={() => assignMutation.mutate()}>Assign</Button>
          </div>
        </div>
      </AppModal>
    </div>
  )
}

export function AttendancePage() {
  const { branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [selectedEmployee, setSelectedEmployee] = useState('')
  const workDate = todayISO()
  const branchId = branch?.id

  const { data: employees = [] } = useQuery({
    queryKey: ['employees', branch?.restaurant_id, 'attendance'],
    queryFn: async () => {
      const res = await listEmployees(branch?.restaurant_id ? { restaurant_id: branch.restaurant_id } : {})
      return res.data || []
    },
    enabled: Boolean(branch?.restaurant_id),
  })

  const employeeOptions = employees.map((e) => ({ value: e.id, label: e.name || e.full_name }))

  const { data: records = [], isLoading, isError, error } = useQuery({
    queryKey: ['attendance', branchId, workDate],
    queryFn: async () => asList(await listAttendance({ branch_id: branchId, work_date: workDate })),
    enabled: Boolean(branchId),
  })

  const clockInMutation = useMutation({
    mutationFn: () => clockIn({ employee_id: selectedEmployee, branch_id: branchId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] })
      queryClient.invalidateQueries({ queryKey: ['hrms-dashboard'] })
      success('Clocked in')
    },
    onError: (err) => toastError(err?.message || 'Clock in failed'),
  })

  const clockOutMutation = useMutation({
    mutationFn: () => clockOut({ employee_id: selectedEmployee }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] })
      success('Clocked out')
    },
    onError: (err) => toastError(err?.message || 'Clock out failed'),
  })

  const breakMutation = useMutation({
    mutationFn: (action) => attendanceBreak({ employee_id: selectedEmployee, action }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] })
      success('Break updated')
    },
    onError: (err) => toastError(err?.message || 'Break action failed'),
  })

  return (
    <>
      {isError && (
        <p className="mb-3 text-sm text-rose-600">{error?.message || 'Failed to load attendance'}</p>
      )}

      <Card className="mb-6 space-y-4 p-4">
        <h2 className="font-semibold text-slate-900 dark:text-white">Clock in / out</h2>
        <Select
          label="Employee"
          value={selectedEmployee}
          onChange={(e) => setSelectedEmployee(e.target.value)}
          options={[{ value: '', label: 'Select employee' }, ...employeeOptions]}
        />
        <div className="flex flex-wrap gap-2">
          <Button disabled={!selectedEmployee || !branchId || clockInMutation.isPending} onClick={() => clockInMutation.mutate()}>
            Clock in
          </Button>
          <Button variant="secondary" disabled={!selectedEmployee || clockOutMutation.isPending} onClick={() => clockOutMutation.mutate()}>
            Clock out
          </Button>
          <Button variant="ghost" disabled={!selectedEmployee || breakMutation.isPending} onClick={() => breakMutation.mutate('start')}>
            Start break
          </Button>
          <Button variant="ghost" disabled={!selectedEmployee || breakMutation.isPending} onClick={() => breakMutation.mutate('end')}>
            End break
          </Button>
        </div>
      </Card>

      <EntityListPage
        title="Today&apos;s attendance"
        description={`${branch?.name || 'Branch'} · ${workDate}`}
        entity="attendance"
        rows={records}
        loading={isLoading}
        columns={[
          { key: 'employee_name', label: 'Employee' },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
          {
            key: 'clock_in',
            label: 'In',
            render: (v) => (v ? new Date(v).toLocaleTimeString() : '—'),
          },
          {
            key: 'clock_out',
            label: 'Out',
            render: (v) => (v ? new Date(v).toLocaleTimeString() : '—'),
          },
          { key: 'late_minutes', label: 'Late (min)' },
          { key: 'overtime_minutes', label: 'OT (min)' },
        ]}
      />
    </>
  )
}

export function LeavesPage() {
  const { branch } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const [requestOpen, setRequestOpen] = useState(false)
  const [form, setForm] = useState({
    employee_id: '',
    leave_type: 'ANNUAL',
    start_date: todayISO(),
    end_date: todayISO(),
    reason: '',
  })

  const branchId = branch?.id

  const { data: employees = [] } = useQuery({
    queryKey: ['employees', branch?.restaurant_id, 'leaves'],
    queryFn: async () => {
      const res = await listEmployees(branch?.restaurant_id ? { restaurant_id: branch.restaurant_id } : {})
      return res.data || []
    },
    enabled: Boolean(branch?.restaurant_id),
  })

  const employeeOptions = employees.map((e) => ({ value: e.id, label: e.name || e.full_name }))

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ['leave-requests', branchId, 'PENDING'],
    queryFn: async () => asList(await listLeaveRequests({ branch_id: branchId, status: 'PENDING' })),
    enabled: Boolean(branchId),
  })

  const requestMutation = useMutation({
    mutationFn: () =>
      createLeaveRequest({
        employee_id: form.employee_id,
        leave_type: form.leave_type,
        start_date: form.start_date,
        end_date: form.end_date,
        reason: form.reason || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave-requests'] })
      queryClient.invalidateQueries({ queryKey: ['hrms-dashboard'] })
      success('Leave request submitted')
      setRequestOpen(false)
    },
    onError: (err) => toastError(err?.message || 'Could not submit leave'),
  })

  const reviewMutation = useMutation({
    mutationFn: ({ id, status }) => reviewLeaveRequest(id, { status, review_notes: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave-requests'] })
      queryClient.invalidateQueries({ queryKey: ['hrms-dashboard'] })
      success('Leave reviewed')
    },
    onError: (err) => toastError(err?.message || 'Review failed'),
  })

  return (
    <>
      <EntityListPage
        title="Pending leave requests"
        description="Approve or reject employee leave"
        entity="leave-requests"
        rows={pending}
        loading={isLoading}
        headerActions={
          <AddEntityButton label="Request leave" onClick={() => setRequestOpen(true)} />
        }
        columns={[
          { key: 'employee_name', label: 'Employee' },
          { key: 'leave_type', label: 'Type', render: (v) => <StatusBadge status={v} /> },
          { key: 'start_date', label: 'From' },
          { key: 'end_date', label: 'To' },
          { key: 'days', label: 'Days' },
          { key: 'reason', label: 'Reason' },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <div className="flex gap-1">
                <Button variant="secondary" className="h-7 px-2 text-xs" onClick={() => reviewMutation.mutate({ id: row.id, status: 'APPROVED' })}>
                  Approve
                </Button>
                <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => reviewMutation.mutate({ id: row.id, status: 'REJECTED' })}>
                  Reject
                </Button>
              </div>
            ),
          },
        ]}
      />

      <AppModal open={requestOpen} title="Request leave" onClose={() => setRequestOpen(false)} hideFooter>
        <div className="space-y-4">
          <Select label="Employee" value={form.employee_id} onChange={(e) => setForm((f) => ({ ...f, employee_id: e.target.value }))} options={[{ value: '', label: 'Select' }, ...employeeOptions]} />
          <Select label="Leave type" value={form.leave_type} onChange={(e) => setForm((f) => ({ ...f, leave_type: e.target.value }))} options={LEAVE_TYPES} />
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Start date" type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} />
            <Input label="End date" type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} />
          </div>
          <Textarea label="Reason" value={form.reason} onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setRequestOpen(false)}>Cancel</Button>
            <Button disabled={!form.employee_id || requestMutation.isPending} onClick={() => requestMutation.mutate()}>Submit</Button>
          </div>
        </div>
      </AppModal>
    </>
  )
}

export function PayrollPage() {
  const { restaurant } = useOrg()
  const queryClient = useQueryClient()
  const { success, error: toastError } = useToast()
  const initial = monthYearNow()
  const [periodYear, setPeriodYear] = useState(String(initial.year))
  const [periodMonth, setPeriodMonth] = useState(String(initial.month))
  const [selectedRunId, setSelectedRunId] = useState('')

  const enabled = Boolean(restaurant?.id)

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['payroll-runs', restaurant?.id],
    queryFn: async () => asList(await listPayrollRuns({ restaurant_id: restaurant.id })),
    enabled,
  })

  const { data: payslips = [], isLoading: payslipsLoading } = useQuery({
    queryKey: ['payslips', selectedRunId],
    queryFn: async () => asList(await listPayslips(selectedRunId)),
    enabled: Boolean(selectedRunId),
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      generatePayroll({
        restaurant_id: restaurant.id,
        period_year: Number(periodYear),
        period_month: Number(periodMonth),
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
      const run = asData(res)
      if (run?.id) setSelectedRunId(run.id)
      success('Payroll generated')
    },
    onError: (err) => toastError(err?.message || 'Generate failed'),
  })

  const lockMutation = useMutation({
    mutationFn: (runId) => lockPayrollRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll-runs'] })
      success('Payroll run locked')
    },
    onError: (err) => toastError(err?.message || 'Lock failed'),
  })

  const printMutation = useMutation({
    mutationFn: (payslipId) => fetchPayslipPrint(payslipId),
    onSuccess: (res) => openPayslipPrintWindow(res),
    onError: (err) => toastError(err?.message || 'Print failed'),
  })

  const monthOptions = Array.from({ length: 12 }, (_, i) => ({
    value: String(i + 1),
    label: new Date(2000, i, 1).toLocaleString('default', { month: 'long' }),
  }))

  return (
    <div className="space-y-6">
      <Card className="space-y-4 p-4">
        <h2 className="font-semibold text-slate-900 dark:text-white">Generate payroll</h2>
        <div className="flex flex-wrap items-end gap-3">
          <Input label="Year" type="number" value={periodYear} onChange={(e) => setPeriodYear(e.target.value)} className="w-28" />
          <Select label="Month" value={periodMonth} onChange={(e) => setPeriodMonth(e.target.value)} options={monthOptions} className="w-40" />
          <Button disabled={!restaurant?.id || generateMutation.isPending} onClick={() => generateMutation.mutate()}>
            Generate
          </Button>
        </div>
      </Card>

      <EntityListPage
        title="Payroll runs"
        description="Monthly payroll batches"
        entity="payroll-runs"
        rows={runs}
        loading={isLoading}
        columns={[
          {
            key: 'period',
            label: 'Period',
            render: (_v, row) => `${row.period_year}-${String(row.period_month).padStart(2, '0')}`,
          },
          { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
          { key: 'payslip_count', label: 'Payslips' },
          {
            key: 'generated_at',
            label: 'Generated',
            render: (v) => (v ? new Date(v).toLocaleString() : '—'),
          },
          {
            key: 'actions',
            label: '',
            sortable: false,
            render: (_v, row) => (
              <div className="flex gap-1">
                <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => setSelectedRunId(row.id)}>
                  View payslips
                </Button>
                {row.status !== 'LOCKED' && (
                  <Button variant="secondary" className="h-7 px-2 text-xs" disabled={lockMutation.isPending} onClick={() => lockMutation.mutate(row.id)}>
                    Lock
                  </Button>
                )}
              </div>
            ),
          },
        ]}
      />

      {selectedRunId && (
        <EntityListPage
          title="Payslips"
          description="Print individual payslips"
          entity="payslips"
          rows={payslips}
          loading={payslipsLoading}
          columns={[
            { key: 'employee_name', label: 'Employee' },
            { key: 'employee_code', label: 'Code', render: (v) => (v ? <CodeChip code={v} /> : '—') },
            { key: 'basic_salary', label: 'Basic', render: (v) => formatCurrency(Number(v)) },
            { key: 'net_salary', label: 'Net', render: (v) => formatCurrency(Number(v)) },
            { key: 'days_present', label: 'Days' },
            {
              key: 'actions',
              label: '',
              sortable: false,
              render: (_v, row) => (
                <Button variant="ghost" className="h-7 px-2 text-xs" disabled={printMutation.isPending} onClick={() => printMutation.mutate(row.id)}>
                  Print
                </Button>
              ),
            },
          ]}
        />
      )}
    </div>
  )
}
