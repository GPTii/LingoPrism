import { api } from './client'
import type { TargetText } from './vocab'

export interface LevelRow {
  level: number
  name: string
  description: string
  total: number
  started: number
  mastered: number
  percent: number
  unlocked: boolean
  current: boolean
  needed: number // words still to start before the next level opens
}

export interface LevelProgress {
  language: 'vi' | 'en' | 'zh'
  current: number
  unlock_percent: number
  test: { size: number; pass: number }
  levels: LevelRow[]
}

export interface LevelTest {
  level: number
  pass: number
  token: string
  questions: { index: number; options: string[]; prompt: { word?: TargetText; audio?: TargetText; emoji?: string } }[]
}

export interface LevelTestResult {
  score: number
  total: number
  passed: boolean
  answers: string[]
  unlocked: number | null
  progress: LevelProgress
}

export const levelsApi = {
  progress: () => api.get<LevelProgress>('/levels/').then((r) => r.data),
  choose: (level: number) => api.post<LevelProgress>('/levels/', { level }).then((r) => r.data),
  test: (level: number) => api.get<LevelTest>(`/levels/${level}/test/`).then((r) => r.data),
  submit: (level: number, token: string, answers: string[]) =>
    api.post<LevelTestResult>(`/levels/${level}/test/`, { token, answers }).then((r) => r.data),
}

export const LEVEL_COLORS = ['#22c55e', '#0ea5e9', '#f59e0b', '#ef4444']
