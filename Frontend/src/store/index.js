/** Auth storage keys. */
export const storeKeys = {
  theme: 'rrps-theme',
  accessToken: 'rrps_access_token',
  refreshToken: 'rrps_refresh_token',
  user: 'rrps_user',
}

export function getAccessToken() {
  return localStorage.getItem(storeKeys.accessToken)
}

export function getRefreshToken() {
  return localStorage.getItem(storeKeys.refreshToken)
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(storeKeys.user)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setAuthSession({ accessToken, refreshToken, user }) {
  if (accessToken) localStorage.setItem(storeKeys.accessToken, accessToken)
  if (refreshToken) localStorage.setItem(storeKeys.refreshToken, refreshToken)
  if (user) localStorage.setItem(storeKeys.user, JSON.stringify(user))
}

export function clearAuthSession() {
  localStorage.removeItem(storeKeys.accessToken)
  localStorage.removeItem(storeKeys.refreshToken)
  localStorage.removeItem(storeKeys.user)
}
