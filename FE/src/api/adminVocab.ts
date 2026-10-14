import { api } from './client'
import type { Paginated } from './types'

export type ReviewStatus = 'draft' | 'verified' | 'flagged' | 'rejected'

export interface AdminTranslation {
  id: number
  word: number
  word_slug: string
  language: 'vi' | 'en' | 'zh-Hans' | 'zh-Hant'
  text: string
  ipa: string
  pinyin: string
  pinyin_numbered: string
  zhuyin: string
  measure_word: string
  accepted_variants: string[]
  regional_difference: boolean
  meaning_vi: string
  meaning_en: string
  level: string
  status: ReviewStatus
  issues: { level: 'error' | 'warning'; message: string }[]
  sources: Record<string, unknown>
  verified_method: string
  verified_at: string | null
  updated_at: string
}

export interface AdminWord {
  id: number
  slug: string
  image: string | null
  image_url: string
  yolo_label: string
  part_of_speech: string
  difficulty: number
  audience: string
  topics: number[]
  translations: AdminTranslation[]
  flagged_count: number
}

export interface AdminReport {
  id: number
  user_email: string
  word: number
  word_slug: string
  translation: number | null
  translation_text: string | null
  reason: string
  details: string
  status: 'open' | 'resolved' | 'rejected'
  created_at: string
}

export const adminVocabApi = {
  stats: () => api.get<{ words: number; topics: number; translations: Record<string, Record<string, number>>; open_reports: number }>('/admin/vocab-stats/').then((r) => r.data),
  words: (params: Record<string, unknown>) => api.get<Paginated<AdminWord>>('/admin/words/', { params }).then((r) => r.data),
  updateWord: (id: number, data: Partial<AdminWord>) => api.patch<AdminWord>(`/admin/words/${id}/`, data).then((r) => r.data),
  translations: (params: Record<string, unknown>) => api.get<Paginated<AdminTranslation>>('/admin/translations/', { params }).then((r) => r.data),
  updateTranslation: (id: number, data: Partial<AdminTranslation>) => api.patch<AdminTranslation>(`/admin/translations/${id}/`, data).then((r) => r.data),
  verify: (id: number) => api.post<AdminTranslation>(`/admin/translations/${id}/verify/`).then((r) => r.data),
  reject: (id: number) => api.post<AdminTranslation>(`/admin/translations/${id}/reject/`).then((r) => r.data),
  recheck: (id: number) => api.post<AdminTranslation>(`/admin/translations/${id}/recheck/`).then((r) => r.data),
  reports: (params: Record<string, unknown>) => api.get<Paginated<AdminReport>>('/admin/reports/', { params }).then((r) => r.data),
  updateReport: (id: number, status: AdminReport['status']) => api.patch(`/admin/reports/${id}/`, { status }),
}

export const STATUS_TAG: Record<ReviewStatus, { color: string; label: string }> = {
  verified: { color: 'green', label: 'Đã kiểm tra' },
  flagged: { color: 'orange', label: 'Cần xem lại' },
  draft: { color: 'default', label: 'Nháp' },
  rejected: { color: 'red', label: 'Loại bỏ' },
}

export const LANG_LABEL: Record<string, string> = { vi: 'Tiếng Việt', en: 'Tiếng Anh', 'zh-Hans': 'Giản thể', 'zh-Hant': 'Phồn thể' }
