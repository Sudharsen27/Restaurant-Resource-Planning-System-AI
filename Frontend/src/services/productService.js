import api from '../api/client'

export async function listProducts(params = {}) {
  const { data } = await api.get('/products', { params })
  return data
}

export async function getProduct(id) {
  const { data } = await api.get(`/products/${id}`)
  return data
}

export async function createProduct(payload) {
  const { data } = await api.post('/products', payload)
  return data
}

export async function updateProduct(id, payload) {
  const { data } = await api.put(`/products/${id}`, payload)
  return data
}

export async function deleteProduct(id) {
  const { data } = await api.delete(`/products/${id}`)
  return data
}

export async function exportProductsCsv(params = {}) {
  const { data } = await api.get('/products/export/csv', {
    params,
    responseType: 'blob',
  })
  return data
}

export async function importProductsCsv(restaurantId, file) {
  const form = new FormData()
  form.append('restaurant_id', restaurantId)
  form.append('file', file)
  const { data } = await api.post('/products/import/csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
