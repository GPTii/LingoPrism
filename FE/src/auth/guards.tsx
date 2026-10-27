import { useEffect } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { authApi } from '../api/auth'
import { isStaffRole, useAuth } from './store'
import { ParentConsentGate } from '../components/AccountGates'

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
  // a child's account waits for a parent (after the first-visit survey, where kid mode is chosen)
  const needsParent = user.parent_consent === 'missing' || user.parent_consent === 'pending'
  if (needsParent && location.pathname !== '/welcome') return <ParentConsentGate />
  return <Outlet />
}

export function RequireStaff() {
  const user = useAuth((s) => s.user)
  if (!isStaffRole(user)) return <Navigate to="/" replace />
  return <Outlet />
}
