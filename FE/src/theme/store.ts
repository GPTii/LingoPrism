import { useEffect, useState } from 'react'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeState {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
}

/** Light / dark / follow the device – remembered in this browser. */
export const useThemeMode = create<ThemeState>()(
  persist((set) => ({ mode: 'system', setMode: (mode) => set({ mode }) }), { name: 'lingoprism-theme' }),
)

const media = () => window.matchMedia('(prefers-color-scheme: dark)')

/** The theme actually shown: 'system' resolved with the device setting, kept in sync when it changes. */
export function useIsDark(): boolean {
  const mode = useThemeMode((s) => s.mode)
  const [systemDark, setSystemDark] = useState(() => media().matches)
  useEffect(() => {
    const m = media()
    const on = (e: MediaQueryListEvent) => setSystemDark(e.matches)
    m.addEventListener('change', on)
    return () => m.removeEventListener('change', on)
  }, [])
  return mode === 'dark' || (mode === 'system' && systemDark)
}
