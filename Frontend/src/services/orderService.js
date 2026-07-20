import api from '../api/client'

export async function listOrders(params = {}) {
  const { data } = await api.get('/orders', { params })
  return data
}

export async function getOrder(id) {
  const { data } = await api.get(`/orders/${id}`)
  return data
}

export async function createOrder(payload) {
  const { data } = await api.post('/orders', payload)
  return data
}

export async function updateOrder(id, payload) {
  const { data } = await api.put(`/orders/${id}`, payload)
  return data
}

export async function deleteOrder(id) {
  const { data } = await api.delete(`/orders/${id}`)
  return data
}
