/**
 * Vietnamese typing helpers for children without a Vietnamese keyboard: put a tone mark on the syllable before the
 * cursor using the same placement rule as the server (BE apps/vocab/lang/vietnamese.py – "kiểu cũ": hòa, thủy).
 */
export const TONE_MARKS: Record<string, string> = {
  huyen: '̀',
  sac: '́',
  hoi: '̉',
  nga: '̃',
  nang: '̣',
  ngang: '',
}
const ALL_MARKS = /[̣̀́̉̃]/g
const VOWELS = 'aăâeêioôơuưy'

export function applyTone(syllable: string, tone: string): string {
  const base = syllable.normalize('NFD').replace(ALL_MARKS, '').normalize('NFC')
  const mark = TONE_MARKS[tone] ?? ''
  if (!mark) return base
  const lower = base.toLowerCase()
  let idx = [...lower].map((ch, i) => (VOWELS.includes(ch) ? i : -1)).filter((i) => i >= 0)
  if (!idx.length) return base
  if ((lower.startsWith('qu') || lower.startsWith('gi')) && idx.length > 1 && idx[0] === 1) idx = idx.slice(1)
  let target = idx[0]
  const special = idx.filter((i) => 'ăâêôơư'.includes(lower[i]))
  if (special.length) {
    target = lower[special[special.length - 1]] === 'ơ' && special.length > 1 ? special[special.length - 1] : special[0]
  } else if (idx.length >= 2) {
    const endsWithVowel = idx[idx.length - 1] === lower.length - 1
    target = idx.length === 3 ? idx[1] : endsWithVowel ? idx[0] : idx[1]
  }
  const chars = [...base]
  chars[target] = (chars[target].normalize('NFD') + mark).normalize('NFC')
  return chars.join('')
}

/** Apply a tone to the word that ends at `cursor`; returns the new text and cursor. */
export function toneAtCursor(text: string, cursor: number, tone: string): { text: string; cursor: number } {
  const before = text.slice(0, cursor)
  const m = before.match(/[\p{L}]+$/u)
  if (!m) return { text, cursor }
  const start = cursor - m[0].length
  const replaced = applyTone(m[0], tone)
  return { text: text.slice(0, start) + replaced + text.slice(cursor), cursor: start + replaced.length }
}

/** Letters with a diacritic that are not tones: tapping 'ă' etc. inserts them. */
export const SPECIAL_LETTERS = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư']
