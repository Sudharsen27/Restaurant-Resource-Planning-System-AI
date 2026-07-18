import axios from 'axios'
import { API_BASE_URL, API_TIMEOUT_MS } from '../constants/config'

/**
 * Shared Axios client with interceptors.
 * Base URL defaults to /api/v1 (legacy root paths still work on the backend).
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: API_TIMEOUT_MS,
})

api.interceptors.request.use((config) => {
  // JWT-ready: attach token when auth is enabled
  const token = localStorage.getItem('rrps_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const data = error.response?.data
    const message =
      (typeof data?.message === 'string' && data.message) ||
      (typeof data?.detail === 'string' && data.detail) ||
      (Array.isArray(data?.detail) ? JSON.stringify(data.detail) : null) ||
      error.message ||
      'An unexpected error occurred'

    return Promise.reject(new Error(message))
  },
)

export default api
