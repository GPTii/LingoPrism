import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Input, Modal, Segmented, Skeleton } from 'antd'
import { DeleteOutlined, FormOutlined, PlayCircleOutlined, PlusOutlined, SaveOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { useState } from 'react'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'
import { TOPIC_TINTS } from './VocabPage'
import { EmptyState, PageHeader } from '../../components/ui'
import Flashcards from '../../components/Flashcards'
import { Prismo } from '../../components/brand/Brand'
import { AppIcon } from '../../components/brand/AppIcon'

export default function TopicPage() {
  const { id } = useParams()
  const topicId = Number(id)
  const { message, modal } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuth((s) => s.user)
  const lang = user?.active_language ?? 'en'
  const script = user?.zh_script ?? 'hans'
  const [saving, setSaving] = useState(false)
  const [level, setLevel] = useState<number | 'all'>('all')
  const [cardsOpen, setCardsOpen] = useState(false)
  const [adding, setAdding] = useState(false)
  const [term, setTerm] = useState('')

  const topic = useQuery({ queryKey: ['topic', topicId, lang, script], queryFn: () => vocabApi.topic(topicId) })
  const words = useQuery({ queryKey: ['topic-words', topicId, lang, script], queryFn: () => vocabApi.topicWords(topicId) })
  const mine = topic.data ? !topic.data.is_system : false
  const found = useQuery({ queryKey: ['search', lang, script, term], queryFn: () => vocabApi.searchWords(term), enabled: adding && term.length > 0 })
  const inTopic = new Set(words.data?.results.map((c) => c.id))

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['topic-words', topicId] })
    queryClient.invalidateQueries({ queryKey: ['topics'] })
    queryClient.invalidateQueries({ queryKey: ['my-words'] })
  }
  const add = async (wordId: number) => {
    try {
      await vocabApi.addToTopic(topicId, wordId)
      message.success('Đã thêm vào chủ đề')
      refresh()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const remove = async (wordId: number) => {
    try {
      await vocabApi.removeFromTopic(topicId, wordId)
      refresh()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const deleteTopic = () => modal.confirm({
    title: 'Xoá chủ đề này?', content: 'Các từ vẫn còn trong thư viện của bạn.', okText: 'Xoá chủ đề', okButtonProps: { danger: true }, cancelText: 'Huỷ',
    onOk: async () => {
      try {
        await vocabApi.deleteTopic(topicId)
        queryClient.invalidateQueries({ queryKey: ['topics'] })
        navigate('/vocab?tab=library')
      } catch (e) {
        message.error(errorMessage(e))
      }
    },
  })

  const saveAll = async () => {
    setSaving(true)
    try {
      const r = await vocabApi.saveTopic(topicId)
      message.success(`Đã lưu ${r.added} từ mới vào thư viện`)
      queryClient.invalidateQueries({ queryKey: ['topic-words'] })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      {topic.data ? (() => {
        const tint = TOPIC_TINTS[topic.data.id % TOPIC_TINTS.length]
        return (
          <PageHeader back={mine ? { to: '/vocab?tab=library', label: 'Từ của tôi' } : { to: '/vocab', label: 'Tất cả chủ đề' }}
            title={
              <span className="flex items-center gap-4">
                <span className="h-16 w-16 rounded-2xl grid place-items-center text-4xl shrink-0" style={{ background: `${tint}1f` }}>{topic.data.icon}</span>
                <span className="min-w-0">
                  {topic.data.name_vi}
                  <span lang={lang === 'zh' ? langTag(script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined} className="block text-lg font-semibold text-slate-500 mt-0.5">
                    {topicTargetName(topic.data, lang, script)}
                  </span>
                </span>
              </span>
            }
            actions={<>
              <Button type="primary" size="large" icon={<PlayCircleOutlined />} disabled={!words.data?.results.length}
                onClick={() => navigate(`/learn?kind=practice&topic=${topicId}`)}>Luyện tập chủ đề</Button>
              <Button size="large" icon={<AppIcon name="vocab" size={20} />} disabled={!words.data?.results.length} onClick={() => setCardsOpen(true)}>Flashcard</Button>
              {mine ? <>
                <Button size="large" icon={<PlusOutlined />} onClick={() => { setTerm(''); setAdding(true) }}>Thêm từ</Button>
                <Button size="large" type="text" danger icon={<DeleteOutlined />} onClick={deleteTopic}>Xoá chủ đề</Button>
              </> : <>
                <Button size="large" icon={<SaveOutlined />} loading={saving} onClick={saveAll}>Lưu cả chủ đề</Button>
                <Button size="large" icon={<FormOutlined />} onClick={() => navigate(`/sentences?topic=${topicId}`)}>Luyện câu</Button>
              </>}
            </>} />
        )
      })() : <Skeleton active paragraph={{ rows: 1 }} />}
      {words.isLoading ? <Skeleton active /> : (
        <>
          <Segmented<number | 'all'> value={level} onChange={(v) => setLevel(v as number | 'all')}
            options={[{ label: `Tất cả (${words.data?.results.length ?? 0})`, value: 'all' },
              ...[1, 2, 3, 4].map((n) => ({ label: `Cấp ${n} (${words.data?.results.filter((c) => c.level === n).length ?? 0})`, value: n }))]} />
          {mine && !words.data?.results.length && (
            <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={80} />} title="Chủ đề còn trống" description="Bấm “Thêm từ” để tìm và đưa từ vào chủ đề của bạn." /></div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {words.data?.results.filter((c) => level === 'all' || c.level === level)
              .map((c) => (
                <div key={c.id} className="relative">
                  <WordCardView card={c} topicId={topicId} />
                  {mine && (
                    <Button size="small" shape="circle" danger icon={<DeleteOutlined />} aria-label={`Bỏ ${c.target?.text ?? ''} khỏi chủ đề`}
                      className="!absolute top-2 right-2" onClick={() => remove(c.id)} />
                  )}
                </div>
              ))}
          </div>
        </>
      )}
      <Flashcards open={cardsOpen} onClose={() => setCardsOpen(false)} cards={words.data?.results ?? []} title={topic.data?.name_vi ?? ''} />
      <Modal open={adding} onCancel={() => setAdding(false)} footer={null} title={`Thêm từ vào “${topic.data?.name_vi ?? ''}”`} width={560}>
        <Input.Search size="large" placeholder="Tìm từ (Việt, Anh, Trung)…" enterButton="Tìm" allowClear onSearch={(v) => setTerm(v.trim())} autoFocus
          aria-label="Tìm từ để thêm" />
        <ul className="m-0 mt-3 p-0 list-none max-h-[50vh] overflow-y-auto divide-y divide-slate-100">
          {found.isLoading && <li className="p-3"><Skeleton active paragraph={{ rows: 2 }} title={false} /></li>}
          {term && found.data?.results.length === 0 && <li className="p-3 text-slate-500">Không có từ nào khớp “{term}”.</li>}
          {found.data?.results.filter((c) => c.target).map((c) => (
            <li key={c.id} className="flex items-center gap-3 py-2.5">
              <span className="text-2xl w-9 text-center">{c.emoji}</span>
              <span className="flex-1 min-w-0">
                <span lang={langTag(c.target!.language)} className="block font-semibold text-slate-800">{c.target!.text}</span>
                <span className="block text-sm text-slate-500 truncate">{c.meaning_vi}</span>
              </span>
              {inTopic.has(c.id) ? <span className="text-sm font-semibold text-emerald-700">Đã có</span>
                : <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => add(c.id)}>Thêm</Button>}
            </li>
          ))}
        </ul>
      </Modal>
    </div>
  )
}
