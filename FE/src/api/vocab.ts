import type { SentenceToken } from './sentences'
import { api } from './client'
import type { Paginated } from './types'

export interface TargetText {
  id: number
  language: 'vi' | 'en' | 'zh-Hans' | 'zh-Hant'
  text: string
  tts_locale: string
  ipa?: string
  pinyin?: string
  zhuyin?: string
  measure_word?: string
  level?: string
  regional_difference?: boolean
  unverified?: boolean
}

export interface WordCard {
  id: number
  slug: string
  image: string | null
  image_credit?: string
  level?: number | null // 1–4 on the learning path of the active language
  image_source?: string
  emoji: string
  part_of_speech: string
  difficulty: number
  audience: string
  yolo_label: string
  target: TargetText | null
  meaning_vi: string
  english: string | null
  examples: { id: number; text: string; transliteration: string; tokens: SentenceToken[]; target_tokens: number[]; translation_vi: string; translation_en: string; source: string; source_id: string }[]
  personal: { id: number; status: 'new' | 'learning' | 'mastered'; stage: number; due_at: string | null; last_reviewed_at: string | null } | null
}

export interface Topic {
  id: number
  slug: string
  name_vi: string
  name_en: string
  name_zh_hans: string
  name_zh_hant: string
  icon: string
  image: string | null
  audience: 'all' | 'kid' | 'adult'
  visibility: 'public' | 'private'
  is_system: boolean
  word_count: number
  learned_count: number
}

export type Question =
  | { type: 'flashcard'; front: TargetText; back: string }
  | { type: 'choose_target'; prompt: string; options: string[]; answer: string }
  | { type: 'choose_meaning'; prompt: TargetText; options: string[]; answer: string }
  | { type: 'choose_pinyin'; prompt: string; options: string[]; answer: string }
  | { type: 'type_target'; prompt: string; accepted: string[]; answer: string }
  | { type: 'listen_type'; audio: TargetText; accepted: string[]; answer: string }

export interface SessionItem {
  item_id: number
  personal_word: number
  answered: boolean
  card: WordCard
  questions: Question[]
}

export interface StudySession {
  id: number
  kind: 'learn' | 'review' | 'practice'
  language: string
  script: string
  planned_count: number
  completed_count: number
  items: SessionItem[]
}

export interface LibrarySummary {
  language: string
  total: number
  new: number
  learning: number
  mastered: number
  due: number
}

export const vocabApi = {
  topics: (params?: Record<string, unknown>) => api.get<Paginated<Topic>>('/topics/', { params: { page_size: 100, ...params } }).then((r) => r.data),
  topic: (id: number) => api.get<Topic>(`/topics/${id}/`).then((r) => r.data),
  topicWords: (id: number, page = 1) => api.get<Paginated<WordCard>>(`/topics/${id}/words/`, { params: { page, page_size: 50 } }).then((r) => r.data),
  saveTopic: (id: number) => api.post<{ added: number; total: number }>(`/topics/${id}/save/`).then((r) => r.data),
  createTopic: (name_vi: string, icon: string) => api.post<Topic>('/topics/', { name_vi, icon, visibility: 'private' }).then((r) => r.data),
  deleteTopic: (id: number) => api.delete(`/topics/${id}/`),
  searchWords: (search: string) => api.get<Paginated<WordCard>>('/words/', { params: { search, page_size: 30 } }).then((r) => r.data),
  /** one page of verified words that have a translation in `lang` (the server only lists checked data) */
  wordPage: (lang: string, script: string, page: number, pageSize = 1) =>
    api.get<Paginated<WordCard>>('/words/', { params: { lang, script, page, page_size: pageSize } }).then((r) => r.data),
  /** the same word seen through another language */
  word: (id: number, lang: string, script?: string) => api.get<WordCard>(`/words/${id}/`, { params: { lang, script } }).then((r) => r.data),
  byLabels: (labels: string[]) => api.get<Record<string, WordCard>>('/words/by-labels/', { params: { labels: labels.join(',') } }).then((r) => r.data),
  report: (word: number, translation: number | undefined, reason: string, details: string) =>
    api.post('/reports/', { word, translation, reason, details }),
  myWords: (params?: Record<string, unknown>) => api.get<Paginated<WordCard>>('/my-words/', { params: { page_size: 50, ...params } }).then((r) => r.data),
  addWord: (word: number, source = 'manual', topic?: number) => api.post<WordCard>('/my-words/', { word, source, topic }).then((r) => r.data),
  removeWord: (personalId: number) => api.delete(`/my-words/${personalId}/`),
  summary: () => api.get<LibrarySummary>('/my-words/summary/').then((r) => r.data),
  startSession: (kind: StudySession['kind'], topic?: number, size?: number) =>
    api.post<StudySession>('/sessions/', { kind, topic, size }).then((r) => r.data),
  answer: (sessionId: number, payload: { personal_word: number; question_type: string; correct: boolean; first_try?: boolean; graded?: boolean; response_ms?: number; answer?: string }) =>
    api.post(`/sessions/${sessionId}/answer/`, payload).then((r) => r.data),
  finish: (sessionId: number) =>
    api.post<{ planned_count: number; completed_count: number; correct_first_try: number; xp_earned: number; needs_more_practice: number[]; level_up: number | null }>(`/sessions/${sessionId}/finish/`).then((r) => r.data),
}

/** Name of a topic in the language being learned. */
export function topicTargetName(topic: Topic, lang: string, script: string): string {
  if (lang === 'zh') return script === 'hant' ? topic.name_zh_hant : topic.name_zh_hans
  if (lang === 'en') return topic.name_en
  return ''
}

/** Normalize a typed answer the same way for every language (NFC, trim, case-insensitive except Chinese). */
export function normalizeAnswer(text: string, isChinese: boolean): string {
  const t = text.normalize('NFC').trim().replace(/\s+/g, isChinese ? '' : ' ')
  return isChinese ? t : t.toLowerCase()
}
