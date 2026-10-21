import { useQuery } from '@tanstack/react-query'
import { App, Button, Card, Empty, Input, Radio, Result, Skeleton, Tag } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { learnApi, targetCode } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { langTag } from '../../components/TargetWord'

export function ExamListPage() {
  const user = useAuth((s) => s.user)
  const navigate = useNavigate()
  const code = targetCode(user)
  const exams = useQuery({ queryKey: ['exams', code], queryFn: () => learnApi.exams(code) })
  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-4">
      <h1 className="text-2xl font-bold m-0">Bài kiểm tra</h1>
      {exams.isLoading ? <Skeleton active /> : exams.data?.length ? (
        <div className="grid md:grid-cols-2 gap-4">
          {exams.data.map((e) => (
            <Card key={e.id} className="!rounded-2xl" hoverable onClick={() => navigate(`/exams/${e.id}`)}>
              <div className="font-semibold text-lg">{e.title}</div>
              <div className="text-slate-500 text-sm">{e.description}</div>
              <div className="flex gap-2 mt-3">
                <Tag>{e.question_count} câu</Tag>
                {e.time_limit_minutes && <Tag>{e.time_limit_minutes} phút</Tag>}
                {e.my_best && <Tag color={e.my_best.status === 'submitted' ? 'orange' : e.my_best.percent >= e.pass_percent ? 'green' : 'red'}>
                  {e.my_best.status === 'submitted' ? 'Chờ chấm' : `Tốt nhất ${Math.round(e.my_best.percent)}%`}
                </Tag>}
              </div>
            </Card>
          ))}
        </div>
      ) : <Empty description="Chưa có bài kiểm tra cho ngôn ngữ đang học" />}
    </div>
  )
}

export function ExamTakePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { message, modal } = App.useApp()
  const started = useQuery({ queryKey: ['exam-start', id], queryFn: () => learnApi.startExam(Number(id)), staleTime: Infinity, gcTime: 0 })
  const [answers, setAnswers] = useState<Record<number, { selected_option?: number; text?: string }>>({})
  const [left, setLeft] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const submitted = useRef(false)
  const data = started.data
  const tag = data ? langTag(data.language) : undefined

  const submit = async (auto = false) => {
    if (!data || submitted.current) return
    const go = async () => {
      submitted.current = true
      setSubmitting(true)
      try {
        const r = await learnApi.submit(data.submission, data.questions.map((q) => ({ question: q.id, ...answers[q.id] })))
        navigate(`/exams/results/${r.id}`, { replace: true })
      } catch (e) {
        submitted.current = false
        message.error(errorMessage(e))
      } finally {
        setSubmitting(false)
      }
    }
    const unanswered = data.questions.filter((q) => answers[q.id] === undefined).length
    if (!auto && unanswered) modal.confirm({ title: 'Nộp bài?', content: `Còn ${unanswered} câu chưa trả lời.`, onOk: go })
    else go()
  }

  useEffect(() => {
    if (!data?.time_limit_minutes) return
    const end = new Date(data.started_at).getTime() + data.time_limit_minutes * 60_000
    const t = window.setInterval(() => {
      const s = Math.max(0, Math.round((end - Date.now()) / 1000))
      setLeft(s)
      if (s === 0) {
        window.clearInterval(t)
        submit(true)
      }
    }, 1000)
    return () => window.clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  if (started.isLoading) return <Skeleton active />
  if (!data) return <Result status="error" title={errorMessage(started.error)} />
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2 sticky top-14 md:top-16 bg-[#f6fbfb] py-2 z-10">
        <h1 className="text-xl font-bold m-0">{data.title}</h1>
        {left !== null && <Tag color={left < 60 ? 'red' : 'blue'} className="!text-base">{String(Math.floor(left / 60)).padStart(2, '0')}:{String(left % 60).padStart(2, '0')}</Tag>}
      </div>
      {data.questions.map((q, i) => (
        <Card key={q.id} className="!rounded-2xl">
          <div className="text-xs text-slate-400">Câu {i + 1} · {q.points} điểm</div>
          <div lang={tag} className="font-medium text-lg my-2">{q.prompt}</div>
          {q.kind === 'mcq' ? (
            <Radio.Group value={answers[q.id]?.selected_option} onChange={(e) => setAnswers({ ...answers, [q.id]: { selected_option: e.target.value } })} className="!flex !flex-col gap-2">
              {q.options.map((o, j) => <Radio key={j} value={j}><span lang={tag} className="text-base">{o}</span></Radio>)}
            </Radio.Group>
          ) : (
            <Input.TextArea lang={tag} rows={q.kind === 'essay' ? 5 : 1} value={answers[q.id]?.text}
              onChange={(e) => setAnswers({ ...answers, [q.id]: { text: e.target.value } })}
              placeholder={q.kind === 'essay' ? 'Viết câu trả lời…' : 'Nhập đáp án'} />
          )}
        </Card>
      ))}
      <Button type="primary" size="large" loading={submitting} onClick={() => submit()}>Nộp bài</Button>
    </div>
  )
}

export function ExamResultPage() {
  const { id } = useParams()
  const result = useQuery({ queryKey: ['submission', id], queryFn: () => learnApi.result(Number(id)) })
  const r = result.data
  if (!r) return <Skeleton active />
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4">
      <Result
        status={r.status === 'submitted' ? 'info' : r.passed ? 'success' : 'warning'}
        title={`${Number(r.score).toFixed(1)} / ${Number(r.max_score).toFixed(1)} điểm`}
        subTitle={r.status === 'submitted' ? 'Phần tự luận đang chờ giáo viên chấm' : r.passed ? 'Bạn đã đạt bài kiểm tra 🎉' : 'Chưa đạt – cố gắng lần sau nhé!'}
      />
      {r.feedback && <Card>Nhận xét của giáo viên: {r.feedback}</Card>}
      {r.answers.map((a, i) => {
        const yours = a.question.kind === 'mcq' ? (a.selected_option != null ? a.question.options[a.selected_option] : '(bỏ trống)') : a.text || '(bỏ trống)'
        const color = a.is_correct == null ? 'border-orange-400' : a.is_correct ? 'border-emerald-500' : 'border-red-500'
        return (
          <Card key={a.id} className={`!rounded-2xl border-l-4 ${color}`}>
            <div className="font-medium">Câu {i + 1}: {a.question.prompt}</div>
            <div>Bạn trả lời: {yours}</div>
            {a.is_correct === false && a.question.kind !== 'essay' && (
              <div className="text-emerald-600">Đáp án: {a.question.kind === 'mcq' && a.question.correct_option != null ? a.question.options[a.question.correct_option] : a.question.accepted_answers.join(' / ')}</div>
            )}
            {a.question.explanation && <div className="text-slate-500">{a.question.explanation}</div>}
            {a.is_correct == null ? <Tag color="orange">Chờ chấm</Tag> : <div>Điểm: {a.score} / {a.question.points}</div>}
            {a.feedback && <div className="italic">Nhận xét: {a.feedback}</div>}
          </Card>
        )
      })}
    </div>
  )
}
