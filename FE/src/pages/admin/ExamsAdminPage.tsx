import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Card, Form, Input, InputNumber, Modal, Select, Space, Switch, Table, Tabs, Tag } from 'antd'
import { useState } from 'react'
import dayjs from 'dayjs'
import { adminApi, type AdminExam, type AdminQuestion } from '../../api/admin'
import type { Submission } from '../../api/app'
import { errorMessage } from '../../api/client'
import { langTag } from '../../components/TargetWord'
import { BulkDeleteBar, DateRangeFilter, dateParams, pagination, useBulkDelete, useSelection, type DateRange } from '../../components/DataTools'

const LANGS = [{ value: 'en', label: 'Tiếng Anh' }, { value: 'zh-Hans', label: 'Giản thể' }, { value: 'zh-Hant', label: 'Phồn thể' }, { value: 'vi', label: 'Tiếng Việt' }]

function Grading() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [current, setCurrent] = useState<Submission | null>(null)
  const [scores, setScores] = useState<Record<number, { score: number; feedback: string }>>({})
  const [feedback, setFeedback] = useState('')
  const [submitted, setSubmitted] = useState<DateRange>(null)
  const list = useQuery({
    queryKey: ['admin-submissions', submitted?.map((d) => d.format('YYYY-MM-DD'))],
    queryFn: () => adminApi.submissions({ status: 'submitted', page_size: 100, ...dateParams(submitted) }),
  })
  const save = async () => {
    if (!current) return
    try {
      await adminApi.grade(current.id, Object.entries(scores).map(([answer, v]) => ({ answer: Number(answer), score: String(v.score), feedback: v.feedback })), feedback)
      message.success('Đã chấm bài – học viên đã nhận thông báo')
      setCurrent(null)
      queryClient.invalidateQueries({ queryKey: ['admin-submissions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <>
      <div className="mb-3"><DateRangeFilter value={submitted} onChange={setSubmitted} placeholder={['Nộp từ ngày', 'đến ngày']} /></div>
      <Table<Submission> rowKey="id" loading={list.isLoading} dataSource={list.data?.results} columns={[
        { title: 'Học viên', dataIndex: 'user_email' },
        { title: 'Đề', dataIndex: 'exam_title' },
        { title: 'Nộp lúc', dataIndex: 'submitted_at', render: (v) => dayjs(v).format('HH:mm DD/MM') },
        { title: 'Điểm tự động', render: (_, s) => `${s.score} / ${s.max_score}` },
        { title: '', render: (_, s) => <Button type="primary" onClick={() => { setCurrent(s); setScores({}); setFeedback('') }}>Chấm</Button> },
      ]} />
      <Modal title={current ? `Chấm bài: ${current.exam_title}` : ''} open={!!current} onOk={save} onCancel={() => setCurrent(null)} width={760} okText="Lưu điểm">
        {current?.answers.filter((a) => a.question.kind === 'essay').map((a) => (
          <Card key={a.id} size="small" className="mb-3">
            <div className="font-medium">{a.question.prompt}</div>
            <div className="bg-slate-50 rounded p-2 my-2 whitespace-pre-wrap">{a.text || '(bỏ trống)'}</div>
            <Space>
              Điểm (tối đa {a.question.points}):
              <InputNumber min={0} max={Number(a.question.points)} step={0.5} value={scores[a.id]?.score}
                onChange={(v) => setScores({ ...scores, [a.id]: { score: Number(v ?? 0), feedback: scores[a.id]?.feedback ?? '' } })} />
            </Space>
            <Input className="mt-2" placeholder="Nhận xét cho câu này" value={scores[a.id]?.feedback}
              onChange={(e) => setScores({ ...scores, [a.id]: { score: scores[a.id]?.score ?? 0, feedback: e.target.value } })} />
          </Card>
        ))}
        <Input.TextArea placeholder="Nhận xét chung" value={feedback} onChange={(e) => setFeedback(e.target.value)} />
      </Modal>
    </>
  )
}

function Exams() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [lang, setLang] = useState<string | undefined>()
  const [published, setPublished] = useState<string | undefined>()
  const [created, setCreated] = useState<DateRange>(null)
  const filters = { search: search || undefined, language: lang, is_published: published, ...dateParams(created) }
  const list = useQuery({ queryKey: ['admin-exams', page, pageSize, filters], queryFn: () => adminApi.exams({ page, page_size: pageSize, ...filters }) })
  const selection = useSelection<AdminExam>([filters])
  const bulk = useBulkDelete('/admin/exams/bulk-delete/', () => { selection.clear(); queryClient.invalidateQueries({ queryKey: ['admin-exams'] }) })
  const filter = <V,>(set: (v: V) => void) => (v: V) => { set(v); setPage(1) }
  const toggle = useMutation({
    mutationFn: (e: AdminExam) => adminApi.updateExam(e.id, { is_published: !e.is_published }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-exams'] }),
    onError: (e) => message.error(errorMessage(e)),
  })
  return (
    <>
    <div className="flex flex-wrap gap-2 mb-3">
      <Input.Search placeholder="Tìm tên đề" allowClear onSearch={filter(setSearch)} style={{ width: 200 }} />
      <Select allowClear placeholder="Ngôn ngữ" options={LANGS} value={lang} onChange={filter(setLang)} style={{ width: 140 }} />
      <Select allowClear placeholder="Xuất bản" value={published} onChange={filter(setPublished)} style={{ width: 140 }}
        options={[{ value: 'true', label: 'Đang xuất bản' }, { value: 'false', label: 'Bản nháp' }]} />
      <DateRangeFilter value={created} onChange={filter(setCreated)} />
    </div>
    <BulkDeleteBar count={selection.keys.length} noun="đề thi" busy={bulk.busy} onClear={selection.clear}
      warning="Đề đã có học viên làm được giữ lại (tắt xuất bản thay vì xoá để giữ kết quả)."
      onDelete={() => bulk.run(selection.keys, (n) => `${n} đề thi`)} />
    <Table<AdminExam> rowKey="id" loading={list.isLoading} dataSource={list.data?.results}
      rowSelection={selection.rowSelection}
      pagination={pagination(page, list.data?.count, pageSize, (p, size) => { setPage(size === pageSize ? p : 1); setPageSize(size) })}
      expandable={{ expandedRowRender: (e) => (
        <ol className="m-0">{e.questions.map((q) => <li key={q.id}><Tag>{q.kind}</Tag><span lang={langTag(e.language)}>{q.prompt}</span> ({q.points}đ)</li>)}</ol>
      ) }}
      columns={[
        { title: 'Tên đề', dataIndex: 'title' },
        { title: 'Ngôn ngữ', dataIndex: 'language', render: (v) => LANGS.find((l) => l.value === v)?.label },
        { title: 'Số câu', render: (_, e) => e.questions.length },
        { title: 'Lượt làm', dataIndex: 'submission_count' },
        { title: 'Xuất bản', render: (_, e) => <Switch checked={e.is_published} onChange={() => toggle.mutate(e)} /> },
      ]} />
    </>
  )
}

function Questions() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [lang, setLang] = useState<string | undefined>()
  const [kindFilter, setKindFilter] = useState<string | undefined>()
  const [search, setSearch] = useState('')
  const [created, setCreated] = useState<DateRange>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()
  const filters = { language: lang, kind: kindFilter, search: search || undefined, ...dateParams(created) }
  const list = useQuery({ queryKey: ['admin-questions', page, pageSize, filters], queryFn: () => adminApi.questions({ page, page_size: pageSize, ...filters }) })
  const selection = useSelection<AdminQuestion>([filters])
  const bulk = useBulkDelete('/admin/questions/bulk-delete/', () => { selection.clear(); queryClient.invalidateQueries({ queryKey: ['admin-questions'] }) })
  const filter = <V,>(set: (v: V) => void) => (v: V) => { set(v); setPage(1) }
  const kind = Form.useWatch('kind', form)
  const create = async () => {
    const v = await form.validateFields()
    const data: Partial<AdminQuestion> = { kind: v.kind, language: v.language, prompt: v.prompt, explanation: v.explanation ?? '' }
    if (v.kind === 'mcq') data.options = (v.options as string[]).map((t, i) => ({ text: t, correct: i === v.correct }))
    if (v.kind === 'fill') data.accepted_answers = String(v.accepted).split(',').map((x: string) => x.trim()).filter(Boolean)
    try {
      await adminApi.createQuestion(data)
      setOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['admin-questions'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <>
      <div className="flex flex-wrap gap-2 mb-3">
        <Input.Search placeholder="Tìm nội dung" allowClear onSearch={filter(setSearch)} style={{ width: 200 }} />
        <Select allowClear placeholder="Ngôn ngữ" options={LANGS} value={lang} onChange={filter(setLang)} style={{ width: 140 }} />
        <Select allowClear placeholder="Loại câu" value={kindFilter} onChange={filter(setKindFilter)} style={{ width: 140 }}
          options={[{ value: 'mcq', label: 'Trắc nghiệm' }, { value: 'fill', label: 'Điền từ' }, { value: 'essay', label: 'Tự luận' }]} />
        <DateRangeFilter value={created} onChange={filter(setCreated)} />
        <Button type="primary" className="ml-auto" onClick={() => setOpen(true)}>Thêm câu hỏi</Button>
      </div>
      <BulkDeleteBar count={selection.keys.length} noun="câu hỏi" busy={bulk.busy} onClear={selection.clear}
        warning="Câu đang nằm trong một đề thi được giữ lại."
        onDelete={() => bulk.run(selection.keys, (n) => `${n} câu hỏi`)} />
      <Table<AdminQuestion> rowKey="id" loading={list.isLoading} dataSource={list.data?.results}
        rowSelection={selection.rowSelection}
        pagination={pagination(page, list.data?.count, pageSize, (p, size) => { setPage(size === pageSize ? p : 1); setPageSize(size) })}
        columns={[
        { title: 'Loại', dataIndex: 'kind', render: (v) => <Tag>{{ mcq: 'Trắc nghiệm', fill: 'Điền từ', essay: 'Tự luận' }[v as string]}</Tag> },
        { title: 'Ngôn ngữ', dataIndex: 'language' },
        { title: 'Nội dung', render: (_, q) => <span lang={langTag(q.language)}>{q.prompt}</span> },
        { title: 'Đáp án', render: (_, q) => <span lang={langTag(q.language)}>{q.kind === 'mcq' ? q.options.find((o) => o.correct)?.text : q.accepted_answers.join(' / ')}</span> },
      ]} />
      <Modal title="Thêm câu hỏi" open={open} onOk={create} onCancel={() => setOpen(false)} width={640}>
        <Form form={form} layout="vertical" initialValues={{ kind: 'mcq', options: ['', '', '', ''], correct: 0 }}>
          <Space wrap>
            <Form.Item name="kind" label="Loại"><Select style={{ width: 150 }} options={[{ value: 'mcq', label: 'Trắc nghiệm' }, { value: 'fill', label: 'Điền từ' }, { value: 'essay', label: 'Tự luận' }]} /></Form.Item>
            <Form.Item name="language" label="Ngôn ngữ" rules={[{ required: true }]}><Select style={{ width: 160 }} options={LANGS} /></Form.Item>
          </Space>
          <Form.Item name="prompt" label="Câu hỏi" rules={[{ required: true }]}><Input.TextArea /></Form.Item>
          {kind === 'mcq' && (
            <>
              <Form.List name="options">{(fields) => fields.map((f, i) => (
                <Form.Item key={f.key} name={f.name} label={`Phương án ${String.fromCharCode(65 + i)}`} rules={[{ required: true }]}><Input /></Form.Item>
              ))}</Form.List>
              <Form.Item name="correct" label="Đáp án đúng"><Select options={[0, 1, 2, 3].map((i) => ({ value: i, label: String.fromCharCode(65 + i) }))} /></Form.Item>
            </>
          )}
          {kind === 'fill' && <Form.Item name="accepted" label="Đáp án chấp nhận (phân tách bằng dấu phẩy)" rules={[{ required: true }]}><Input /></Form.Item>}
          <Form.Item name="explanation" label="Giải thích"><Input /></Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default function ExamsAdminPage() {
  return (
    <Card title="Câu hỏi & đề thi">
      <Tabs items={[
        { key: 'grading', label: 'Chấm tự luận', children: <Grading /> },
        { key: 'exams', label: 'Đề thi', children: <Exams /> },
        { key: 'questions', label: 'Ngân hàng câu hỏi', children: <Questions /> },
      ]} />
    </Card>
  )
}
