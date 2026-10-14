import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Tokens, User } from '../api/types'

interface AuthState {
  user: User | null
  tokens: Tokens | null
  setSession: (user: User, tokens: Tokens) => void
  setUser: (user: User) => void
  setTokens: (tokens: Tokens) => void
  logout: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      setSession: (user, tokens) => set({ user, tokens }),
      setUser: (user) => set({ user }),
      setTokens: (tokens) => set({ tokens }),
      logout: () => set({ user: null, tokens: null }),
    }),
    { name: 'lingoprism-auth' },
  ),
)

export const isStaffRole = (user: User | null) => user?.role === 'admin' || user?.role === 'staff'
