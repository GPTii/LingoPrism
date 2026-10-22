import { useEffect, useRef, useState } from 'react'
import { AudioOutlined, LoadingOutlined, SoundOutlined } from '@ant-design/icons'
import { canRecognise, listen, score, type Score } from '../lib/pronounce'
import { speak } from '../lib/speech'
import { langTag } from './TargetWord'

/**
 * "Nói thử": listen to the model voice, say the word, get a score and see which parts were heard right.
 * Hidden where the browser has no speech recognition.
 */
export default function SpeakCheck({ text, language, locale, onScore, compact = false }: {
  text: string
  /** vi | en | zh-Hans | zh-Hant */
  language: string
  /** BCP-47 voice / recogniser locale, e.g. en-US, zh-CN, zh-TW, vi-VN */
  locale: string
  onScore?: (s: Score) => void
  compact?: boolean
}) {
  const [state, setState] = useState<'idle' | 'listening'>('idle')
  const [result, setResult] = useState<Score | null>(null)
  const [error, setError] = useState('')
  const stopRef = useRef<(() => void) | undefined>(undefined)
  useEffect(() => { setResult(null); setError('') }, [text])
  useEffect(() => () => stopRef.current?.(), [])
  if (!canRecognise()) return null

  const go = async () => {
    if (state === 'listening') { stopRef.current?.(); return }
    setError(''); setResult(null); setState('listening')
    const { result: heard, stop } = listen(locale)
    stopRef.current = stop
    try {
      const s = score(text, await heard, language)
      setResult(s)
      onScore?.(s)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setState('idle')
    }
  }

  const tone = result ? { right: 'text-emerald-600', close: 'text-amber-700', wrong: 'text-red-600' }[result.verdict] : ''
  return (
    <div className={`flex flex-col items-center gap-2 ${compact ? '' : 'w-full'}`}>
      <div className="flex items-center gap-2">
        {!compact && (
          <button type="button" onClick={() => speak(text, locale)} aria-label="Nghe mẫu"
            className="h-11 px-4 rounded-full bg-slate-100 text-slate-700 font-semibold inline-flex items-center gap-2 cursor-pointer hover:bg-slate-200 transition-colors">
            <SoundOutlined /> Nghe mẫu
          </button>
        )}
        <button type="button" onClick={go} aria-pressed={state === 'listening'}
          aria-label={state === 'listening' ? 'Dừng nghe' : 'Nói thử'}
          className={`h-11 px-4 rounded-full font-semibold inline-flex items-center gap-2 cursor-pointer transition-colors ${
            state === 'listening' ? 'bg-[#ff6b81] text-white' : 'bg-brand-600 text-white hover:bg-brand-700'}`}>
          {state === 'listening' ? <><LoadingOutlined /> Đang nghe…</> : <><AudioOutlined /> Nói thử</>}
        </button>
      </div>
      {result && (
        <div className="text-center animate-rise" aria-live="polite">
          <div className={`text-lg font-bold ${tone}`}>
            {result.verdict === 'right' ? 'Phát âm chuẩn!' : result.verdict === 'close' ? 'Gần đúng rồi' : 'Chưa đúng'}
            <span className="num ml-2">{result.score}/100</span>
          </div>
          <div className="text-xl tracking-wide" lang={langTag(language)}>
            {result.units.map((u, i) => <span key={i} className={u.ok ? 'text-emerald-600' : 'text-red-500 underline decoration-2 underline-offset-4'}>{u.unit}</span>)}
          </div>
          {result.verdict !== 'right' && result.heard && (
            <div className="text-sm text-slate-500">Máy nghe thành: <span lang={langTag(language)} className="font-semibold text-slate-700">{result.heard}</span></div>
          )}
        </div>
      )}
      {error && <div className="text-sm text-red-600 text-center max-w-[40ch]" role="alert">{error}</div>}
    </div>
  )
}
