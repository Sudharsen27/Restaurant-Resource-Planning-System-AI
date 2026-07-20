import api from '../api/client'

export async function fetchExecutiveDashboard(params = {}) {
  const { data } = await api.get('/erp/dashboard', { params })
  return data
}
