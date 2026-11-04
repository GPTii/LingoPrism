import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert, App, Button, DatePicker, Drawer, Empty, Input, InputNumber, Modal, Popconfirm, Radio, Select, Skeleton, Switch,
  Table, Tag, Tooltip, Upload,
} from 'antd'
import {
  ArrowDownOutlined, ArrowLeftOutlined, ArrowUpOutlined, CheckCircleFilled, CloseCircleFilled, DeleteOutlined,
  FileTextOutlined, PaperClipOutlined, PlusOutlined, RobotOutlined, SendOutlined,
} from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  classworkApi, type Assignment, type AssignmentQuestion, type AssignmentSummary, type QuestionKind, type HandInBrief,
} from '../../api/app'
import { errorMessage } from '../../api/client'
import { EmptyState, UserAvatar } from '../../components/ui'
import { Prismo } from '../../components/brand/Brand'

const KIND_LABEL: Record<QuestionKind, string> = { mcq: 'Trắc nghiệm', fill: 'Điền từ', essay: 'Tự luận', file: 'Nộp file' }
const FILE_ACCEPT = '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.webp,.heic,.mp3,.m4a,.wav,.zip'
const num = (v: string | number | null | undefined) => (v == null || v === '' ? null : Number(v))
const fmt = (v: string | number | null | undefined) => { const n = num(v); return n == null ? '–' : `${+n.toFixed(2)}` }
const when = (iso: string | null) => (iso ? dayjs(iso).format('HH:mm DD/MM/YYYY') : '')

function statusTag(a: AssignmentSummary) {
  if (a.status === 'draft') return <Tag>Bản nháp</Tag>
  if (a.status === 'closed') return <Tag color="default">Đã đóng</Tag>
  const s = a.my_submission
  if (a.is_leader) return <Tag color="blue">Đã giao</Tag>
  if (!s) return a.due_at && dayjs(a.due_at).isBefore(dayjs()) ? <Tag color="red">Quá hạn</Tag> : <Tag color="gold">Chưa làm</Tag>
  return s.status === 'graded' ? <Tag color="green">Đã chấm {fmt(s.score)}/{fmt(s.max_score)}</Tag> : <Tag color="cyan">Đã nộp – chờ chấm</Tag>
}

/** Tab "Bài tập" of a study group: leaders give and mark work, members do it. ?a=<id> opens one, ?s=<id> a hand-in. */
export default function GroupAssignments({ groupId, isLeader }: { groupId: number; isLeader: boolean }) {
  const [params, setParams] = useSearchParams()
  const openId = Number(params.get('a')) || null
  const [view, setView] = useState<'list' | 'grades'>('list')
  const [creating, setCreating] = useState(false)
  const open = (id: number | null) => {
    const p = new URLSearchParams(params)
    if (id) p.set('a', String(id))
    else { p.delete('a'); p.delete('s') }
    setParams(p, { replace: !id })
  }
  if (openId) return <AssignmentView id={openId} onBack={() => open(null)} />
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Radio.Group value={view} onChange={(e) => setView(e.target.value)} optionType="button" buttonStyle="solid" size="small"
          options={[{ label: 'Bài tập', value: 'list' }, { label: 'Bảng điểm', value: 'grades' }]} />
        {isLeader && <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreating(true)}>Tạo bài tập</Button>}
      </div>
      {view === 'list' ? <AssignmentList groupId={groupId} onOpen={open} isLeader={isLeader} /> : <GradebookTable groupId={groupId} onOpen={open} />}
      <CreateModal groupId={groupId} open={creating} onClose={() => setCreating(false)} onCreated={(id) => { setCreating(false); open(id) }} />
    </div>
  )
}

function AssignmentList({ groupId, onOpen, isLeader }: { groupId: number; onOpen: (id: number) => void; isLeader: boolean }) {
  const list = useQuery({ queryKey: ['assignments', groupId], queryFn: () => classworkApi.list(groupId) })
  if (list.isLoading) return <Skeleton active />
  if (!list.data?.length) {
    return <EmptyState art={<Prismo mood="think" size={80} />} title="Chưa có bài tập"
      description={isLeader ? 'Bấm "Tạo bài tập" để giao bài: tự soạn câu hỏi hoặc tải file đề lên.' : 'Trưởng nhóm chưa giao bài nào.'} />
  }
  return (
    <ul className="m-0 p-0 list-none flex flex-col gap-2">
      {list.data.map((a) => (
        <li key={a.id}>
          <button type="button" onClick={() => onOpen(a.id)}
            className="w-full text-left lp-card px-4 py-3 flex items-center gap-3 cursor-pointer hover:border-brand-300">
            <FileTextOutlined className="text-xl text-brand-600" />
            <span className="min-w-0 flex-1">
              <span className="block font-semibold text-slate-800 truncate">{a.title}</span>
              <span className="block text-xs text-slate-500">
                {a.question_count ? `${a.question_count} câu` : 'Nộp bài làm / file'} · {fmt(a.max_score)} điểm
                {a.due_at && ` · hạn ${when(a.due_at)}`}
                {a.is_leader && a.counts && a.status !== 'draft' && ` · đã nộp ${a.counts.submitted}/${a.counts.members}, đã chấm ${a.counts.graded}`}
              </span>
            </span>
            {statusTag(a)}
          </button>
        </li>
      ))}
    </ul>
  )
}

function CreateModal({ groupId, open, onClose, onCreated }: { groupId: number; open: boolean; onClose: () => void; onCreated: (id: number) => void }) {
  const { message } = App.useApp()
  const qc = useQueryClient()
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState<'' | 'blank' | 'ai'>('')
  const make = async (file?: File) => {
    setBusy(file ? 'ai' : 'blank')
    try {
      const draft = file ? await classworkApi.importFile(groupId, file) : null
      const a = await classworkApi.create({ group: groupId, title: title.trim() || draft?.title || file?.name.replace(/\.[^.]+$/, '') || 'Bài tập mới',
        questions: draft?.questions ?? [], ai_generated: !!draft })
      if (file && /\.(pdf|docx?|jpe?g|png|webp)$/i.test(file.name)) await classworkApi.attach(a.id, file).catch(() => undefined)
      qc.invalidateQueries({ queryKey: ['assignments', groupId] })
      setTitle('')
      onCreated(a.id)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy('')
    }
  }
  return (
    <Modal title="Tạo bài tập" open={open} onCancel={onClose} footer={null} destroyOnClose>
      <div className="flex flex-col gap-3">
        <Input placeholder="Tên bài tập (VD: Bài 3 – Gia đình)" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={150} />
        <Button block size="large" icon={<PlusOutlined />} loading={busy === 'blank'} disabled={!!busy} onClick={() => make()}>
          Tự soạn câu hỏi
        </Button>
        <Upload accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp" showUploadList={false} disabled={!!busy}
          beforeUpload={(f) => { make(f); return false }}>
          <Button block size="large" type="primary" icon={<RobotOutlined />} loading={busy === 'ai'} disabled={!!busy && busy !== 'ai'}>
            {busy === 'ai' ? 'AI đang đọc đề…' : 'Tải file đề lên – AI tách thành câu hỏi'}
          </Button>
        </Upload>
        <p className="m-0 text-xs text-slate-500">
          Nhận PDF, Word (.docx), ảnh chụp phiếu bài tập hoặc .txt. File đề được đính kèm vào bài để cả nhóm xem; câu hỏi AI tách ra
          là bản nháp – bạn kiểm tra, sửa đáp án rồi mới giao. Muốn giao nguyên file (học viên nộp bài làm / file) thì chọn
          "Tự soạn câu hỏi" và đính kèm file trong bài.
        </p>
      </div>
    </Modal>
  )
}

function AssignmentView({ id, onBack }: { id: number; onBack: () => void }) {
  const q = useQuery({ queryKey: ['assignment', id], queryFn: () => classworkApi.get(id) })
  const [editing, setEditing] = useState(false)
  const a = q.data
  const back = <Button type="text" icon={<ArrowLeftOutlined />} onClick={onBack}>Tất cả bài tập</Button>
  if (q.isLoading) return <Skeleton active />
  if (!a) return <div>{back}<Alert type="error" message="Không mở được bài tập" /></div>
  const canEdit = a.is_leader && (a.status === 'draft' || editing)
  return (
    <div className="flex flex-col gap-3">
      <div>{back}</div>
      {canEdit ? <Editor a={a} onDone={() => setEditing(false)} />
        : a.is_leader ? <LeaderView a={a} onEdit={() => setEditing(true)} onDeleted={onBack} />
          : <DoView a={a} />}
    </div>
  )
}

// ---------------------------------------------------------------- leader: editor

function blank(kind: QuestionKind): AssignmentQuestion {
  return { kind, prompt: '', points: 1, options: kind === 'mcq' ? [{ text: '', correct: true }, { text: '', correct: false }] : [],
    accepted_answers: [], explanation: '' }
}

function Editor({ a, onDone }: { a: Assignment; onDone: () => void }) {
  const { message, modal } = App.useApp()
  const qc = useQueryClient()
  const [title, setTitle] = useState(a.title)
  const [instructions, setInstructions] = useState(a.instructions)
  const [due, setDue] = useState<Dayjs | null>(a.due_at ? dayjs(a.due_at) : null)
  const [points, setPoints] = useState<number>(num(a.points) ?? 10)
  const [allowLate, setAllowLate] = useState(a.allow_late)
  const [showAnswers, setShowAnswers] = useState(a.show_answers)
  const [questions, setQuestions] = useState<AssignmentQuestion[]>(a.questions)
  const [ai, setAi] = useState(a.ai_generated)
  const [busy, setBusy] = useState('')
  const locked = a.status !== 'draft' && (a.counts?.submitted ?? 0) > 0
  const refresh = (x: Assignment) => { qc.setQueryData(['assignment', a.id], x); qc.invalidateQueries({ queryKey: ['assignments', a.group] }) }
  const patchQ = (i: number, p: Partial<AssignmentQuestion>) => setQuestions((l) => l.map((x, j) => (j === i ? { ...x, ...p } : x)))
  const move = (i: number, d: number) => setQuestions((l) => { const c = [...l]; const [x] = c.splice(i, 1); c.splice(i + d, 0, x); return c })

  const save = async (then?: 'publish') => {
    setBusy(then ?? 'save')
    try {
      let x = await classworkApi.update(a.id, { title, instructions, due_at: due ? due.toISOString() : null, points, allow_late: allowLate,
        show_answers: showAnswers, ai_generated: ai, ...(locked ? {} : { questions }) })
      if (then === 'publish') x = await classworkApi.publish(a.id)
      refresh(x)
      message.success(then === 'publish' ? 'Đã giao bài cho cả nhóm' : 'Đã lưu')
      if (then === 'publish' || a.status !== 'draft') onDone()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy('')
    }
  }
  const importAi = async (file: File) => {
    setBusy('ai')
    try {
      const d = await classworkApi.importFile(a.group, file)
      setQuestions((l) => [...l, ...d.questions])
      if (!title.trim() && d.title) setTitle(d.title)
      setAi(true)
      message.success(`AI tách được ${d.questions.length} câu – hãy kiểm tra lại`)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy('')
    }
  }
  const total = questions.reduce((s, q) => s + (num(q.points) ?? 0), 0)

  return (
    <div className="flex flex-col gap-4">
      <div className="lp-card p-4 flex flex-col gap-3">
        <Input size="large" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Tên bài tập" maxLength={150} aria-label="Tên bài tập" />
        <Input.TextArea value={instructions} onChange={(e) => setInstructions(e.target.value)} autoSize={{ minRows: 2, maxRows: 8 }}
          placeholder="Đề bài / hướng dẫn (VD: Đọc file đính kèm rồi làm bài 1–3, chụp bài làm nộp lên)" aria-label="Hướng dẫn" />
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          <span className="flex items-center gap-2">Hạn nộp <DatePicker showTime={{ format: 'HH:mm' }} format="HH:mm DD/MM/YYYY" value={due} onChange={setDue} /></span>
          <span className="flex items-center gap-2"><Switch size="small" checked={allowLate} onChange={setAllowLate} /> Cho nộp muộn</span>
          <span className="flex items-center gap-2"><Switch size="small" checked={showAnswers} onChange={setShowAnswers} /> Cho xem đáp án sau khi chấm</span>
          {questions.length === 0 && <span className="flex items-center gap-2">Điểm tối đa <InputNumber min={1} max={1000} value={points} onChange={(v) => setPoints(v ?? 10)} /></span>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {a.attachment ? (
            <span className="flex items-center gap-2">
              <a href={a.attachment} target="_blank" rel="noreferrer"><PaperClipOutlined /> {a.attachment_name}</a>
              <Button size="small" type="text" danger onClick={async () => refresh(await classworkApi.detach(a.id))}>Bỏ file</Button>
            </span>
          ) : (
            <Upload accept={FILE_ACCEPT} showUploadList={false} beforeUpload={(f) => {
              classworkApi.attach(a.id, f).then(refresh).catch((e) => message.error(errorMessage(e))); return false
            }}>
              <Button icon={<PaperClipOutlined />}>Đính kèm file đề</Button>
            </Upload>
          )}
          {!locked && (
            <Upload accept=".pdf,.docx,.txt,.jpg,.jpeg,.png,.webp" showUploadList={false} beforeUpload={(f) => { importAi(f); return false }}>
              <Button icon={<RobotOutlined />} loading={busy === 'ai'}>{busy === 'ai' ? 'AI đang đọc đề…' : 'Thêm câu hỏi từ file (AI)'}</Button>
            </Upload>
          )}
        </div>
      </div>

      {ai && !locked && <Alert type="warning" showIcon message="Câu hỏi do AI tách từ file – kiểm tra nội dung và đáp án đúng trước khi giao." />}
      {locked && <Alert type="info" showIcon message="Đã có người nộp bài: chỉ sửa được tên, hướng dẫn, hạn nộp và file." />}

      {questions.map((qn, i) => (
        <div key={i} className="lp-card p-4 flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <b className="num">Câu {i + 1}</b>
            <Select size="small" value={qn.kind} disabled={locked} style={{ width: 130 }}
              options={(Object.keys(KIND_LABEL) as QuestionKind[]).map((k) => ({ value: k, label: KIND_LABEL[k] }))}
              onChange={(k) => patchQ(i, { ...blank(k), prompt: qn.prompt, points: qn.points })} />
            <span className="text-sm text-slate-500">Điểm</span>
            <InputNumber size="small" min={0.25} max={100} step={0.25} value={num(qn.points) ?? 1} disabled={locked}
              onChange={(v) => patchQ(i, { points: v ?? 1 })} />
            <span className="flex-1" />
            {!locked && (
              <>
                <Button size="small" type="text" icon={<ArrowUpOutlined />} disabled={i === 0} onClick={() => move(i, -1)} aria-label="Lên" />
                <Button size="small" type="text" icon={<ArrowDownOutlined />} disabled={i === questions.length - 1} onClick={() => move(i, 1)} aria-label="Xuống" />
                <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => setQuestions((l) => l.filter((_, j) => j !== i))} aria-label="Xoá câu" />
              </>
            )}
          </div>
          <Input.TextArea value={qn.prompt} disabled={locked} autoSize={{ minRows: 1, maxRows: 6 }} placeholder="Nội dung câu hỏi"
            onChange={(e) => patchQ(i, { prompt: e.target.value })} />
          {qn.kind === 'mcq' && (
            <Radio.Group value={qn.options.findIndex((o) => o.correct)} disabled={locked} className="flex flex-col gap-1.5"
              onChange={(e) => patchQ(i, { options: qn.options.map((o, j) => ({ ...o, correct: j === e.target.value })) })}>
              {qn.options.map((o, j) => (
                <div key={j} className="flex items-center gap-2">
                  <Tooltip title="Đáp án đúng"><Radio value={j} /></Tooltip>
                  <Input size="small" value={o.text} disabled={locked} placeholder={`Phương án ${String.fromCharCode(65 + j)}`}
                    onChange={(e) => patchQ(i, { options: qn.options.map((x, k) => (k === j ? { ...x, text: e.target.value } : x)) })} />
                  {!locked && qn.options.length > 2 && (
                    <Button size="small" type="text" icon={<DeleteOutlined />} aria-label="Xoá phương án"
                      onClick={() => patchQ(i, { options: qn.options.filter((_, k) => k !== j) })} />
                  )}
                </div>
              ))}
              {!locked && qn.options.length < 8 && (
                <Button size="small" type="dashed" icon={<PlusOutlined />} className="self-start"
                  onClick={() => patchQ(i, { options: [...qn.options, { text: '', correct: false }] })}>Thêm phương án</Button>
              )}
            </Radio.Group>
          )}
          {qn.kind === 'fill' && (
            <Select mode="tags" value={qn.accepted_answers} disabled={locked} open={false} tokenSeparators={[';']}
              placeholder="Các đáp án đúng (Enter sau mỗi đáp án, VD: nǐ hǎo ↵ ni hao)" onChange={(v) => patchQ(i, { accepted_answers: v })} />
          )}
          {qn.kind === 'essay' && <span className="text-xs text-slate-500">Học viên viết câu trả lời, bạn chấm tay.</span>}
          {qn.kind === 'file' && <span className="text-xs text-slate-500">Học viên nộp file (ảnh chụp bài làm, ghi âm, Word…), bạn chấm tay.</span>}
          {!locked && (
            <Input size="small" value={qn.explanation} placeholder="Giải thích (hiện sau khi chấm – không bắt buộc)"
              onChange={(e) => patchQ(i, { explanation: e.target.value })} />
          )}
        </div>
      ))}
      {!locked && (
        <div className="flex flex-wrap gap-2">
          {(Object.keys(KIND_LABEL) as QuestionKind[]).map((k) => (
            <Button key={k} icon={<PlusOutlined />} onClick={() => setQuestions((l) => [...l, blank(k)])}>{KIND_LABEL[k]}</Button>
          ))}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2 sticky bottom-0 bg-[var(--surface)] py-2">
        <span className="text-sm text-slate-500 mr-auto">{questions.length ? `${questions.length} câu · ${+total.toFixed(2)} điểm` : `Không có câu hỏi · ${points} điểm`}</span>
        {a.status !== 'draft' && <Button onClick={onDone}>Huỷ</Button>}
        <Button loading={busy === 'save'} onClick={() => save()}>Lưu</Button>
        {a.status === 'draft' && (
          <Button type="primary" icon={<SendOutlined />} loading={busy === 'publish'}
            onClick={() => modal.confirm({ title: 'Giao bài cho cả nhóm?', content: 'Mọi thành viên nhận thông báo và bắt đầu làm được.',
              okText: 'Giao bài', cancelText: 'Chưa', onOk: () => save('publish') })}>Giao bài</Button>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- leader: hand-ins and marking

function LeaderView({ a, onEdit, onDeleted }: { a: Assignment; onEdit: () => void; onDeleted: () => void }) {
  const { message } = App.useApp()
  const qc = useQueryClient()
  const [params, setParams] = useSearchParams()
  const rows = useQuery({ queryKey: ['assignment-subs', a.id], queryFn: () => classworkApi.submissions(a.id) })
  const sid = Number(params.get('s')) || null
  const setSid = (s: number | null) => { const p = new URLSearchParams(params); if (s) p.set('s', String(s)); else p.delete('s'); setParams(p) }
  const act = async (fn: () => Promise<Assignment>) => {
    try { qc.setQueryData(['assignment', a.id], await fn()); qc.invalidateQueries({ queryKey: ['assignments', a.group] }) } catch (e) { message.error(errorMessage(e)) }
  }
  const submitted = rows.data?.filter((r) => r.submission).length ?? 0
  return (
    <div className="flex flex-col gap-3">
      <AssignmentHeader a={a} extra={
        <div className="flex flex-wrap gap-2">
          <Button onClick={onEdit}>Sửa</Button>
          {a.status === 'published'
            ? <Button onClick={() => act(() => classworkApi.close(a.id))}>Đóng nộp bài</Button>
            : <Button onClick={() => act(() => classworkApi.reopen(a.id))}>Mở lại</Button>}
          <Popconfirm title="Xoá bài tập này và mọi bài đã nộp?" okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}
            onConfirm={async () => { await classworkApi.remove(a.id); qc.invalidateQueries({ queryKey: ['assignments', a.group] }); onDeleted() }}>
            <Button danger>Xoá</Button>
          </Popconfirm>
        </div>
      } />
      <div className="font-semibold text-slate-700">Bài nộp ({submitted}/{rows.data?.length ?? 0})</div>
      <Table size="small" rowKey={(r) => r.user.id} loading={rows.isLoading} dataSource={rows.data} pagination={false} scroll={{ x: true }}
        columns={[
          { title: 'Thành viên', render: (_, r) => <span className="flex items-center gap-2"><UserAvatar name={r.user.display_name} src={r.user.avatar} mascot={r.user.mascot} size={26} />{r.user.display_name}</span> },
          { title: 'Trạng thái', render: (_, r) => !r.submission ? <Tag>Chưa nộp</Tag>
            : r.submission.graded_at ? <Tag color="green">Đã chấm</Tag> : <Tag color="cyan">Chờ chấm</Tag> },
          { title: 'Điểm', render: (_, r) => r.submission ? `${fmt(r.submission.score)}/${fmt(r.submission.max_score)}` : '' },
          { title: 'Nộp lúc', render: (_, r) => r.submission ? <span>{when(r.submission.submitted_at)}{r.submission.late && <Tag color="red" className="ml-1">muộn</Tag>}</span> : '' },
          { title: '', render: (_, r) => r.submission && <Button size="small" type={r.submission.graded_at ? 'default' : 'primary'} onClick={() => setSid(r.submission!.id)}>{r.submission.graded_at ? 'Xem / chấm lại' : 'Chấm'}</Button> },
        ]} />
      <GradeDrawer a={a} sid={sid} onClose={() => setSid(null)} onGraded={() => { rows.refetch(); qc.invalidateQueries({ queryKey: ['assignments', a.group] }) }} />
    </div>
  )
}

function GradeDrawer({ a, sid, onClose, onGraded }: { a: Assignment; sid: number | null; onClose: () => void; onGraded: () => void }) {
  const { message } = App.useApp()
  const sub = useQuery({ queryKey: ['submission', a.id, sid], queryFn: () => classworkApi.submission(a.id, sid!), enabled: !!sid })
  const [marks, setMarks] = useState<Record<number, { score: number | null; feedback: string }>>({})
  const [score, setScore] = useState<number | null>(null)
  const [feedback, setFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  useEffect(() => {
    const s = sub.data
    if (!s) return
    setMarks(Object.fromEntries(s.answers.map((x) => [x.id, { score: num(x.score), feedback: x.feedback }])))
    setScore(num(s.score))
    setFeedback(s.feedback)
  }, [sub.data])
  const s = sub.data
  const save = async () => {
    if (!s) return
    setSaving(true)
    try {
      const byQ = Object.fromEntries(a.questions.map((q) => [q.id, q]))
      const manual = s.answers.filter((x) => !['mcq', 'fill'].includes(byQ[x.question]?.kind ?? '') || marks[x.id]?.score !== num(x.score))
      if (manual.some((x) => marks[x.id]?.score == null) || (!a.questions.length && score == null)) {
        message.warning('Còn câu chưa cho điểm')
        return
      }
      await classworkApi.grade(a.id, s.id, {
        answers: manual.map((x) => ({ answer: x.id, score: marks[x.id]?.score ?? 0, feedback: marks[x.id]?.feedback ?? '' })),
        ...(a.questions.length ? {} : { score: score ?? 0 }), feedback })
      message.success('Đã chấm – học viên nhận được thông báo')
      sub.refetch()
      onGraded()
      onClose()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }
  return (
    <Drawer open={!!sid} onClose={onClose} width={640} title={s?.user ? `Bài của ${s.user.display_name}` : 'Bài nộp'}
      extra={<Button type="primary" loading={saving} onClick={save}>Lưu điểm</Button>}>
      {!s ? <Skeleton active /> : (
        <div className="flex flex-col gap-4">
          <div className="text-sm text-slate-500">Nộp lúc {when(s.submitted_at)}{s.late && <Tag color="red" className="ml-2">nộp muộn</Tag>}</div>
          {a.questions.length === 0 && (
            <div className="flex flex-col gap-2">
              {s.text && <div className="whitespace-pre-wrap rounded-lg bg-slate-100 p-3">{s.text}</div>}
              {s.attachment && <a href={s.attachment} target="_blank" rel="noreferrer"><PaperClipOutlined /> {s.attachment_name}</a>}
              <span className="flex items-center gap-2">Điểm <InputNumber min={0} max={num(a.points) ?? 10} step={0.25} value={score} onChange={setScore} /> / {fmt(a.points)}</span>
            </div>
          )}
          {a.questions.map((q, i) => {
            const x = s.answers.find((y) => y.question === q.id)
            const auto = q.kind === 'mcq' || q.kind === 'fill'
            return (
              <div key={q.id} className="border-b border-slate-100 pb-3">
                <div className="font-medium whitespace-pre-wrap">Câu {i + 1} <span className="text-xs text-slate-400">({KIND_LABEL[q.kind]}, {fmt(q.points)} đ)</span>: {q.prompt}</div>
                {q.kind === 'mcq' && <div className="text-sm mt-1">Chọn: <b>{x?.selected_option != null ? q.options[x.selected_option]?.text : '—'}</b> · Đúng: {q.options.find((o) => o.correct)?.text}</div>}
                {q.kind === 'fill' && <div className="text-sm mt-1">Trả lời: <b>{x?.text || '—'}</b> · Đáp án: {q.accepted_answers?.join(' / ')}</div>}
                {(q.kind === 'essay' || q.kind === 'file') && x?.text && <div className="whitespace-pre-wrap rounded-lg bg-slate-100 p-2 mt-1 text-sm">{x.text}</div>}
                {x?.attachment && <a href={x.attachment} target="_blank" rel="noreferrer" className="block mt-1"><PaperClipOutlined /> {x.attachment_name}</a>}
                {x && (
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    {auto && (x.is_correct ? <CheckCircleFilled className="text-green-600" /> : <CloseCircleFilled className="text-red-500" />)}
                    <InputNumber size="small" min={0} max={num(q.points) ?? 1} step={0.25} value={marks[x.id]?.score}
                      onChange={(v) => setMarks((m) => ({ ...m, [x.id]: { ...m[x.id], score: v } }))} />
                    <span className="text-sm text-slate-500">/ {fmt(q.points)}</span>
                    <Input size="small" className="flex-1 min-w-[180px]" placeholder="Nhận xét câu này" value={marks[x.id]?.feedback}
                      onChange={(e) => setMarks((m) => ({ ...m, [x.id]: { ...m[x.id], feedback: e.target.value } }))} />
                  </div>
                )}
              </div>
            )
          })}
          <Input.TextArea value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="Nhận xét chung cho bài này"
            autoSize={{ minRows: 2, maxRows: 6 }} />
        </div>
      )}
    </Drawer>
  )
}

// ---------------------------------------------------------------- member: doing the work

function AssignmentHeader({ a, extra }: { a: Assignment; extra?: React.ReactNode }) {
  return (
    <div className="lp-card p-4 flex flex-col gap-2">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="m-0 text-xl font-bold text-slate-800">{a.title} {statusTag(a)}</h3>
          <div className="text-sm text-slate-500">
            {a.question_count ? `${a.question_count} câu` : 'Nộp bài làm / file'} · {fmt(a.max_score)} điểm
            {a.due_at && ` · hạn ${when(a.due_at)}${a.allow_late ? '' : ' (không nhận bài muộn)'}`}
          </div>
        </div>
        {extra}
      </div>
      {a.instructions && <div className="whitespace-pre-wrap text-slate-700">{a.instructions}</div>}
      {a.attachment && <a href={a.attachment} target="_blank" rel="noreferrer" className="self-start"><PaperClipOutlined /> {a.attachment_name}</a>}
      {a.ai_generated && a.is_leader && <span className="text-xs text-slate-400">Câu hỏi do AI tách từ file</span>}
    </div>
  )
}

function DoView({ a }: { a: Assignment }) {
  const { message, modal } = App.useApp()
  const qc = useQueryClient()
  const mine = a.my_submission
  const done = !!mine?.graded_at
  const [answers, setAnswers] = useState<Record<number, { selected_option?: number | null; text?: string }>>({})
  const [files, setFiles] = useState<Record<string, File>>({})
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  useEffect(() => {
    if (!mine) return
    setAnswers(Object.fromEntries(mine.answers.map((x) => [x.question, { selected_option: x.selected_option, text: x.text }])))
    setText(mine.text)
  }, [mine])
  const closed = a.status !== 'published' || (!!a.due_at && dayjs(a.due_at).isBefore(dayjs()) && !a.allow_late)
  const submit = async () => {
    setSending(true)
    try {
      const x = await classworkApi.submit(a.id, a.questions.map((q) => ({ question: q.id!, ...answers[q.id!] })), files, text)
      qc.setQueryData(['assignment', a.id], x)
      qc.invalidateQueries({ queryKey: ['assignments', a.group] })
      setFiles({})
      message.success(x.my_submission?.graded_at ? 'Đã nộp và chấm xong' : 'Đã nộp bài')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSending(false)
    }
  }
  const pick = (key: string) => (
    <Upload accept={FILE_ACCEPT} maxCount={1} disabled={done || closed} beforeUpload={(f) => { setFiles((m) => ({ ...m, [key]: f })); return false }}
      onRemove={() => setFiles((m) => { const c = { ...m }; delete c[key]; return c })}
      fileList={files[key] ? [{ uid: key, name: files[key].name, status: 'done' }] : []}>
      <Button icon={<PaperClipOutlined />} disabled={done || closed}>Chọn file</Button>
    </Upload>
  )
  const result = (qid: number) => mine?.answers.find((x) => x.question === qid)
  return (
    <div className="flex flex-col gap-3">
      <AssignmentHeader a={a} />
      {mine && (
        <Alert type={done ? 'success' : 'info'} showIcon
          message={done ? `Đã chấm: ${fmt(mine.score)}/${fmt(mine.max_score)} điểm${mine.percent != null ? ` (${mine.percent}%)` : ''}`
            : `Đã nộp lúc ${when(mine.submitted_at)}${mine.late ? ' (muộn)' : ''} – chờ trưởng nhóm chấm. Bạn vẫn sửa và nộp lại được.`}
          description={mine.feedback || undefined} />
      )}
      {a.questions.length === 0 ? (
        <div className="lp-card p-4 flex flex-col gap-2">
          <Input.TextArea value={text} onChange={(e) => setText(e.target.value)} disabled={done || closed} autoSize={{ minRows: 4, maxRows: 14 }}
            placeholder="Bài làm của bạn (hoặc chụp bài làm rồi đính kèm)" />
          {mine?.attachment && <a href={mine.attachment} target="_blank" rel="noreferrer"><PaperClipOutlined /> {mine.attachment_name} (đã nộp)</a>}
          {pick('file')}
        </div>
      ) : a.questions.map((q, i) => {
        const r = result(q.id!)
        const val = answers[q.id!] ?? {}
        const set = (p: { selected_option?: number | null; text?: string }) => setAnswers((m) => ({ ...m, [q.id!]: { ...m[q.id!], ...p } }))
        return (
          <div key={q.id} className="lp-card p-4 flex flex-col gap-2">
            <div className="flex items-start gap-2">
              <b className="num shrink-0">Câu {i + 1}.</b>
              <span className="whitespace-pre-wrap flex-1">{q.prompt}</span>
              <span className="text-xs text-slate-400 shrink-0">{fmt(q.points)} đ</span>
              {done && r && (r.is_correct ? <CheckCircleFilled className="text-green-600" /> : r.is_correct === false ? <CloseCircleFilled className="text-red-500" /> : null)}
            </div>
            {q.kind === 'mcq' && (
              <Radio.Group value={val.selected_option ?? null} disabled={done || closed} onChange={(e) => set({ selected_option: e.target.value })}
                className="flex flex-col gap-1">
                {q.options.map((o, j) => (
                  <Radio key={j} value={j}>
                    <span className={done && o.correct ? 'font-semibold text-green-700' : ''}>{String.fromCharCode(65 + j)}. {o.text}</span>
                  </Radio>
                ))}
              </Radio.Group>
            )}
            {q.kind === 'fill' && <Input value={val.text} disabled={done || closed} onChange={(e) => set({ text: e.target.value })} placeholder="Câu trả lời" />}
            {(q.kind === 'essay' || q.kind === 'file') && (
              <Input.TextArea value={val.text} disabled={done || closed} onChange={(e) => set({ text: e.target.value })} autoSize={{ minRows: q.kind === 'essay' ? 3 : 1, maxRows: 12 }}
                placeholder={q.kind === 'essay' ? 'Câu trả lời của bạn' : 'Ghi chú (không bắt buộc)'} />
            )}
            {q.kind === 'file' && (
              <>
                {r?.attachment && <a href={r.attachment} target="_blank" rel="noreferrer"><PaperClipOutlined /> {r.attachment_name} (đã nộp)</a>}
                {pick(`file_${q.id}`)}
              </>
            )}
            {done && r && (r.score != null || r.feedback) && (
              <div className="text-sm text-slate-600">{fmt(r.score)}/{fmt(q.points)} điểm{r.feedback && ` – ${r.feedback}`}</div>
            )}
            {done && q.kind === 'fill' && q.accepted_answers && <div className="text-sm text-green-700">Đáp án: {q.accepted_answers.join(' / ')}</div>}
            {done && q.explanation && <div className="text-sm text-slate-500">{q.explanation}</div>}
          </div>
        )
      })}
      {!done && !closed && (
        <Button type="primary" size="large" icon={<SendOutlined />} loading={sending} className="self-end"
          onClick={() => {
            const empty = a.questions.filter((q) => { const v = answers[q.id!]; return q.kind === 'mcq' ? v?.selected_option == null : q.kind === 'file' ? !files[`file_${q.id}`] && !result(q.id!)?.attachment : !v?.text?.trim() }).length
            if (empty && a.questions.length) {
              modal.confirm({ title: `Còn ${empty} câu chưa làm`, content: 'Vẫn nộp bài?', okText: 'Nộp', cancelText: 'Làm tiếp', onOk: submit })
            } else submit()
          }}>{mine ? 'Nộp lại' : 'Nộp bài'}</Button>
      )}
      {closed && !mine && <Alert type="warning" showIcon message="Bài tập đã đóng hoặc đã quá hạn nộp." />}
    </div>
  )
}

// ---------------------------------------------------------------- gradebook

function GradebookTable({ groupId, onOpen }: { groupId: number; onOpen: (id: number) => void }) {
  const book = useQuery({ queryKey: ['gradebook', groupId], queryFn: () => classworkApi.gradebook(groupId) })
  const b = book.data
  if (book.isLoading) return <Skeleton active />
  if (!b?.assignments.length) return <Empty description="Chưa có bài tập nào được giao" />
  const cell = (c: HandInBrief | null) => !c ? <span className="text-slate-300">–</span>
    : c.graded_at ? <span className={c.percent != null && c.percent < 50 ? 'text-red-600' : ''}>{fmt(c.score)}</span>
      : <Tag color="cyan">chờ chấm</Tag>
  return (
    <Table size="small" rowKey={(r) => r.user.id} dataSource={b.rows} pagination={false} scroll={{ x: true }}
      columns={[
        { title: 'Thành viên', fixed: 'left', render: (_, r) => r.user.display_name },
        ...b.assignments.map((a, i) => ({
          title: <button type="button" className="cursor-pointer text-left" onClick={() => onOpen(a.id)} title={a.title}>
            {a.title.length > 14 ? a.title.slice(0, 13) + '…' : a.title}<div className="text-[11px] text-slate-400">/{fmt(a.max_score)}</div></button>,
          render: (_: unknown, r: (typeof b.rows)[number]) => cell(r.cells[i]),
        })),
        { title: 'TB (%)', render: (_, r) => (r.average == null ? '–' : <b>{r.average}</b>) },
      ]} />
  )
}

