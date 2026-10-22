// Lesson sound effects (the same files as the mobile app). Played only after a click, so the browser allows it;
// a blocked or missing sound is ignored.
const cache: Partial<Record<Sfx, HTMLAudioElement>> = {}

export type Sfx = 'correct' | 'wrong' | 'complete'

export function sfx(name: Sfx, volume = 0.6) {
  try {
    const a = (cache[name] ??= new Audio(`/sounds/${name}.wav`))
    a.currentTime = 0
    a.volume = volume
    void a.play().catch(() => undefined)
  } catch {
    // no audio in this browser
  }
}
