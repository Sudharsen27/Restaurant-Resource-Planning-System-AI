import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { Input, Select } from '../../components/forms/FormControls'
import EntityListPage from '../../components/pages/EntityListPage'
import { useOrg } from '../../context/OrgContext'
import { useToast } from '../../context/ToastContext'
import {
  bootstrapJobs,
  createApiKey,
  createWebhook,
  dispatchNotification,
  fetchAdminDashboard,
  fetchApiKeys,
  fetchAuditLogs,
  fetchFileAssets,
  fetchIntegrations,
  fetchJobRuns,
  fetchJobs,
  fetchNotifications,
  fetchReportSchedules,
  fetchSecurityOverview,
  fetchSettings,
  fetchSystemHealth,
  fetchWebhooks,
  fetchWorkflows,
  pauseJob,
  runJobNow,
  saveFileAsset,
  saveIntegration,
  saveJob,
  saveReportSchedule,
  saveSetting,
  saveWorkflow,
} from '../../services/adminService'

function asData(res) {
  if (res?.data !== undefined) return res.data
  return res
}

function useRestaurantId() {
  const { restaurant } = useOrg()
  return restaurant?.id || null
}

function Pill({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-white">{value}</p>
    </div>
  )
}

export function AdminOverviewPage() {
  const dashboardQ = useQuery({ queryKey: ['admin-dashboard'], queryFn: fetchAdminDashboard })
  const healthQ = useQuery({ queryKey: ['admin-health'], queryFn: fetchSystemHealth })
  const d = asData(dashboardQ.data) || {}
  const h = asData(healthQ.data) || {}
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Enterprise Admin Console</h1>
        <p className="mt-1 text-sm text-slate-500">Phase 10 automation control center on live PostgreSQL.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Pill label="Running jobs" value={d.running_jobs ?? '—'} />
        <Pill label="Failed jobs" value={d.failed_jobs ?? '—'} />
        <Pill label="Unread notifications" value={d.unread_notifications ?? '—'} />
        <Pill label="DB latency" value={`${h.database?.latency_ms ?? '—'} ms`} />
      </div>
      <Card title="Recent activity feed" subtitle="Immutable audit timeline">
        <div className="space-y-2">
          {(d.recent_activity || []).slice(0, 8).map((row) => (
            <div
              key={row.id}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-zinc-800"
            >
              <span className="font-semibold text-slate-900 dark:text-white">{row.action}</span>
              <span className="mx-2 text-slate-500">·</span>
              <span className="text-slate-600 dark:text-slate-400">{row.entity_type}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

export function WorkflowBuilderPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const [name, setName] = useState('Purchase Approval Flow')
  const [code, setCode] = useState('PURCHASE_APPROVAL_MAIN')
  const [entityType, setEntityType] = useState('PURCHASE_APPROVAL')
  const rowsQ = useQuery({
    queryKey: ['admin-workflows', restaurant_id],
    queryFn: () => fetchWorkflows(restaurant_id),
    enabled: Boolean(restaurant_id),
  })
  const saveMut = useMutation({
    mutationFn: saveWorkflow,
    onSuccess: () => {
      toast.success('Workflow saved')
      qClient.invalidateQueries({ queryKey: ['admin-workflows', restaurant_id] })
    },
    onError: (e) => toast.error(e.message),
  })
  const rows = asData(rowsQ.data) || []
  return (
    <EntityListPage
      title="Workflow Builder"
      description="Configurable approvals for purchase, expense, leave, discount, refund, reservation, and custom flows."
      entity="workflows"
      loading={rowsQ.isLoading}
      rows={rows}
      columns={[
        { key: 'name', label: 'Workflow' },
        { key: 'code', label: 'Code' },
        { key: 'entity_type', label: 'Entity type' },
        { key: 'trigger_event', label: 'Trigger' },
        { key: 'is_active', label: 'Active', render: (v) => (v ? 'Yes' : 'No') },
      ]}
      headerActions={
        <div className="flex flex-wrap items-end gap-2">
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} className="w-44" />
          <Input label="Code" value={code} onChange={(e) => setCode(e.target.value)} className="w-44" />
          <Select
            label="Entity"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="w-52"
            options={[
              { value: 'PURCHASE_APPROVAL', label: 'Purchase approval' },
              { value: 'EXPENSE_APPROVAL', label: 'Expense approval' },
              { value: 'LEAVE_APPROVAL', label: 'Leave approval' },
              { value: 'DISCOUNT_APPROVAL', label: 'Discount approval' },
              { value: 'REFUND_APPROVAL', label: 'Refund approval' },
              { value: 'RESERVATION_APPROVAL', label: 'Reservation approval' },
              { value: 'CUSTOM', label: 'Custom workflow' },
            ]}
          />
          <Button
            onClick={() =>
              saveMut.mutate({
                restaurant_id,
                name,
                code,
                entity_type: entityType,
                steps: [
                  { step_name: 'Manager approval', step_type: 'APPROVAL', approver_role: 'MANAGER' },
                  { step_name: 'Admin approval', step_type: 'APPROVAL', approver_role: 'ADMIN' },
                ],
              })
            }
            disabled={!restaurant_id || !name || !code || saveMut.isPending}
          >
            Save workflow
          </Button>
        </div>
      }
    />
  )
}

export function NotificationCenterPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const rowsQ = useQuery({ queryKey: ['admin-deliveries'], queryFn: () => fetchNotifications(200) })
  const [title, setTitle] = useState('System information')
  const [body, setBody] = useState('Background jobs are healthy.')
  const [category, setCategory] = useState('INFORMATION')
  const sendMut = useMutation({
    mutationFn: dispatchNotification,
    onSuccess: () => {
      toast.success('Notification dispatched')
      qClient.invalidateQueries({ queryKey: ['admin-deliveries'] })
    },
    onError: (e) => toast.error(e.message),
  })
  return (
    <EntityListPage
      title="Notification Center"
      description="Centralized in-app/email/SMS/push/WhatsApp delivery logs."
      entity="notification-deliveries"
      loading={rowsQ.isLoading}
      rows={asData(rowsQ.data) || []}
      columns={[
        { key: 'channel', label: 'Channel' },
        { key: 'category', label: 'Category' },
        { key: 'status', label: 'Status' },
        { key: 'recipient_user_id', label: 'Recipient' },
        { key: 'created_at', label: 'Created' },
      ]}
      headerActions={
        <div className="flex flex-wrap items-end gap-2">
          <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} className="w-44" />
          <Input label="Body" value={body} onChange={(e) => setBody(e.target.value)} className="w-56" />
          <Select
            label="Category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-44"
            options={[
              { value: 'INFORMATION', label: 'Information' },
              { value: 'SUCCESS', label: 'Success' },
              { value: 'WARNING', label: 'Warning' },
              { value: 'CRITICAL', label: 'Critical' },
            ]}
          />
          <Button
            onClick={() =>
              sendMut.mutate({
                title,
                body,
                restaurant_id,
                category,
                channels: ['IN_APP', 'EMAIL', 'SMS', 'PUSH', 'WHATSAPP'],
              })
            }
            disabled={!title || !body || sendMut.isPending}
          >
            Dispatch
          </Button>
        </div>
      }
    />
  )
}

export function JobSchedulerPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const jobsQ = useQuery({
    queryKey: ['admin-jobs', restaurant_id],
    queryFn: () => fetchJobs(restaurant_id),
    enabled: Boolean(restaurant_id),
  })
  const runsQ = useQuery({ queryKey: ['admin-job-runs'], queryFn: () => fetchJobRuns(null, 120) })
  const bootstrapMut = useMutation({
    mutationFn: bootstrapJobs,
    onSuccess: () => qClient.invalidateQueries({ queryKey: ['admin-jobs', restaurant_id] }),
  })
  const runMut = useMutation({
    mutationFn: runJobNow,
    onSuccess: () => {
      toast.success('Job queued')
      qClient.invalidateQueries({ queryKey: ['admin-job-runs'] })
    },
  })
  const pauseMut = useMutation({
    mutationFn: ({ id, paused }) => pauseJob(id, paused),
    onSuccess: () => qClient.invalidateQueries({ queryKey: ['admin-jobs', restaurant_id] }),
  })

  const jobs = asData(jobsQ.data) || []
  const runs = asData(runsQ.data) || []
  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Task Scheduler</h1>
          <p className="mt-1 text-sm text-slate-500">Run immediately, pause/resume, retry by rerun, and inspect execution history.</p>
        </div>
        <Button onClick={() => bootstrapMut.mutate(restaurant_id)} disabled={!restaurant_id || bootstrapMut.isPending}>
          Bootstrap default jobs
        </Button>
      </div>
      <Card title="Job definitions">
        <div className="space-y-2">
          {jobs.map((job) => (
            <div key={job.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 dark:border-zinc-800">
              <div>
                <p className="font-semibold text-slate-900 dark:text-white">{job.name}</p>
                <p className="text-xs text-slate-500">{job.code} · {job.schedule_cron || 'manual only'}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => pauseMut.mutate({ id: job.id, paused: !job.paused })}>
                  {job.paused ? 'Resume' : 'Pause'}
                </Button>
                <Button size="sm" onClick={() => runMut.mutate(job.id)}>
                  Run now
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <EntityListPage
        title="Execution history"
        description="Latest job runs"
        entity="job-runs"
        rows={runs}
        loading={runsQ.isLoading}
        columns={[
          { key: 'job_definition_id', label: 'Job id' },
          { key: 'run_status', label: 'Status' },
          { key: 'trigger_type', label: 'Trigger' },
          { key: 'duration_ms', label: 'Duration ms' },
          { key: 'created_at', label: 'Created' },
        ]}
      />
    </div>
  )
}

export function ReportSchedulerPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const rowsQ = useQuery({
    queryKey: ['admin-report-schedules', restaurant_id],
    queryFn: () => fetchReportSchedules(restaurant_id),
    enabled: Boolean(restaurant_id),
  })
  const saveMut = useMutation({
    mutationFn: saveReportSchedule,
    onSuccess: () => {
      toast.success('Report schedule saved')
      qClient.invalidateQueries({ queryKey: ['admin-report-schedules', restaurant_id] })
    },
  })
  return (
    <EntityListPage
      title="Report Scheduler"
      description="Schedule daily/weekly/monthly BI reports with email delivery and export formats."
      entity="report-schedules"
      rows={asData(rowsQ.data) || []}
      loading={rowsQ.isLoading}
      columns={[
        { key: 'report_kind', label: 'Report' },
        { key: 'frequency', label: 'Frequency' },
        { key: 'delivery_channel', label: 'Channel' },
        { key: 'export_format', label: 'Format' },
        { key: 'next_send_at', label: 'Next send' },
      ]}
      headerActions={
        <Button
          onClick={() =>
            saveMut.mutate({
              restaurant_id,
              report_kind: 'executive',
              frequency: 'daily',
              delivery_channel: 'EMAIL',
              export_format: 'PDF',
              recipients: { emails: ['ops@example.com'] },
            })
          }
          disabled={!restaurant_id || saveMut.isPending}
        >
          Add daily schedule
        </Button>
      }
    />
  )
}

export function SystemSettingsPage() {
  const toast = useToast()
  const qClient = useQueryClient()
  const rowsQ = useQuery({ queryKey: ['admin-settings'], queryFn: () => fetchSettings(null) })
  const saveMut = useMutation({
    mutationFn: saveSetting,
    onSuccess: () => {
      toast.success('Setting saved')
      qClient.invalidateQueries({ queryKey: ['admin-settings'] })
    },
  })
  return (
    <EntityListPage
      title="System Settings"
      description="Restaurant, company, branch, tax, timezone, localization, email and invoice templates."
      entity="system-settings"
      rows={asData(rowsQ.data) || []}
      loading={rowsQ.isLoading}
      columns={[
        { key: 'scope_type', label: 'Scope' },
        { key: 'scope_id', label: 'Scope id' },
        { key: 'setting_key', label: 'Key' },
        { key: 'updated_at', label: 'Updated' },
      ]}
      headerActions={
        <Button
          onClick={() =>
            saveMut.mutate({
              scope_type: 'restaurant',
              scope_id: null,
              setting_key: 'tax_configuration',
              setting_value: { gst: 5, currency: 'INR', timezone: 'Asia/Kolkata' },
            })
          }
          disabled={saveMut.isPending}
        >
          Save tax/timezone preset
        </Button>
      }
    />
  )
}

export function AuditCenterPage() {
  const rowsQ = useQuery({ queryKey: ['admin-audit'], queryFn: () => fetchAuditLogs(400) })
  return (
    <EntityListPage
      title="Audit Center"
      description="Immutable log stream for auth, role, inventory, order, payment, payroll, reservation, and settings actions."
      entity="audit-logs"
      rows={asData(rowsQ.data) || []}
      loading={rowsQ.isLoading}
      columns={[
        { key: 'created_at', label: 'Time' },
        { key: 'action', label: 'Action' },
        { key: 'entity_type', label: 'Entity' },
        { key: 'entity_id', label: 'Entity id' },
        { key: 'actor_user_id', label: 'Actor' },
      ]}
    />
  )
}

export function FileManagementPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const rowsQ = useQuery({
    queryKey: ['admin-files', restaurant_id],
    queryFn: () => fetchFileAssets(restaurant_id, 300),
    enabled: Boolean(restaurant_id),
  })
  const saveMut = useMutation({
    mutationFn: saveFileAsset,
    onSuccess: () => {
      toast.success('File metadata added')
      qClient.invalidateQueries({ queryKey: ['admin-files', restaurant_id] })
    },
  })
  return (
    <EntityListPage
      title="File Management"
      description="Storage abstraction metadata for documents, images, invoices, employee and supplier files, menu assets, and reports."
      entity="file-assets"
      rows={asData(rowsQ.data) || []}
      loading={rowsQ.isLoading}
      columns={[
        { key: 'category', label: 'Category' },
        { key: 'file_name', label: 'File' },
        { key: 'storage_path', label: 'Storage path' },
        { key: 'file_size_bytes', label: 'Size bytes' },
        { key: 'created_at', label: 'Uploaded' },
      ]}
      headerActions={
        <Button
          onClick={() =>
            saveMut.mutate({
              restaurant_id,
              category: 'REPORT',
              file_name: `report-${Date.now()}.pdf`,
              storage_path: `reports/${Date.now()}.pdf`,
              file_size_bytes: 1024,
            })
          }
          disabled={!restaurant_id || saveMut.isPending}
        >
          Register sample file
        </Button>
      }
    />
  )
}

export function ApiManagementPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const keysQ = useQuery({
    queryKey: ['admin-api-keys', restaurant_id],
    queryFn: () => fetchApiKeys(restaurant_id),
    enabled: Boolean(restaurant_id),
  })
  const hooksQ = useQuery({
    queryKey: ['admin-webhooks', restaurant_id],
    queryFn: () => fetchWebhooks(restaurant_id),
    enabled: Boolean(restaurant_id),
  })
  const keyMut = useMutation({
    mutationFn: createApiKey,
    onSuccess: (res) => {
      toast.success(`API key created (${asData(res)?.key_id})`)
      qClient.invalidateQueries({ queryKey: ['admin-api-keys', restaurant_id] })
    },
  })
  const hookMut = useMutation({
    mutationFn: createWebhook,
    onSuccess: () => qClient.invalidateQueries({ queryKey: ['admin-webhooks', restaurant_id] }),
  })

  const keyRows = asData(keysQ.data) || []
  const hookRows = asData(hooksQ.data) || []
  const rows = useMemo(
    () => [...keyRows.map((r) => ({ type: 'API_KEY', ...r })), ...hookRows.map((r) => ({ type: 'WEBHOOK', ...r }))],
    [keyRows, hookRows],
  )
  return (
    <EntityListPage
      title="API Management"
      description="API keys, webhook endpoints, and third-party access control."
      entity="api-management"
      rows={rows}
      loading={keysQ.isLoading || hooksQ.isLoading}
      columns={[
        { key: 'type', label: 'Type' },
        { key: 'name', label: 'Name' },
        { key: 'key_id', label: 'Key id' },
        { key: 'url', label: 'Webhook URL' },
        { key: 'status', label: 'Status' },
      ]}
      headerActions={
        <div className="flex gap-2">
          <Button onClick={() => keyMut.mutate({ restaurant_id, name: 'Partner API Key', requests_per_minute: 300 })}>
            Create API key
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              hookMut.mutate({
                restaurant_id,
                name: 'Ops Webhook',
                url: 'https://example.com/webhooks/ops',
                subscribed_events: ['order.paid', 'inventory.low_stock'],
              })
            }
          >
            Add webhook
          </Button>
        </div>
      }
    />
  )
}

export function IntegrationsPage() {
  const restaurant_id = useRestaurantId()
  const toast = useToast()
  const qClient = useQueryClient()
  const rowsQ = useQuery({
    queryKey: ['admin-integrations', restaurant_id],
    queryFn: () => fetchIntegrations(restaurant_id),
    enabled: Boolean(restaurant_id),
  })
  const saveMut = useMutation({
    mutationFn: saveIntegration,
    onSuccess: () => {
      toast.success('Integration saved')
      qClient.invalidateQueries({ queryKey: ['admin-integrations', restaurant_id] })
    },
  })
  return (
    <EntityListPage
      title="Integrations"
      description="Adapter registry for payment gateways, SMS, email, maps, calendars, accounting, food delivery, and loyalty ecosystems."
      entity="integrations"
      rows={asData(rowsQ.data) || []}
      loading={rowsQ.isLoading}
      columns={[
        { key: 'provider', label: 'Provider' },
        { key: 'status', label: 'Status' },
        { key: 'health_score', label: 'Health score' },
        { key: 'last_sync_at', label: 'Last sync' },
      ]}
      headerActions={
        <Button
          onClick={() =>
            saveMut.mutate({
              restaurant_id,
              provider: 'GOOGLE_CALENDAR',
              status: 'CONNECTED',
              config: { sync_enabled: true, reminder_minutes: 30 },
            })
          }
          disabled={!restaurant_id || saveMut.isPending}
        >
          Connect sample integration
        </Button>
      }
    />
  )
}

export function HealthDashboardPage() {
  const q = useQuery({ queryKey: ['admin-system-health'], queryFn: fetchSystemHealth })
  const d = asData(q.data) || {}
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Health</h1>
      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Database health">
          <p className="text-sm text-slate-600 dark:text-slate-300">Status: {d.database?.status || '—'}</p>
          <p className="text-sm text-slate-600 dark:text-slate-300">Latency: {d.database?.latency_ms ?? '—'} ms</p>
        </Card>
        <Card title="Background jobs">
          <p className="text-sm text-slate-600 dark:text-slate-300">Queued: {d.jobs?.queued ?? '—'}</p>
          <p className="text-sm text-slate-600 dark:text-slate-300">Failed: {d.jobs?.failed ?? '—'}</p>
        </Card>
      </div>
      <Card title="Storage usage">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Tracked file bytes: {d.storage?.tracked_file_bytes ?? '—'}
        </p>
      </Card>
    </div>
  )
}

export function SecurityCenterPage() {
  const q = useQuery({ queryKey: ['admin-security-overview'], queryFn: fetchSecurityOverview })
  const d = asData(q.data) || {}
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Security Center</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Pill label="Active sessions" value={d.active_sessions ?? '—'} />
        <Pill label="Failed logins (7d)" value={d.failed_logins_7d ?? '—'} />
        <Pill label="Open alerts" value={d.open_security_alerts ?? '—'} />
      </div>
    </div>
  )
}
