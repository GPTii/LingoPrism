import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { App, Button, Progress, Result, Spin } from 'antd'
import { SoundOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { levelsApi, type LevelTest, type LevelTestResult } from '../../api/levels'
import { errorMessage } from '../../api/client'
import TargetWord from '../../components/TargetWord'
import { speak } from '../../lib/speech'

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

  if (error) return <Result status="info" title={error} extra={<Button onClick={() => navigate('/')}>Về trang chủ</Button>} />
  if (!test) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (result) {
    return (
      <Result
        status={result.passed ? 'success' : 'warning'}
        title={result.passed ? `Chúc mừng! Bạn đã mở Cấp ${result.unlocked}` : `Chưa qua – đúng ${result.score}/${result.total} câu`}
        subTitle={result.passed ? `Đúng ${result.score}/${result.total} câu. Từ giờ từ mới sẽ lấy từ cấp ${result.unlocked}.`
          : `Cần đúng ít nhất ${test.pass} câu. Học thêm các từ của cấp ${n} rồi thử lại nhé.`}
        extra={[
          <Button key="home" onClick={() => navigate('/')}>Về trang chủ</Button>,
          <Button key="learn" type="primary" onClick={() => navigate('/learn?kind=learn')}>Học từ mới</Button>,
        ]}
      />
    )
  }
  if (!q) return <Spin />

  return (
    <div className="max-w-xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 m-0">Kiểm tra vượt cấp {n}</h1>
        <div className="text-slate-500 text-sm">Đúng từ {test.pass}/{test.questions.length} câu để mở cấp {n + 1}</div>
      </div>
      <Progress percent={Math.round((100 * answers.length) / test.questions.length)} showInfo={false} />
      <div className="rounded-3xl bg-white border border-slate-200 p-8 flex flex-col items-center gap-6">
        {q.prompt.word && (
          <>
            <div className="text-slate-500">Từ này nghĩa là gì?</div>
            <TargetWord target={q.prompt.word} size="xl" />
          </>
        )}
        {q.prompt.audio && (
          <>
            <div className="text-slate-500">Nghe rồi chọn từ đúng</div>
            {q.prompt.emoji && <div className="text-6xl">{q.prompt.emoji}</div>}
            <Button shape="circle" size="large" icon={<SoundOutlined />} onClick={() => speak(q.prompt.audio!.text, q.prompt.audio!.tts_locale)} />
          </>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
          {q.options.map((o) => (
            <Button key={o} size="large" className="h-auto py-3 whitespace-normal" onClick={() => pick(o)}>{o}</Button>
          ))}
        </div>
      </div>
    </div>
  )
}
