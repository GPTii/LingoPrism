import { useMutation, useQuery } from '@tanstack/react-query'
import { App, Button, Input, Segmented, Select, Tooltip } from 'antd'
import { AudioOutlined, CloseOutlined, CopyOutlined, ExpandOutlined, SoundOutlined, SwapOutlined, TranslationOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { learnApi, type TranslateLang } from '../api/app'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/store'
import { canRecognise, listen } from '../lib/pronounce'
import { offlineSupport, translateOffline } from '../lib/offlineTranslate'
import { speak } from '../lib/speech'
import { langTag } from './TargetWord'

const LANGS: { value: TranslateLang; label: string; locale: string }[] = [
  { value: 'vi', label: 'Việt', locale: 'vi-VN' },
  { value: 'en', label: 'Anh', locale: 'en-US' },
  { value: 'zh-Hans', label: 'Trung giản', locale: 'zh-CN' },
  { value: 'zh-Hant', label: 'Trung phồn', locale: 'zh-TW' },
]
const locale = (l: TranslateLang) => LANGS.find((x) => x.value === l)!.locale
const isZh = (l: TranslateLang) => l.startsWith('zh')
type Mode = 'auto' | 'online' | 'offline'
type Result = { text: string; reading?: string; target: TranslateLang; via: 'online' | 'offline' }

const POS_KEY = 'lp-translate-bubble'
const SIZE = 56

function loadPos(): { x: number; y: number } {
  try {
    const p = JSON.parse(localStorage.getItem(POS_KEY) ?? '')
    if (typeof p?.x === 'number' && typeof p?.y === 'number') return p
  } catch { /* first visit or storage blocked */ }
  return { x: 20, y: 96 } // from the right / bottom edge: above the phone tab bar
}

/**
 * Nút dịch nổi: a round button that follows the learner on every screen (drag it anywhere), opening a small
 * translator. Online = the server's AI translation; offline = the browser's own on-device translator (Chrome),
 * used automatically when the network or the server is out.
 */
export default function TranslateBubble() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const location = useLocation()
  const learning: TranslateLang = user?.active_language === 'zh' ? (user.zh_script === 'hant' ? 'zh-Hant' : 'zh-Hans') : 'en'
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState(loadPos)
  const [source, setSource] = useState<TranslateLang>(user?.active_language === 'vi' ? 'en' : 'vi')
  const [target, setTarget] = useState<TranslateLang>(user?.active_language === 'vi' ? 'vi' : learning)
  const [mode, setMode] = useState<Mode>('auto')
  const [text, setText] = useState('')
  const [listening, setListening] = useState(false)
  const [progress, setProgress] = useState<number | null>(null)
  const drag = useRef<{ dx: number; dy: number; moved: boolean } | null>(null)
  const posRef = useRef(pos) // the latest position while dragging (pointer events come faster than renders)
  const stopRef = useRef<(() => void) | undefined>(undefined)
  const status = useQuery({ queryKey: ['ai-status'], queryFn: learnApi.aiStatus, staleTime: 5 * 60_000, retry: false })
  const offline = offlineSupport()

  useEffect(() => () => stopRef.current?.(), [])

  const run = useMutation<Result, Error, { text: string; source: TranslateLang; target: TranslateLang }>({
    mutationFn: async ({ text: t, source: s, target: g }) => {
      const viaOffline = async (): Promise<Result> => {
        const out = await translateOffline(t, s, g, (p) => setProgress(p < 1 ? p : null))
        setProgress(null)
        return { text: out, target: g, via: 'offline' }
      }
      const online = !!status.data?.translate && navigator.onLine
      if (mode === 'offline' || (mode === 'auto' && !online && offline)) return viaOffline()
      try {
        const r = await learnApi.translate(t, s, g)
        return { text: r.translation, reading: r.reading, target: g, via: 'online' }
      } catch (e) {
        if (mode === 'auto' && offline) return viaOffline() // server or network down: the browser still translates
        throw new Error(errorMessage(e, 'Không dịch được lúc này.'))
      }
    },
  })

  if (!user || location.pathname.startsWith('/dich')) return null

  const translate = (t = text, s = source, g = target) => { if (t.trim()) run.mutate({ text: t.trim(), source: s, target: g }) }
  const pick = (side: 'source' | 'target', v: TranslateLang) => {
    const other = side === 'source' ? target : source
    const fix = v === other || (isZh(v) && isZh(other)) ? (v === 'vi' ? learning : 'vi') : other
    if (side === 'source') { setSource(v); setTarget(fix) } else { setTarget(v); setSource(fix) }
  }
  const swap = () => {
    setSource(target); setTarget(source)
    if (run.data) { setText(run.data.text); translate(run.data.text, target, source) }
  }
  const talk = async () => {
    if (listening) { stopRef.current?.(); return }
    const { result, stop } = listen(locale(source), 12000)
    stopRef.current = stop
    setListening(true)
    try {
      const heard = (await result).alternatives[0] ?? ''
      setText(heard)
      translate(heard)
    } catch (e) {
      message.warning((e as Error).message)
    } finally {
      setListening(false)
    }
  }

  // drag the bubble (pointer events: mouse and touch); a tap without moving opens the panel
  const onDown = (e: React.PointerEvent) => {
    try { (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId) } catch { /* pointer already gone */ }
    drag.current = { dx: window.innerWidth - e.clientX - pos.x, dy: window.innerHeight - e.clientY - pos.y, moved: false }
  }
  const onMove = (e: React.PointerEvent) => {
    const d = drag.current
    if (!d) return
    const x = Math.min(Math.max(8, window.innerWidth - e.clientX - d.dx), window.innerWidth - SIZE - 8)
    const y = Math.min(Math.max(8, window.innerHeight - e.clientY - d.dy), window.innerHeight - SIZE - 8)
    if (Math.abs(x - posRef.current.x) + Math.abs(y - posRef.current.y) > 4) d.moved = true
    if (d.moved) { posRef.current = { x, y }; setPos({ x, y }) }
  }
  const onUp = () => {
    const d = drag.current
    drag.current = null
    if (!d) return
    if (d.moved) {
      try { localStorage.setItem(POS_KEY, JSON.stringify(posRef.current)) } catch { /* storage blocked */ }
    } else {
      setOpen((o) => !o)
    }
  }

  const out = run.data
  const panelRight = Math.min(pos.x, Math.max(8, window.innerWidth - 380))
  const panelBottom = pos.y + SIZE + 12 > window.innerHeight - 420 ? 8 : pos.y + SIZE + 12
  const options = (other: TranslateLang) => LANGS.map((l) => ({ value: l.value, label: l.label, disabled: l.value === other || (isZh(l.value) && isZh(other)) }))

  return (
    <>
      {open && (
        <section aria-label="Dịch nhanh" style={{ right: panelRight, bottom: panelBottom }}
          className="fixed z-50 w-[min(360px,calc(100vw-16px))] lp-card p-4 flex flex-col gap-3 shadow-2xl animate-rise">
          <div className="flex items-center gap-2">
            <TranslationOutlined className="text-brand-600 text-lg" />
            <strong className="flex-1">Dịch nhanh</strong>
            <Tooltip title="Mở trang Dịch đầy đủ"><Link to="/dich" onClick={() => setOpen(false)}><Button type="text" size="small" icon={<ExpandOutlined />} aria-label="Mở trang Dịch" /></Link></Tooltip>
            <Button type="text" size="small" icon={<CloseOutlined />} onClick={() => setOpen(false)} aria-label="Đóng" />
          </div>
          <Segmented size="small" block value={mode} onChange={(v) => setMode(v as Mode)}
            options={[{ label: 'Tự động', value: 'auto' }, { label: 'Online (AI)', value: 'online' }, { label: 'Offline', value: 'offline', disabled: !offline }]} />
          <div className="flex items-center gap-1">
            <Select<TranslateLang> size="small" value={source} onChange={(v) => pick('source', v)} options={options(target)} className="flex-1" aria-label="Dịch từ" />
            <Button size="small" type="text" icon={<SwapOutlined />} onClick={swap} aria-label="Đổi chiều" />
            <Select<TranslateLang> size="small" value={target} onChange={(v) => pick('target', v)} options={options(source)} className="flex-1" aria-label="Dịch sang" />
          </div>
          <Input.TextArea value={text} onChange={(e) => setText(e.target.value)} maxLength={500} autoSize={{ minRows: 2, maxRows: 5 }}
            lang={langTag(source)} placeholder={listening ? 'Đang nghe…' : 'Nhập hoặc bấm mic để nói'} autoFocus
            onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); translate() } }} />
          <div className="flex items-center gap-2">
            {canRecognise() && (
              <Button shape="circle" type={listening ? 'primary' : 'default'} danger={listening} icon={<AudioOutlined />} onClick={talk} aria-label="Nói" />
            )}
            <span className="flex-1 text-xs text-slate-400">{progress != null ? `Đang tải gói dịch offline… ${Math.round(progress * 100)}%` : ''}</span>
            <Button type="primary" loading={run.isPending} disabled={!text.trim()} onClick={() => translate()}>Dịch</Button>
          </div>
          {(out || run.isError) && (
            <div className="rounded-xl bg-slate-50 p-3 flex flex-col gap-1" aria-live="polite">
              {run.isError ? <span className="text-red-600 text-sm">{run.error.message}</span> : out && (
                <>
                  <div lang={langTag(out.target)} className="text-base text-slate-900 whitespace-pre-wrap">{out.text}</div>
                  {out.reading && <div className="text-xs text-slate-500">{out.reading}</div>}
                  <div className="flex items-center gap-1">
                    <Button type="text" size="small" icon={<SoundOutlined />} onClick={() => speak(out.text, locale(out.target))} aria-label="Nghe bản dịch" />
                    <Button type="text" size="small" icon={<CopyOutlined />} aria-label="Chép"
                      onClick={() => navigator.clipboard?.writeText(out.text).then(() => message.success('Đã chép'))} />
                    <span className="flex-1" />
                    <span className="rounded-md bg-slate-200/70 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                      {out.via === 'online' ? 'Dịch online (AI)' : 'Dịch offline trên máy'}
                    </span>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}
      <button type="button" aria-label="Dịch nhanh" title="Dịch nhanh (kéo để di chuyển)"
        onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}
        style={{ right: pos.x, bottom: pos.y, width: SIZE, height: SIZE, touchAction: 'none' }}
        className="fixed z-50 rounded-full bg-brand-600 hover:bg-brand-700 text-white shadow-xl flex items-center justify-center cursor-grab active:cursor-grabbing select-none">
        {open ? <CloseOutlined className="text-xl" /> : <TranslationOutlined className="text-2xl" />}
      </button>
    </>
  )
}
