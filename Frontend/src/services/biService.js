import api from '../api/client'
import { downloadCsv } from '../utils/csv'

function cleanParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, v]) => v != null && v !== ''),
  )
}

export async function fetchExecutive(params = {}) {
  const { data } = await api.get('/bi/executive', { params: cleanParams(params) })
  return data
}

export async function fetchRevenueTrend(params = {}) {
  const { data } = await api.get('/bi/trends/revenue', { params: cleanParams(params) })
  return data
}

export async function fetchMenuAnalytics(params = {}) {
  const { data } = await api.get('/bi/menu', { params: cleanParams(params) })
  return data
}

export async function fetchCustomerAnalytics(params = {}) {
  const { data } = await api.get('/bi/customers', { params: cleanParams(params) })
  return data
}

export async function fetchEmployeeAnalytics(params = {}) {
  const { data } = await api.get('/bi/employees', { params: cleanParams(params) })
  return data
}

export async function fetchSmartInventory(params = {}) {
  const { data } = await api.get('/bi/inventory/smart', { params: cleanParams(params) })
  return data
}

export async function fetchSalesForecast(params = {}) {
  const { data } = await api.get('/bi/forecast/sales', { params: cleanParams(params) })
  return data
}

export async function fetchDemandForecast(params = {}) {
  const { data } = await api.get('/bi/forecast/demand', { params: cleanParams(params) })
  return data
}

export async function fetchInsights(params = {}) {
  const { data } = await api.get('/bi/insights', { params: cleanParams(params) })
  return data
}

export async function acknowledgeInsight(insightId) {
  const { data } = await api.post(`/bi/insights/${insightId}/acknowledge`)
  return data
}

export async function fetchAlerts(params = {}) {
  const { data } = await api.get('/bi/alerts', { params: cleanParams(params) })
  return data
}

export async function resolveAlert(alertId) {
  const { data } = await api.post(`/bi/alerts/${alertId}/resolve`)
  return data
}

export async function askAssistant(payload) {
  const { data } = await api.post('/bi/assistant/query', payload)
  return data
}

export async function exportReport(kind, params = {}) {
  const response = await api.get('/bi/reports/export', {
    params: cleanParams({ kind, format: 'csv', ...params }),
    responseType: 'blob',
  })
  const disposition = response.headers['content-disposition'] || ''
  let filename = `bi-report-${kind}.csv`
  const match = disposition.match(/filename="([^"]+)"/)
  if (match) filename = match[1]
  const text = await response.data.text()
  downloadCsv(filename, text)
  return { filename }
}
