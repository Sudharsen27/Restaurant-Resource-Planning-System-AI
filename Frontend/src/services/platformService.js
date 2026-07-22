import api from '../api/client'

export async function fetchPlatformMonitoring() {
  const { data } = await api.get('/platform/monitoring')
  return data
}

export async function fetchPlatformHealthCenter() {
  const { data } = await api.get('/platform/health-center')
  return data
}

export async function fetchDeploymentStatus() {
  const { data } = await api.get('/platform/deployment')
  return data
}

export async function fetchMigrations() {
  const { data } = await api.get('/platform/migrations')
  return data
}

export async function fetchCacheStatus() {
  const { data } = await api.get('/platform/cache')
  return data
}

export async function clearCache(namespace = 'cache') {
  const { data } = await api.post('/platform/cache/clear', { namespace })
  return data
}

export async function fetchQueueMonitor() {
  const { data } = await api.get('/platform/queue')
  return data
}

export async function enqueueJob(job_type, payload = {}) {
  const { data } = await api.post('/platform/queue/enqueue', { job_type, payload })
  return data
}

export async function fetchPlatformLogs(limit = 100) {
  const { data } = await api.get('/platform/logs', { params: { limit } })
  return data
}

export async function fetchBackups() {
  const { data } = await api.get('/platform/backups')
  return data
}

export async function runBackup() {
  const { data } = await api.post('/platform/backups/run')
  return data
}

export async function pruneBackups() {
  const { data } = await api.post('/platform/backups/prune')
  return data
}

export async function fetchStorageStatus() {
  const { data } = await api.get('/platform/storage')
  return data
}
