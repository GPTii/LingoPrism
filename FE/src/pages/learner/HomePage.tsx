import { useQuery } from '@tanstack/react-query'
import { Button, Statistic } from 'antd'
import { BookOutlined, CameraOutlined, RedoOutlined, RocketOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { vocabApi } from '../../api/vocab'
import { useAuth } from '../../auth/store'

const LANG_NAME: Record<string, string> = { en: 'Tiếng Anh', zh: 'Tiếng Trung', vi: 'Tiếng Việt' }

export default function HomePage() {
  const user = useAuth((s) => s.user)
  const navigate = useNavigate()
  const lang = user?.active_language ?? 'en'
  const summary = useQuery({ queryKey: ['summary', lang, user?.zh_script], queryFn: vocabApi.summary })
  const s = summary.data
  const langLabel = LANG_NAME[lang] + (lang === 'zh' ? (user?.zh_script === 'hant' ? ' · phồn thể (Đài Loan)' : ' · giản thể (đại lục)') : '')

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="rounded-3xl bg-gradient-to-r from-brand-500 to-sky-500 p-8 text-white">
        <h1 className="text-3xl font-bold m-0">Xin chào, {user?.display_name}! 👋</h1>
        <p className="mt-2 opacity-90">Đang học: <b>{langLabel}</b>. Chụp một bức ảnh – học ngay ba thứ tiếng.</p>
        <div className="flex flex-wrap gap-3 mt-6">
          <Button size="large" icon={<RocketOutlined />} onClick={() => navigate('/learn?kind=learn')}>
            Học {user?.goal?.daily_new_target ?? 10} từ mới
          </Button>
          <Button size="large" ghost icon={<RedoOutlined />} disabled={!s?.due} onClick={() => navigate('/learn?kind=review')}>
            Ôn tập ngay {s?.due ? `(${s.due})` : ''}
          </Button>
          <Button size="large" ghost icon={<CameraOutlined />} onClick={() => navigate('/camera')}>Gửi ảnh, học ngay từ mới!</Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { title: 'Tổng số từ', value: s?.total ?? 0 },
          { title: 'Đang học', value: s?.learning ?? 0 },
          { title: 'Đã thuộc', value: s?.mastered ?? 0 },
          { title: 'Cần ôn hôm nay', value: s?.due ?? 0 },
        ].map((it) => (
          <div key={it.title} className="rounded-2xl bg-white border border-slate-200 p-5">
            <Statistic title={it.title} value={it.value} loading={summary.isLoading} />
          </div>
        ))}
      </div>

      <button type="button" onClick={() => navigate('/vocab')} className="rounded-2xl bg-white border border-slate-200 p-6 text-left flex items-center gap-4 hover:shadow-md cursor-pointer">
        <BookOutlined className="text-3xl text-brand-600" />
        <div>
          <div className="font-semibold text-slate-800">Khám phá chủ đề</div>
          <div className="text-slate-500 text-sm">Động vật, thực phẩm, đồ vật, giao thông… mỗi từ đều có đủ Việt · Anh · Trung</div>
        </div>
      </button>
    </div>
  )
}
