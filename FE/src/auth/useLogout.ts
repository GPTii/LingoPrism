import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'
import { useAuth } from './store'

export function useLogout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  return async () => {
    const refresh = useAuth.getState().tokens?.refresh
    if (refresh) await authApi.logout(refresh).catch(() => undefined)
    useAuth.getState().logout()
    queryClient.clear()
    navigate('/login', { replace: true })
  }
}
