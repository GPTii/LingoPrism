import { App, Button, Progress, Spin } from 'antd'
import { CheckCircleFilled, CloseCircleFilled, CloseOutlined, SoundOutlined } from '@ant-design/icons'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { errorMessage } from '../../api/client'
import { sentencesApi, type CheckResult, type SentenceExercise } from '../../api/sentences'
import { useAuth } from '../../auth/store'
import SentenceView, { TokenLine } from '../../components/SentenceView'
import { langTag } from '../../components/TargetWord'
import { speak } from '../../lib/speech'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState } from '../../components/ui'

const TITLES: Record<SentenceExercise['type'], string> = {
  arrange: 'Sắp xếp các từ thành câu đúng',
  listen: 'Nghe và sắp xếp lại câu',
  fill: 'Chọn từ còn thiếu',
  meaning: 'Câu này có nghĩa là gì?',
}

export default function SentencePage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [params] = useSearchParams()
  const showZhuyin = useAuth((s) => s.user?.show_zhuyin)
  const topic = params.get('topic') ? Number(params.get('topic')) : undefined

  const [language, setLanguage] = useState('')
  const [exercises, setExercises] = useState<SentenceExercise[] | null>(null)
  const [index, setIndex] = useState(0)
  const [picked, setPicked] = useState<number[]>([]) // tile indexes in answer order
  const [result, setResult] = useState<CheckResult | null>(null)
  const [score, setScore] = useState({ correct: 0, xp: 0 })
  const [error, setError] = useState('')
  const [checking, setChecking] = useState(false)
  const started = useRef(Date.now())
  const loaded = useRef(false)

  useEffect(() => {
    if (loaded.current) return
    loaded.current = true
    sentencesApi.lesson(topic, 10)
      .then((d) => { setLanguage(d.language); setExercises(d.exercises) })
      .catch((e) => setError(errorMessage(e)))
  }, [topic])

  const ex = exercises?.[index]
  const tag = langTag(language)
  const isZh = language.startsWith('zh')

  useEffect(() => {
    started.current = Date.now()
    setPicked([])
    setResult(null)
    if (ex?.type === 'listen' && ex.tts) speak(ex.tts.text, ex.tts.locale)
  }, [ex])

  const submit = async (answer: string | string[]) => {
    if (!ex || result || checking) return
    setChecking(true)
    try {
      const r = await sentencesApi.check({ sentence: ex.id, type: ex.type, answer, response_ms: Date.now() - started.current })
      setResult(r)
      if (r.correct) setScore((s) => ({ correct: s.correct + 1, xp: s.xp + r.xp }))
      speak(r.sentence.text, r.sentence.tts_locale)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setChecking(false)
    }
  }

  const next = () => {
    if (exercises && index + 1 >= exercises.length) {
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      setIndex(exercises.length)
    } else setIndex(index + 1)
  }

  if (error) {
    return (
      <div className="lp-card max-w-xl mx-auto">
        <EmptyState art={<Prismo mood="sad" size={96} />} title="Không mở được bài luyện câu" description={error}
          action={<Button onClick={() => navigate('/vocab')}>Về trang từ vựng</Button>} />
      </div>
    )
  }
  if (!exercises) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (exercises.length === 0) {
    return (
      <div className="lp-card max-w-xl mx-auto">
        <EmptyState art={<Prismo mood="think" size={96} />} title="Chưa có câu luyện tập cho phần này"
          description="Câu luyện tập chỉ lấy từ nguồn đã kiểm tra (Tatoeba, người bản xứ). Hãy học thêm từ hoặc chọn chủ đề khác."
          action={<Button type="primary" onClick={() => navigate('/vocab')}>Chọn chủ đề</Button>} />
      </div>
    )
  }
  if (!ex) {
    return (
      <div className="max-w-xl mx-auto flex flex-col items-center text-center gap-4 pt-4">
        <Prismo mood={score.correct === exercises.length ? 'celebrate' : 'happy'} size={150} className="animate-pop" />
        <h1 className="text-3xl font-extrabold text-slate-800 m-0">Xong bài luyện câu</h1>
        <p className="num text-lg text-slate-600 m-0">Đúng {score.correct}/{exercises.length} câu · +{score.xp} XP</p>
        <div className="flex flex-wrap justify-center gap-3 mt-2">
          <Button size="large" onClick={() => navigate('/')}>Về trang chủ</Button>
          <Button size="large" type="primary" onClick={() => window.location.reload()}>Luyện tiếp 10 câu</Button>
        </div>
      </div>
    )
  }

  const optionClass = (opt: string, answer: string | null) => {
    if (!result) return ''
    return opt === answer ? 'is-right' : 'opacity-60'
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <button type="button" onClick={() => navigate(-1)} aria-label="Thoát bài luyện"
          className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 cursor-pointer transition">
          <CloseOutlined />
        </button>
        <Progress percent={Math.round((index / exercises.length) * 100)} showInfo={false} className="flex-1 m-0" />
        <span className="num text-sm font-bold text-slate-500">{index + 1}/{exercises.length}</span>
      </div>
      <AnimatePresence mode="wait">
        <motion.div key={index} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="lp-card p-6 sm:p-8 min-h-80 flex flex-col items-center gap-6">
          <div className="text-slate-600 font-semibold">{TITLES[ex.type]}</div>

          {(ex.type === 'arrange' || ex.type === 'listen') && (
            <>
              {ex.type === 'arrange' && ex.prompt && <div className="text-xl text-slate-800 text-center">{ex.prompt.text}</div>}
              {ex.type === 'listen' && ex.tts && (
                <button type="button" aria-label="Nghe lại câu" onClick={() => speak(ex.tts!.text, ex.tts!.locale)}
                  className="h-20 w-20 rounded-3xl prism-bg text-white text-3xl grid place-items-center cursor-pointer hover:bg-brand-700 active:scale-95 transition">
                  <SoundOutlined />
                </button>
              )}
              <div lang={tag} className="w-full min-h-16 rounded-xl bg-slate-50 flex flex-wrap gap-2 p-3 justify-center items-center">
                {picked.map((ti, pos) => (
                  <button key={`${ti}-${pos}`} type="button" disabled={!!result}
                    onClick={() => setPicked(picked.filter((_, p) => p !== pos))}
                    className="btn-3d !border-brand-400 !bg-brand-50 text-brand-700 px-3 py-2 text-xl cursor-pointer animate-pop">
                    {ex.tiles[ti].t}
                  </button>
                ))}
              </div>
              <div lang={tag} className="flex flex-wrap gap-2 justify-center">
                {ex.tiles.map((tile, ti) => (
                  <button key={ti} type="button" disabled={picked.includes(ti) || !!result}
                    onClick={() => setPicked([...picked, ti])}
                    className={`btn-3d px-3 py-2 text-xl text-slate-800 flex flex-col items-center cursor-pointer ${picked.includes(ti) ? 'invisible' : ''}`}>
                    {isZh && ex.type === 'arrange' && <span className="text-xs text-slate-500">{showZhuyin && tile.z ? tile.z : tile.p}</span>}
                    {tile.t}
                  </button>
                ))}
              </div>
              {!result && (
                <Button type="primary" size="large" disabled={picked.length !== ex.tiles.length} loading={checking}
                  onClick={() => submit(picked.map((ti) => ex.tiles[ti].t))}>
                  Kiểm tra
                </Button>
              )}
            </>
          )}

          {ex.type === 'fill' && (
            <>
              <TokenLine tokens={ex.tokens} language={language} />
              <div className="text-slate-600 text-center">{ex.prompt.text}</div>
              <div lang={tag} className="grid grid-cols-2 gap-3 w-full">
                {ex.options.map((opt) => (
                  <button key={opt} type="button" disabled={!!result} onClick={() => submit(opt)}
                    className={`btn-3d px-4 py-3 text-xl font-medium text-slate-800 cursor-pointer disabled:cursor-default ${optionClass(opt, result?.answer ?? null)}`}>
                    {opt}
                  </button>
                ))}
              </div>
            </>
          )}

          {ex.type === 'meaning' && (
            <>
              <SentenceView sentence={ex.sentence} showTranslation={false} />
              <div className="grid grid-cols-1 gap-3 w-full">
                {ex.options.map((opt) => (
                  <button key={opt} type="button" disabled={!!result} onClick={() => submit(opt)}
                    className={`btn-3d px-4 py-3 text-left text-slate-800 cursor-pointer disabled:cursor-default ${optionClass(opt, result?.sentence.translation?.text ?? null)}`}>
                    {opt}
                  </button>
                ))}
              </div>
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {result && (
        <div className={`rounded-2xl p-4 flex flex-col sm:flex-row gap-4 sm:items-center justify-between animate-rise ${result.correct ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-lg font-bold text-slate-800">
              {result.correct ? <CheckCircleFilled className="text-green-600" /> : <CloseCircleFilled className="text-red-500" />}
              {result.correct ? `Chính xác!${result.xp ? ` +${result.xp} XP` : ''}` : 'Chưa đúng – câu đúng là:'}
            </div>
            <SentenceView sentence={result.sentence} />
          </div>
          <Button type="primary" size="large" onClick={next}>Tiếp tục</Button>
        </div>
      )}
    </div>
  )
}
