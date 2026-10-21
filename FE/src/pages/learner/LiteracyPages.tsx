import { App, Button, Input, Progress, Result, Spin } from 'antd'
import type { InputRef } from 'antd'
import { CheckCircleFilled, CloseCircleFilled, LockFilled, SoundOutlined, StarFilled } from '@ant-design/icons'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { errorMessage } from '../../api/client'
import { literacyApi, type LitCheck, type LitExercise, type LitFinish, type LitIntro, type LitLesson } from '../../api/literacy'
import { speak } from '../../lib/speech'
import { SPECIAL_LETTERS, toneAtCursor } from '../../lib/vietnamese'
import WordPicture from '../../components/WordPicture'

const VI = 'vi-VN'
const say = (text: string) => speak(text, VI)

function SpeakButton({ text, size = 'large' }: { text: string; size?: 'large' | 'middle' }) {
  return <Button shape="circle" size={size} type="primary" icon={<SoundOutlined />} onClick={() => say(text)} />
}

/** Tappable spelling steps: bờ – a – ba – huyền – bà */
function SpellSteps({ steps }: { steps: string[] }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-1 text-lg">
      {steps.map((s, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <span className="text-slate-300">–</span>}
          <button type="button" onClick={() => say(s)}
            className={`px-2 py-0.5 rounded-lg cursor-pointer hover:bg-brand-50 ${i === steps.length - 1 ? 'font-bold text-brand-700' : 'text-slate-600'}`}>
            {s}
          </button>
        </span>
      ))}
    </div>
  )
}

// ====================================================================== lesson map

export function LiteracyMapPage() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useQuery({ queryKey: ['literacy-lessons'], queryFn: literacyApi.lessons })
  if (isLoading) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (error || !data) return <Result status="warning" title={errorMessage(error)} />

  const done = data.lessons.filter((l) => l.status === 'done').length
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <div className="rounded-3xl bg-gradient-to-r from-amber-100 to-pink-100 p-6 flex items-center gap-4">
        <div className="text-6xl">📖</div>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-800 m-0">Học đọc – viết tiếng Việt</h1>
          <p className="text-slate-600 m-0">Học âm, dấu thanh, vần rồi tập đọc, tập viết từng câu.</p>
          <Progress percent={Math.round((done / data.lessons.length) * 100)} format={() => `${done}/${data.lessons.length} bài`} />
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {data.lessons.map((l) => {
          const locked = l.status === 'locked'
          return (
            <button key={l.n} type="button" disabled={locked} onClick={() => navigate(`/doc-viet/${l.n}`)}
              className={`rounded-2xl border-2 p-3 flex flex-col items-center gap-1 text-center transition ${
                locked ? 'border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed'
                  : l.status === 'done' ? 'border-green-300 bg-green-50 cursor-pointer hover:shadow'
                    : 'border-brand-300 bg-white cursor-pointer hover:shadow'}`}>
              <div className="text-xs text-slate-400">Bài {l.n}</div>
              <div className="text-2xl font-bold text-slate-800 min-h-8">
                {locked ? <LockFilled className="text-slate-400" /> : l.review ? '✍️' : l.units.slice(0, 3).map((u) => u.kind === 'thanh' ? u.symbol || '·' : u.code).join(' ')}
              </div>
              <div className="text-xs text-slate-600 line-clamp-2">{l.title}</div>
              <div className="flex gap-0.5 text-amber-400">
                {[1, 2, 3].map((s) => <StarFilled key={s} className={s <= l.stars ? '' : 'text-slate-200'} />)}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ====================================================================== lesson

function IntroCard({ intro }: { intro: LitIntro }) {
  const u = intro.unit
  useEffect(() => { say(u.kind === 'thanh' ? u.label : u.sound.split(' – ').pop() ?? u.code) }, [u])
  return (
    <div className="flex flex-col items-center gap-5 w-full">
      <div className="text-slate-500">{u.kind === 'am' ? 'Âm mới' : u.kind === 'van' ? 'Vần mới' : 'Dấu thanh mới'}</div>
      <button type="button" onClick={() => say(u.kind === 'thanh' ? u.label : u.sound.split(' – ').pop() ?? u.code)}
        className="text-8xl font-bold text-brand-700 cursor-pointer">
        {u.kind === 'thanh' ? (u.symbol || '–') : u.code}
      </button>
      <div className="text-xl text-slate-700">{u.kind === 'thanh' ? u.label : `đọc là “${u.sound.split(' – ').pop()}”`}</div>
      {intro.rhyme_spell.length > 1 && <SpellSteps steps={intro.rhyme_spell} />}
      <div className="flex flex-col gap-2 w-full">
        {intro.examples.map((e) => (
          <div key={e.text} className="rounded-2xl bg-slate-50 py-2"><SpellSteps steps={e.spell} /></div>
        ))}
      </div>
      {intro.words.length > 0 && (
        <div className="flex flex-wrap justify-center gap-3">
          {intro.words.map((w) => (
            <button key={w.id} type="button" onClick={() => say(w.text)}
              className="rounded-2xl border-2 border-slate-200 px-4 py-2 flex flex-col items-center cursor-pointer hover:border-brand-400">
              <WordPicture image={w.image} emoji={w.emoji} alt={w.text} height="h-24" />
              <span className="text-lg font-medium">{w.text}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function Options({ options, picked, expected, onPick, big = true }: {
  options: string[]; picked: string | null; expected: string | null; onPick: (o: string) => void; big?: boolean
}) {
  return (
    <div className="grid grid-cols-2 gap-3 w-full">
      {options.map((o) => {
        const state = expected === null ? (picked === o ? 'border-brand-500' : 'border-slate-200 hover:border-brand-400')
          : o === expected ? 'border-green-500 bg-green-50' : picked === o ? 'border-red-400 bg-red-50' : 'border-slate-200 opacity-60'
        return (
          <button key={o} type="button" disabled={expected !== null} onClick={() => { say(o); onPick(o) }}
            className={`rounded-2xl border-2 py-4 ${big ? 'text-3xl' : 'text-lg'} font-semibold cursor-pointer transition ${state}`}>
            {o}
          </button>
        )
      })}
    </div>
  )
}

/** Text box + on-screen Vietnamese letters and tone marks (children often have no Vietnamese keyboard). */
function VietInput({ value, onChange, onEnter, disabled }: { value: string; onChange: (v: string) => void; onEnter: () => void; disabled: boolean }) {
  const ref = useRef<InputRef>(null)
  const insert = (fn: (text: string, cursor: number) => { text: string; cursor: number }) => {
    const el = ref.current?.input
    const cursor = el?.selectionStart ?? value.length
    const r = fn(value, cursor)
    onChange(r.text)
    requestAnimationFrame(() => { el?.focus(); el?.setSelectionRange(r.cursor, r.cursor) })
  }
  return (
    <div className="flex flex-col gap-3 w-full items-center">
      <Input ref={ref} size="large" lang="vi" value={value} disabled={disabled} autoFocus autoComplete="off"
        onChange={(e) => onChange(e.target.value)} onPressEnter={onEnter} className="max-w-md text-center text-2xl" />
      {!disabled && (
        <div className="flex flex-wrap justify-center gap-1">
          {SPECIAL_LETTERS.map((l) => (
            <Button key={l} onClick={() => insert((t, c) => ({ text: t.slice(0, c) + l + t.slice(c), cursor: c + 1 }))}>{l}</Button>
          ))}
          <span className="w-2" />
          {[['huyen', '`'], ['sac', '´'], ['hoi', '?'], ['nga', '~'], ['nang', '.'], ['ngang', '⌫ dấu']].map(([tone, label]) => (
            <Button key={tone} type="dashed" onClick={() => insert((t, c) => toneAtCursor(t, c, tone))}>{label}</Button>
          ))}
        </div>
      )}
    </div>
  )
}

export function LiteracyLessonPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const n = Number(useParams().n)
  const [lesson, setLesson] = useState<LitLesson | null>(null)
  const [error, setError] = useState('')
  const [step, setStep] = useState(0) // intro cards first, then exercises
  const [picked, setPicked] = useState<string | null>(null)
  const [build, setBuild] = useState<{ onset?: string; rhyme?: string; tone?: string }>({})
  const [typed, setTyped] = useState('')
  const [result, setResult] = useState<LitCheck | null>(null)
  const [finish, setFinish] = useState<LitFinish | null>(null)
  const [checking, setChecking] = useState(false)
  const started = useRef(Date.now())

  useEffect(() => {
    setLesson(null); setStep(0); setFinish(null); setError('')
    literacyApi.lesson(n).then(setLesson).catch((e) => setError(errorMessage(e)))
  }, [n])

  const introCount = lesson?.intro.length ?? 0
  const total = lesson ? introCount + lesson.exercises.length : 0
  const ex: LitExercise | undefined = lesson && step >= introCount ? lesson.exercises[step - introCount] : undefined

  useEffect(() => {
    setPicked(null); setBuild({}); setTyped(''); setResult(null)
    started.current = Date.now()
    if (ex && ex.type !== 'find_unit') setTimeout(() => say(ex.tts.text), 300)
  }, [ex])

  const submit = async (answer: unknown) => {
    if (!ex || result || checking) return
    setChecking(true)
    try {
      const r = await literacyApi.check(ex.token, answer, Date.now() - started.current)
      setResult(r)
      say(r.correct ? 'Đúng rồi!' : r.word || r.expected)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setChecking(false)
    }
  }

  const next = async () => {
    if (!lesson) return
    if (step + 1 < total) { setStep(step + 1); return }
    try {
      setFinish(await literacyApi.finish(n, lesson.session, lesson.exercises.length))
      queryClient.invalidateQueries({ queryKey: ['literacy-lessons'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  if (error) return <Result status="info" title={error} extra={<Button onClick={() => navigate('/doc-viet')}>Về lộ trình</Button>} />
  if (!lesson) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (finish) {
    return (
      <Result
        icon={<div className="text-7xl">{finish.passed ? '🎉' : '💪'}</div>}
        title={finish.passed ? 'Giỏi lắm! Con đã xong bài học.' : 'Cố lên! Mình học lại bài này nhé.'}
        subTitle={
          <div className="flex flex-col items-center gap-2">
            <div className="flex gap-1 text-3xl text-amber-400">
              {[1, 2, 3].map((s) => <StarFilled key={s} className={s <= finish.stars ? '' : 'text-slate-200'} />)}
            </div>
            <span>Đúng ngay lần đầu {finish.correct_first_try}/{finish.total} câu</span>
          </div>
        }
        extra={[
          <Button key="map" size="large" onClick={() => navigate('/doc-viet')}>Về lộ trình</Button>,
          finish.next_unlocked
            ? <Button key="next" size="large" type="primary" onClick={() => navigate(`/doc-viet/${n + 1}`)}>Bài tiếp theo</Button>
            : <Button key="again" size="large" type="primary" onClick={() => window.location.reload()}>Học lại</Button>,
        ]}
      />
    )
  }

  const expected = result ? result.expected : null
  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-5">
      <div className="flex items-center gap-3">
        <Button onClick={() => navigate('/doc-viet')}>✕</Button>
        <Progress percent={Math.round((step / total) * 100)} showInfo={false} strokeColor="#f59e0b" className="flex-1 m-0" />
      </div>
      <div className="text-center text-slate-500 font-medium">Bài {lesson.n}: {lesson.title}</div>
      <AnimatePresence mode="wait">
        <motion.div key={step} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}
          className="rounded-3xl bg-white border border-slate-200 p-6 sm:p-8 min-h-96 flex flex-col items-center gap-6">
          {!ex && <IntroCard intro={lesson.intro[step]} />}

          {ex?.type === 'listen_choose' && (
            <>
              <div className="text-lg text-slate-600">Nghe rồi chọn tiếng đúng</div>
              <SpeakButton text={ex.tts.text} />
              <Options options={ex.options} picked={picked} expected={expected} onPick={(o) => { setPicked(o); submit(o) }} />
            </>
          )}

          {ex?.type === 'find_unit' && (
            <>
              <div className="text-lg text-slate-600">{ex.question}</div>
              <button type="button" onClick={() => say(ex.syllable)} className="text-6xl font-bold cursor-pointer">{ex.syllable}</button>
              <Options options={ex.options} picked={picked} expected={expected} big={false} onPick={(o) => { setPicked(o); submit(o) }} />
            </>
          )}

          {ex?.type === 'build' && (
            <>
              <div className="text-lg text-slate-600">Nghe rồi ghép tiếng: âm đầu + vần + dấu</div>
              <SpeakButton text={ex.tts.text} />
              {([['onset', 'Âm đầu', ex.onsets.map((o) => ({ v: o, l: o === '∅' ? '(không có)' : o }))],
                ['rhyme', 'Vần', ex.rhymes.map((r) => ({ v: r, l: r }))],
                ['tone', 'Dấu', ex.tones.map((t) => ({ v: t.code, l: t.symbol ? `${t.symbol}  ${t.label}` : t.label }))]] as const).map(([key, label, opts]) => (
                <div key={key} className="w-full">
                  <div className="text-sm text-slate-400 mb-1">{label}</div>
                  <div className="flex flex-wrap gap-2">
                    {opts.map((o) => (
                      <button key={o.v} type="button" disabled={!!result} onClick={() => setBuild({ ...build, [key]: o.v })}
                        className={`rounded-xl border-2 px-4 py-2 text-xl cursor-pointer ${build[key] === o.v ? 'border-brand-500 bg-brand-50' : 'border-slate-200'}`}>
                        {o.l}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              {!result && (
                <Button type="primary" size="large" loading={checking} disabled={!build.onset || !build.rhyme || !build.tone}
                  onClick={() => submit(build)}>Kiểm tra</Button>
              )}
            </>
          )}

          {ex?.type === 'rule' && (
            <>
              <div className="text-lg text-slate-600">{ex.question}</div>
              <div className="flex items-center gap-3"><span className="text-6xl font-bold tracking-wide">{ex.pattern}</span><SpeakButton text={ex.tts.text} size="middle" /></div>
              <Options options={ex.options} picked={picked} expected={expected} onPick={(o) => { setPicked(o); submit(o) }} />
            </>
          )}

          {(ex?.type === 'dictation' || ex?.type === 'sentence') && (
            <>
              <div className="text-lg text-slate-600">{ex.type === 'sentence' ? 'Nghe rồi viết lại câu' : 'Nghe rồi viết lại'} ({ex.syllables} tiếng)</div>
              {ex.type === 'dictation' && <WordPicture image={ex.image} emoji={ex.emoji} height="h-44" />}
              <SpeakButton text={ex.tts.text} />
              <VietInput value={typed} onChange={setTyped} disabled={!!result} onEnter={() => typed.trim() && submit(typed)} />
              {!result && <Button type="primary" size="large" loading={checking} disabled={!typed.trim()} onClick={() => submit(typed)}>Kiểm tra</Button>}
              {ex.type === 'sentence' && (
                <a href={ex.source.url} target="_blank" rel="noreferrer" className="text-xs text-slate-400">Câu #{ex.source.id} · Tatoeba · {ex.source.license}</a>
              )}
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {!ex ? (
        <Button type="primary" size="large" block onClick={next}>Tiếp tục</Button>
      ) : result && (
        <div className={`rounded-2xl p-4 flex flex-col gap-3 ${result.correct ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex items-center gap-2 text-xl font-semibold">
            {result.correct ? <CheckCircleFilled className="text-green-600" /> : <CloseCircleFilled className="text-red-500" />}
            {result.correct ? `Đúng rồi!${result.xp ? ` +${result.xp} XP` : ''}` : 'Chưa đúng rồi, xem lại nhé:'}
          </div>
          {result.diff && (
            <div className="flex flex-wrap gap-2 text-2xl">
              {result.diff.map((d, i) => (
                <span key={i} className={`rounded-lg px-2 ${d.ok ? 'text-green-700' : 'bg-red-100 text-red-700'}`} title={d.hint}>
                  {d.expected || <s>{d.given}</s>}
                  {!d.ok && d.given && d.expected && <span className="text-sm text-red-400 ml-1">(con viết: {d.given}{d.hint ? ` – ${d.hint}` : ''})</span>}
                </span>
              ))}
            </div>
          )}
          {result.spell && <SpellSteps steps={result.spell} />}
          <Button type="primary" size="large" onClick={next}>Tiếp tục</Button>
        </div>
      )}
    </div>
  )
}
