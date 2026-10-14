/**
 * Text-to-speech with the browser's Web Speech API.
 * Only speaks with a voice of the exact locale (zh-CN vs zh-TW...); never falls back to a wrong accent.
 */
let warned = new Set<string>()

function findVoice(locale: string): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis?.getVoices() ?? []
  const norm = (s: string) => s.toLowerCase().replace('_', '-')
  const target = norm(locale)
  return (
    voices.find((v) => norm(v.lang) === target) ??
    // zh-TW voices are sometimes tagged zh-Hant-TW
    voices.find((v) => norm(v.lang).endsWith(target.split('-')[1] ?? '') && norm(v.lang).startsWith(target.split('-')[0]))
  )
}

export function speak(text: string, locale: string): boolean {
  if (!('speechSynthesis' in window)) return false
  const voice = findVoice(locale)
  if (!voice) {
    if (!warned.has(locale)) {
      warned.add(locale)
      window.dispatchEvent(new CustomEvent('lingoprism:no-voice', { detail: locale }))
    }
    return false
  }
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.voice = voice
  u.lang = voice.lang
  u.rate = 0.9
  window.speechSynthesis.speak(u)
  return true
}

export function resetVoiceWarnings() {
  warned = new Set()
}
