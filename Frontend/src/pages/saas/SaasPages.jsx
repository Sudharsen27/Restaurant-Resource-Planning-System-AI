import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { Input, Select } from '../../components/forms/FormControls'
import EntityListPage from '../../components/pages/EntityListPage'
import { useToast } from '../../context/ToastContext'
import { useAuth } from '../../context/AuthContext'
import {
  backfillTenants,
  cancelSubscription,
  changePlan,
  createOrganization,
  createSupportTicket,
  fetchBranchAnalytics,
  fetchInvoices,
  fetchOrganization,
  fetchOrganizations,
  fetchPayments,
  fetchPlans,
  fetchSuperAdminDashboard,
  fetchSupportTickets,
  payInvoice,
  runOnboarding,
  updateOrganization,
} from '../../services/saasService'

function asData(res) {
  if (res?.data !== undefined) return res.data
  return res
}

function useSelectedOrgId(orgs) {
  const [orgId, setOrgId] = useState(() => localStorage.getItem('rrps-saas-org') || '')
  useEffect(() => {
    if (!orgs?.length) return
    const exists = orgs.some((o) => o.id === orgId)
    if (!orgId || !exists) {
      const next = orgs[0].id
      setOrgId(next)
      localStorage.setItem('rrps-saas-org', next)
    }
  }, [orgs, orgId])
  const select = (id) => {
    setOrgId(id)
    localStorage.setItem('rrps-saas-org', id)
  }
  return [orgId, select]
}

function Pill({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-white">{value}</p>
    </div>
  )
}

function OrgSwitcher({ orgs, orgId, onChange }) {
  if (!orgs?.length) return null
  return (
    <Select
      label="Organization"
      value={orgId}
      onChange={(e) => onChange(e.target.value)}
      className="w-64"
      options={orgs.map((o) => ({ value: o.id, label: `${o.name} (${o.status})` }))}
    />
  )
}

export function OrganizationDashboardPage() {
  const toast = useToast()
  const orgsQ = useQuery({ queryKey: ['saas-orgs'], queryFn: fetchOrganizations })
  const orgs = asData(orgsQ.data) || []
  const [orgId, setOrgId] = useSelectedOrgId(orgs)
  const detailQ = useQuery({
    queryKey: ['saas-org', orgId],
    queryFn: () => fetchOrganization(orgId),
    enabled: Boolean(orgId),
  })
  const d = asData(detailQ.data) || {}
  const usage = d.usage || {}
  const limits = d.limits || {}
  const features = d.features || {}

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Organization Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">Tenant overview, plan, usage, and branding settings.</p>
        </div>
        <OrgSwitcher orgs={orgs} orgId={orgId} onChange={setOrgId} />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Pill label="Status" value={d.status || '—'} />
        <Pill label="Plan" value={d.plan_name || d.plan_code || '—'} />
        <Pill label="Branches" value={`${usage.branches ?? 0} / ${limits.max_branches ?? '—'}`} />
        <Pill label="Read-only" value={d.read_only ? 'Yes' : 'No'} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Usage">
          <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li>Employees: {usage.employees ?? 0} / {limits.max_employees ?? '—'}</li>
            <li>Products: {usage.products ?? 0} / {limits.max_products ?? '—'}</li>
            <li>Orders (month): {usage.orders_month ?? 0} / {limits.max_orders_monthly ?? '—'}</li>
            <li>Storage: {usage.storage_mb ?? 0} MB / {limits.max_storage_mb ?? '—'} MB</li>
          </ul>
        </Card>
        <Card title="Feature flags">
          <div className="flex flex-wrap gap-2">
            {Object.entries(features).map(([k, v]) => (
              <span
                key={k}
                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                  v
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                    : 'bg-slate-100 text-slate-500 dark:bg-zinc-900 dark:text-zinc-400'
                }`}
              >
                {k}: {v ? 'ON' : 'OFF'}
              </span>
            ))}
          </div>
        </Card>
      </div>
      <Card title="White-label branding">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Primary color: {d.branding?.primary_color || '—'} · Theme: {d.branding?.theme || '—'}
        </p>
        <Button
          className="mt-3"
          variant="secondary"
          onClick={async () => {
            try {
              await updateOrganization(orgId, {
                branding: { primary_color: '#0f766e', theme: 'light', invoice_footer: d.name },
              })
              toast.success('Branding saved')
              detailQ.refetch()
            } catch (e) {
              toast.error(e.message)
            }
          }}
          disabled={!orgId}
        >
          Save default branding
        </Button>
      </Card>
    </div>
  )
}

export function PlanComparisonPage() {
  const plansQ = useQuery({ queryKey: ['saas-plans'], queryFn: fetchPlans })
  const plans = asData(plansQ.data) || []
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Subscription Plans</h1>
        <p className="mt-1 text-sm text-slate-500">Compare Starter, Professional, Business, and Enterprise limits.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {plans.map((plan) => (
          <Card key={plan.id} title={plan.name} subtitle={plan.code}>
            <p className="text-2xl font-semibold text-slate-900 dark:text-white">
              ₹{Number(plan.price_monthly || 0).toLocaleString('en-IN')}
              <span className="text-sm font-normal text-slate-500"> /mo</span>
            </p>
            <p className="mt-2 text-sm text-slate-500">{plan.description}</p>
            <ul className="mt-4 space-y-1 text-sm text-slate-600 dark:text-slate-300">
              <li>Branches: {plan.max_branches}</li>
              <li>Employees: {plan.max_employees}</li>
              <li>Products: {plan.max_products}</li>
              <li>Orders/mo: {plan.max_orders_monthly}</li>
              <li>Storage: {plan.max_storage_mb} MB</li>
            </ul>
          </Card>
        ))}
      </div>
    </div>
  )
}

export function SubscriptionCenterPage() {
  const toast = useToast()
  const qClient = useQueryClient()
  const orgsQ = useQuery({ queryKey: ['saas-orgs'], queryFn: fetchOrganizations })
  const plansQ = useQuery({ queryKey: ['saas-plans'], queryFn: fetchPlans })
  const orgs = asData(orgsQ.data) || []
  const plans = asData(plansQ.data) || []
  const [orgId, setOrgId] = useSelectedOrgId(orgs)
  const [planCode, setPlanCode] = useState('PROFESSIONAL')
  const detailQ = useQuery({
    queryKey: ['saas-org', orgId],
    queryFn: () => fetchOrganization(orgId),
    enabled: Boolean(orgId),
  })
  const d = asData(detailQ.data) || {}

  const changeMut = useMutation({
    mutationFn: () => changePlan(orgId, { plan_code: planCode, billing_cycle: 'monthly' }),
    onSuccess: () => {
      toast.success('Plan upgraded')
      qClient.invalidateQueries({ queryKey: ['saas-org', orgId] })
      qClient.invalidateQueries({ queryKey: ['saas-invoices', orgId] })
    },
    onError: (e) => toast.error(e.message),
  })
  const cancelMut = useMutation({
    mutationFn: () => cancelSubscription(orgId, { at_period_end: true }),
    onSuccess: () => {
      toast.success('Cancellation scheduled')
      detailQ.refetch()
    },
    onError: (e) => toast.error(e.message),
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Subscription Center</h1>
          <p className="mt-1 text-sm text-slate-500">Upgrade, downgrade, trial, grace, and cancellation controls.</p>
        </div>
        <OrgSwitcher orgs={orgs} orgId={orgId} onChange={setOrgId} />
      </div>
      <Card title="Current subscription">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Plan: <strong>{d.plan_name || d.plan_code || '—'}</strong> · Status:{' '}
          <strong>{d.subscription_status || d.status || '—'}</strong>
        </p>
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <Select
            label="Target plan"
            value={planCode}
            onChange={(e) => setPlanCode(e.target.value)}
            className="w-56"
            options={plans.map((p) => ({ value: p.code, label: p.name }))}
          />
          <Button onClick={() => changeMut.mutate()} disabled={!orgId || changeMut.isPending}>
            Change plan
          </Button>
          <Button variant="secondary" onClick={() => cancelMut.mutate()} disabled={!orgId || cancelMut.isPending}>
            Cancel at period end
          </Button>
        </div>
      </Card>
    </div>
  )
}

export function BillingPortalPage() {
  const toast = useToast()
  const qClient = useQueryClient()
  const orgsQ = useQuery({ queryKey: ['saas-orgs'], queryFn: fetchOrganizations })
  const orgs = asData(orgsQ.data) || []
  const [orgId, setOrgId] = useSelectedOrgId(orgs)
  const invoicesQ = useQuery({
    queryKey: ['saas-invoices', orgId],
    queryFn: () => fetchInvoices(orgId),
    enabled: Boolean(orgId),
  })
  const paymentsQ = useQuery({
    queryKey: ['saas-payments', orgId],
    queryFn: () => fetchPayments(orgId),
    enabled: Boolean(orgId),
  })
  const payMut = useMutation({
    mutationFn: (invoiceId) => payInvoice(invoiceId),
    onSuccess: () => {
      toast.success('Invoice paid')
      qClient.invalidateQueries({ queryKey: ['saas-invoices', orgId] })
      qClient.invalidateQueries({ queryKey: ['saas-payments', orgId] })
    },
    onError: (e) => toast.error(e.message),
  })
  const invoices = asData(invoicesQ.data) || []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Billing Portal</h1>
          <p className="mt-1 text-sm text-slate-500">Invoices, renewals, and payment history.</p>
        </div>
        <OrgSwitcher orgs={orgs} orgId={orgId} onChange={setOrgId} />
      </div>
      <EntityListPage
        title="Invoices"
        description="Open and paid subscription invoices"
        entity="invoices"
        loading={invoicesQ.isLoading}
        rows={invoices}
        columns={[
          { key: 'invoice_number', label: 'Invoice #' },
          { key: 'status', label: 'Status' },
          { key: 'total_amount', label: 'Total' },
          { key: 'due_date', label: 'Due' },
          {
            key: 'id',
            label: 'Action',
            render: (_v, row) =>
              row.status === 'OPEN' ? (
                <Button size="sm" onClick={() => payMut.mutate(row.id)}>
                  Pay
                </Button>
              ) : (
                '—'
              ),
          },
        ]}
      />
      <EntityListPage
        title="Payment history"
        description="Successful billing payments"
        entity="payments"
        loading={paymentsQ.isLoading}
        rows={asData(paymentsQ.data) || []}
        columns={[
          { key: 'paid_at', label: 'Paid at' },
          { key: 'amount', label: 'Amount' },
          { key: 'provider', label: 'Provider' },
          { key: 'status', label: 'Status' },
          { key: 'provider_ref', label: 'Reference' },
        ]}
      />
    </div>
  )
}

export function UsageDashboardPage() {
  const orgsQ = useQuery({ queryKey: ['saas-orgs'], queryFn: fetchOrganizations })
  const orgs = asData(orgsQ.data) || []
  const [orgId, setOrgId] = useSelectedOrgId(orgs)
  const detailQ = useQuery({
    queryKey: ['saas-org', orgId],
    queryFn: () => fetchOrganization(orgId),
    enabled: Boolean(orgId),
  })
  const analyticsQ = useQuery({
    queryKey: ['saas-branch-analytics', orgId],
    queryFn: () => fetchBranchAnalytics(orgId),
    enabled: Boolean(orgId),
  })
  const d = asData(detailQ.data) || {}
  const usage = d.usage || {}
  const branches = asData(analyticsQ.data)?.branches || []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Usage Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">API, storage, orders, employees, branches, products.</p>
        </div>
        <OrgSwitcher orgs={orgs} orgId={orgId} onChange={setOrgId} />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Pill label="Branches" value={usage.branches ?? 0} />
        <Pill label="Employees" value={usage.employees ?? 0} />
        <Pill label="Products" value={usage.products ?? 0} />
        <Pill label="Orders (month)" value={usage.orders_month ?? 0} />
        <Pill label="Storage MB" value={usage.storage_mb ?? 0} />
        <Pill label="API calls" value={usage.api_calls_month ?? 0} />
      </div>
      <EntityListPage
        title="Multi-branch analytics"
        description="Revenue / orders / employees across branches"
        entity="branch-analytics"
        loading={analyticsQ.isLoading}
        rows={branches}
        columns={[
          { key: 'restaurant_name', label: 'Restaurant' },
          { key: 'branch_name', label: 'Branch' },
          { key: 'revenue', label: 'Revenue' },
          { key: 'orders', label: 'Orders' },
          { key: 'employees', label: 'Employees' },
          { key: 'profit', label: 'Est. profit' },
        ]}
      />
    </div>
  )
}

export function OnboardingWizardPage() {
  const toast = useToast()
  const [form, setForm] = useState({
    organization_name: '',
    restaurant_name: '',
    restaurant_code: '',
    branch_name: 'Main Branch',
    branch_code: 'MAIN',
    tax_rate: 5,
    plan_code: 'STARTER',
  })
  const mut = useMutation({
    mutationFn: runOnboarding,
    onSuccess: (res) => {
      toast.success('Organization onboarded')
      const org = asData(res)?.organization
      if (org?.id) localStorage.setItem('rrps-saas-org', org.id)
    },
    onError: (e) => toast.error(e.message),
  })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Restaurant Setup Wizard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Create organization → restaurant → branch → tax defaults in one flow.
        </p>
      </div>
      <Card>
        <div className="grid gap-3 sm:grid-cols-2">
          <Input label="Organization name" value={form.organization_name} onChange={set('organization_name')} />
          <Input label="Restaurant name" value={form.restaurant_name} onChange={set('restaurant_name')} />
          <Input label="Restaurant code" value={form.restaurant_code} onChange={set('restaurant_code')} />
          <Input label="Branch name" value={form.branch_name} onChange={set('branch_name')} />
          <Input label="Branch code" value={form.branch_code} onChange={set('branch_code')} />
          <Input label="Tax rate %" type="number" value={form.tax_rate} onChange={set('tax_rate')} />
          <Select
            label="Plan"
            value={form.plan_code}
            onChange={set('plan_code')}
            options={[
              { value: 'STARTER', label: 'Starter' },
              { value: 'PROFESSIONAL', label: 'Professional' },
              { value: 'BUSINESS', label: 'Business' },
              { value: 'ENTERPRISE', label: 'Enterprise' },
            ]}
          />
        </div>
        <Button
          className="mt-4"
          onClick={() =>
            mut.mutate({
              ...form,
              tax_rate: Number(form.tax_rate),
            })
          }
          disabled={mut.isPending || !form.organization_name || !form.restaurant_name || !form.restaurant_code}
        >
          Complete onboarding
        </Button>
      </Card>
    </div>
  )
}

export function SuperAdminConsolePage() {
  const { hasRole } = useAuth()
  const toast = useToast()
  const qClient = useQueryClient()
  const can = hasRole('SUPER_ADMIN')
  const dashQ = useQuery({
    queryKey: ['saas-super-admin'],
    queryFn: fetchSuperAdminDashboard,
    enabled: can,
  })
  const ticketsQ = useQuery({
    queryKey: ['saas-tickets'],
    queryFn: () => fetchSupportTickets(),
    enabled: can,
  })
  const backfillMut = useMutation({
    mutationFn: backfillTenants,
    onSuccess: (res) => {
      toast.success(`Backfilled ${asData(res)?.organizations_created ?? 0} orgs`)
      qClient.invalidateQueries({ queryKey: ['saas-orgs'] })
      qClient.invalidateQueries({ queryKey: ['saas-super-admin'] })
    },
    onError: (e) => toast.error(e.message),
  })
  const d = asData(dashQ.data) || {}

  if (!can) {
    return (
      <Card title="Super Admin Console">
        <p className="text-sm text-slate-500">SUPER_ADMIN role required. Use superadmin@restaurant.com.</p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Super Admin Console</h1>
          <p className="mt-1 text-sm text-slate-500">Global organizations, revenue, health, and support.</p>
        </div>
        <Button onClick={() => backfillMut.mutate()} disabled={backfillMut.isPending}>
          Backfill tenants from restaurants
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Pill label="Organizations" value={d.organizations_total ?? 0} />
        <Pill label="Active" value={d.organizations_active ?? 0} />
        <Pill label="Trial" value={d.organizations_trial ?? 0} />
        <Pill label="Revenue collected" value={`₹${Number(d.revenue_collected || 0).toLocaleString('en-IN')}`} />
      </div>
      <EntityListPage
        title="Support tickets"
        description="Open platform support requests"
        entity="support-tickets"
        rows={asData(ticketsQ.data) || []}
        loading={ticketsQ.isLoading}
        columns={[
          { key: 'subject', label: 'Subject' },
          { key: 'status', label: 'Status' },
          { key: 'priority', label: 'Priority' },
          { key: 'created_at', label: 'Created' },
        ]}
        headerActions={
          <Button
            variant="secondary"
            onClick={async () => {
              try {
                await createSupportTicket({
                  subject: 'Platform assistance',
                  body: 'Need help reviewing tenant configuration.',
                  priority: 'MEDIUM',
                  category: 'saas',
                })
                toast.success('Ticket created')
                ticketsQ.refetch()
              } catch (e) {
                toast.error(e.message)
              }
            }}
          >
            Create sample ticket
          </Button>
        }
      />
    </div>
  )
}

export function OrganizationsListPage() {
  const toast = useToast()
  const qClient = useQueryClient()
  const [name, setName] = useState('')
  const orgsQ = useQuery({ queryKey: ['saas-orgs'], queryFn: fetchOrganizations })
  const createMut = useMutation({
    mutationFn: createOrganization,
    onSuccess: () => {
      toast.success('Organization created')
      qClient.invalidateQueries({ queryKey: ['saas-orgs'] })
      setName('')
    },
    onError: (e) => toast.error(e.message),
  })
  const rows = asData(orgsQ.data) || []

  return (
    <EntityListPage
      title="Organizations"
      description="SaaS tenants with plan and license status."
      entity="organizations"
      loading={orgsQ.isLoading}
      rows={rows}
      columns={[
        { key: 'name', label: 'Organization' },
        { key: 'slug', label: 'Slug' },
        { key: 'status', label: 'License' },
        { key: 'plan_name', label: 'Plan' },
        { key: 'subscription_status', label: 'Subscription' },
        { key: 'country', label: 'Country' },
        { key: 'created_at', label: 'Created' },
      ]}
      headerActions={
        <div className="flex items-end gap-2">
          <Input label="New org name" value={name} onChange={(e) => setName(e.target.value)} className="w-56" />
          <Button
            onClick={() => createMut.mutate({ name, plan_code: 'STARTER' })}
            disabled={!name || createMut.isPending}
          >
            Create organization
          </Button>
        </div>
      }
    />
  )
}
