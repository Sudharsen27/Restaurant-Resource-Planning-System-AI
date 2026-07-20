import { Navigate, Outlet, useLocation } from 'react-router-dom'
import LoadingSpinner from '../ui/LoadingSpinner'
import { useAuth } from '../../context/AuthContext'

export default function ProtectedRoute({ roles }) {
  const { isAuthenticated, bootstrapping, user, hasRole } = useAuth()
  const location = useLocation()

  if (bootstrapping) {
    return <LoadingSpinner label="Checking session…" />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (roles?.length && !hasRole(...roles)) {
    return <Navigate to="/unauthorized" replace />
  }

  return <Outlet context={{ user }} />
}
