import { useEffect } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { authApi } from '../api/auth'
import { isStaffRole, useAuth } from './store'

export function RequireAuth() {
  const user = useAuth((s) => s.user)
  const signedIn = !!user
  const location = useLocation()
  // The saved user may predate newer fields (e.g. public_id), so it is refreshed once per page load.
  useEffect(() => {
    if (!signedIn) return
    authApi.me().then((fresh) => useAuth.getState().setUser(fresh)).catch(() => {})
  }, [signedIn])
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

export function RequireStaff() {
  const user = useAuth((s) => s.user)
  if (!isStaffRole(user)) return <Navigate to="/" replace />
  return <Outlet />
}
