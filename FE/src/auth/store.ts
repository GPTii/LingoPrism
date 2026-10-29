import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Tokens, User } from '../api/types'

interface AuthState {
  user: User | null
  tokens: Tokens | null
  /** set by every sign-in; the profile prompt (ProfilePrompt) shows once while it is set */
  askProfile: boolean
  setSession: (user: User, tokens: Tokens) => void
  doneAskingProfile: () => void
  setUser: (user: User) => void
  setTokens: (tokens: Tokens) => void
  logout: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      askProfile: false,
      setSession: (user, tokens) => set({ user, tokens, askProfile: true }),
      doneAskingProfile: () => set({ askProfile: false }),
      setUser: (user) => set({ user }),
      setTokens: (tokens) => set({ tokens }),
      logout: () => set({ user: null, tokens: null, askProfile: false }),
    }),
    { name: 'lingoprism-auth' },
  ),
)

export const isStaffRole = (user: User | null) => user?.role === 'admin' || user?.role === 'staff'
