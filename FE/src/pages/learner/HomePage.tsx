import { useQuery } from '@tanstack/react-query'
import { Progress, Skeleton } from 'antd'
import { ArrowRightOutlined, BookOutlined, CameraFilled, CheckCircleFilled, EditOutlined, RedoOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { vocabApi } from '../../api/vocab'
import { gameApi } from '../../api/app'
import { useAuth } from '../../auth/store'
import LevelPath from '../../components/LevelPath'
import { LangGlyph, Prismo, ScaleIcon, StreakIcon, XpIcon, type Mood } from '../../components/brand/Brand'

const LANG_NAME: Record<string, string> = { en: 'tiếng Anh', zh: 'tiếng Trung', vi: 'tiếng Việt' }

function greeting() {
  const h = new Date().getHours()
  return h < 11 ? 'Chào buổi sáng' : h < 14 ? 'Chào buổi trưa' : h < 18 ? 'Chào buổi chiều' : 'Chào buổi tối'
}

/**
 * The day's goal drawn as light leaving Prismo: the three beams (one per language) grow with
 * the words learned today and reach the edge when the goal is met.
 */
function GoalBeam({ learned, target }: { learned: number; target: number }) {
  const pct = Math.min(100, Math.round((learned / Math.max(target, 1)) * 100))
  return (
    <div className="w-full">
      <div className="h-[18px] rounded-r-full bg-white/10 overflow-hidden" role="progressbar" aria-valuemin={0} aria-valuemax={target}
        aria-valuenow={learned} aria-label="Mục tiêu từ mới hôm nay">
        <div className="h-full beams rounded-r-full transition-[width] duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
          style={{ width: `${Math.max(pct, 3)}%` }} />
      </div>
      <div className="mt-2 flex items-baseline justify-between text-sm text-white/75">
        <span><span className="num text-white font-bold text-base">{learned}/{target}</span> từ mới hôm nay</span>
        {pct >= 100 && <span className="text-[#ffd27a] font-semibold">Đã đạt mục tiêu</span>}
      </div>
    </div>
  )
}

export default function HomePage() {
  const user = useAuth((s) => s.user)
  const navigate = useNavigate()
  const lang = user?.active_language ?? 'en'
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
  const mood: Mood = goalPct >= 100 ? 'celebrate' : g?.studied_today ? 'happy' : due > 0 ? 'think' : 'wow'
  const line = goalPct >= 100 ? 'Bạn đã đạt mục tiêu hôm nay. Ôn thêm vài từ để nhớ lâu hơn.'
    : g?.studied_today ? `Còn ${target - learned} từ nữa là đạt mục tiêu hôm nay.`
      : due > 0 ? `${due} từ đến lịch ôn. Ôn trước, học từ mới sau.`
        : 'Năm phút là đủ cho một lượt học hôm nay.'

  const facts = [
    { icon: <StreakIcon size={20} active={!!g?.studied_today} />, value: g?.streak ?? 0, label: 'ngày liên tiếp' },
    { icon: <XpIcon size={20} />, value: g?.today_xp ?? 0, label: 'XP hôm nay' },
    { icon: <BookOutlined className="text-[#8fd8ff]" />, value: s?.learning ?? 0, label: 'từ đang học' },
    { icon: <CheckCircleFilled className="text-[#10c79a]" />, value: s?.mastered ?? 0, label: 'từ đã thuộc' },
  ]
  const script = user?.zh_script ?? 'hans'

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-5 md:gap-6">
      {/* today: the one strong surface on the page */}
      <section className="ink-bg text-white rounded-3xl overflow-hidden animate-rise">
        <div className="grid md:grid-cols-[1fr_minmax(260px,380px)] gap-6 md:gap-4 p-6 sm:p-8 md:p-10">
          <div className="min-w-0 flex flex-col">
            <div className="flex items-center gap-2 text-white/75 text-sm">
              <LangGlyph lang={lang} script={script} size={20} />
              Đang học {LANG_NAME[lang]}{lang === 'zh' ? (script === 'hant' ? ' phồn thể' : ' giản thể') : ''}
            </div>
            <h1 className="text-[1.75rem] sm:text-4xl font-extrabold leading-[1.15] mt-3 mb-2 text-white">
              {greeting()}, {user?.display_name}
            </h1>
            <p className="text-white/80 text-base sm:text-lg m-0 max-w-[46ch]">{line}</p>
            <div className="flex flex-wrap gap-3 mt-6">
              <button type="button" onClick={() => navigate('/learn?kind=learn')}
                className="cursor-pointer rounded-xl bg-[#fff] text-[#1b1538] font-bold px-5 h-12 text-base hover:bg-[#f2efff] active:scale-[0.97] transition">
                Học {target} từ mới
              </button>
              <button type="button" disabled={!due} onClick={() => navigate('/learn?kind=review')}
                className="cursor-pointer rounded-xl bg-white/10 font-bold px-5 h-12 text-base inline-flex items-center gap-2 hover:bg-white/15 active:scale-[0.97] transition disabled:opacity-45 disabled:cursor-not-allowed">
                <RedoOutlined /> {due ? `Ôn ${due} từ đến hạn` : 'Chưa có từ cần ôn'}
              </button>
            </div>
          </div>
          <div className="flex items-center md:items-end gap-2 md:flex-col md:justify-end">
            <Prismo mood={mood} size={124} className="shrink-0 md:self-start" />
            <div className="flex-1 w-full md:-mt-10 md:pl-[110px]"><GoalBeam learned={learned} target={target} /></div>
          </div>
        </div>
        <dl className="m-0 grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-3 px-6 sm:px-8 md:px-10 py-4 bg-white/[0.06]">
          {facts.map((f) => (
            <div key={f.label} className="flex items-center gap-2.5 min-w-0">
              <span className="text-lg leading-none">{f.icon}</span>
              <dt className="order-last text-sm text-white/70 truncate">{f.label}</dt>
              <dd className="m-0 num text-xl font-bold">{loading ? '–' : f.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <div className="grid lg:grid-cols-5 gap-5 md:gap-6">
        {/* camera: the heart of LingoPrism */}
        <button type="button" onClick={() => navigate('/camera')}
          className="lift lp-card lg:col-span-3 p-5 sm:p-6 text-left cursor-pointer flex items-center gap-5 group">
          <span className="h-16 w-16 rounded-2xl prism-bg grid place-items-center text-3xl text-white shrink-0 transition-transform duration-150 group-hover:scale-[1.04]">
            <CameraFilled />
          </span>
          <span className="flex-1 min-w-0">
            <span className="block text-xl font-bold text-slate-800">Chụp một đồ vật</span>
            <span className="block text-slate-500 mt-1">Máy nhận ra vật trong ảnh và cho bạn ngay từ tiếng Việt, tiếng Anh và tiếng Trung.</span>
          </span>
          <ArrowRightOutlined className="text-slate-400 text-lg hidden sm:block transition-transform duration-150 group-hover:translate-x-0.5" />
        </button>

        {/* today's quests */}
        <section className="lp-card lg:col-span-2 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-800 m-0">Nhiệm vụ hôm nay</h2>
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
            <EditOutlined className="text-2xl text-slate-500" />
            <div className="flex-1 min-w-0">
              <div className="font-bold text-slate-800 text-lg">Học đọc – viết tiếng Việt</div>
              <div className="text-slate-500 text-sm">Âm, dấu thanh, vần, đánh vần, nghe rồi viết lại</div>
            </div>
            <ArrowRightOutlined className="text-slate-400 transition-transform duration-150 group-hover:translate-x-0.5" />
          </Link>
        )}
        <Link to="/vocab" className="lift lp-card p-5 flex items-center gap-4 group">
          <BookOutlined className="text-2xl text-slate-500" />
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
