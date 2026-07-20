import api from '../api/client'

export async function listCategories(params = {}) {
  const { data } = await api.get('/categories', { params })
  return data
}

export async function getCategory(id) {
  const { data } = await api.get(`/categories/${id}`)
  return data
}

export async function createCategory(payload) {
  const { data } = await api.post('/categories', payload)
  return data
}

export async function updateCategory(id, payload) {
  const { data } = await api.put(`/categories/${id}`, payload)
  return data
}

export async function deleteCategory(id) {
  const { data } = await api.delete(`/categories/${id}`)
  return data
}
