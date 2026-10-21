import { App, Button, Progress, Result, Spin } from 'antd'
import { CheckCircleFilled, CloseCircleFilled, SoundOutlined } from '@ant-design/icons'
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

  if (error) return <Result status="warning" title={error} extra={<Button onClick={() => navigate('/vocab')}>Về trang từ vựng</Button>} />
  if (!exercises) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (exercises.length === 0) {
    return (
      <Result status="info" title="Chưa có câu luyện tập cho phần này"
        subTitle="Câu luyện tập chỉ lấy từ nguồn đã kiểm tra (Tatoeba, người bản xứ). Hãy học thêm từ hoặc chọn chủ đề khác."
        extra={<Button type="primary" onClick={() => navigate('/vocab')}>Chọn chủ đề</Button>} />
    )
  }
  if (!ex) {
    return (
      <Result status="success" title="Hoàn thành bài luyện câu!"
        subTitle={`Đúng ${score.correct}/${exercises.length} câu · +${score.xp} XP`}
        extra={[
          <Button key="home" onClick={() => navigate('/')}>Về trang chủ</Button>,
          <Button key="again" type="primary" onClick={() => window.location.reload()}>Luyện tiếp</Button>,
        ]} />
    )
  }

  const optionClass = (opt: string, answer: string | null) => {
    if (!result) return 'border-slate-200 hover:border-brand-500'
    return opt === answer ? 'border-green-500 bg-green-50' : 'border-slate-200 opacity-60'
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <Progress percent={Math.round((index / exercises.length) * 100)} showInfo={false} strokeColor="#14b8a6" />
      <AnimatePresence mode="wait">
        <motion.div key={index} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}
          className="rounded-3xl bg-white border border-slate-200 p-6 sm:p-8 min-h-80 flex flex-col items-center gap-6">
          <div className="text-slate-500 font-medium">{TITLES[ex.type]}</div>

          {(ex.type === 'arrange' || ex.type === 'listen') && (
            <>
              {ex.type === 'arrange' && ex.prompt && <div className="text-xl text-slate-800 text-center">{ex.prompt.text}</div>}
              {ex.type === 'listen' && ex.tts && (
                <Button size="large" shape="circle" icon={<SoundOutlined />} onClick={() => speak(ex.tts!.text, ex.tts!.locale)} />
              )}
              <div lang={tag} className="w-full min-h-16 border-b-2 border-slate-200 flex flex-wrap gap-2 pb-3 justify-center">
                {picked.map((ti, pos) => (
                  <button key={`${ti}-${pos}`} type="button" disabled={!!result}
                    onClick={() => setPicked(picked.filter((_, p) => p !== pos))}
                    className="rounded-xl border-2 border-brand-300 bg-brand-50 px-3 py-2 text-xl cursor-pointer">
                    {ex.tiles[ti].t}
                  </button>
                ))}
              </div>
              <div lang={tag} className="flex flex-wrap gap-2 justify-center">
                {ex.tiles.map((tile, ti) => (
                  <button key={ti} type="button" disabled={picked.includes(ti) || !!result}
                    onClick={() => setPicked([...picked, ti])}
                    className={`rounded-xl border-2 px-3 py-2 text-xl flex flex-col items-center cursor-pointer transition ${picked.includes(ti) ? 'opacity-0' : 'border-slate-200 hover:border-brand-500'}`}>
                    {isZh && ex.type === 'arrange' && <span className="text-xs text-slate-400">{showZhuyin && tile.z ? tile.z : tile.p}</span>}
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
                    className={`rounded-2xl border-2 px-4 py-3 text-xl font-medium transition cursor-pointer ${optionClass(opt, result?.answer ?? null)}`}>
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
                    className={`rounded-2xl border-2 px-4 py-3 text-left transition cursor-pointer ${optionClass(opt, result?.sentence.translation?.text ?? null)}`}>
                    {opt}
                  </button>
                ))}
              </div>
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {result && (
        <div className={`rounded-2xl p-4 flex flex-col sm:flex-row gap-4 sm:items-center justify-between ${result.correct ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-lg font-medium">
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
