import { api } from './client'

/** Phone-level pronunciation scoring (BE apps.speech, docs/thiet-ke-luyen-noi.md). */
export interface SpeechPhone { expected: string; heard: string | null; status: 'ok' | 'close' | 'wrong' | 'missing'; score: number }
export interface SpeechTone { expected: string | number; heard: string | number; status: 'ok' | 'close' | 'wrong' }
export interface SpeechUnit { text: string; reading: string; score: number; status: 'right' | 'close' | 'wrong'; tone: SpeechTone | null; phones: SpeechPhone[] }
export interface SpeechError { code: string; unit: number; expected: string; heard: string | null; tip: string; severity: 'major' | 'minor' }
export interface PronunciationResult {
  id: number
  text: string
  language: string
  score: number
  verdict: 'right' | 'close' | 'wrong'
  phone_score: number
  tone_score: number | null
  completeness: number
  units: SpeechUnit[]
  errors: SpeechError[]
  heard_ipa: string
}
export interface SpeechProgress {
  attempts: number
  average_7d: number | null
  by_day: { date: string; average: number; count: number }[]
  weak_sounds: { code: string; count: number; expected: string; heard: string | null; tip: string }[]
  recent: { id: number; text: string; kind: string; score: number; created_at: string }[]
}

export const speechApi = {
  status: () => api.get<{ enabled: boolean; languages: string[] }>('/speech/status/').then((r) => r.data),
  assess: (wav: Blob, item: { translation_id?: number; sentence_id?: number }) => {
    const form = new FormData()
    form.append('audio', wav, 'speech.wav')
    if (item.translation_id) form.append('translation_id', String(item.translation_id))
    if (item.sentence_id) form.append('sentence_id', String(item.sentence_id))
    return api.post<PronunciationResult>('/speech/assess/', form).then((r) => r.data)
  },
  progress: () => api.get<SpeechProgress>('/speech/progress/').then((r) => r.data),
}
