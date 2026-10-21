import { useQuery } from '@tanstack/react-query'
import { Input, Segmented, Skeleton, Empty } from 'antd'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'

/** every topic its own colour (stable: by id) */
export const TOPIC_TINTS = ['#6d4aff', '#3fa9f5', '#10c79a', '#ff8a3d', '#ec4899', '#ffb020', '#8b5cf6', '#14b8a6', '#ff6b81', '#0ea5e9']

export default function VocabPage() {
  const user = useAuth((s) => s.user)
  const lang = user?.active_language ?? 'en'
  const script = user?.zh_script ?? 'hans'
  const [tab, setTab] = useState<'topics' | 'library'>('topics')
  const [search, setSearch] = useState('')

  const topics = useQuery({ queryKey: ['topics', lang, script], queryFn: () => vocabApi.topics() })
  const library = useQuery({ queryKey: ['my-words', lang, script], queryFn: () => vocabApi.myWords(), enabled: tab === 'library' })
  const found = useQuery({ queryKey: ['search', lang, script, search], queryFn: () => vocabApi.searchWords(search), enabled: search.length > 0 })
  const zhTag = lang === 'zh' ? langTag(script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-800 m-0">Thư viện từ vựng</h1>
          <div className="text-slate-500 mt-1">Chọn một chủ đề – mỗi từ đều có đủ Việt · Anh · Trung, ảnh thật và câu ví dụ.</div>
        </div>
        <Input.Search size="large" placeholder="Tìm nhanh từ vựng (Việt, Anh, Trung)…" allowClear onSearch={setSearch} style={{ maxWidth: 380 }} />
      </div>

      {search ? (
        <section>
          <h2 className="text-lg font-semibold mb-3">Kết quả cho “{search}”</h2>
          {found.isLoading ? <Skeleton active /> : found.data?.results.length ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {found.data.results.map((c) => <WordCardView key={c.id} card={c} />)}
            </div>
          ) : <Empty description="Không tìm thấy từ nào" />}
        </section>
      ) : (
        <>
          <Segmented size="large" value={tab} onChange={(v) => setTab(v as typeof tab)} options={[{ value: 'topics', label: 'Chủ đề' }, { value: 'library', label: 'Từ của tôi' }]} />
          {tab === 'topics' && (
            topics.isLoading ? <Skeleton active /> : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {topics.data?.results.filter((t) => t.word_count > 0).map((t) => {
                  const tint = TOPIC_TINTS[t.id % TOPIC_TINTS.length]
                  const pct = Math.round((t.learned_count / Math.max(t.word_count, 1)) * 100)
                  return (
                    <Link key={t.id} to={`/vocab/topics/${t.id}`} className="lift lp-card overflow-hidden flex flex-col">
                      <div className="relative h-24 grid place-items-center" style={{ background: `${tint}17` }}>
                        <span className="text-5xl">{t.icon || '📘'}</span>
                        {pct >= 100 && <span className="absolute top-2 right-2 rounded-md bg-[#fff] px-2 py-0.5 text-xs font-bold text-[#0e9f7b]">Đã học xong</span>}
                      </div>
                      <div className="p-4 flex flex-col gap-1 flex-1">
                        <span className="font-bold text-slate-800 leading-tight">{t.name_vi}</span>
                        <span lang={zhTag} className="text-sm font-semibold text-slate-500 truncate">{topicTargetName(t, lang, script)}</span>
                        <div className="mt-auto pt-2 flex items-center gap-2">
                          <div className="h-2 flex-1 rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: tint }} />
                          </div>
                          <span className="num text-xs font-semibold text-slate-500">{t.learned_count}/{t.word_count}</span>
                        </div>
                      </div>
                    </Link>
                  )
                })}
              </div>
            )
          )}
          {tab === 'library' && (
            library.isLoading ? <Skeleton active /> : library.data?.results.length ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {library.data.results.map((c) => <WordCardView key={c.id} card={c} />)}
              </div>
            ) : <Empty description="Bạn chưa lưu từ nào. Hãy mở một chủ đề hoặc chụp ảnh để lưu từ mới!" />
          )}
        </>
      )}
    </div>
  )
}
