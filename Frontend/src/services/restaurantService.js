import api from '../api/client'

export async function listRestaurants(params = {}) {
  const { data } = await api.get('/restaurants', { params })
  return data
}

export async function getRestaurant(id) {
  const { data } = await api.get(`/restaurants/${id}`)
  return data
}

export async function createRestaurant(payload) {
  const { data } = await api.post('/restaurants', payload)
  return data
}

export async function updateRestaurant(id, payload) {
  const { data } = await api.put(`/restaurants/${id}`, payload)
  return data
}

export async function deleteRestaurant(id) {
  const { data } = await api.delete(`/restaurants/${id}`)
  return data
}
