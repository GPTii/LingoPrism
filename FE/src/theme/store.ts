import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeMode = 'light' | 'dark'

interface ThemeState {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  toggle: () => void
}

/** Light or dark – remembered in this browser. Dark first: the prism's light reads best on a dark ground. */
export const useThemeMode = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'dark',
      setMode: (mode) => set({ mode }),
      toggle: () => set({ mode: get().mode === 'dark' ? 'light' : 'dark' }),
    }),
    {
      name: 'lingoprism-theme-v2',
      // an older "follow the device" choice becomes dark
      merge: (persisted, current) => {
        const mode = (persisted as Partial<ThemeState> | undefined)?.mode
        return { ...current, mode: mode === 'light' ? 'light' : 'dark' }
      },
    },
  ),
)

/** The theme actually shown. */
export function useIsDark(): boolean {
  return useThemeMode((s) => s.mode) === 'dark'
}
