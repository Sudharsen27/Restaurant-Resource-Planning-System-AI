import axios from 'axios'
import { API_BASE_URL, API_TIMEOUT_MS } from '../constants/config'
import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  setAuthSession,
} from '../store'

/**
 * Shared Axios client with interceptors.
 * Base URL defaults to /api/v1 (legacy root paths still work on the backend).
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: API_TIMEOUT_MS,
})

let refreshPromise = null

function toErrorMessage(error) {
  const data = error.response?.data
  return (
    (typeof data?.message === 'string' && data.message) ||
    (typeof data?.detail === 'string' && data.detail) ||
    (Array.isArray(data?.detail) ? JSON.stringify(data.detail) : null) ||
    error.message ||
    'An unexpected error occurred'
  )
}

function isCredentialAuthUrl(url = '') {
  return (
    url.includes('/auth/login') ||
    url.includes('/auth/refresh') ||
    url.includes('/auth/google') ||
    url.includes('/auth/providers') ||
    url.includes('/auth/forgot-password') ||
    url.includes('/auth/reset-password') ||
    url.includes('/auth/register')
  )
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('Session expired. Please sign in again.')
  }
  const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  })
  const tokens = data.data
  setAuthSession({
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
  })
  return tokens.access_token
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const url = `${original?.baseURL || ''}${original?.url || ''}`

    // Never refresh credential/auth bootstrap calls, and never refresh without a token.
    if (
      status === 401 &&
      original &&
      !original._retry &&
      !isCredentialAuthUrl(url) &&
      getRefreshToken()
    ) {
      original._retry = true
      try {
        refreshPromise = refreshPromise || refreshAccessToken()
        const accessToken = await refreshPromise
        refreshPromise = null
        original.headers.Authorization = `Bearer ${accessToken}`
        return api(original)
      } catch (refreshError) {
        refreshPromise = null
        clearAuthSession()
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
          window.location.assign('/login')
        }
        return Promise.reject(
          new Error(toErrorMessage(refreshError) || 'Session expired. Please sign in again.'),
        )
      }
    }

    return Promise.reject(new Error(toErrorMessage(error)))
  },
)

export default api
