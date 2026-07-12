import api from './api'

export const healthCheck = () => api.get('/health')

export const predictCustomers = (payload) =>
  api.post('/forecast/predict', payload)
