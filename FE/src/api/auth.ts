import { api } from './client'
import type { AuthResponse, User, UserGoal } from './types'

export interface NotificationSettings {
  push_enabled: boolean
  social_enabled: boolean
  contextual_allowed: boolean
  morning_time: string | null
  evening_time: string | null
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login/', { email, password }).then((r) => r.data),
  register: (email: string, password: string, display_name?: string) =>
    api.post<AuthResponse>('/auth/register/', { email, password, display_name }).then((r) => r.data),
  /** public Web client ID for the Google button; null when Google sign-in is not set up on the server */
  googleConfig: () => api.get<{ client_id: string | null }>('/auth/google/config/').then((r) => r.data),
  google: (id_token: string) => api.post<AuthResponse>('/auth/google/', { id_token }).then((r) => r.data),
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
  forgot: (email: string) => api.post('/auth/password/forgot/', { email }),
  verify: (email: string, code: string) =>
    api.post<{ reset_token: string }>('/auth/password/verify/', { email, code }).then((r) => r.data),
  reset: (reset_token: string, new_password: string) =>
    api.post('/auth/password/reset/', { reset_token, new_password }),
  me: () => api.get<User>('/me/').then((r) => r.data),
  updateMe: (data: Partial<User>) => api.patch<User>('/me/', data).then((r) => r.data),
  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('avatar', file)
    return api.patch<User>('/me/', form).then((r) => r.data)
  },
  goal: () => api.get<UserGoal>('/me/goal/').then((r) => r.data),
  updateGoal: (data: Partial<UserGoal>) => api.patch<UserGoal>('/me/goal/', data).then((r) => r.data),
  /** signs out every device afterwards */
  changePassword: (old_password: string, new_password: string) => api.post('/auth/password/change/', { old_password, new_password }),
  notificationSettings: () => api.get<NotificationSettings>('/notification-settings/').then((r) => r.data),
  updateNotificationSettings: (data: Partial<NotificationSettings>) =>
    api.patch<NotificationSettings>('/notification-settings/', data).then((r) => r.data),
}
