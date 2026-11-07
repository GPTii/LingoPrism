/**
 * Offline translation in the browser: Chrome's built-in Translator API (on-device model, Chrome 138+ on desktop).
 * The language pack is downloaded once by the browser, then translating needs no network and no server.
 * Elsewhere (Firefox, Safari, Chrome on phones) `offlineSupport()` says so and the online translation is used.
 */
type Availability = 'unavailable' | 'downloadable' | 'downloading' | 'available'
interface BrowserTranslator {
  translate: (text: string) => Promise<string>
  destroy?: () => void
}
interface TranslatorStatic {
  availability: (o: { sourceLanguage: string; targetLanguage: string }) => Promise<Availability>
  create: (o: { sourceLanguage: string; targetLanguage: string; monitor?: (m: EventTarget) => void }) => Promise<BrowserTranslator>
}

const api = (): TranslatorStatic | undefined =>
  typeof self !== 'undefined' ? (self as unknown as { Translator?: TranslatorStatic }).Translator : undefined

/** LingoPrism language -> BCP 47 tag of the browser's translator */
const tag = (l: string) => (l === 'zh-Hans' ? 'zh' : l)

export const offlineSupport = () => !!api()

/** Some Chromium builds expose the API without the on-device model: their promises never settle. */
function within<T>(p: Promise<T>, ms: number, message: string): Promise<T> {
  return Promise.race([p, new Promise<T>((_, reject) => setTimeout(() => reject(new Error(message)), ms))])
}
const NO_MODEL = 'Trình duyệt này chưa có bộ dịch offline. Hãy dùng Chrome 138+ trên máy tính, hoặc chế độ Online.'

export async function offlineAvailability(source: string, target: string): Promise<Availability> {
  const T = api()
  if (!T) return 'unavailable'
  try {
    return await within(T.availability({ sourceLanguage: tag(source), targetLanguage: tag(target) }), 5000, NO_MODEL)
  } catch {
    return 'unavailable'
  }
}

const cache = new Map<string, BrowserTranslator>()

/** Translate on this device. `onProgress` (0–1) reports the first download of a language pack. */
export async function translateOffline(text: string, source: string, target: string, onProgress?: (p: number) => void): Promise<string> {
  const T = api()
  if (!T) throw new Error(NO_MODEL)
  const key = `${source}>${target}`
  let tr = cache.get(key)
  if (!tr) {
    // a timeout here means no on-device model at all (NO_MODEL), 'unavailable' that this pair is not offered
    if ((await within(T.availability({ sourceLanguage: tag(source), targetLanguage: tag(target) }), 5000, NO_MODEL)) === 'unavailable') {
      throw new Error('Bộ dịch offline của trình duyệt chưa hỗ trợ cặp ngôn ngữ này.')
    }
    // the first time the browser downloads the language pack (tens of MB): allow it a few minutes
    tr = await within(
      T.create({
        sourceLanguage: tag(source),
        targetLanguage: tag(target),
        monitor: (m) => m.addEventListener('downloadprogress', (e) => onProgress?.((e as unknown as { loaded: number }).loaded)),
      }),
      180_000,
      NO_MODEL,
    )
    cache.set(key, tr)
  }
  return within(tr.translate(text), 30_000, 'Dịch offline quá lâu, thử lại nhé.')
}
