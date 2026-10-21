import { api } from './client'

export interface SentenceToken {
  t: string
  p?: string // pinyin
  z?: string // zhuyin
  x?: 1 // punctuation
  blank?: 1
}

export interface Sentence {
  id: number
  language: 'vi' | 'en' | 'zh-Hans' | 'zh-Hant'
  text: string
  tokens: SentenceToken[]
  target_tokens: number[]
  transliteration: string
  tts_locale: string
  translation: { language: 'vi' | 'en'; text: string } | null
  source: { name: string; id?: string; url?: string; license?: string }
}

interface Base {
  id: number
  word: { id: number; text: string }
}
export interface ArrangeExercise extends Base {
  type: 'arrange' | 'listen'
  tiles: { t: string; p: string; z: string }[]
  joiner: string
  prompt: { language: string; text: string } | null
  tts: { text: string; locale: string } | null
}
export interface FillExercise extends Base {
  type: 'fill'
  tokens: SentenceToken[]
  options: string[]
  prompt: { language: string; text: string }
}
export interface MeaningExercise extends Base {
  type: 'meaning'
  sentence: Sentence
  options: string[]
}
export type SentenceExercise = ArrangeExercise | FillExercise | MeaningExercise

export interface CheckResult {
  correct: boolean
  xp: number
  answer: string | null
  sentence: Sentence
}

export const sentencesApi = {
  lesson: (topic?: number, size = 10) =>
    api.get<{ language: string; scope: 'topic' | 'my_words' | 'all'; exercises: SentenceExercise[] }>('/sentences/lesson/', { params: { topic, size } }).then((r) => r.data),
  check: (body: { sentence: number; type: SentenceExercise['type']; answer: string | string[]; response_ms: number }) =>
    api.post<CheckResult>('/sentences/check/', body).then((r) => r.data),
}
