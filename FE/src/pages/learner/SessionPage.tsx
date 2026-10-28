import { App, Button, Input, Result, Spin } from 'antd'
import { CloseOutlined, SoundOutlined } from '@ant-design/icons'
import { motion, AnimatePresence, animate, useReducedMotion } from 'framer-motion'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { normalizeAnswer, vocabApi, type Question, type SessionItem, type StudySession } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import TargetWord, { langTag } from '../../components/TargetWord'
import { speak } from '../../lib/speech'
import SpeakCheck from '../../components/SpeakCheck'
import WordPicture from '../../components/WordPicture'
import { Prismo, XpIcon } from '../../components/brand/Brand'
import { sfx } from '../../lib/sfx'

const PRAISE = ['Chính xác!', 'Tuyệt vời!', 'Giỏi quá!', 'Quá đỉnh!', 'Chuẩn luôn!']

/** a number that counts up from 0 after [delay] seconds */
function CountUp({ value, delay = 0, prefix = '', suffix = '' }: { value: number; delay?: number; prefix?: string; suffix?: string }) {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? value : 0)
  useEffect(() => {
    if (reduce) return setShown(value)
    const c = animate(0, value, { duration: 0.9, delay, ease: [0.22, 1, 0.36, 1], onUpdate: (v) => setShown(Math.round(v)) })
    return () => c.stop()
  }, [value, delay, reduce])
  return <>{prefix}{shown}{suffix}</>
}

/** one result on the finish screen: a coloured band with its name over a number that counts up (as on Duolingo) */
function ResultCard({ label, color, delay, children }: { label: string; color: string; delay: number; children: ReactNode }) {
  return (
    <motion.div className="rounded-2xl p-0.5" style={{ background: color }}
      initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, type: 'spring', stiffness: 380, damping: 16 }}>
      <div className="text-[11px] font-extrabold tracking-wider text-white py-1">{label}</div>
      <div className="rounded-[14px] bg-[var(--surface)] py-3 num text-2xl font-extrabold text-slate-800 flex items-center justify-center gap-1.5">
        {children}
      </div>
    </motion.div>
  )
}

/** a burst of colourful confetti when the lesson is done */
function Confetti() {
  const bits = useMemo(() => Array.from({ length: 36 }, (_, i) => ({
    x: (Math.random() - 0.5) * 700, y: -Math.random() * 380 - 80, r: Math.random() * 540,
    c: ['#1899f0', '#ce82ff', '#10c79a', '#ffb020', '#ff6b81'][i % 5], d: Math.random() * 0.25,
  })), [])
  return (
    <div className="pointer-events-none absolute left-1/2 top-40 z-10">
      {bits.map((b, i) => (
        <motion.span key={i} className="absolute block h-3 w-2 rounded-sm" style={{ background: b.c }}
          initial={{ x: 0, y: 0, opacity: 1, rotate: 0 }} animate={{ x: b.x, y: [0, b.y, b.y + 520], opacity: [1, 1, 0], rotate: b.r }}
          transition={{ duration: 2.2, delay: b.d, ease: 'easeOut' }} />
      ))}
    </div>
  )
}

interface Step {
  item: SessionItem
  question: Question
  graded: boolean
  firstTry: boolean
}

type Summary = Awaited<ReturnType<typeof vocabApi.finish>>

function buildSteps(session: StudySession, kid: boolean): Step[] {
  const flash: Step[] = []
  const quiz: Step[] = []
  const final: Step[] = []
  const isZh = session.language === 'zh'
  for (const item of session.items) {
    const by = Object.fromEntries(item.questions.map((q) => [q.type, q])) as Record<string, Question>
    if (session.kind !== 'review' && by.flashcard) flash.push({ item, question: by.flashcard, graded: false, firstTry: true })
    const mc = [by.choose_meaning, by.choose_pinyin, by.choose_target].filter(Boolean)
    if (mc.length) quiz.push({ item, question: mc[Math.floor(Math.random() * mc.length)], graded: false, firstTry: true })
    const typed = !kid && !isZh ? (session.language === 'en' && Math.random() < 0.5 ? by.listen_type : by.type_target) : undefined
    const graded = typed ?? by.choose_target ?? by.choose_meaning ?? by.type_target ?? by.listen_type
    if (graded) final.push({ item, question: graded, graded: true, firstTry: true })
  }
  return [...flash, ...quiz, ...final]
}

export default function SessionPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const user = useAuth((s) => s.user)
  const [session, setSession] = useState<StudySession | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [index, setIndex] = useState(0)
  const [feedback, setFeedback] = useState<null | { correct: boolean; answer: string; picked: string; praise: string }>(null)
  const [typed, setTyped] = useState('')
  const [flipped, setFlipped] = useState(false)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [error, setError] = useState('')
  const [combo, setCombo] = useState(0)
  const started = useRef(Date.now())
  const startedOnce = useRef(false)

  const kind = (params.get('kind') ?? 'learn') as StudySession['kind']
  const topic = params.get('topic') ? Number(params.get('topic')) : undefined
  // "Ôn lại những từ còn sai" from a lost game round: exactly those words
  const words = params.get('words')?.split(',').map(Number).filter(Boolean)

  useEffect(() => {
    if (startedOnce.current) return
    startedOnce.current = true
    vocabApi.startSession(kind, topic, undefined, words)
      .then((s) => { setSession(s); setSteps(buildSteps(s, user?.learner_type === 'kid')) })
      .catch((e) => setError(errorMessage(e)))
  }, [kind, topic, user?.learner_type])

  const step = steps[index]
  const isZh = session?.language === 'zh'
  const zhTag = isZh ? langTag(session?.script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined
  const progress = steps.length ? Math.round((index / steps.length) * 100) : 0

  useEffect(() => {
    started.current = Date.now()
    setTyped('')
    setFlipped(false)
    if (step?.question.type === 'listen_type') speak(step.question.audio.text, step.question.audio.tts_locale)
  }, [index, step])

  const finish = async () => {
    if (!session) return
    try {
      setSummary(await vocabApi.finish(session.id))
      sfx('complete', 0.7)
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  const next = () => {
    setFeedback(null)
    if (index + 1 >= steps.length) finish()
    else setIndex(index + 1)
  }

  const submit = async (answer: string) => {
    if (!session || !step || feedback) return
    const q = step.question
    let correct: boolean
    if (q.type === 'type_target' || q.type === 'listen_type') {
      const a = normalizeAnswer(answer, isZh)
      correct = q.accepted.some((x) => normalizeAnswer(x, isZh) === a)
    } else if ('answer' in q) {
      correct = answer === q.answer
    } else {
      correct = true
    }
    setFeedback({ correct, answer: 'answer' in q ? q.answer : '', picked: answer, praise: PRAISE[Math.floor(Math.random() * PRAISE.length)] })
    setCombo((c) => (correct ? c + 1 : 0))
    sfx(correct ? 'correct' : 'wrong')
    if (!correct) setSteps((s) => [...s, { ...step, graded: false, firstTry: false }])
    vocabApi.answer(session.id, {
      personal_word: step.item.personal_word, question_type: q.type, correct, first_try: step.firstTry,
      graded: step.graded && step.firstTry, response_ms: Date.now() - started.current, answer,
    }).catch(() => undefined)
  }

  const meaningPrompt = useMemo(() => {
    if (!step) return null
    const card = step.item.card
    return (
      <div className="flex flex-col items-center gap-2">
        {/* learning Vietnamese (children): the picture alone is the prompt – the Vietnamese word is the answer */}
        <WordPicture image={card.image} emoji={card.emoji} credit={card.image_credit} source={card.image_source}
          height={session?.language === 'vi' ? 'h-48' : 'h-32'} />
        {session?.language !== 'vi' && <div className="text-2xl font-black text-slate-800">{card.meaning_vi}</div>}
      </div>
    )
  }, [step, session?.language])

  if (error) return <Result status="info" title={error} extra={<Button type="primary" onClick={() => navigate('/vocab')}>Chọn chủ đề để học</Button>} />
  if (!session) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (summary) {
    const missed = session.items.filter((i) => summary.needs_more_practice.includes(i.personal_word))
    const perfect = summary.correct_first_try === summary.completed_count
    return (
      <div className="relative max-w-xl mx-auto flex flex-col items-center text-center gap-5 pt-4">
        <Confetti />
        <motion.div initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 11 }}>
          <Prismo mood="celebrate" size={170} />
        </motion.div>
        <motion.h1 className="text-3xl font-extrabold text-slate-800 m-0"
          initial={{ y: -16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2, type: 'spring', stiffness: 300, damping: 18 }}>
          {summary.level_up ? `Bạn đã lên Cấp ${summary.level_up}!` : perfect ? 'Hoàn hảo! Không sai câu nào!' : 'Hoàn thành bài học!'}
        </motion.h1>
        <div className="grid grid-cols-2 gap-3 w-full">
          <ResultCard label="KINH NGHIỆM" color="#ffb020" delay={0.45}>
            <XpIcon size={26} /><CountUp value={summary.xp_earned} prefix="+" delay={0.55} />
          </ResultCard>
          <ResultCard label="ĐÚNG NGAY LẦN ĐẦU" color="#10c79a" delay={0.6}>
            <CountUp value={summary.correct_first_try} delay={0.7} />/{summary.completed_count}
          </ResultCard>
        </div>
        {missed.length > 0 && (
          <div className="lp-card p-4 w-full">
            <div className="font-bold text-slate-700 mb-2">Từ cần ôn thêm</div>
            <div className="flex flex-wrap justify-center gap-2">
              {missed.map((i) => <span key={i.item_id} lang={zhTag} className="px-3 py-1 rounded-full bg-amber-50 text-amber-700 font-bold">{i.card.target?.text} – {i.card.meaning_vi}</span>)}
            </div>
          </div>
        )}
        <div className="flex flex-wrap justify-center gap-3 w-full animate-rise" style={{ animationDelay: '900ms' }}>
          <Button size="large" onClick={() => navigate('/')}>Về trang chủ</Button>
          <Button size="large" type="primary" onClick={() => window.location.reload()}>Học tiếp</Button>
        </div>
      </div>
    )
  }
  if (!step) return null
  const q = step.question

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-5 pb-36">
      <div className="flex items-center gap-3">
        <button type="button" onClick={() => navigate('/')} aria-label="Thoát bài học"
          className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 cursor-pointer transition">
          <CloseOutlined />
        </button>
        {/* a thick tube that fills with a little spring and a light stripe on top, as on Duolingo */}
        <div className="flex-1 h-4 rounded-full bg-slate-200 overflow-hidden" role="progressbar" aria-valuemin={0} aria-valuemax={steps.length}
          aria-valuenow={Math.min(index, steps.length)} aria-label="Tiến độ bài học">
          <motion.div className="h-full rounded-full prism-bg px-2 pt-[3px]" initial={false} animate={{ width: `${Math.max(progress, 4)}%` }}
            transition={{ type: 'spring', stiffness: 170, damping: 17 }}>
            <div className="h-[4px] rounded-full bg-white/35" />
          </motion.div>
        </div>
        {combo >= 2 && (
          <motion.span key={combo} initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 14 }}
            className="num text-sm font-extrabold text-amber-500 whitespace-nowrap" title="Số câu đúng liên tiếp">
            ×{combo}
          </motion.span>
        )}
        <span className="num text-sm font-bold text-slate-500 w-14 text-right">{Math.min(index + 1, steps.length)}/{steps.length}</span>
      </div>
      <AnimatePresence mode="wait">
        <motion.div key={index} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="lp-card p-6 sm:p-8 min-h-80 flex flex-col items-center justify-center gap-6">
          {q.type === 'flashcard' && (
            <button type="button" onClick={() => setFlipped(!flipped)} className="w-full flex flex-col items-center gap-4 cursor-pointer">
              {session.language !== 'vi' && <WordPicture image={step.item.card.image} credit={step.item.card.image_credit} source={step.item.card.image_source} />}
              <TargetWord target={q.front} size="xl" />
              {session.language === 'vi'
                ? (flipped
                    ? <WordPicture image={step.item.card.image} emoji={step.item.card.emoji || '—'} credit={step.item.card.image_credit} source={step.item.card.image_source} height="h-48" />
                    : <div className="text-slate-400">Chạm để xem hình</div>)
                : (flipped ? <div className="text-2xl text-slate-700">{q.back || '—'}</div> : <div className="text-slate-400">Chạm để xem nghĩa tiếng Việt</div>)}
            </button>
          )}
          {/* once the card is turned over: say the word and get a score (only where the browser can listen) */}
          {q.type === 'flashcard' && flipped && (
            <SpeakCheck text={q.front.text} language={q.front.language} locale={q.front.tts_locale} compact />
          )}

          {(q.type === 'choose_target' || q.type === 'choose_meaning' || q.type === 'choose_pinyin') && (
            <>
              {q.type === 'choose_target' && meaningPrompt}
              {q.type === 'choose_meaning' && <TargetWord target={q.prompt} size="lg" showReading={false} />}
              {q.type === 'choose_pinyin' && <div lang={zhTag} className="text-5xl font-semibold">{q.prompt}</div>}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                {q.options.map((opt, i) => {
                  const state = !feedback ? '' : opt === q.answer ? 'is-right' : opt === feedback.picked ? 'is-wrong' : 'opacity-60'
                  return (
                    // the options deal in one after another
                    <button key={opt} type="button" disabled={!!feedback} onClick={() => submit(opt)}
                      lang={q.type === 'choose_target' ? zhTag : undefined} style={{ animationDelay: `${i * 60}ms` }}
                      className={`btn-3d animate-deal px-4 py-4 text-lg font-semibold text-slate-700 cursor-pointer disabled:cursor-default ${state}`}>
                      {opt}
                    </button>
                  )
                })}
              </div>
            </>
          )}

          {(q.type === 'type_target' || q.type === 'listen_type') && (
            <>
              {q.type === 'type_target' ? meaningPrompt : (
                <button type="button" onClick={() => speak(q.audio.text, q.audio.tts_locale)} aria-label="Nghe lại"
                  className="h-24 w-24 rounded-3xl prism-bg text-white text-4xl grid place-items-center cursor-pointer hover:bg-brand-700 btn-lip">
                  <SoundOutlined />
                </button>
              )}
              <div className="text-slate-500 font-semibold">{q.type === 'listen_type' ? 'Nghe phát âm và gõ lại từ đã nghe.' : 'Gõ lại từ bằng ngôn ngữ đang học'}</div>
              <Input size="large" value={typed} lang={zhTag} disabled={!!feedback} autoFocus
                onChange={(e) => setTyped(e.target.value)} onPressEnter={() => typed && submit(typed)}
                className={`max-w-sm text-center ${feedback && !feedback.correct ? 'lp-shake' : ''}`} />
              {!feedback && <Button type="primary" size="large" disabled={!typed} onClick={() => submit(typed)}>Kiểm tra</Button>}
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {/* answer bar: fixed at the bottom like a game, green / red with Prismo's reaction */}
      <div className={`fixed inset-x-0 bottom-0 z-40 border-t-2 transition-colors md:left-[var(--nav-w,256px)] ${
        feedback ? (feedback.correct ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-400') : 'bg-white border-slate-200'}`}
        style={{ paddingBottom: 'max(0.75rem, env(safe-area-inset-bottom))' }}>
        <div className="max-w-2xl mx-auto px-4 pt-3 flex items-center gap-3">
          {feedback ? (
            // the verdict rises into the bar; Prismo hops in on a spring
            <motion.div key={`verdict-${index}`} className="flex-1 min-w-0 flex items-center gap-3"
              initial={{ y: 24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.26, ease: [0.22, 1, 0.36, 1] }}>
              <motion.div className="shrink-0" initial={{ scale: 0.4 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 420, damping: 12 }}>
                <Prismo mood={feedback.correct ? 'celebrate' : 'sad'} size={64} />
              </motion.div>
              <div className="flex-1 min-w-0">
                <div className={`text-xl font-extrabold ${feedback.correct ? 'text-emerald-600' : 'text-red-500'}`}>
                  {feedback.correct ? feedback.praise : 'Chưa đúng rồi'}
                </div>
                {feedback.correct
                  ? combo >= 3 && <div className="text-emerald-700 font-bold">{combo} câu đúng liên tiếp</div>
                  : <div className="text-slate-700 font-bold break-words">Đáp án: <span lang={zhTag}>{feedback.answer}</span></div>}
              </div>
            </motion.div>
          ) : <div className="flex-1" />}
          {q.type === 'flashcard'
            ? <Button type="primary" size="large" className="min-w-36" onClick={next}>Tiếp tục</Button>
            : feedback && <Button type="primary" size="large" danger={!feedback.correct} className={`min-w-36 ${feedback.correct ? 'lp-ok' : ''}`} onClick={next}>Tiếp tục</Button>}
        </div>
      </div>
    </div>
  )
}
