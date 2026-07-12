import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(
      typeof message === 'string' ? new Error(message) : new Error(JSON.stringify(message)),
    )
  },
)

export default api
