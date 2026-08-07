import axios from 'axios'
import api from '../api/client'
import { API_BASE_URL } from '../constants/config'
import { clearAuthSession, getRefreshToken, setAuthSession } from '../store'

const AUTH_TIMEOUT_MS = 30_000

/** Plain client — no refresh interceptor (used for sign-in entrypoints). */
const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: AUTH_TIMEOUT_MS,
})

function authErrorMessage(error) {
  const data = error.response?.data
  return (
    (typeof data?.message === 'string' && data.message) ||
    (typeof data?.detail === 'string' && data.detail) ||
    (Array.isArray(data?.detail) ? JSON.stringify(data.detail) : null) ||
    error.message ||
    'Authentication failed'
  )
}

function storeLoginPayload(payload) {
  setAuthSession({
    accessToken: payload.tokens.access_token,
    refreshToken: payload.tokens.refresh_token,
    user: payload.user,
  })
  return payload
}

export async function login(email, password) {
  try {
    const { data } = await authApi.post('/auth/login', { email, password })
    return storeLoginPayload(data.data)
  } catch (error) {
    throw new Error(authErrorMessage(error), { cause: error })
  }
}

export async function loginWithGoogle(idToken) {
  try {
    const { data } = await authApi.post('/auth/google', { id_token: idToken })
    return storeLoginPayload(data.data)
  } catch (error) {
    throw new Error(authErrorMessage(error), { cause: error })
  }
}

export async function getAuthProviders() {
  const { data } = await authApi.get('/auth/providers')
  return data.data
}

export async function refreshTokens() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) throw new Error('Session expired. Please sign in again.')
  const { data } = await authApi.post('/auth/refresh', { refresh_token: refreshToken })
  const tokens = data.data
  setAuthSession({
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
  })
  return tokens
}

export async function logout(allSessions = false) {
  try {
    await api.post('/auth/logout', {
      refresh_token: getRefreshToken(),
      all_sessions: allSessions,
    })
  } finally {
    clearAuthSession()
  }
}

export async function fetchMe() {
  const { data } = await api.get('/auth/me')
  return data.data
}

export async function changePassword(currentPassword, newPassword) {
  const { data } = await api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}

export async function forgotPassword(email) {
  const { data } = await authApi.post('/auth/forgot-password', { email })
  return data
}

export async function resetPassword(token, newPassword) {
  const { data } = await authApi.post('/auth/reset-password', {
    token,
    new_password: newPassword,
  })
  return data
}

export async function listSessions() {
  const { data } = await api.get('/auth/sessions')
  return data
}

export async function revokeSession(sessionId) {
  const { data } = await api.delete(`/auth/sessions/${sessionId}`)
  return data
}

export async function revokeAllSessions() {
  const { data } = await api.post('/auth/sessions/revoke-others')
  return data
}
