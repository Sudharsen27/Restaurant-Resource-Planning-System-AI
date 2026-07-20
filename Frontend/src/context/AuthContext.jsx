import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  clearAuthSession,
  getAccessToken,
  getStoredUser,
  setAuthSession,
} from '../store'
import * as authService from '../services/authService'
import { ROLE_PATHS } from '../constants/navigation'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser())
  const [bootstrapping, setBootstrapping] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function bootstrap() {
      const token = getAccessToken()
      if (!token) {
        if (!cancelled) setBootstrapping(false)
        return
      }
      try {
        const me = await authService.fetchMe()
        if (!cancelled) {
          setUser(me)
          setAuthSession({ user: me })
        }
      } catch {
        clearAuthSession()
        if (!cancelled) setUser(null)
      } finally {
        if (!cancelled) setBootstrapping(false)
      }
    }
    bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const payload = await authService.login(email, password)
    setUser(payload.user)
    return payload
  }, [])

  const logout = useCallback(async (allSessions = false) => {
    await authService.logout(allSessions)
    setUser(null)
  }, [])

  const refreshProfile = useCallback(async () => {
    const me = await authService.fetchMe()
    setUser(me)
    setAuthSession({ user: me })
    return me
  }, [])

  const hasRole = useCallback(
    (...roles) => (user ? roles.includes(user.role) : false),
    [user],
  )

  const canAccessPath = useCallback(
    (path) => {
      if (!user) return false
      const allowed = ROLE_PATHS[user.role] || ROLE_PATHS.EMPLOYEE
      if (allowed.includes('*')) return true
      return allowed.some((p) => (p === '/' ? path === '/' : path === p || path.startsWith(`${p}/`)))
    },
    [user],
  )

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      bootstrapping,
      login,
      logout,
      refreshProfile,
      hasRole,
      canAccessPath,
    }),
    [user, bootstrapping, login, logout, refreshProfile, hasRole, canAccessPath],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
