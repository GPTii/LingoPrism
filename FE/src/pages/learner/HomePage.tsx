import { useQuery } from '@tanstack/react-query'
import { Progress, Skeleton } from 'antd'
import { ArrowRightOutlined, CheckCircleFilled } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { vocabApi } from '../../api/vocab'
import { gameApi } from '../../api/app'
import { useAuth } from '../../auth/store'
import LevelPath from '../../components/LevelPath'
import TodayWord from '../../components/TodayWord'
import { QuestGo } from '../../components/QuestGo'
import { LangGlyph, Prismo, ScaleIcon, StreakIcon, XpIcon, type Mood } from '../../components/brand/Brand'
import { AppIcon } from '../../components/brand/AppIcon'

const LANG_NAME: Record<string, string> = { en: 'tiếng Anh', zh: 'tiếng Trung', vi: 'tiếng Việt' }

function greeting() {
  const h = new Date().getHours()
  return h < 11 ? 'Chào buổi sáng' : h < 14 ? 'Chào buổi trưa' : h < 18 ? 'Chào buổi chiều' : 'Chào buổi tối'
}

/**
 * The signature of the page: Prismo splits light into three beams that run across the whole width.
 * How far the light reaches is how much of today's goal is done.
 */
function Spectrum({ learned, target, mood }: { learned: number; target: number; mood: Mood }) {
  const pct = Math.min(100, Math.round((learned / Math.max(target, 1)) * 100))
  const bands = ['#ffb020', '#10c79a', '#ff6b81']
  return (
    <div className="flex items-center gap-1 sm:gap-2">
      <Link to="/prismo" title="Tủ đồ Prismo" className="shrink-0 -mr-3 relative z-[1] -mt-6">
        <Prismo mood={mood} size={104} />
      </Link>
      <div className="flex-1 min-w-0" role="progressbar" aria-valuemin={0} aria-valuemax={target} aria-valuenow={learned} aria-label="Mục tiêu từ mới hôm nay">
        <div className="flex flex-col gap-[3px]">
          {bands.map((c, i) => (
            <div key={c} className="h-[7px] sm:h-[9px] rounded-r-full overflow-hidden" style={{ background: `${c}24` }}>
              <div className="h-full rounded-r-full transition-[width] duration-1000 ease-[cubic-bezier(0.22,1,0.36,1)]"
                style={{ width: `${Math.max(pct, 2)}%`, background: c, transitionDelay: `${i * 80}ms` }} />
            </div>
          ))}
        </div>
        <div className="mt-3 pl-4 flex items-baseline justify-between gap-4 text-slate-500">
          <span><b className="num text-slate-900 text-lg">{learned}/{target}</b> từ mới hôm nay</span>
          {pct >= 100 && <span className="font-semibold text-[#10c79a]">Đã đạt mục tiêu</span>}
        </div>
      </div>
    </div>
  )
}

export default function HomePage() {
  const user = useAuth((s) => s.user)
  const navigate = useNavigate()
  const lang = user?.active_language ?? 'en'
  const script = user?.zh_script ?? 'hans'
  const summary = useQuery({ queryKey: ['summary', lang, user?.zh_script], queryFn: vocabApi.summary })
  const game = useQuery({ queryKey: ['game-summary'], queryFn: gameApi.summary })
  const quests = useQuery({ queryKey: ['quests'], queryFn: gameApi.quests })
  const s = summary.data
  const g = game.data
  const loading = summary.isLoading || game.isLoading

  const target = g?.today.new_target || user?.goal?.daily_new_target || 10
  const learned = g?.today.new_learned ?? 0
  const goalPct = Math.min(100, Math.round((learned / target) * 100))
  const due = s?.due ?? 0
  // Prismo feels the day: sad right after a lost streak, sleepy while a kept streak waits for today's lesson
  const lost = !g?.studied_today && (g?.repairable_streak ?? 0) > 0
  const waiting = !g?.studied_today && (g?.streak ?? 0) > 0
  const pet = user?.mascot?.name || 'Prismo'
  const mood: Mood = goalPct >= 100 ? 'celebrate' : lost ? 'sad' : g?.studied_today ? 'happy' : waiting ? 'sleepy' : due > 0 ? 'think' : 'wow'
  const line = goalPct >= 100 ? 'Bạn đã đạt mục tiêu hôm nay. Ôn thêm vài từ để nhớ lâu hơn.'
    : lost ? `${pet} buồn vì mất chuỗi ${g?.repairable_streak} ngày. Hồi chuỗi trong Cửa hàng để nối lại.`
      : g?.studied_today ? `Còn ${target - learned} từ nữa là đạt mục tiêu hôm nay.`
        : waiting ? `${pet} đang ngủ gật. Học một bài để giữ chuỗi ${g?.streak} ngày.`
          : due > 0 ? `${due} từ đến lịch ôn. Ôn trước, học từ mới sau.`
            : 'Năm phút là đủ cho một lượt học hôm nay.'

  const facts = [
    { icon: <StreakIcon size={30} active={!!g?.studied_today} />, value: g?.streak ?? 0, label: 'ngày liên tiếp' },
    { icon: <XpIcon size={30} />, value: g?.today_xp ?? 0, label: 'XP hôm nay' },
    { icon: <AppIcon name="book" size={30} />, value: s?.learning ?? 0, label: 'từ đang học' },
    { icon: <AppIcon name="check" size={30} />, value: s?.mastered ?? 0, label: 'từ đã thuộc' },
  ]

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-14 md:gap-20 pb-6">
      {/* today */}
      <section className="flex flex-col gap-8 pt-4 md:pt-10 animate-rise">
        <div>
          <div className="flex items-center gap-2 text-slate-500">
            <LangGlyph lang={lang} script={script} size={20} />
            Đang học {LANG_NAME[lang]}{lang === 'zh' ? (script === 'hant' ? ' phồn thể' : ' giản thể') : ''}
          </div>
          <h1 className="text-[2.5rem] sm:text-6xl xl:text-7xl font-extrabold text-slate-900 leading-[1.02] tracking-[-0.035em] mt-4 mb-0">
            {greeting()},<br />{user?.display_name}
          </h1>
          <p className="text-lg sm:text-xl text-slate-500 mt-5 mb-0 max-w-[48ch]">{line}</p>
        </div>

        <Spectrum learned={learned} target={target} mood={mood} />

        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <button type="button" onClick={() => navigate('/learn?kind=learn')}
            className="cursor-pointer rounded-2xl bg-brand-600 text-white font-bold px-7 h-14 text-lg hover:bg-brand-700 btn-lip">
            Học {target} từ mới
          </button>
          {due > 0 ? (
            <Link to="/learn?kind=review" className="group text-lg font-semibold !text-slate-800 inline-flex items-center gap-2">
              Ôn {due} từ đến hạn <ArrowRightOutlined className="transition-transform group-hover:translate-x-1" />
            </Link>
          ) : <span className="text-slate-500">Chưa có từ nào cần ôn</span>}
        </div>

        <dl className="m-0 flex flex-wrap gap-x-10 gap-y-4">
          {facts.map((f) => (
            <div key={f.label} className="flex items-center gap-2.5">
              <span className="text-xl leading-none">{f.icon}</span>
              <dt className="order-last text-slate-500">{f.label}</dt>
              <dd className="m-0 num text-2xl font-bold text-slate-900">{loading ? '–' : f.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <TodayWord />

      <div className="grid lg:grid-cols-5 gap-5 md:gap-6">
        {/* camera: the heart of LingoPrism */}
        <button type="button" onClick={() => navigate('/camera')}
          className="lift lp-card lg:col-span-3 p-6 sm:p-8 text-left cursor-pointer flex flex-col justify-between gap-8 group min-h-56">
          <AppIcon name="camera" size={64} className="transition-transform duration-200 group-hover:-rotate-6 group-hover:scale-105" />
          <span>
            <span className="block text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-[-0.02em]">Chụp một đồ vật</span>
            <span className="flex items-end justify-between gap-4 mt-2">
              <span className="text-slate-500 max-w-[44ch]">Máy nhận ra vật trong ảnh và cho bạn ngay tên của nó bằng tiếng Việt, tiếng Anh và tiếng Trung.</span>
              <ArrowRightOutlined className="text-xl text-slate-400 transition-transform duration-150 group-hover:translate-x-1" />
            </span>
          </span>
        </button>

        <section className="lp-card lg:col-span-2 p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-slate-900 m-0">Nhiệm vụ hôm nay</h2>
            <Link to="/achievements" className="text-sm font-semibold">Xem tất cả</Link>
          </div>
          {quests.isLoading ? <Skeleton active paragraph={{ rows: 3 }} title={false} /> : (
            <ul className="flex flex-col gap-4 m-0 p-0 list-none">
              {(quests.data?.quests ?? []).slice(0, 3).map((q) => (
                <li key={q.id} className="flex items-center gap-3">
                  {q.completed
                    ? <CheckCircleFilled className="text-xl shrink-0" style={{ color: '#10c79a' }} />
                    : <XpIcon size={20} className="shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-semibold truncate ${q.completed ? 'text-slate-400 line-through decoration-slate-300' : 'text-slate-700'}`}>{q.title}</div>
                    <Progress percent={Math.round((Math.min(q.progress, q.target) / Math.max(q.target, 1)) * 100)} size="small" showInfo={false}
                      strokeColor={q.completed ? '#10c79a' : undefined} />
                  </div>
                  <span className="num inline-flex items-center gap-1 text-sm font-bold text-slate-600 shrink-0">
                    <ScaleIcon size={16} />{q.reward_scales}
                  </span>
                  {!q.completed && <QuestGo kind={q.kind} title={q.title} />}
                </li>
              ))}
              {!quests.data?.quests.length && <li className="text-slate-500 text-sm">Hôm nay chưa có nhiệm vụ. Học một bài để mở nhiệm vụ mới.</li>}
            </ul>
          )}
        </section>
      </div>

      <LevelPath />

      <div className={`grid gap-5 md:gap-6 ${user?.active_language === 'vi' ? 'md:grid-cols-2' : ''}`}>
        {user?.active_language === 'vi' && (
          <Link to="/doc-viet" className="lift lp-card p-5 flex items-center gap-4 group">
            <AppIcon name="pencil" size={44} />
            <div className="flex-1 min-w-0">
              <div className="font-bold text-slate-800 text-lg">Học đọc – viết tiếng Việt</div>
              <div className="text-slate-500 text-sm">Âm, dấu thanh, vần, đánh vần, nghe rồi viết lại</div>
            </div>
            <ArrowRightOutlined className="text-slate-400 transition-transform duration-150 group-hover:translate-x-0.5" />
          </Link>
        )}
        <Link to="/vocab" className="lift lp-card p-5 flex items-center gap-4 group">
          <AppIcon name="shapes" size={44} />
          <div className="flex-1 min-w-0">
            <div className="font-bold text-slate-800 text-lg">Học theo chủ đề</div>
            <div className="text-slate-500 text-sm">Động vật, thực phẩm, đồ vật, giao thông… mỗi từ có đủ Việt · Anh · Trung</div>
          </div>
          <ArrowRightOutlined className="text-slate-400 transition-transform duration-150 group-hover:translate-x-0.5" />
        </Link>
      </div>
    </div>
  )
}
