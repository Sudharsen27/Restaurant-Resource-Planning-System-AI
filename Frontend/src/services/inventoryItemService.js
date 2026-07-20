import api from '../api/client'

export async function listInventoryItems(params = {}) {
  const { data } = await api.get('/inventory-items', { params })
  return data
}

export async function createInventoryItem(payload) {
  const { data } = await api.post('/inventory-items', payload)
  return data
}

export async function updateInventoryItem(id, payload) {
  const { data } = await api.put(`/inventory-items/${id}`, payload)
  return data
}

export async function deleteInventoryItem(id) {
  const { data } = await api.delete(`/inventory-items/${id}`)
  return data
}
