import api from '../api/client'

export async function listDiningAreas(params = {}) {
  const { data } = await api.get('/dining-areas', { params })
  return data
}

export async function createDiningArea(payload) {
  const { data } = await api.post('/dining-areas', payload)
  return data
}

export async function updateDiningArea(id, payload) {
  const { data } = await api.put(`/dining-areas/${id}`, payload)
  return data
}

export async function deleteDiningArea(id) {
  const { data } = await api.delete(`/dining-areas/${id}`)
  return data
}

export async function listTables(params = {}) {
  const { data } = await api.get('/tables', { params })
  return data
}

export async function createTable(payload) {
  const { data } = await api.post('/tables', payload)
  return data
}

export async function updateTable(id, payload) {
  const { data } = await api.put(`/tables/${id}`, payload)
  return data
}

export async function deleteTable(id) {
  const { data } = await api.delete(`/tables/${id}`)
  return data
}

export async function bulkDeleteTables(ids) {
  const { data } = await api.post('/tables/bulk-delete', ids)
  return data
}

export async function listDepartments(params = {}) {
  const { data } = await api.get('/departments', { params })
  return data
}

export async function createDepartment(payload) {
  const { data } = await api.post('/departments', payload)
  return data
}

export async function updateDepartment(id, payload) {
  const { data } = await api.put(`/departments/${id}`, payload)
  return data
}

export async function deleteDepartment(id) {
  const { data } = await api.delete(`/departments/${id}`)
  return data
}

export async function getBusinessSettings(restaurantId) {
  const { data } = await api.get(`/business-settings/${restaurantId}`)
  return data
}

export async function saveBusinessSettings(restaurantId, payload) {
  const { data } = await api.put(`/business-settings/${restaurantId}`, payload)
  return data
}

export async function listDocuments(params = {}) {
  const { data } = await api.get('/restaurant-documents', { params })
  return data
}

export async function registerDocument(payload) {
  const { data } = await api.post('/restaurant-documents', payload)
  return data
}

export async function uploadDocument({ restaurantId, title, documentType, notes, file }) {
  const form = new FormData()
  form.append('restaurant_id', restaurantId)
  form.append('title', title)
  form.append('document_type', documentType || 'OTHER')
  if (notes) form.append('notes', notes)
  form.append('file', file)
  const { data } = await api.post('/restaurant-documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteDocument(id) {
  const { data } = await api.delete(`/restaurant-documents/${id}`)
  return data
}

export async function fetchOpsDashboard(params = {}) {
  const { data } = await api.get('/ops/dashboard', { params })
  return data
}
