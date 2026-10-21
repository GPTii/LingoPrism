import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Segmented, Skeleton } from 'antd'
import { FormOutlined, PlayCircleOutlined, SaveOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { useState } from 'react'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'
import { TOPIC_TINTS } from './VocabPage'
import { PageHeader } from '../../components/ui'

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
      {topic.data ? (() => {
        const tint = TOPIC_TINTS[topic.data.id % TOPIC_TINTS.length]
        return (
          <PageHeader back={{ to: '/vocab', label: 'Tất cả chủ đề' }}
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
              <Button type="primary" size="large" icon={<PlayCircleOutlined />} onClick={() => navigate(`/learn?kind=practice&topic=${topicId}`)}>Luyện tập chủ đề</Button>
              <Button size="large" icon={<SaveOutlined />} loading={saving} onClick={saveAll}>Lưu cả chủ đề</Button>
              <Button size="large" icon={<FormOutlined />} onClick={() => navigate(`/sentences?topic=${topicId}`)}>Luyện câu</Button>
            </>} />
        )
      })() : <Skeleton active paragraph={{ rows: 1 }} />}
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
