import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, App, AutoComplete, Button, Input, Popconfirm, Select, Space, Table, Tag, Tooltip } from 'antd'
import { CheckOutlined, CloseOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { api, errorMessage } from '../../api/client'
import type { Paginated } from '../../api/types'
import { vocabApi } from '../../api/vocab'
import SearchBox from '../../components/SearchBox'

interface Candidate {
  id: number
  zh_hans: string
  zh_hant: string
  pinyin: string
  hsk_level: number
  glosses: string[]
  en: string
  vi: string
  vi_options: string[]
  part_of_speech: string
  topics: string
  confidence: 'high' | 'low'
  status: 'pending' | 'approved' | 'rejected'
  checks: Record<string, { errors: string[]; warnings: string[] }>
  word_slug: string | null
}

const candidatesApi = {
  list: (params: Record<string, unknown>) => api.get<Paginated<Candidate>>('/admin/candidates/', { params }).then((r) => r.data),
  update: (id: number, data: Partial<Candidate>) => api.patch<Candidate>(`/admin/candidates/${id}/`, data).then((r) => r.data),
  act: (id: number, kind: 'check' | 'approve' | 'reject') => api.post<Candidate>(`/admin/candidates/${id}/${kind}/`).then((r) => r.data),
}

const POS = [{ value: 'noun', label: 'Danh từ' }, { value: 'verb', label: 'Động từ' }, { value: 'adj', label: 'Tính từ' },
  { value: 'phrase', label: 'Cụm từ' }, { value: 'other', label: 'Khác' }]

/** Teachers review machine-suggested HSK words: fix the meanings, run the source checks, approve or skip. */
export default function CandidateQueue() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState('pending')
  const [level, setLevel] = useState<number | undefined>(1)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [busy, setBusy] = useState<number | null>(null)
  const list = useQuery({
    queryKey: ['admin-candidates', status, level, search, page],
    queryFn: () => candidatesApi.list({ status, hsk_level: level, search: search || undefined, page }),
  })
  const topics = useQuery({ queryKey: ['topics-all'], queryFn: () => vocabApi.topics() })

  const patch = async (c: Candidate, data: Partial<Candidate>) => {
    try {
      await candidatesApi.update(c.id, data)
      queryClient.invalidateQueries({ queryKey: ['admin-candidates'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const act = async (c: Candidate, kind: 'check' | 'approve' | 'reject') => {
    setBusy(c.id)
    try {
      await candidatesApi.act(c.id, kind)
      if (kind === 'approve') message.success(`Đã thêm "${c.vi}" vào kho từ vựng`)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(null)
      queryClient.invalidateQueries({ queryKey: ['admin-candidates'] })
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <Alert type="warning" showIcon
        message="Gợi ý do máy ghép từ CC-CEDICT và Wiktionary tiếng Việt – thường chọn nhầm nghĩa (VD 打 → 'dozen'). Hãy sửa nghĩa Anh/Việt và chủ đề cho đúng; khi bấm Duyệt, hệ thống chạy lại kiểm tra nguồn như dữ liệu gốc." />
      <Space wrap>
        <Select value={status} onChange={(v) => { setStatus(v); setPage(1) }} style={{ width: 140 }}
          options={[{ value: 'pending', label: 'Chờ duyệt' }, { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Bỏ qua' }]} />
        <Select allowClear placeholder="Cấp HSK" value={level} onChange={(v) => { setLevel(v); setPage(1) }} style={{ width: 120 }}
          options={[1, 2, 3, 4, 5, 6].map((n) => ({ value: n, label: `HSK ${n}` }))} />
        <SearchBox allowClear placeholder="Tìm chữ Hán / nghĩa" onSearch={(v) => { setSearch(v); setPage(1) }} style={{ width: 240 }} />
      </Space>
      <Table<Candidate> rowKey="id" size="small" loading={list.isLoading} dataSource={list.data?.results}
        pagination={{ current: page, total: list.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        columns={[
          {
            title: 'Từ (HSK)', key: 'zh', width: 150,
            render: (_, c) => (
              <div>
                <div className="text-lg" lang="zh-Hans">{c.zh_hans}{c.zh_hant !== c.zh_hans && <span lang="zh-Hant" className="text-slate-400"> / {c.zh_hant}</span>}</div>
                <div className="text-xs text-slate-500">{c.pinyin} · HSK {c.hsk_level}</div>
                {c.confidence === 'high' && <Tag color="green" className="mt-1">khớp nghĩa chính</Tag>}
              </div>
            ),
          },
          {
            title: 'Nghĩa trong CC-CEDICT', dataIndex: 'glosses', width: 220,
            render: (g: string[]) => <div className="text-xs text-slate-600">{g.slice(0, 5).join('; ')}</div>,
          },
          {
            title: 'Tiếng Anh', key: 'en', width: 150,
            render: (_, c) => <Input size="small" defaultValue={c.en} disabled={c.status !== 'pending'}
              onBlur={(e) => e.target.value !== c.en && patch(c, { en: e.target.value.trim() })} />,
          },
          {
            title: 'Tiếng Việt', key: 'vi', width: 170,
            render: (_, c) => <AutoComplete size="small" defaultValue={c.vi} style={{ width: '100%' }} disabled={c.status !== 'pending'}
              options={c.vi_options.map((v) => ({ value: v }))}
              onBlur={(e) => { const v = (e.target as HTMLInputElement).value.trim(); if (v !== c.vi) patch(c, { vi: v }) }}
              onSelect={(v: string) => patch(c, { vi: v })} />,
          },
          {
            title: 'Loại · chủ đề', key: 'meta', width: 220,
            render: (_, c) => (
              <div className="flex flex-col gap-1">
                <Select size="small" value={c.part_of_speech} options={POS} disabled={c.status !== 'pending'}
                  onChange={(v) => patch(c, { part_of_speech: v })} />
                <Select size="small" mode="multiple" placeholder="Chủ đề" value={c.topics ? c.topics.split('|') : []}
                  disabled={c.status !== 'pending'} maxTagCount={2}
                  options={topics.data?.results.map((t) => ({ value: t.slug, label: t.name_vi }))}
                  onChange={(v: string[]) => patch(c, { topics: v.join('|') })} />
              </div>
            ),
          },
          {
            title: 'Kiểm tra nguồn', key: 'checks',
            render: (_, c) => {
              const rows = Object.entries(c.checks ?? {})
              if (c.status === 'approved') return <Tag color="green">Đã thêm: {c.word_slug}</Tag>
              if (!rows.length) return <span className="text-xs text-slate-400">Chưa kiểm tra</span>
              const errors = rows.flatMap(([, r]) => r.errors)
              const warnings = rows.flatMap(([, r]) => r.warnings)
              return errors.length
                ? <div className="text-xs text-red-600">{errors.map((m) => <div key={m}>✗ {m}</div>)}</div>
                : <Tooltip title={warnings.join(' · ') || 'Không có cảnh báo'}><Tag color="green">Đạt cả 4 dạng chữ</Tag></Tooltip>
            },
          },
          {
            title: '', key: 'actions', width: 150,
            render: (_, c) => c.status === 'pending' && (
              <Space>
                <Tooltip title="Kiểm tra nguồn"><Button size="small" icon={<SafetyCertificateOutlined />} loading={busy === c.id} onClick={() => act(c, 'check')} /></Tooltip>
                <Tooltip title="Duyệt – thêm vào kho từ"><Button size="small" type="primary" icon={<CheckOutlined />} loading={busy === c.id} onClick={() => act(c, 'approve')} /></Tooltip>
                <Popconfirm title="Bỏ qua từ này?" onConfirm={() => act(c, 'reject')}>
                  <Button size="small" danger icon={<CloseOutlined />} />
                </Popconfirm>
              </Space>
            ),
          },
        ]} />
    </div>
  )
}
