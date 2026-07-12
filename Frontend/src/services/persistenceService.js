import api from './api'

export const getLatestForecast = () => api.get('/forecast/latest')

export const getLatestStaff = () => api.get('/staff/latest')

export const getLatestInventory = () => api.get('/inventory/latest')

export const getLatestDashboard = () => api.get('/dashboard/latest')
