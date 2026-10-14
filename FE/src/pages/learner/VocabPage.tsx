import { useQuery } from '@tanstack/react-query'
import { Input, Progress, Segmented, Skeleton, Empty } from 'antd'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'

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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-800 m-0">Thư viện từ vựng</h1>
        <Input.Search placeholder="Tìm nhanh từ vựng (Việt, Anh, Trung)…" allowClear onSearch={setSearch} style={{ maxWidth: 360 }} />
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
          <Segmented value={tab} onChange={(v) => setTab(v as typeof tab)} options={[{ value: 'topics', label: 'Chủ đề' }, { value: 'library', label: 'Từ của tôi' }]} />
          {tab === 'topics' && (
            topics.isLoading ? <Skeleton active /> : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {topics.data?.results.filter((t) => t.word_count > 0).map((t) => (
                  <Link key={t.id} to={`/vocab/topics/${t.id}`} className="rounded-2xl bg-white border border-slate-200 p-5 hover:shadow-md hover:border-brand-500 transition flex flex-col gap-2">
                    <span className="text-4xl">{t.icon || '📘'}</span>
                    <span className="font-semibold text-slate-800">{t.name_vi}</span>
                    <span lang={zhTag} className="text-sm text-slate-500">{topicTargetName(t, lang, script)}</span>
                    <Progress percent={Math.round((t.learned_count / Math.max(t.word_count, 1)) * 100)} size="small" format={() => `${t.learned_count}/${t.word_count}`} />
                  </Link>
                ))}
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
