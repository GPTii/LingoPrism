import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { App, Button, Progress, Spin } from 'antd'
import { SoundOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { levelsApi, type LevelTest, type LevelTestResult } from '../../api/levels'
import { errorMessage } from '../../api/client'
import TargetWord from '../../components/TargetWord'
import { speak } from '../../lib/speech'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader } from '../../components/ui'

/** Skip test: 10 words of a level, pick the Vietnamese meaning (children: listen and pick the written word). */
export default function LevelTestPage() {
  const n = Number(useParams().n)
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [test, setTest] = useState<LevelTest | null>(null)
  const [answers, setAnswers] = useState<string[]>([])
  const [result, setResult] = useState<LevelTestResult | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    levelsApi.test(n).then(setTest).catch((e) => setError(errorMessage(e)))
  }, [n])

  const q = test?.questions[answers.length]
  useEffect(() => {
    if (q?.prompt.audio) speak(q.prompt.audio.text, q.prompt.audio.tts_locale)
  }, [q])

  const pick = async (opt: string) => {
    if (!test) return
    const next = [...answers, opt]
    setAnswers(next)
    if (next.length === test.questions.length) {
      try {
        const r = await levelsApi.submit(n, test.token, next)
        setResult(r)
        queryClient.invalidateQueries({ queryKey: ['levels'] })
      } catch (e) {
        message.error(errorMessage(e))
      }
    }
  }

  if (error) {
    return (
      <div className="lp-card max-w-xl mx-auto">
        <EmptyState art={<Prismo mood="think" size={96} />} title="Chưa làm được bài kiểm tra này" description={error}
          action={<Button onClick={() => navigate('/')}>Về trang chủ</Button>} />
      </div>
    )
  }
  if (!test) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (result) {
    return (
      <div className="max-w-xl mx-auto flex flex-col items-center text-center gap-4 pt-4">
        <Prismo mood={result.passed ? 'celebrate' : 'think'} size={150} className="animate-pop" />
        <h1 className="text-3xl font-extrabold text-slate-800 m-0">
          {result.passed ? `Bạn đã mở Cấp ${result.unlocked}` : `Chưa qua – đúng ${result.score}/${result.total} câu`}
        </h1>
        <p className="text-lg text-slate-600 m-0 max-w-[46ch]">
          {result.passed ? `Đúng ${result.score}/${result.total} câu. Từ giờ từ mới sẽ lấy từ cấp ${result.unlocked}.`
            : `Cần đúng ít nhất ${test.pass} câu. Học thêm các từ của cấp ${n} rồi thử lại nhé.`}
        </p>
        <div className="flex flex-wrap justify-center gap-3 mt-2">
          <Button size="large" onClick={() => navigate('/')}>Về trang chủ</Button>
          <Button size="large" type="primary" onClick={() => navigate('/learn?kind=learn')}>Học từ mới</Button>
        </div>
      </div>
    )
  }
  if (!q) return <Spin />

  return (
    <div className="max-w-xl mx-auto flex flex-col gap-6">
      <PageHeader title={`Kiểm tra vượt cấp ${n}`} description={`Đúng từ ${test.pass}/${test.questions.length} câu để mở cấp ${n + 1}.`} />
      <div className="flex items-center gap-3">
        <Progress percent={Math.round((100 * answers.length) / test.questions.length)} showInfo={false} className="flex-1 m-0" />
        <span className="num text-sm font-bold text-slate-500">{answers.length + 1}/{test.questions.length}</span>
      </div>
      <div key={answers.length} className="lp-card p-6 sm:p-8 flex flex-col items-center gap-6 animate-rise">
        {q.prompt.word && (
          <>
            <div className="text-slate-600 font-semibold">Từ này nghĩa là gì?</div>
            <TargetWord target={q.prompt.word} size="xl" />
          </>
        )}
        {q.prompt.audio && (
          <>
            <div className="text-slate-600 font-semibold">Nghe rồi chọn từ đúng</div>
            {q.prompt.emoji && <div className="text-6xl">{q.prompt.emoji}</div>}
            <button type="button" aria-label="Nghe lại" onClick={() => speak(q.prompt.audio!.text, q.prompt.audio!.tts_locale)}
              className="h-20 w-20 rounded-3xl prism-bg text-white text-3xl grid place-items-center cursor-pointer hover:bg-brand-700 active:scale-95 transition">
              <SoundOutlined />
            </button>
          </>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
          {q.options.map((o) => (
            <button key={o} type="button" className="btn-3d px-4 py-3.5 text-lg font-semibold text-slate-800 cursor-pointer" onClick={() => pick(o)}>{o}</button>
          ))}
        </div>
      </div>
    </div>
  )
}
