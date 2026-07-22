import api from '../api/client'

export async function fetchPlans() {
  const { data } = await api.get('/saas/plans')
  return data
}

export async function fetchOrganizations() {
  const { data } = await api.get('/saas/organizations')
  return data
}

export async function fetchOrganization(organizationId) {
  const { data } = await api.get(`/saas/organizations/${organizationId}`)
  return data
}

export async function createOrganization(payload) {
  const { data } = await api.post('/saas/organizations', payload)
  return data
}

export async function updateOrganization(organizationId, payload) {
  const { data } = await api.patch(`/saas/organizations/${organizationId}`, payload)
  return data
}

export async function fetchOrgUsage(organizationId) {
  const { data } = await api.get(`/saas/organizations/${organizationId}/usage`)
  return data
}

export async function fetchOrgFeatures(organizationId) {
  const { data } = await api.get(`/saas/organizations/${organizationId}/features`)
  return data
}

export async function fetchInvoices(organizationId) {
  const { data } = await api.get(`/saas/organizations/${organizationId}/invoices`)
  return data
}

export async function fetchPayments(organizationId) {
  const { data } = await api.get(`/saas/organizations/${organizationId}/payments`)
  return data
}

export async function changePlan(organizationId, payload) {
  const { data } = await api.post(`/saas/organizations/${organizationId}/change-plan`, payload)
  return data
}

export async function cancelSubscription(organizationId, payload = { at_period_end: true }) {
  const { data } = await api.post(`/saas/organizations/${organizationId}/cancel`, payload)
  return data
}

export async function payInvoice(invoiceId, payload = { provider: 'manual' }) {
  const { data } = await api.post(`/saas/invoices/${invoiceId}/pay`, payload)
  return data
}

export async function runOnboarding(payload) {
  const { data } = await api.post('/saas/onboarding', payload)
  return data
}

export async function backfillTenants() {
  const { data } = await api.post('/saas/backfill')
  return data
}

export async function fetchSuperAdminDashboard() {
  const { data } = await api.get('/saas/super-admin/dashboard')
  return data
}

export async function fetchBranchAnalytics(organizationId) {
  const { data } = await api.get(`/saas/organizations/${organizationId}/branch-analytics`)
  return data
}

export async function createSupportTicket(payload) {
  const { data } = await api.post('/saas/support-tickets', payload)
  return data
}

export async function fetchSupportTickets(organizationId = null) {
  const { data } = await api.get('/saas/support-tickets', {
    params: organizationId ? { organization_id: organizationId } : {},
  })
  return data
}
