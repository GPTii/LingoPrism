import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, App, Button, Card, Descriptions, Form, Input, Modal, Select, Space, Table, Tabs, Tag } from 'antd'
import { CheckOutlined, CloseOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons'
import { useState } from 'react'
import dayjs from 'dayjs'
import { adminVocabApi, LANG_LABEL, STATUS_TAG, type AdminExample, type AdminReport, type AdminTranslation, type ReviewStatus } from '../../api/adminVocab'
import { errorMessage } from '../../api/client'
import { langTag } from '../../components/TargetWord'
import { TokenLine } from '../../components/SentenceView'
import CandidateQueue from './CandidateQueue'
import SearchBox from '../../components/SearchBox'

function SourcesView({ tr }: { tr: AdminTranslation }) {
  return (
    <div className="flex flex-col gap-3">
      {tr.issues.map((i, idx) => (
        <Alert key={idx} type={i.level === 'error' ? 'error' : 'warning'} message={i.message} showIcon />
      ))}
      <pre className="bg-slate-50 rounded-lg p-3 text-xs max-h-80 overflow-auto whitespace-pre-wrap">{JSON.stringify(tr.sources, null, 2)}</pre>
    </div>
  )
}

function TranslationQueue() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<ReviewStatus>('flagged')
  const [language, setLanguage] = useState<string | undefined>()
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<AdminTranslation | null>(null)
  const [form] = Form.useForm()

  const list = useQuery({
    queryKey: ['admin-translations', status, language, page],
    queryFn: () => adminVocabApi.translations({ status, language, page }),
  })
  const done = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-translations'] })
    queryClient.invalidateQueries({ queryKey: ['admin-vocab-stats'] })
  }
  const act = useMutation({
    mutationFn: ({ id, kind }: { id: number; kind: 'verify' | 'reject' | 'recheck' }) => adminVocabApi[kind](id),
    onSuccess: (tr) => { message.success(`Trạng thái: ${STATUS_TAG[tr.status].label}`); done() },
    onError: (e) => message.error(errorMessage(e)),
  })

  const saveEdit = async () => {
    if (!editing) return
    const v = await form.validateFields()
    try {
      await adminVocabApi.updateTranslation(editing.id, {
        ...v, accepted_variants: (v.accepted_variants ?? '').split(',').map((x: string) => x.trim()).filter(Boolean),
      })
      message.success('Đã lưu – bản dịch cần được duyệt lại')
      setEditing(null)
      done()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  return (
    <>
      <div className="flex gap-2 mb-4">
        <Select value={status} onChange={(v) => { setStatus(v); setPage(1) }} style={{ width: 160 }}
          options={Object.entries(STATUS_TAG).map(([value, t]) => ({ value, label: t.label }))} />
        <Select allowClear placeholder="Ngôn ngữ" value={language} onChange={(v) => { setLanguage(v); setPage(1) }} style={{ width: 160 }}
          options={Object.entries(LANG_LABEL).map(([value, label]) => ({ value, label }))} />
      </div>
      <Table<AdminTranslation>
        rowKey="id"
        loading={list.isLoading}
        dataSource={list.data?.results}
        pagination={{ current: page, total: list.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        expandable={{ expandedRowRender: (tr) => <SourcesView tr={tr} /> }}
        columns={[
          { title: 'Khái niệm', dataIndex: 'word_slug', render: (v) => <span className="font-mono">{v}</span> },
          { title: 'Ngôn ngữ', dataIndex: 'language', render: (v) => LANG_LABEL[v] },
          { title: 'Nội dung', render: (_, tr) => (
            <div>
              <div lang={langTag(tr.language)} className="text-lg font-medium">{tr.text}</div>
              <div className="text-xs text-slate-500">{tr.ipa ? `/${tr.ipa}/` : tr.pinyin}{tr.zhuyin ? ` · ${tr.zhuyin}` : ''}</div>
            </div>
          ) },
          { title: 'Lỗi', render: (_, tr) => tr.issues.filter((i) => i.level === 'error').map((i, idx) => <div key={idx} className="text-red-600 text-xs">{i.message}</div>) },
          { title: 'Trạng thái', dataIndex: 'status', render: (v: ReviewStatus, tr) => <Tag color={STATUS_TAG[v].color}>{STATUS_TAG[v].label}{tr.verified_method === 'manual' ? ' (thủ công)' : ''}</Tag> },
          { title: '', render: (_, tr) => (
            <Space>
              <Button size="small" icon={<ReloadOutlined />} onClick={() => act.mutate({ id: tr.id, kind: 'recheck' })}>Kiểm tra lại</Button>
              <Button size="small" icon={<EditOutlined />} onClick={() => { setEditing(tr); form.setFieldsValue({ ...tr, accepted_variants: tr.accepted_variants.join(', ') }) }} />
              <Button size="small" type="primary" icon={<CheckOutlined />} onClick={() => Modal.confirm({
                title: 'Xác nhận duyệt thủ công?',
                content: 'Chỉ duyệt khi bạn chắc chắn mặt chữ, phiên âm và nghĩa đều đúng (đã đối chiếu nguồn bên dưới).',
                onOk: () => act.mutate({ id: tr.id, kind: 'verify' }),
              })}>Duyệt</Button>
              <Button size="small" danger icon={<CloseOutlined />} onClick={() => act.mutate({ id: tr.id, kind: 'reject' })} />
            </Space>
          ) },
        ]}
      />
      <Modal title="Sửa bản dịch" open={!!editing} onOk={saveEdit} onCancel={() => setEditing(null)} okText="Lưu" width={640}>
        {editing && (
          <Form form={form} layout="vertical">
            <Descriptions size="small" column={{ xs: 1, sm: 2 }} className="mb-4" items={[
              { label: 'Khái niệm', children: editing.word_slug }, { label: 'Ngôn ngữ', children: LANG_LABEL[editing.language] },
            ]} />
            <Form.Item name="text" label="Nội dung" rules={[{ required: true }]}><Input lang={langTag(editing.language)} /></Form.Item>
            {editing.language === 'en' && <Form.Item name="ipa" label="IPA"><Input /></Form.Item>}
            {editing.language.startsWith('zh') && (
              <>
                <Form.Item name="pinyin" label="Pinyin (có dấu)"><Input /></Form.Item>
                {editing.language === 'zh-Hant' && <Form.Item name="zhuyin" label="Zhuyin"><Input lang="zh-Hant-TW" /></Form.Item>}
                <Form.Item name="measure_word" label="Lượng từ"><Input lang={langTag(editing.language)} /></Form.Item>
              </>
            )}
            <Form.Item name="accepted_variants" label="Dạng viết khác được chấp nhận khi chấm (phân tách bằng dấu phẩy)"><Input /></Form.Item>
            <Alert type="info" showIcon message="Sau khi sửa, bản dịch chuyển về 'Cần xem lại'. Bấm 'Kiểm tra lại' để chạy bộ đối chiếu nguồn tự động." />
          </Form>
        )}
      </Modal>
    </>
  )
}

function ReportsQueue() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<AdminReport['status']>('open')
  const list = useQuery({ queryKey: ['admin-reports', status], queryFn: () => adminVocabApi.reports({ status }) })
  const update = useMutation({
    mutationFn: ({ id, s }: { id: number; s: AdminReport['status'] }) => adminVocabApi.updateReport(id, s),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-reports'] }),
  })
  return (
    <>
      <Select value={status} onChange={setStatus} className="mb-4" style={{ width: 160 }}
        options={[{ value: 'open', label: 'Chờ xử lý' }, { value: 'resolved', label: 'Đã sửa' }, { value: 'rejected', label: 'Không phải lỗi' }]} />
      <Table<AdminReport>
        rowKey="id"
        loading={list.isLoading}
        dataSource={list.data?.results}
        columns={[
          { title: 'Thời gian', dataIndex: 'created_at', render: (v) => dayjs(v).format('DD/MM HH:mm') },
          { title: 'Người báo', dataIndex: 'user_email' },
          { title: 'Từ', render: (_, r) => <span><span className="font-mono">{r.word_slug}</span> {r.translation_text && <b>· {r.translation_text}</b>}</span> },
          { title: 'Lý do', dataIndex: 'reason' },
          { title: 'Mô tả', dataIndex: 'details' },
          { title: '', render: (_, r) => r.status === 'open' && (
            <Space>
              <Button size="small" onClick={() => update.mutate({ id: r.id, s: 'resolved' })}>Đã sửa</Button>
              <Button size="small" onClick={() => update.mutate({ id: r.id, s: 'rejected' })}>Không phải lỗi</Button>
            </Space>
          ) },
        ]}
      />
    </>
  )
}

function ExampleQueue() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<ReviewStatus>('flagged')
  const [language, setLanguage] = useState<string | undefined>()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const list = useQuery({
    queryKey: ['admin-examples', status, language, search, page],
    queryFn: () => adminVocabApi.examples({ status, language, page, search: search || undefined }),
  })
  const act = useMutation({
    mutationFn: ({ id, to }: { id: number; to: ReviewStatus }) => adminVocabApi.setExampleStatus(id, to),
    onSuccess: (ex) => {
      message.success(`Trạng thái: ${STATUS_TAG[ex.status].label}`)
      queryClient.invalidateQueries({ queryKey: ['admin-examples'] })
    },
    onError: (e) => message.error(errorMessage(e)),
  })

  return (
    <div className="flex flex-col gap-3">
      <Alert type="info" showIcon message="Câu ví dụ lấy từ Tatoeba (người bản xứ viết, CC BY 2.0 FR). Câu bị gắn cờ khi pinyin không khớp nguồn đối chiếu, lẫn chữ giản/phồn hoặc khác cách đọc Đài Loan – học viên không thấy cho tới khi được duyệt." />
      <Space wrap>
        <Select value={status} onChange={(v) => { setStatus(v); setPage(1) }} style={{ width: 150 }}
          options={(['flagged', 'verified', 'rejected', 'draft'] as ReviewStatus[]).map((v) => ({ value: v, label: STATUS_TAG[v].label }))} />
        <Select allowClear placeholder="Ngôn ngữ" value={language} onChange={(v) => { setLanguage(v); setPage(1) }} style={{ width: 170 }}
          options={Object.entries(LANG_LABEL).map(([value, label]) => ({ value, label }))} />
        <SearchBox allowClear placeholder="Tìm trong câu / bản dịch" onSearch={(v) => { setSearch(v); setPage(1) }} style={{ width: 260 }} />
      </Space>
      <Table<AdminExample>
        rowKey="id"
        loading={list.isLoading}
        dataSource={list.data?.results}
        scroll={{ x: 900 }}
        pagination={{ current: page, total: list.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        columns={[
          { title: 'Từ', dataIndex: 'word_slug', width: 120 },
          {
            title: 'Câu', key: 'text',
            render: (_, ex) => (
              <div className="flex flex-col gap-1 items-start">
                {ex.tokens.length ? <TokenLine tokens={ex.tokens} language={ex.language} highlight={ex.target_tokens} size="text-lg" /> : <span lang={langTag(ex.language)}>{ex.text}</span>}
                <span className="text-slate-500 text-xs">{ex.translation_vi || ex.translation_en}</span>
                {ex.source === 'tatoeba' && <a className="text-xs" href={`https://tatoeba.org/sentences/show/${ex.source_id}`} target="_blank" rel="noreferrer">Tatoeba #{ex.source_id}</a>}
              </div>
            ),
          },
          { title: 'Ngôn ngữ', dataIndex: 'language', width: 110, render: (v) => LANG_LABEL[v] ?? v },
          {
            title: 'Kiểm tra tự động', key: 'checks', width: 300,
            render: (_, ex) => (
              <div className="flex flex-col gap-1 text-xs">
                {ex.checks.errors?.map((m, i) => <Tag key={i} color="red" className="whitespace-normal">{m}</Tag>)}
                {ex.checks.warnings?.map((m, i) => <Tag key={`w${i}`} className="whitespace-normal">{m}</Tag>)}
                {ex.checks.manual && <span className="text-slate-400">Duyệt tay: {ex.checks.manual.by} · {dayjs(ex.checks.manual.at).format('DD/MM HH:mm')}</span>}
              </div>
            ),
          },
          {
            title: '', key: 'actions', width: 120,
            render: (_, ex) => (
              <Space>
                {ex.status !== 'verified' && <Button size="small" type="primary" icon={<CheckOutlined />} title="Duyệt" onClick={() => act.mutate({ id: ex.id, to: 'verified' })} />}
                {ex.status !== 'rejected' && <Button size="small" danger icon={<CloseOutlined />} title="Loại" onClick={() => act.mutate({ id: ex.id, to: 'rejected' })} />}
              </Space>
            ),
          },
        ]}
      />
    </div>
  )
}

export default function LanguageReviewPage() {
  return (
    <Card title="Kiểm tra dữ liệu ngôn ngữ">
      <Alert className="mb-4" type="info" showIcon
        message="Học viên chỉ nhìn thấy bản dịch 'Đã kiểm tra'. Bản dịch lệch nguồn (CC-CEDICT, HSK, từ điển Bộ GD Đài Loan, CMUdict) hoặc bị nhiều học viên báo lỗi sẽ vào đây." />
      <Tabs items={[
        { key: 'queue', label: 'Hàng chờ bản dịch', children: <TranslationQueue /> },
        { key: 'examples', label: 'Câu ví dụ', children: <ExampleQueue /> },
        { key: 'reports', label: 'Báo lỗi từ học viên', children: <ReportsQueue /> },
        { key: 'candidates', label: 'Từ mới chờ duyệt (HSK)', children: <CandidateQueue /> },
      ]} />
    </Card>
  )
}
