import { useEffect, useRef, useState } from 'react'
import { AudioOutlined, BulbFilled, LoadingOutlined } from '@ant-design/icons'
import { Button, Modal } from 'antd'
import { speechApi, type PronunciationResult, type SpeechError, type SpeechUnit } from '../api/speech'
import { errorMessage } from '../api/client'
import { canRecord, startRecording, type Recording } from '../lib/recordWav'
import { langTag } from './TargetWord'

const MAX_SECONDS = 7
const tone = (s: string) => (s === 'right' || s === 'ok' ? 'text-emerald-600' : s === 'close' ? 'text-amber-500' : 'text-red-600')
const line = (s: string) => (s === 'right' || s === 'ok' ? 'border-emerald-500' : s === 'close' ? 'border-amber-400' : 'border-red-500')

/**
 * "Chấm chi tiết": record the learner, the server scores the recording sound by sound (BE apps.speech) and the
 * result shows which syllable / sound was wrong and how to fix it. Tones are checked from the pitch (experimental).
 */
export default function PronunciationCheck({
  translationId,
  sentenceId,
  language,
  onScore,
}: {
  translationId?: number
  sentenceId?: number
  /** vi | en | zh-Hans | zh-Hant */
  language: string
  onScore?: (score: number) => void
}) {
  const [phase, setPhase] = useState<'idle' | 'recording' | 'scoring'>('idle')
  const [result, setResult] = useState<PronunciationResult | null>(null)
  const [error, setError] = useState('')
  const [left, setLeft] = useState(MAX_SECONDS)
  const [open, setOpen] = useState<number | null>(null)
  const rec = useRef<Recording | null>(null)
  const timer = useRef<number | undefined>(undefined)
  // a new word / sentence: the parent gives this component a new key, so the state starts fresh
  useEffect(
    () => () => {
      window.clearInterval(timer.current)
      rec.current?.cancel()
    },
    [],
  )
  if (!canRecord()) return null

  const stop = async () => {
    window.clearInterval(timer.current)
    const r = rec.current
    rec.current = null
    if (!r) return
    setPhase('scoring')
    try {
      const res = await speechApi.assess(await r.stop(), { translation_id: translationId, sentence_id: sentenceId })
      setResult(res)
      onScore?.(res.score)
    } catch (e) {
      setError(e instanceof Error && !('isAxiosError' in e) ? e.message : errorMessage(e, 'Chưa chấm được, thử lại nhé.'))
    } finally {
      setPhase('idle')
    }
  }

  const go = async () => {
    if (phase === 'recording') return stop()
    setError('')
    setResult(null)
    try {
      rec.current = await startRecording()
    } catch (e) {
      setError((e as Error).message)
      return
    }
    setPhase('recording')
    setLeft(MAX_SECONDS)
    let n = MAX_SECONDS
    timer.current = window.setInterval(() => {
      n -= 1
      setLeft(n)
      if (n <= 0) void stop()
    }, 1000)
  }

  const zh = language.startsWith('zh')
  const toneName = (t: string | number) => (zh ? `thanh ${t}` : String(t))
  const unit = open != null ? result?.units[open] : undefined

  return (
    <div className="flex flex-col items-center gap-3 w-full">
      <Button
        size="large"
        type="primary"
        danger={phase === 'recording'}
        disabled={phase === 'scoring'}
        onClick={go}
        icon={phase === 'scoring' ? <LoadingOutlined /> : <AudioOutlined />}
      >
        {phase === 'recording'
          ? `Đang ghi… ${left}s (bấm để dừng)`
          : phase === 'scoring'
            ? 'Đang chấm từng âm…'
            : result
              ? 'Đọc lại'
              : 'Bấm và đọc to'}
      </Button>
      {error && <div className="text-red-600 text-sm text-center">{error}</div>}
      {result && (
        <div className="flex flex-col items-center gap-3 w-full animate-rise">
          <div className={`text-xl font-extrabold ${tone(result.verdict)}`}>
            {result.verdict === 'right' ? 'Phát âm chuẩn!' : result.verdict === 'close' ? 'Gần đúng rồi' : 'Chưa đúng'}{' '}
            <span className="num">{result.score}</span>/100
          </div>
          <div className="flex flex-wrap justify-center gap-2 text-sm font-bold">
            <Chip label="Âm" value={result.phone_score} />
            {result.tone_score != null && <Chip label="Thanh điệu*" value={result.tone_score} />}
            <Chip label="Đầy đủ" value={result.completeness} />
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {result.units.map((u, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setOpen(i)}
                className={`px-2 pb-1 border-b-4 rounded-lg hover:bg-slate-50 cursor-pointer ${line(u.status)}`}
              >
                <div lang={langTag(language)} className={`text-2xl font-extrabold ${tone(u.status)}`}>
                  {u.text}
                </div>
                {zh && u.reading && <div className="text-xs text-slate-500">{u.reading}</div>}
              </button>
            ))}
          </div>
          <div className="text-xs text-slate-400">Bấm vào một chữ để xem từng âm</div>
          {result.errors.slice(0, 3).map((e, i) => (
            <Tip key={i} error={e} />
          ))}
          {result.tone_score != null && (
            <div className="text-xs text-slate-400 text-center">
              * Chấm thanh điệu theo cao độ giọng – đang thử nghiệm, có thể chưa chính xác.
            </div>
          )}
        </div>
      )}
      <Modal open={!!unit} onCancel={() => setOpen(null)} footer={null} title="Chi tiết phát âm">
        {unit && <UnitDetail unit={unit} errors={result!.errors.filter((e) => e.unit === open)} language={language} toneName={toneName} />}
      </Modal>
    </div>
  )
}

function Chip({ label, value }: { label: string; value: number }) {
  const c = value >= 90 ? 'bg-emerald-50 text-emerald-700' : value >= 60 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'
  return (
    <span className={`px-3 py-1 rounded-full ${c}`}>
      {label} <span className="num">{value}</span>
    </span>
  )
}

function Tip({ error }: { error: SpeechError }) {
  return (
    <div className={`w-full flex gap-2 rounded-xl p-3 text-sm ${error.severity === 'major' ? 'bg-red-50' : 'bg-amber-50'}`}>
      <BulbFilled className={error.severity === 'major' ? 'text-red-500 mt-0.5' : 'text-amber-500 mt-0.5'} />
      <span className="text-slate-700">{error.tip}</span>
    </div>
  )
}

function UnitDetail({
  unit,
  errors,
  language,
  toneName,
}: {
  unit: SpeechUnit
  errors: SpeechError[]
  language: string
  toneName: (t: string | number) => string
}) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <div lang={langTag(language)} className={`text-4xl font-extrabold ${tone(unit.status)}`}>
          {unit.text}
        </div>
        {unit.reading && <div className="text-slate-500">{unit.reading}</div>}
      </div>
      <div className="text-sm font-bold">Từng âm (âm đúng → máy nghe được)</div>
      <div className="flex flex-wrap gap-2">
        {unit.phones.map((p, i) => (
          <span key={i} className={`px-2.5 py-1 rounded-lg border font-semibold ${line(p.status)} ${tone(p.status)}`}>
            {p.status === 'ok' ? `/${p.expected}/` : `/${p.expected}/ → ${p.heard ? `/${p.heard}/` : 'thiếu'}`}
          </span>
        ))}
      </div>
      {unit.tone && (
        <div className={`font-semibold ${tone(unit.tone.status)}`}>
          Thanh điệu (thử nghiệm): cần {toneName(unit.tone.expected)}, máy nghe {toneName(unit.tone.heard)}
        </div>
      )}
      {errors.map((e, i) => (
        <Tip key={i} error={e} />
      ))}
    </div>
  )
}
