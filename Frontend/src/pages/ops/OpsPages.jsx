import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { Select } from '../../components/forms/FormControls'
import { useToast } from '../../context/ToastContext'
import {
  clearCache,
  enqueueJob,
  fetchBackups,
  fetchCacheStatus,
  fetchDeploymentStatus,
  fetchMigrations,
  fetchPlatformHealthCenter,
  fetchPlatformLogs,
  fetchPlatformMonitoring,
  fetchQueueMonitor,
  pruneBackups,
  runBackup,
} from '../../services/platformService'

function asData(res) {
  if (res?.data !== undefined) return res.data
  return res
}

function Pill({ label, value, tone = 'slate' }) {
  const tones = {
    slate: 'border-slate-200 dark:border-zinc-800',
    green: 'border-emerald-300 dark:border-emerald-800',
    amber: 'border-amber-300 dark:border-amber-800',
    red: 'border-rose-300 dark:border-rose-800',
  }
  return (
    <div className={`rounded-xl border bg-white p-4 dark:bg-zinc-950 ${tones[tone] || tones.slate}`}>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-white">{value}</p>
    </div>
  )
}

function statusTone(ok) {
  if (ok === true) return 'green'
  if (ok === false) return 'red'
  return 'amber'
}

export function SystemMonitoringPage() {
  const q = useQuery({ queryKey: ['platform-monitoring'], queryFn: fetchPlatformMonitoring, refetchInterval: 15000 })
  const d = asData(q.data) || {}
  const res = d.resources || {}
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Monitoring</h1>
        <p className="mt-1 text-sm text-slate-500">CPU, memory, disk, database, Redis, and queue depth.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Pill label="CPU" value={`${res.cpu_percent ?? '—'}%`} />
        <Pill label="Memory" value={`${res.memory?.percent ?? '—'}%`} />
        <Pill label="Disk" value={`${res.disk?.percent ?? '—'}%`} />
        <Pill label="DB latency" value={`${d.database?.latency_ms ?? '—'} ms`} tone={statusTone(d.database?.ok)} />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Pill label="Redis" value={d.redis?.backend || '—'} tone={statusTone(d.redis?.ok)} />
        <Pill label="Queue workers" value={(d.queue?.workers || []).length} tone={statusTone(d.queue?.ok)} />
        <Pill label="Queue depth" value={d.queue?.default_queue_depth ?? 'n/a'} />
      </div>
      <Card title="Resource detail" subtitle="Live process metrics">
        <pre className="overflow-auto text-xs text-slate-700 dark:text-slate-300">{JSON.stringify(d, null, 2)}</pre>
      </Card>
    </div>
  )
}

export function HealthCenterPage() {
  const q = useQuery({ queryKey: ['platform-health-center'], queryFn: fetchPlatformHealthCenter, refetchInterval: 10000 })
  const d = asData(q.data) || {}
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Health Center</h1>
        <p className="mt-1 text-sm text-slate-500">Liveness, readiness dependencies, and storage health.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Pill label="Overall" value={d.status || '—'} tone={d.status === 'ok' ? 'green' : 'amber'} />
        <Pill label="Database" value={d.database?.ok ? 'healthy' : 'down'} tone={statusTone(d.database?.ok)} />
        <Pill label="Redis" value={d.redis?.ok ? 'healthy' : 'down'} tone={statusTone(d.redis?.ok)} />
        <Pill label="Storage" value={d.storage?.ok ? 'healthy' : 'check'} tone={statusTone(d.storage?.ok)} />
      </div>
      <Card title="Detailed health payload">
        <pre className="overflow-auto text-xs text-slate-700 dark:text-slate-300">{JSON.stringify(d, null, 2)}</pre>
      </Card>
    </div>
  )
}

export function DeploymentStatusPage() {
  const q = useQuery({ queryKey: ['platform-deployment'], queryFn: fetchDeploymentStatus })
  const d = asData(q.data) || {}
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Deployment Status</h1>
        <p className="mt-1 text-sm text-slate-500">Build metadata, environment flags, and migration revision.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Pill label="Environment" value={d.app_env || '—'} />
        <Pill label="Version" value={d.app_version || '—'} />
        <Pill label="Git SHA" value={(d.git_sha || '—').toString().slice(0, 12)} />
        <Pill label="Region" value={d.region || '—'} />
      </div>
      <Card title="Flags">
        <ul className="space-y-1 text-sm text-slate-700 dark:text-slate-300">
          <li>Rate limit: {String(d.rate_limit_enabled)}</li>
          <li>CSRF: {String(d.csrf_enabled)}</li>
          <li>HTTPS redirect: {String(d.https_redirect_enabled)}</li>
          <li>Redis: {String(d.redis_enabled)}</li>
          <li>Storage: {d.storage_backend}</li>
        </ul>
      </Card>
      <Card title="Alembic">
        <pre className="overflow-auto text-xs">{JSON.stringify({ current: d.alembic, heads: d.alembic_heads }, null, 2)}</pre>
      </Card>
    </div>
  )
}

export function MigrationDashboardPage() {
  const q = useQuery({ queryKey: ['platform-migrations'], queryFn: fetchMigrations })
  const d = asData(q.data) || {}
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Migration Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Safe Alembic upgrades — expand/contract before cutover.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Pill label="USE_ALEMBIC" value={String(d.use_alembic)} />
        <Pill label="ALLOW_CREATE_ALL" value={String(d.allow_create_all)} tone={d.allow_create_all ? 'amber' : 'green'} />
      </div>
      <Card title="Current revision">
        <pre className="overflow-auto text-xs">{JSON.stringify(d.current, null, 2)}</pre>
      </Card>
      <Card title="Heads">
        <pre className="overflow-auto text-xs">{JSON.stringify(d.heads, null, 2)}</pre>
      </Card>
    </div>
  )
}

export function CacheManagementPage() {
  const toast = useToast()
  const qClient = useQueryClient()
  const q = useQuery({ queryKey: ['platform-cache'], queryFn: fetchCacheStatus })
  const d = asData(q.data) || {}
  const clearM = useMutation({
    mutationFn: () => clearCache('cache'),
    onSuccess: (res) => {
      toast.success(`Cleared ${asData(res)?.deleted ?? 0} keys`)
      qClient.invalidateQueries({ queryKey: ['platform-cache'] })
    },
    onError: () => toast.error('Cache clear failed'),
  })
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Cache Management</h1>
          <p className="mt-1 text-sm text-slate-500">Redis-backed cache with in-memory fallback.</p>
        </div>
        <Button onClick={() => clearM.mutate()} disabled={clearM.isPending}>
          Clear cache namespace
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Pill label="Backend" value={d.backend || '—'} />
        <Pill label="Ping" value={d.ping ? 'ok' : 'fail'} tone={statusTone(d.ping)} />
        <Pill label="Default TTL" value={`${d.default_ttl ?? '—'}s`} />
      </div>
    </div>
  )
}

export function QueueMonitorPage() {
  const toast = useToast()
  const [jobType, setJobType] = useState('email')
  const q = useQuery({ queryKey: ['platform-queue'], queryFn: fetchQueueMonitor, refetchInterval: 10000 })
  const d = asData(q.data) || {}
  const enqueueM = useMutation({
    mutationFn: () =>
      enqueueJob(jobType, {
        to: 'ops@example.com',
        subject: 'Queue probe',
        body: 'Phase 12 queue monitor test',
      }),
    onSuccess: (res) => toast.success(`Queued ${asData(res)?.task_id || jobType}`),
    onError: () => toast.error('Enqueue failed'),
  })
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Queue Monitor</h1>
          <p className="mt-1 text-sm text-slate-500">Celery workers, active tasks, and enqueue probes.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={jobType}
            onChange={(e) => setJobType(e.target.value)}
            options={(d.job_types || ['email', 'report', 'inventory_check', 'notification', 'analytics']).map(
              (t) => ({ value: t, label: t }),
            )}
          />
          <Button onClick={() => enqueueM.mutate()} disabled={enqueueM.isPending}>
            Enqueue test job
          </Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Pill label="Workers" value={(d.health?.workers || []).length} tone={statusTone(d.health?.ok)} />
        <Pill label="Active tasks" value={d.health?.active_tasks ?? '—'} />
        <Pill label="Default depth" value={d.depth?.default_queue_depth ?? 'n/a'} />
      </div>
      <Card title="Queue health">
        <pre className="overflow-auto text-xs">{JSON.stringify(d, null, 2)}</pre>
      </Card>
    </div>
  )
}

export function LogViewerPage() {
  const q = useQuery({ queryKey: ['platform-logs'], queryFn: () => fetchPlatformLogs(150), refetchInterval: 8000 })
  const d = asData(q.data) || {}
  const entries = d.entries || []
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Log Viewer</h1>
        <p className="mt-1 text-sm text-slate-500">Recent platform ops events (in-process buffer).</p>
      </div>
      <Card title={`${entries.length} recent entries`}>
        <div className="max-h-[32rem] space-y-2 overflow-auto">
          {entries.map((row, idx) => (
            <div
              key={`${row.ts}-${idx}`}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs dark:border-zinc-800"
            >
              <span className="font-mono text-slate-500">{row.ts}</span>
              <span className="mx-2 font-semibold text-slate-900 dark:text-white">{row.level}</span>
              <span className="text-slate-700 dark:text-slate-300">
                {row.event}: {row.message}
              </span>
            </div>
          ))}
          {!entries.length && <p className="text-sm text-slate-500">No buffered events yet.</p>}
        </div>
      </Card>
    </div>
  )
}

export function BackupCenterPage() {
  const toast = useToast()
  const qClient = useQueryClient()
  const q = useQuery({ queryKey: ['platform-backups'], queryFn: fetchBackups })
  const d = asData(q.data) || {}
  const runM = useMutation({
    mutationFn: runBackup,
    onSuccess: () => {
      toast.success('Backup started')
      qClient.invalidateQueries({ queryKey: ['platform-backups'] })
    },
    onError: () => toast.error('Backup failed'),
  })
  const pruneM = useMutation({
    mutationFn: pruneBackups,
    onSuccess: (res) => {
      toast.success(`Pruned ${(asData(res)?.removed || []).length} files`)
      qClient.invalidateQueries({ queryKey: ['platform-backups'] })
    },
  })
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Backup Center</h1>
          <p className="mt-1 text-sm text-slate-500">PostgreSQL dumps, retention, and disk verification.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => runM.mutate()} disabled={runM.isPending}>
            Run backup
          </Button>
          <Button variant="secondary" onClick={() => pruneM.mutate()} disabled={pruneM.isPending}>
            Prune old
          </Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Pill label="Backups" value={d.disk?.backup_count ?? (d.items || []).length} />
        <Pill label="Free disk" value={`${d.disk?.free_gb ?? '—'} GB`} />
        <Pill label="Path" value={d.disk?.path || '—'} />
      </div>
      <Card title="Backup files">
        <div className="space-y-2">
          {(d.items || []).map((row) => (
            <div
              key={row.name}
              className="flex justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-zinc-800"
            >
              <span className="font-medium text-slate-900 dark:text-white">{row.name}</span>
              <span className="text-slate-500">
                {row.bytes} bytes · {row.modified}
              </span>
            </div>
          ))}
          {!(d.items || []).length && <p className="text-sm text-slate-500">No backups yet.</p>}
        </div>
      </Card>
    </div>
  )
}
