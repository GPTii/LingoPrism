import { App, Button, Input, Progress, Result, Spin } from 'antd'
import { CheckCircleFilled, CloseCircleFilled, SoundOutlined } from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { normalizeAnswer, vocabApi, type Question, type SessionItem, type StudySession } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import TargetWord, { langTag } from '../../components/TargetWord'
import { speak } from '../../lib/speech'

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
    const graded = typed ?? by.choose_target ?? by.choose_meaning ?? by.type_target
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
  const [feedback, setFeedback] = useState<null | { correct: boolean; answer: string }>(null)
  const [typed, setTyped] = useState('')
  const [flipped, setFlipped] = useState(false)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [error, setError] = useState('')
  const started = useRef(Date.now())
  const startedOnce = useRef(false)

  const kind = (params.get('kind') ?? 'learn') as StudySession['kind']
  const topic = params.get('topic') ? Number(params.get('topic')) : undefined

  useEffect(() => {
    if (startedOnce.current) return
    startedOnce.current = true
    vocabApi.startSession(kind, topic)
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
    setFeedback({ correct, answer: 'answer' in q ? q.answer : '' })
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
        {card.image && <img src={card.image} alt="" className="h-32 object-contain" />}
        <div className="text-2xl font-semibold text-slate-800">{card.meaning_vi}</div>
      </div>
    )
  }, [step])

  if (error) return <Result status="info" title={error} extra={<Button type="primary" onClick={() => navigate('/vocab')}>Chọn chủ đề để học</Button>} />
  if (!session) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (summary) {
    const missed = session.items.filter((i) => summary.needs_more_practice.includes(i.personal_word))
    return (
      <Result
        status="success"
        title="Chúc mừng bạn đã hoàn thành bài học!"
        subTitle={`Đúng ngay lần đầu ${summary.correct_first_try}/${summary.completed_count} từ · +${summary.xp_earned} XP`}
        extra={[
          <Button key="home" onClick={() => navigate('/')}>Về trang chủ</Button>,
          <Button key="again" type="primary" onClick={() => window.location.reload()}>Học tiếp</Button>,
        ]}
      >
        {missed.length > 0 && (
          <div className="text-center">
            <div className="font-medium mb-2">Từ cần ôn thêm:</div>
            <div className="flex flex-wrap justify-center gap-2">
              {missed.map((i) => <span key={i.item_id} lang={zhTag} className="px-3 py-1 rounded-full bg-amber-50 text-amber-700">{i.card.target?.text} – {i.card.meaning_vi}</span>)}
            </div>
          </div>
        )}
      </Result>
    )
  }
  if (!step) return null
  const q = step.question

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <Progress percent={progress} showInfo={false} strokeColor="#14b8a6" />
      <AnimatePresence mode="wait">
        <motion.div key={index} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}
          className="rounded-3xl bg-white border border-slate-200 p-8 min-h-80 flex flex-col items-center justify-center gap-6">
          {q.type === 'flashcard' && (
            <button type="button" onClick={() => setFlipped(!flipped)} className="w-full flex flex-col items-center gap-4 cursor-pointer">
              {step.item.card.image && <img src={step.item.card.image} alt="" className="h-32 object-contain" />}
              <TargetWord target={q.front} size="xl" />
              {flipped ? <div className="text-2xl text-slate-700">{q.back}</div> : <div className="text-slate-400">Chạm để xem nghĩa tiếng Việt</div>}
            </button>
          )}

          {(q.type === 'choose_target' || q.type === 'choose_meaning' || q.type === 'choose_pinyin') && (
            <>
              {q.type === 'choose_target' && meaningPrompt}
              {q.type === 'choose_meaning' && <TargetWord target={q.prompt} size="lg" showReading={false} />}
              {q.type === 'choose_pinyin' && <div lang={zhTag} className="text-5xl font-semibold">{q.prompt}</div>}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                {q.options.map((opt) => {
                  const state = feedback ? (opt === q.answer ? 'right' : 'idle') : 'idle'
                  return (
                    <button key={opt} type="button" disabled={!!feedback} onClick={() => submit(opt)}
                      lang={q.type === 'choose_target' ? zhTag : undefined}
                      className={`rounded-2xl border-2 px-4 py-4 text-lg font-medium transition cursor-pointer ${state === 'right' ? 'border-green-500 bg-green-50' : 'border-slate-200 hover:border-brand-500'}`}>
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
                <Button size="large" shape="circle" icon={<SoundOutlined />} onClick={() => speak(q.audio.text, q.audio.tts_locale)} />
              )}
              <div className="text-slate-500">{q.type === 'listen_type' ? 'Nghe phát âm và gõ lại từ đã nghe.' : 'Gõ lại từ bằng ngôn ngữ đang học'}</div>
              <Input size="large" value={typed} lang={zhTag} disabled={!!feedback} autoFocus
                onChange={(e) => setTyped(e.target.value)} onPressEnter={() => typed && submit(typed)} className="max-w-sm text-center" />
              {!feedback && <Button type="primary" size="large" disabled={!typed} onClick={() => submit(typed)}>Kiểm tra</Button>}
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {q.type === 'flashcard' ? (
        <Button type="primary" size="large" block onClick={next}>Tiếp tục</Button>
      ) : feedback && (
        <div className={`rounded-2xl p-4 flex items-center justify-between ${feedback.correct ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex items-center gap-3 text-lg">
            {feedback.correct ? <CheckCircleFilled className="text-green-600" /> : <CloseCircleFilled className="text-red-500" />}
            {feedback.correct ? 'Chính xác!' : <span>Đáp án đúng: <b lang={zhTag}>{feedback.answer}</b></span>}
          </div>
          <Button type="primary" size="large" onClick={next}>Tiếp tục</Button>
        </div>
      )}
    </div>
  )
}
