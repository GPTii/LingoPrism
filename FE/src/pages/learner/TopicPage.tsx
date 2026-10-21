import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Segmented, Skeleton } from 'antd'
import { ArrowLeftOutlined, FormOutlined, PlayCircleOutlined, SaveOutlined } from '@ant-design/icons'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useState } from 'react'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'
import { TOPIC_TINTS } from './VocabPage'

export default function TopicPage() {
  const { id } = useParams()
  const topicId = Number(id)
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuth((s) => s.user)
  const lang = user?.active_language ?? 'en'
  const script = user?.zh_script ?? 'hans'
  const [saving, setSaving] = useState(false)
  const [level, setLevel] = useState<number | 'all'>('all')

  const topic = useQuery({ queryKey: ['topic', topicId, lang, script], queryFn: () => vocabApi.topic(topicId) })
  const words = useQuery({ queryKey: ['topic-words', topicId, lang, script], queryFn: () => vocabApi.topicWords(topicId) })

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
      <Link to="/vocab" className="text-slate-500 font-bold"><ArrowLeftOutlined /> Chủ đề</Link>
      {topic.data && (() => {
        const tint = TOPIC_TINTS[topic.data.id % TOPIC_TINTS.length]
        return (
          <div className="relative overflow-hidden lp-card p-5 sm:p-6 flex flex-wrap items-center justify-between gap-4"
            style={{ background: `linear-gradient(135deg, ${tint}22, var(--surface) 60%)` }}>
            <div className="flex items-center gap-4">
              <span className="h-20 w-20 rounded-3xl grid place-items-center text-5xl shrink-0" style={{ background: `${tint}26` }}>{topic.data.icon}</span>
              <div>
                <h1 className="text-3xl font-black text-slate-800 m-0">{topic.data.name_vi}</h1>
                <div lang={lang === 'zh' ? langTag(script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined} className="text-slate-500 font-bold text-lg">
                  {topicTargetName(topic.data, lang, script)}
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="primary" size="large" icon={<PlayCircleOutlined />} onClick={() => navigate(`/learn?kind=practice&topic=${topicId}`)}>Luyện tập chủ đề</Button>
              <Button size="large" icon={<SaveOutlined />} loading={saving} onClick={saveAll}>Lưu cả chủ đề</Button>
              <Button size="large" icon={<FormOutlined />} onClick={() => navigate(`/sentences?topic=${topicId}`)}>Luyện câu</Button>
            </div>
          </div>
        )
      })()}
      {words.isLoading ? <Skeleton active /> : (
        <>
          <Segmented<number | 'all'> value={level} onChange={(v) => setLevel(v as number | 'all')}
            options={[{ label: `Tất cả (${words.data?.results.length ?? 0})`, value: 'all' },
              ...[1, 2, 3, 4].map((n) => ({ label: `Cấp ${n} (${words.data?.results.filter((c) => c.level === n).length ?? 0})`, value: n }))]} />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {words.data?.results.filter((c) => level === 'all' || c.level === level)
              .map((c) => <WordCardView key={c.id} card={c} topicId={topicId} />)}
          </div>
        </>
      )}
    </div>
  )
}
