import api from '../api/client'
import { clearAuthSession, getRefreshToken, setAuthSession } from '../store'

export async function login(email, password) {
  const { data } = await api.post('/auth/login', { email, password })
  const payload = data.data
  setAuthSession({
    accessToken: payload.tokens.access_token,
    refreshToken: payload.tokens.refresh_token,
    user: payload.user,
  })
  return payload
}

export async function refreshTokens() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) throw new Error('No refresh token')
  const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken })
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
  const { data } = await api.post('/auth/forgot-password', { email })
  return data
}

export async function resetPassword(token, newPassword) {
  const { data } = await api.post('/auth/reset-password', {
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
