import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuth } from '../auth/store'
import type { ApiError } from './types'

export const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = useAuth.getState().tokens?.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const { tokens, setTokens, logout } = useAuth.getState()
  if (!tokens?.refresh) return null
  try {
    const res = await axios.post('/api/v1/auth/refresh/', { refresh: tokens.refresh })
    setTokens({ access: res.data.access, refresh: res.data.refresh ?? tokens.refresh })
    return res.data.access
  } catch {
    logout()
    return null
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true
      refreshing ??= refreshAccessToken().finally(() => (refreshing = null))
      const access = await refreshing
      if (access) {
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      }
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error: unknown, fallback = 'Có lỗi xảy ra, vui lòng thử lại.'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined
    if (data?.detail) return data.detail
    if (!error.response) return 'Không kết nối được máy chủ.'
  }
  return fallback
}
