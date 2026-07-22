import api from '../api/client'

export async function fetchAdminDashboard() {
  const { data } = await api.get('/admin/dashboard')
  return data
}

export async function fetchSystemHealth() {
  const { data } = await api.get('/admin/system-health')
  return data
}

export async function fetchSecurityOverview() {
  const { data } = await api.get('/admin/security/overview')
  return data
}

export async function fetchAuditLogs(limit = 200) {
  const { data } = await api.get('/admin/audit/logs', { params: { limit } })
  return data
}

export async function fetchWorkflows(restaurant_id) {
  const { data } = await api.get('/admin/workflows', { params: { restaurant_id } })
  return data
}

export async function saveWorkflow(payload) {
  const { data } = await api.post('/admin/workflows', payload)
  return data
}

export async function fetchJobs(restaurant_id) {
  const { data } = await api.get('/admin/jobs', { params: { restaurant_id } })
  return data
}

export async function saveJob(payload) {
  const { data } = await api.post('/admin/jobs', payload)
  return data
}

export async function bootstrapJobs(restaurant_id) {
  const { data } = await api.post('/admin/jobs/bootstrap', null, { params: { restaurant_id } })
  return data
}

export async function runJobNow(jobId) {
  const { data } = await api.post(`/admin/jobs/${jobId}/run-now`)
  return data
}

export async function pauseJob(jobId, paused) {
  const { data } = await api.post(`/admin/jobs/${jobId}/pause`, { paused })
  return data
}

export async function fetchJobRuns(job_id = null, limit = 200) {
  const { data } = await api.get('/admin/jobs/runs', { params: { job_id, limit } })
  return data
}

export async function fetchNotifications(limit = 100) {
  const { data } = await api.get('/admin/notifications/deliveries', { params: { limit } })
  return data
}

export async function dispatchNotification(payload) {
  const { data } = await api.post('/admin/notifications/dispatch', payload)
  return data
}

export async function fetchReportSchedules(restaurant_id) {
  const { data } = await api.get('/admin/report-schedules', { params: { restaurant_id } })
  return data
}

export async function saveReportSchedule(payload) {
  const { data } = await api.post('/admin/report-schedules', payload)
  return data
}

export async function fetchSettings(scope_type = null) {
  const { data } = await api.get('/admin/settings', { params: { scope_type } })
  return data
}

export async function saveSetting(payload) {
  const { data } = await api.post('/admin/settings', payload)
  return data
}

export async function fetchApiKeys(restaurant_id = null) {
  const { data } = await api.get('/admin/api-keys', { params: { restaurant_id } })
  return data
}

export async function createApiKey(payload) {
  const { data } = await api.post('/admin/api-keys', payload)
  return data
}

export async function fetchWebhooks(restaurant_id = null) {
  const { data } = await api.get('/admin/webhooks', { params: { restaurant_id } })
  return data
}

export async function createWebhook(payload) {
  const { data } = await api.post('/admin/webhooks', payload)
  return data
}

export async function fetchIntegrations(restaurant_id) {
  const { data } = await api.get('/admin/integrations', { params: { restaurant_id } })
  return data
}

export async function saveIntegration(payload) {
  const { data } = await api.post('/admin/integrations', payload)
  return data
}

export async function fetchFileAssets(restaurant_id = null, limit = 200) {
  const { data } = await api.get('/admin/files/assets', { params: { restaurant_id, limit } })
  return data
}

export async function saveFileAsset(payload) {
  const { data } = await api.post('/admin/files/assets', payload)
  return data
}
