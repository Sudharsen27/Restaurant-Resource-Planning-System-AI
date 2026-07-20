import api from '../api/client'

export async function listEmployees(params = {}) {
  const { data } = await api.get('/employees', { params })
  return data
}

export async function getEmployee(id) {
  const { data } = await api.get(`/employees/${id}`)
  return data
}

export async function createEmployee(payload) {
  const { data } = await api.post('/employees', payload)
  return data
}

export async function updateEmployee(id, payload) {
  const { data } = await api.put(`/employees/${id}`, payload)
  return data
}

export async function deleteEmployee(id) {
  const { data } = await api.delete(`/employees/${id}`)
  return data
}
