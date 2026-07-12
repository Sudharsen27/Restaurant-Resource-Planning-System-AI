import api from './api'

export const getStaffRecommendation = (payload) => {
  const body =
    typeof payload === 'number'
      ? { predicted_customers: payload }
      : payload
  return api.post('/recommendation/staff', body)
}

export const getInventoryRecommendation = (payload) =>
  api.post('/recommendation/inventory', payload)
