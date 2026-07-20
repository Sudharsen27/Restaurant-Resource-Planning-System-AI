import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

/**
 * Renders children only when the user has one of the allowed roles.
 * Prefer route-level ProtectedRoute for pages; use this for in-page sections.
 */
export default function PermissionGuard({ roles = [], children, fallback = null }) {
  const { isAuthenticated, hasRole } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  if (roles.length && !hasRole(...roles)) {
    return fallback ?? <Navigate to="/unauthorized" replace />
  }
  return children
}
