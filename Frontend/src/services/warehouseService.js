import api from '../api/client'

export async function listWarehouses(params = {}) {
  const { data } = await api.get('/warehouses', { params })
  return data
}

export async function createWarehouse(payload) {
  const { data } = await api.post('/warehouses', payload)
  return data
}

export async function updateWarehouse(id, payload) {
  const { data } = await api.put(`/warehouses/${id}`, payload)
  return data
}

export async function deleteWarehouse(id) {
  const { data } = await api.delete(`/warehouses/${id}`)
  return data
}
