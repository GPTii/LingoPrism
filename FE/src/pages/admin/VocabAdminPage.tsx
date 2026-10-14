import { useQuery } from '@tanstack/react-query'
import { Card, Input, Segmented, Statistic, Table, Tag, Tooltip } from 'antd'
import { useState } from 'react'
import { adminVocabApi, LANG_LABEL, STATUS_TAG, type AdminTranslation, type AdminWord } from '../../api/adminVocab'
import { langTag } from '../../components/TargetWord'

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
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [flagged, setFlagged] = useState<'all' | 'flagged'>('all')
  const stats = useQuery({ queryKey: ['admin-vocab-stats'], queryFn: adminVocabApi.stats })
  const words = useQuery({
    queryKey: ['admin-words', page, search, flagged],
    queryFn: () => adminVocabApi.words({ page, search: search || undefined, flagged: flagged === 'flagged' ? 1 : undefined }),
  })
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
        extra={
          <div className="flex gap-2">
            <Segmented value={flagged} onChange={(v) => { setFlagged(v as typeof flagged); setPage(1) }} options={[{ value: 'all', label: 'Tất cả' }, { value: 'flagged', label: 'Có lỗi' }]} />
            <Input.Search placeholder="Tìm slug, nhãn YOLO, chữ…" allowClear onSearch={(v) => { setSearch(v); setPage(1) }} style={{ width: 260 }} />
          </div>
        }
      >
        <Table<AdminWord>
          rowKey="id"
          loading={words.isLoading}
          dataSource={words.data?.results}
          pagination={{ current: page, total: words.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
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
