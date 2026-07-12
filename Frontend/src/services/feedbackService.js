import api from './api'

export const submitFeedback = (payload) =>
  api.post('/feedback', payload)

export const getFeedbackHistory = (params = {}) =>
  api.get('/feedback/history', { params })
