import api from '../api/client'

export async function listCustomers(params = {}) {
  const { data } = await api.get('/customers', { params })
  return data
}

export async function getCustomer(id) {
  const { data } = await api.get(`/customers/${id}`)
  return data
}

export async function createCustomer(payload) {
  const { data } = await api.post('/customers', payload)
  return data
}

export async function updateCustomer(id, payload) {
  const { data } = await api.put(`/customers/${id}`, payload)
  return data
}

export async function deleteCustomer(id) {
  const { data } = await api.delete(`/customers/${id}`)
  return data
}
