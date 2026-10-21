import { useQuery } from '@tanstack/react-query'
import { App, Button, Input, Radio, Skeleton } from 'antd'
import { ArrowRightOutlined, CheckCircleFilled, ClockCircleOutlined, CloseCircleFilled, HourglassOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { learnApi, targetCode } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { langTag } from '../../components/TargetWord'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader, Section } from '../../components/ui'

export function ExamListPage() {
  const user = useAuth((s) => s.user)
  const code = targetCode(user)
  const exams = useQuery({ queryKey: ['exams', code], queryFn: () => learnApi.exams(code) })
  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <PageHeader title="Bài kiểm tra" description="Đề do giáo viên soạn cho ngôn ngữ bạn đang học. Phần tự luận sẽ được giáo viên chấm." />
      {exams.isLoading ? <Skeleton active /> : exams.data?.length ? (
        <ul className="m-0 p-0 list-none flex flex-col gap-3">
          {exams.data.map((e) => {
            const best = e.my_best
            const passed = best && best.status !== 'submitted' && best.percent >= e.pass_percent
            return (
              <li key={e.id}>
                <Link to={`/exams/${e.id}`} className="lift lp-card p-5 flex items-center gap-4 group">
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-lg text-slate-800">{e.title}</div>
                    {e.description && <div className="text-slate-500 text-sm mt-0.5">{e.description}</div>}
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-slate-500">
                      <span className="num">{e.question_count} câu</span>
                      {e.time_limit_minutes && <span className="num"><ClockCircleOutlined /> {e.time_limit_minutes} phút</span>}
                      <span className="num">Đạt từ {e.pass_percent}%</span>
                      {best && (
                        <span className={`font-semibold ${best.status === 'submitted' ? 'text-amber-700' : passed ? 'text-emerald-600' : 'text-red-600'}`}>
                          {best.status === 'submitted' ? 'Đang chờ chấm' : `Tốt nhất ${Math.round(best.percent)}%`}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="hidden sm:inline text-sm font-semibold text-brand-600">{best ? 'Làm lại' : 'Làm bài'}</span>
                  <ArrowRightOutlined className="text-slate-400 transition-transform duration-150 group-hover:translate-x-0.5" />
                </Link>
              </li>
            )
          })}
        </ul>
      ) : (
        <div className="lp-card">
          <EmptyState art={<Prismo mood="sleepy" size={96} />} title="Chưa có bài kiểm tra"
            description="Giáo viên chưa đăng đề cho ngôn ngữ bạn đang học. Trong lúc chờ, hãy ôn lại từ vựng."
            action={<Link to="/learn?kind=review"><Button type="primary">Ôn tập từ vựng</Button></Link>} />
        </div>
      )}
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
    if (!auto && unanswered) {
      modal.confirm({ title: 'Nộp bài khi còn câu trống?', content: `Còn ${unanswered} câu chưa trả lời. Câu trống được tính 0 điểm.`, okText: 'Nộp bài', cancelText: 'Làm tiếp', onOk: go })
    } else go()
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
  if (!data) {
    return (
      <div className="lp-card max-w-xl mx-auto">
        <EmptyState art={<Prismo mood="sad" size={96} />} title="Không mở được bài kiểm tra" description={errorMessage(started.error)}
          action={<Link to="/exams"><Button>Về danh sách đề</Button></Link>} />
      </div>
    )
  }
  const done = data.questions.filter((q) => answers[q.id] !== undefined).length
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4 pb-6">
      {/* sticky bar: title, how many answered, time left */}
      <div className="sticky top-14 md:top-16 z-10 -mx-3 sm:-mx-4 md:-mx-6 xl:-mx-8 px-3 sm:px-4 md:px-6 xl:px-8 py-3 bg-[var(--page-bg)] border-b border-slate-200">
        <div className="max-w-3xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-xl font-bold text-slate-800 m-0">{data.title}</h1>
          <div className="flex items-center gap-4 text-sm">
            <span className="num text-slate-500">Đã làm {done}/{data.questions.length}</span>
            {left !== null && (
              <span className={`num inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 font-bold ${left < 60 ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-700'}`}
                role="timer" aria-label="Thời gian còn lại">
                <HourglassOutlined />{String(Math.floor(left / 60)).padStart(2, '0')}:{String(left % 60).padStart(2, '0')}
              </span>
            )}
          </div>
        </div>
      </div>
      <ol className="m-0 p-0 list-none flex flex-col gap-3">
        {data.questions.map((q, i) => (
          <li key={q.id} className="lp-card p-5">
            <div className="text-sm text-slate-500">Câu {i + 1} · {q.points} điểm</div>
            <div lang={tag} className="font-semibold text-lg text-slate-800 my-2">{q.prompt}</div>
            {q.kind === 'mcq' ? (
              <Radio.Group value={answers[q.id]?.selected_option} onChange={(e) => setAnswers({ ...answers, [q.id]: { selected_option: e.target.value } })} className="!flex !flex-col gap-2">
                {q.options.map((o, j) => <Radio key={j} value={j}><span lang={tag} className="text-base">{o}</span></Radio>)}
              </Radio.Group>
            ) : (
              <Input.TextArea lang={tag} rows={q.kind === 'essay' ? 5 : 1} value={answers[q.id]?.text} aria-label={`Câu trả lời câu ${i + 1}`}
                onChange={(e) => setAnswers({ ...answers, [q.id]: { text: e.target.value } })}
                placeholder={q.kind === 'essay' ? 'Viết câu trả lời…' : 'Nhập đáp án'} />
            )}
          </li>
        ))}
      </ol>
      <Button type="primary" size="large" loading={submitting} onClick={() => submit()}>Nộp bài</Button>
    </div>
  )
}

export function ExamResultPage() {
  const { id } = useParams()
  const result = useQuery({ queryKey: ['submission', id], queryFn: () => learnApi.result(Number(id)) })
  const r = result.data
  if (!r) return <Skeleton active />
  const waiting = r.status === 'submitted'
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4">
      <section className="ink-bg text-white rounded-3xl p-6 sm:p-8 flex items-center gap-5 animate-rise">
        <Prismo mood={waiting ? 'think' : r.passed ? 'celebrate' : 'sad'} size={96} className="shrink-0" />
        <div className="min-w-0">
          <div className="num text-4xl font-extrabold">{Number(r.score).toFixed(1)}<span className="text-white/60 text-2xl font-bold"> / {Number(r.max_score).toFixed(1)} điểm</span></div>
          <p className="text-white/80 mt-1 mb-0">
            {waiting ? 'Phần tự luận đang chờ giáo viên chấm. Điểm sẽ cập nhật khi chấm xong.' : r.passed ? 'Bạn đã đạt bài kiểm tra.' : 'Chưa đạt lần này. Xem lại các câu sai bên dưới rồi làm lại nhé.'}
          </p>
        </div>
      </section>
      {r.feedback && <Section title="Nhận xét của giáo viên"><p className="m-0 text-slate-700">{r.feedback}</p></Section>}
      <ol className="m-0 p-0 list-none flex flex-col gap-3">
        {r.answers.map((a, i) => {
          const yours = a.question.kind === 'mcq' ? (a.selected_option != null ? a.question.options[a.selected_option] : '(bỏ trống)') : a.text || '(bỏ trống)'
          const state = a.is_correct == null
            ? { icon: <HourglassOutlined className="text-amber-600" />, label: 'Chờ chấm' }
            : a.is_correct ? { icon: <CheckCircleFilled className="text-emerald-500" />, label: 'Đúng' } : { icon: <CloseCircleFilled className="text-red-500" />, label: 'Sai' }
          return (
            <li key={a.id} className="lp-card p-5 flex gap-3">
              <span className="text-xl leading-7" aria-label={state.label}>{state.icon}</span>
              <div className="flex-1 min-w-0 flex flex-col gap-1">
                <div className="font-semibold text-slate-800">Câu {i + 1}: {a.question.prompt}</div>
                <div className="text-slate-700">Bạn trả lời: {yours}</div>
                {a.is_correct === false && a.question.kind !== 'essay' && (
                  <div className="text-emerald-700">Đáp án: {a.question.kind === 'mcq' && a.question.correct_option != null ? a.question.options[a.question.correct_option] : a.question.accepted_answers.join(' / ')}</div>
                )}
                {a.question.explanation && <div className="text-slate-500 text-sm">{a.question.explanation}</div>}
                {a.is_correct != null && <div className="num text-sm text-slate-500">Điểm: {a.score} / {a.question.points}</div>}
                {a.feedback && <div className="text-sm text-slate-600">Giáo viên nhận xét: {a.feedback}</div>}
              </div>
            </li>
          )
        })}
      </ol>
      <div className="flex flex-wrap gap-3">
        <Link to="/exams"><Button size="large">Về danh sách đề</Button></Link>
      </div>
    </div>
  )
}
