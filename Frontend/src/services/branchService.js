import api from '../api/client'

export async function listBranches(params = {}) {
  const { data } = await api.get('/branches', { params })
  return data
}

export async function getBranch(id) {
  const { data } = await api.get(`/branches/${id}`)
  return data
}

export async function createBranch(payload) {
  const { data } = await api.post('/branches', payload)
  return data
}

export async function updateBranch(id, payload) {
  const { data } = await api.put(`/branches/${id}`, payload)
  return data
}

export async function deleteBranch(id) {
  const { data } = await api.delete(`/branches/${id}`)
  return data
}
