/**
 * Pronunciation check with the browser's speech recognition (Web Speech API – Chrome, Edge, Safari).
 * The learner says the word; we compare what the recogniser heard with the expected text.
 * For Chinese the comparison is character by character, so a wrong tone that turns 买 into 卖 shows up.
 */

interface Alternative { transcript: string; confidence: number }
interface RecognitionLike {
  lang: string
  interimResults: boolean
  maxAlternatives: number
  continuous: boolean
  start: () => void
  abort: () => void
  onresult: ((e: { results: ArrayLike<ArrayLike<Alternative>> }) => void) | null
  onerror: ((e: { error: string }) => void) | null
  onend: (() => void) | null
}

type Ctor = new () => RecognitionLike
const Recognition = (): Ctor | undefined =>
  (window as unknown as { SpeechRecognition?: Ctor; webkitSpeechRecognition?: Ctor }).SpeechRecognition
  ?? (window as unknown as { webkitSpeechRecognition?: Ctor }).webkitSpeechRecognition

export const canRecognise = () => typeof window !== 'undefined' && !!Recognition()

export interface Heard { alternatives: string[] }

/** Listen once (stops by itself after a pause). Rejects with a Vietnamese message on mic / network errors. */
export function listen(locale: string, timeoutMs = 7000): { result: Promise<Heard>; stop: () => void } {
  const C = Recognition()
  let rec: RecognitionLike | null = null
  const result = new Promise<Heard>((resolve, reject) => {
    if (!C) { reject(new Error('Trình duyệt này chưa nhận dạng được giọng nói. Hãy dùng Chrome hoặc Edge.')); return }
    rec = new C()
    rec.lang = locale
    rec.interimResults = false
    rec.continuous = false
    rec.maxAlternatives = 5
    let done = false
    const timer = window.setTimeout(() => rec?.abort(), timeoutMs)
    rec.onresult = (e) => {
      done = true
      const first = e.results[0]
      resolve({ alternatives: Array.from({ length: first.length }, (_, i) => first[i].transcript) })
    }
    rec.onerror = (e) => {
      done = true
      window.clearTimeout(timer)
      const msg: Record<string, string> = {
        'not-allowed': 'Bạn chưa cho phép dùng micro. Bấm biểu tượng ổ khoá trên thanh địa chỉ để bật.',
        'no-speech': 'Chưa nghe thấy gì. Bấm mic rồi đọc to, rõ hơn nhé.',
        'audio-capture': 'Không tìm thấy micro trên máy.',
        network: 'Nhận dạng giọng nói cần mạng. Kiểm tra kết nối rồi thử lại.',
        aborted: 'Chưa nghe thấy gì. Bấm mic rồi đọc to, rõ hơn nhé.',
      }
      reject(new Error(msg[e.error] ?? 'Không nhận dạng được giọng nói, thử lại nhé.'))
    }
    rec.onend = () => {
      window.clearTimeout(timer)
      if (!done) reject(new Error('Chưa nghe thấy gì. Bấm mic rồi đọc to, rõ hơn nhé.'))
    }
    rec.start()
  })
  return { result, stop: () => rec?.abort() }
}

/** Compare form: lower case, no punctuation or spaces; Vietnamese keeps its marks (they change the word). */
export function normalise(text: string, language: string): string {
  const t = text.normalize('NFC').toLowerCase().replace(/[\p{P}\p{S}]/gu, '')
  return language.startsWith('zh') ? t.replace(/\s+/g, '') : t.replace(/\s+/g, ' ').trim()
}

function levenshtein(a: string[], b: string[]): number {
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)])
  for (let j = 1; j <= b.length; j++) dp[0][j] = j
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1))
  return dp[a.length][b.length]
}

export interface Score {
  /** 0–100 */
  score: number
  /** what the recogniser heard (the best alternative) */
  heard: string
  verdict: 'right' | 'close' | 'wrong'
  /** per unit of the expected text (character for Chinese, letter otherwise): heard right or not */
  units: { unit: string; ok: boolean }[]
}

/** Best match among the recogniser's alternatives. Chinese compares characters, other languages letters. */
export function score(expected: string, heard: Heard, language: string): Score {
  const want = normalise(expected, language)
  const split = (s: string) => Array.from(language.startsWith('zh') ? s : s.replace(/ /g, ''))
  let best: Score = { score: 0, heard: heard.alternatives[0] ?? '', verdict: 'wrong', units: split(want).map((u) => ({ unit: u, ok: false })) }
  for (const alt of heard.alternatives) {
    const got = normalise(alt, language)
    const a = split(want), b = split(got)
    const s = got === want || (got.includes(want) && want.length > 0) ? 100
      : Math.max(0, Math.round(100 * (1 - levenshtein(a, b) / Math.max(a.length, b.length, 1))))
    if (s > best.score) {
      const set = new Set(b)
      best = {
        score: s, heard: alt, verdict: s >= 90 ? 'right' : s >= 50 ? 'close' : 'wrong',
        units: a.map((u) => ({ unit: u, ok: s === 100 || set.has(u) })),
      }
    }
  }
  return best
}
