import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { isStaffRole, useAuth } from './store'

export function RequireAuth() {
  const user = useAuth((s) => s.user)
  const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

export function RequireStaff() {
  const user = useAuth((s) => s.user)
  if (!isStaffRole(user)) return <Navigate to="/" replace />
  return <Outlet />
}
