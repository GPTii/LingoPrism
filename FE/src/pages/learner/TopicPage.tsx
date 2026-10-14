import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Skeleton } from 'antd'
import { ArrowLeftOutlined, PlayCircleOutlined, SaveOutlined } from '@ant-design/icons'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useState } from 'react'
import { vocabApi, topicTargetName } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import WordCardView from '../../components/WordCardView'
import { langTag } from '../../components/TargetWord'

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
      <Link to="/vocab" className="text-slate-500"><ArrowLeftOutlined /> Chủ đề</Link>
      {topic.data && (
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="text-5xl">{topic.data.icon}</span>
            <div>
              <h1 className="text-2xl font-bold text-slate-800 m-0">{topic.data.name_vi}</h1>
              <div lang={lang === 'zh' ? langTag(script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined} className="text-slate-500">
                {topicTargetName(topic.data, lang, script)}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button icon={<SaveOutlined />} loading={saving} onClick={saveAll}>Lưu cả chủ đề</Button>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => navigate(`/learn?kind=practice&topic=${topicId}`)}>Luyện tập chủ đề</Button>
          </div>
        </div>
      )}
      {words.isLoading ? <Skeleton active /> : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {words.data?.results.map((c) => <WordCardView key={c.id} card={c} topicId={topicId} />)}
        </div>
      )}
    </div>
  )
}
