import api from '../api/client'

export async function listSuppliers(params = {}) {
  const { data } = await api.get('/suppliers', { params })
  return data
}

export async function getSupplier(id) {
  const { data } = await api.get(`/suppliers/${id}`)
  return data
}

export async function createSupplier(payload) {
  const { data } = await api.post('/suppliers', payload)
  return data
}

export async function updateSupplier(id, payload) {
  const { data } = await api.put(`/suppliers/${id}`, payload)
  return data
}

export async function deleteSupplier(id) {
  const { data } = await api.delete(`/suppliers/${id}`)
  return data
}
