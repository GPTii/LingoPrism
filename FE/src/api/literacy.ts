import { api } from './client'

export interface LitUnit {
  kind: 'am' | 'thanh' | 'van'
  code: string
  label: string
  sound: string
  symbol: string
}

export interface LitLessonInfo {
  n: number
  title: string
  review: boolean
  units: LitUnit[]
  status: 'done' | 'open' | 'locked'
  stars: number
  best_percent: number
}

export interface SpellExample {
  text: string
  onset: string
  rhyme: string
  tone: string
  spell: string[]
}

export interface LitIntro {
  type: 'intro'
  unit: LitUnit
  examples: SpellExample[]
  words: { id: number; text: string; emoji: string; image: string | null }[]
  rhyme_spell: string[]
}

interface Tts { text: string; locale: string }
interface Base { token: string; tts: Tts }

export type LitExercise =
  | (Base & { type: 'listen_choose'; options: string[] })
  | (Base & { type: 'find_unit'; question: string; syllable: string; options: string[] })
  | (Base & { type: 'build'; onsets: string[]; rhymes: string[]; tones: { code: string; label: string; symbol: string }[] })
  | (Base & { type: 'rule'; question: string; pattern: string; options: string[] })
  | (Base & { type: 'dictation'; emoji: string; image: string | null; syllables: number })
  | (Base & { type: 'sentence'; syllables: number; source: { name: string; id: number; license: string; url: string } })

export interface LitLesson {
  n: number
  title: string
  session: string
  units: LitUnit[]
  intro: LitIntro[]
  exercises: LitExercise[]
}

export interface LitCheck {
  correct: boolean
  xp: number
  expected: string
  given?: string
  spell?: string[]
  word?: string
  diff?: { expected: string; given: string; ok: boolean; hint?: string }[]
}

export interface LitFinish {
  correct_first_try: number
  total: number
  percent: number
  stars: number
  passed: boolean
  best_percent: number
  next_unlocked: boolean
}

export const literacyApi = {
  lessons: () => api.get<{ lessons: LitLessonInfo[]; pass_percent: number }>('/literacy/lessons/').then((r) => r.data),
  lesson: (n: number) => api.get<LitLesson>(`/literacy/lessons/${n}/`).then((r) => r.data),
  check: (token: string, answer: unknown, response_ms: number) =>
    api.post<LitCheck>('/literacy/check/', { token, answer, response_ms }).then((r) => r.data),
  finish: (n: number, session: string, total: number) =>
    api.post<LitFinish>(`/literacy/lessons/${n}/finish/`, { session, total }).then((r) => r.data),
}
