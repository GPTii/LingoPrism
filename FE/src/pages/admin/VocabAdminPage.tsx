import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Card, Segmented, Select, Statistic, Table, Tag, Tooltip } from 'antd'
import { useState } from 'react'
import { adminVocabApi, LANG_LABEL, STATUS_TAG, type AdminTranslation, type AdminWord } from '../../api/adminVocab'
import { langTag } from '../../components/TargetWord'
import { BulkDeleteBar, DateRangeFilter, dateParams, pagination, useBulkDelete, useSelection, type DateRange } from '../../components/DataTools'
import SearchBox from '../../components/SearchBox'

function TranslationCell({ tr }: { tr?: AdminTranslation }) {
  if (!tr) return <span className="text-slate-300">—</span>
  const tag = STATUS_TAG[tr.status]
  const reading = tr.ipa ? `/${tr.ipa}/` : tr.pinyin
  return (
    <Tooltip title={tr.issues.length ? tr.issues.map((i) => i.message).join(' • ') : undefined}>
      <div className="flex flex-col">
        <span lang={langTag(tr.language)} className="font-medium">
          {tr.text} {tr.regional_difference && <Tag color="purple" className="ml-1">từ vùng</Tag>}
        </span>
        {reading && <span className="text-xs text-slate-500">{reading}{tr.zhuyin ? ` · ${tr.zhuyin}` : ''}</span>}
        <span><Tag color={tag.color} className="mt-1">{tag.label}</Tag></span>
      </div>
    </Tooltip>
  )
}

export default function VocabAdminPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [flagged, setFlagged] = useState<'all' | 'flagged'>('all')
  const [audience, setAudience] = useState<string | undefined>()
  const [hasImage, setHasImage] = useState<string | undefined>()
  const [created, setCreated] = useState<DateRange>(null)
  const filters = {
    search: search || undefined, flagged: flagged === 'flagged' ? 1 : undefined, audience, has_image: hasImage, ...dateParams(created),
  }
  const stats = useQuery({ queryKey: ['admin-vocab-stats'], queryFn: adminVocabApi.stats })
  const words = useQuery({
    queryKey: ['admin-words', page, pageSize, filters],
    queryFn: () => adminVocabApi.words({ page, page_size: pageSize, ...filters }),
  })
  const selection = useSelection<AdminWord>([filters])
  const bulk = useBulkDelete('/admin/words/bulk-delete/', () => {
    selection.clear()
    queryClient.invalidateQueries({ queryKey: ['admin-words'] })
    queryClient.invalidateQueries({ queryKey: ['admin-vocab-stats'] })
  })
  const filter = <V,>(set: (v: V) => void) => (v: V) => { set(v); setPage(1) }
  const by = (w: AdminWord, code: string) => w.translations.find((t) => t.language === code)

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <Card><Statistic title="Khái niệm từ" value={stats.data?.words} /></Card>
        <Card><Statistic title="Chủ đề hệ thống" value={stats.data?.topics} /></Card>
        {['vi', 'en', 'zh-Hans', 'zh-Hant'].map((code) => (
          <Card key={code}>
            <Statistic
              title={`${LANG_LABEL[code]} đã kiểm tra`}
              value={stats.data?.translations[code]?.verified ?? 0}
              suffix={stats.data?.translations[code]?.flagged ? <span className="text-orange-500 text-sm"> · {stats.data.translations[code].flagged} cần xem</span> : null}
            />
          </Card>
        ))}
      </div>
      <Card
        title="Từ vựng"
        extra={<Segmented value={flagged} onChange={(v) => { setFlagged(v as typeof flagged); setPage(1) }} options={[{ value: 'all', label: 'Tất cả' }, { value: 'flagged', label: 'Có lỗi' }]} />}
      >
        <div className="flex flex-wrap gap-2 mb-3">
          <SearchBox placeholder="Tìm slug, nhãn YOLO, chữ…" allowClear onSearch={filter(setSearch)} style={{ width: 240 }} />
          <Select allowClear placeholder="Đối tượng" value={audience} onChange={filter(setAudience)} style={{ width: 130 }}
            options={[{ value: 'all', label: 'Tất cả' }, { value: 'kid', label: 'Trẻ em' }, { value: 'adult', label: 'Người lớn' }]} />
          <Select allowClear placeholder="Ảnh minh hoạ" value={hasImage} onChange={filter(setHasImage)} style={{ width: 150 }}
            options={[{ value: '1', label: 'Có ảnh' }, { value: '0', label: 'Chưa có ảnh' }]} />
          <DateRangeFilter value={created} onChange={filter(setCreated)} placeholder={['Thêm từ ngày', 'đến ngày']} />
        </div>
        <BulkDeleteBar count={selection.keys.length} noun="từ" busy={bulk.busy} onClear={selection.clear}
          warning="Bản dịch, câu ví dụ của các từ này bị xoá theo. Từ đã có học viên lưu vào thư viện được giữ lại."
          onDelete={() => bulk.run(selection.keys, (n) => `${n} từ`)} />
        <Table<AdminWord>
          rowKey="id"
          loading={words.isLoading}
          dataSource={words.data?.results}
          rowSelection={selection.rowSelection}
          pagination={pagination(page, words.data?.count, pageSize, (p, size) => { setPage(size === pageSize ? p : 1); setPageSize(size) })}
          scroll={{ x: 1000 }}
          columns={[
            { title: 'Khái niệm', dataIndex: 'slug', render: (v, w) => <div><div className="font-mono">{v}</div>{w.yolo_label && <Tag color="cyan">YOLO: {w.yolo_label}</Tag>}</div> },
            { title: 'Tiếng Việt', render: (_, w) => <TranslationCell tr={by(w, 'vi')} /> },
            { title: 'Tiếng Anh', render: (_, w) => <TranslationCell tr={by(w, 'en')} /> },
            { title: 'Giản thể (đại lục)', render: (_, w) => <TranslationCell tr={by(w, 'zh-Hans')} /> },
            { title: 'Phồn thể (Đài Loan)', render: (_, w) => <TranslationCell tr={by(w, 'zh-Hant')} /> },
            { title: 'Đối tượng', dataIndex: 'audience', render: (v) => ({ all: 'Tất cả', kid: 'Trẻ em', adult: 'Người lớn' } as Record<string, string>)[v] },
          ]}
        />
      </Card>
    </div>
  )
}
