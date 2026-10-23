import { useQuery } from '@tanstack/react-query'
import { App, Button, Input, Modal, Segmented, Skeleton } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useQueryClient } from '@tanstack/react-query'
import { errorMessage } from '../../api/client'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'
import { EmptyState, PageHeader, ShowMore } from '../../components/ui'
import { Prismo } from '../../components/brand/Brand'

/** every topic its own colour (stable: by id) */
export const TOPIC_TINTS = ['#1899f0', '#7c5cff', '#10c79a', '#ff8a3d', '#ec4899', '#ffb020', '#8b5cf6', '#14b8a6', '#ff6b81', '#0ea5e9']

const TOPIC_ICONS = ['📘', '⭐', '🍜', '✈️', '💼', '🏠', '🐾', '🎵', '⚽', '🛒', '🌿', '💬']

/** "Chủ đề của tôi": the learner's own topics, and making a new one (name + icon). */
function MyTopics() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuth((s) => s.user)
  const topics = useQuery({ queryKey: ['topics', user?.active_language, user?.zh_script, 'mine'], queryFn: () => vocabApi.topics({ mine: 1 }) })
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [icon, setIcon] = useState(TOPIC_ICONS[0])
  const [busy, setBusy] = useState(false)
  const create = async () => {
    if (!name.trim()) return message.warning('Đặt tên cho chủ đề')
    setBusy(true)
    try {
      const t = await vocabApi.createTopic(name.trim(), icon)
      queryClient.invalidateQueries({ queryKey: ['topics'] })
      setOpen(false)
      navigate(`/vocab/topics/${t.id}`)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="m-0 text-lg font-bold text-slate-800">Chủ đề của tôi</h2>
        <Button icon={<PlusOutlined />} onClick={() => { setName(''); setIcon(TOPIC_ICONS[0]); setOpen(true) }}>Tạo chủ đề</Button>
      </div>
      {topics.data?.results.length ? (
        <ShowMore items={topics.data.results} limit={8} label="Xem tất cả chủ đề của tôi">{(shown) => (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {shown.map((t) => (
            <Link key={t.id} to={`/vocab/topics/${t.id}`} className="lift lp-card p-4 flex items-center gap-3">
              <span className="text-4xl">{t.icon || '📘'}</span>
              <span className="min-w-0">
                <span className="block font-bold text-slate-800 truncate">{t.name_vi}</span>
                <span className="num block text-sm text-slate-500">{t.word_count} từ</span>
              </span>
            </Link>
          ))}
        </div>
        )}</ShowMore>
      ) : !topics.isLoading && <p className="m-0 text-slate-500">Gom những từ bạn hay dùng thành chủ đề riêng để ôn bằng flashcard.</p>}
      <Modal open={open} title="Tạo chủ đề của bạn" okText="Tạo chủ đề" cancelText="Huỷ" confirmLoading={busy} onOk={create} onCancel={() => setOpen(false)}>
        <Input size="large" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} placeholder="VD: Từ vựng công việc" aria-label="Tên chủ đề" onPressEnter={create} />
        <div className="mt-4 mb-2 text-sm font-semibold text-slate-600">Biểu tượng</div>
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Biểu tượng">
          {TOPIC_ICONS.map((i) => (
            <button key={i} type="button" role="radio" aria-checked={icon === i} onClick={() => setIcon(i)}
              className={`h-11 w-11 rounded-xl text-2xl cursor-pointer border-2 ${icon === i ? 'border-brand-500 bg-brand-50' : 'border-transparent bg-slate-100'}`}>{i}</button>
          ))}
        </div>
      </Modal>
    </section>
  )
}

export default function VocabPage() {
  const user = useAuth((s) => s.user)
  const lang = user?.active_language ?? 'en'
  const script = user?.zh_script ?? 'hans'
  const [params, setParams] = useSearchParams()
  const tab: 'topics' | 'library' = params.get('tab') === 'library' ? 'library' : 'topics'
  const setTab = (t: typeof tab) => setParams(t === 'library' ? { tab: t } : {}, { replace: true })
  const [search, setSearch] = useState('')

  const topics = useQuery({ queryKey: ['topics', lang, script], queryFn: () => vocabApi.topics() })
  const library = useQuery({ queryKey: ['my-words', lang, script], queryFn: () => vocabApi.myWords(), enabled: tab === 'library' })
  const found = useQuery({ queryKey: ['search', lang, script, search], queryFn: () => vocabApi.searchWords(search), enabled: search.length > 0 })
  const zhTag = lang === 'zh' ? langTag(script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <PageHeader title="Thư viện từ vựng" description="Chọn một chủ đề – mỗi từ đều có đủ Việt · Anh · Trung, ảnh thật và câu ví dụ."
        actions={<Input.Search size="large" placeholder="Tìm từ (Việt, Anh, Trung)…" aria-label="Tìm từ vựng" allowClear onSearch={setSearch} style={{ width: 340, maxWidth: '100%' }} />} />

      {search ? (
        <section>
          <h2 className="text-lg font-bold text-slate-800 mb-3">Kết quả cho “{search}”</h2>
          {found.isLoading ? <Skeleton active /> : found.data?.results.length ? (
            <ShowMore items={found.data.results} limit={24} label="Xem tất cả kết quả">{(shown) => (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {shown.map((c) => <WordCardView key={c.id} card={c} />)}
            </div>
            )}</ShowMore>
          ) : <div className="lp-card"><EmptyState art={<Prismo mood="think" size={80} />} title={`Không có từ nào khớp “${search}”`} description="Thử từ khác, hoặc gõ nghĩa tiếng Việt." /></div>}
        </section>
      ) : (
        <>
          <Segmented size="large" value={tab} onChange={(v) => setTab(v as typeof tab)} options={[{ value: 'topics', label: 'Chủ đề' }, { value: 'library', label: 'Từ của tôi' }]} />
          {tab === 'topics' && (
            topics.isLoading ? <Skeleton active /> : (
              <ShowMore items={topics.data?.results.filter((t) => t.is_system && t.word_count > 0)} limit={12} label="Xem tất cả chủ đề">{(shown) => (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {shown.map((t) => {
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
              )}</ShowMore>
            )
          )}
          {tab === 'library' && <MyTopics />}
          {tab === 'library' && <h2 className="m-0 -mb-2 text-lg font-bold text-slate-800">Tất cả từ đã lưu</h2>}
          {tab === 'library' && (
            library.isLoading ? <Skeleton active /> : library.data?.results.length ? (
              <ShowMore items={library.data.results} limit={24} label="Xem tất cả từ đã lưu">{(shown) => (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {shown.map((c) => <WordCardView key={c.id} card={c} />)}
              </div>
              )}</ShowMore>
            ) : <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={80} />} title="Thư viện của bạn còn trống" description="Mở một chủ đề rồi bấm “Lưu từ”, hoặc chụp ảnh một đồ vật để lưu từ mới." /></div>
          )}
        </>
      )}
    </div>
  )
}
