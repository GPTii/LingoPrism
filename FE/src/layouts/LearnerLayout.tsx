import type React from 'react'
import { App, Avatar, Badge, ConfigProvider, Drawer, Dropdown, Grid, Select, Tooltip } from 'antd'
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { gameApi } from '../api/app'
import { authApi } from '../api/auth'
import {
  AppstoreOutlined, BookOutlined, CameraFilled, CameraOutlined, DesktopOutlined, EnvironmentOutlined, EditOutlined,
  FileDoneOutlined, FormOutlined, HomeOutlined, LogoutOutlined, MoonOutlined, RedoOutlined, SettingOutlined,
  SunOutlined, TrophyOutlined, TeamOutlined, UserOutlined, BellOutlined, MessageOutlined,
} from '@ant-design/icons'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { isStaffRole, useAuth } from '../auth/store'
import { useLogout } from '../auth/useLogout'
import type { User } from '../api/types'
import { useUnread, useUserEvents } from '../lib/useUserEvents'
import { GemIcon, LangGlyph, Logo, LogoMark, ScaleIcon, StreakIcon } from '../components/brand/Brand'
import { useThemeMode, type ThemeMode } from '../theme/store'

/** One quiet colour system: the page you are on is marked, the rest stay out of the way. */
const NAV: { to: string; label: string; icon: React.ReactNode; only?: string }[] = [
  { to: '/', label: 'Trang chủ', icon: <HomeOutlined /> },
  { to: '/vocab', label: 'Từ vựng', icon: <BookOutlined /> },
  { to: '/doc-viet', label: 'Học đọc – viết', icon: <EditOutlined />, only: 'vi' },
  { to: '/review', label: 'Ôn tập', icon: <RedoOutlined /> },
  { to: '/sentences', label: 'Luyện câu', icon: <FormOutlined /> },
  { to: '/camera', label: 'Nhận diện', icon: <CameraOutlined /> },
  { to: '/exams', label: 'Đề thi', icon: <FileDoneOutlined /> },
  { to: '/community', label: 'Cộng đồng', icon: <TeamOutlined /> },
  { to: '/map', label: 'Bản đồ', icon: <EnvironmentOutlined /> },
  { to: '/achievements', label: 'Thành tích', icon: <TrophyOutlined /> },
  { to: '/support', label: 'Hỏi giáo viên', icon: <MessageOutlined /> },
]

const THEMES: { mode: ThemeMode; label: string; icon: React.ReactNode }[] = [
  { mode: 'light', label: 'Sáng', icon: <SunOutlined /> },
  { mode: 'dark', label: 'Tối', icon: <MoonOutlined /> },
  { mode: 'system', label: 'Theo máy', icon: <DesktopOutlined /> },
]

const LANGUAGES = [
  { value: 'en', label: 'Tiếng Anh', glyph: <LangGlyph lang="en" /> },
  { value: 'zh:hans', label: 'Tiếng Trung giản thể', glyph: <LangGlyph lang="zh" script="hans" /> },
  { value: 'zh:hant', label: 'Tiếng Trung phồn thể', glyph: <LangGlyph lang="zh" script="hant" /> },
  { value: 'vi', label: 'Tiếng Việt', glyph: <LangGlyph lang="vi" /> },
]

function ThemeSwitch({ full = false }: { full?: boolean }) {
  const { mode, setMode } = useThemeMode()
  if (full) {
    return (
      <div className="grid grid-cols-3 gap-2">
        {THEMES.map((t) => (
          <button key={t.mode} type="button" onClick={() => setMode(t.mode)}
            aria-pressed={mode === t.mode}
            className={`btn-3d py-2 flex flex-col items-center gap-0.5 text-xs font-semibold cursor-pointer ${mode === t.mode ? '!border-brand-500 text-brand-700' : 'text-slate-500'}`}>
            <span className="text-base">{t.icon}</span>{t.label}
          </button>
        ))}
      </div>
    )
  }
  const i = THEMES.findIndex((t) => t.mode === mode)
  const next = THEMES[(i + 1) % THEMES.length]
  return (
    <Tooltip title={`Giao diện: ${THEMES[i].label} – bấm để chuyển sang ${next.label.toLowerCase()}`}>
      <button type="button" onClick={() => setMode(next.mode)} aria-label="Đổi giao diện sáng / tối"
        className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-600 hover:bg-slate-100 cursor-pointer transition">
        {THEMES[i].icon}
      </button>
    </Tooltip>
  )
}

function Stat({ icon, value, title, className = '' }: { icon: React.ReactNode; value: number; title: string; className?: string }) {
  return (
    <Tooltip title={title}>
      <span className={`num items-center gap-1 rounded-lg pl-1 pr-2 py-1 font-bold text-slate-700 hover:bg-slate-100 transition ${className}`}>
        {icon}{value}
      </span>
    </Tooltip>
  )
}

export default function LearnerLayout() {
  const user = useAuth((s) => s.user)
  const nav = NAV.filter((item) => !item.only || item.only === user?.active_language)
  const setUser = useAuth((s) => s.setUser)
  const logout = useLogout()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const unread = useUnread((s) => s.unread)
  useUserEvents()
  const game = useQuery({ queryKey: ['game-summary'], queryFn: gameApi.summary, enabled: !!user })

  useEffect(() => {
    const onNoVoice = (e: Event) =>
      message.warning(`Trình duyệt chưa có giọng đọc ${(e as CustomEvent).detail}. Hãy cài thêm giọng đọc trong cài đặt hệ điều hành hoặc dùng Chrome/Edge.`)
    window.addEventListener('lingoprism:no-voice', onNoVoice)
    return () => window.removeEventListener('lingoprism:no-voice', onNoVoice)
  }, [message])

  const switchLanguage = async (value: string) => {
    const [active_language, zh_script] = value.split(':') as [User['active_language'], User['zh_script'] | undefined]
    const updated = await authApi.updateMe({ active_language, ...(zh_script ? { zh_script } : {}) })
    setUser(updated)
    queryClient.invalidateQueries()
  }
  const languageValue = user?.active_language === 'zh' ? `zh:${user.zh_script}` : user?.active_language
  const screens = Grid.useBreakpoint()
  const [moreOpen, setMoreOpen] = useState(false)
  const location = useLocation()
  useEffect(() => setMoreOpen(false), [location.pathname])
  const focus = location.pathname.startsWith('/learn') // during a lesson: no tab bar on the phone
  const isActive = (to: string) => (to === '/' ? location.pathname === '/' : location.pathname.startsWith(to))

  const menu = [
    { key: 'profile', icon: <UserOutlined />, label: 'Hồ sơ & cài đặt', onClick: () => navigate('/profile') },
    ...(isStaffRole(user) ? [{ key: 'admin', icon: <SettingOutlined />, label: 'Trang quản trị', onClick: () => navigate('/admin') }] : []),
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', danger: true, onClick: logout },
  ]
  const streak = game.data?.streak ?? 0
  const pick = (to: string) => nav.find((i) => i.to === to)!
  const bottom = [pick('/'), pick('/vocab'), null, pick('/review')]
  const onTab = bottom.some((i) => i && isActive(i.to)) || isActive('/camera')

  return (
    <ConfigProvider theme={{ token: { borderRadius: 10, controlHeightLG: 48, fontSizeLG: 16 }, components: { Card: { borderRadiusLG: 16, headerFontSize: 17 } } }}>
      <div className="learner min-h-screen flex relative">
        {/* tablet: icons only; laptop and larger: icons + labels */}
        <aside className="hidden md:flex md:w-[88px] lg:w-60 shrink-0 flex-col bg-white border-r border-slate-200 px-3 py-5 sticky top-0 h-screen overflow-y-auto z-10">
          <NavLink to="/" className="flex items-center justify-center lg:justify-start lg:px-2 mb-7">
            <span className="lg:hidden"><LogoMark size={40} /></span>
            <span className="hidden lg:inline"><Logo /></span>
          </NavLink>
          <nav className="flex flex-col gap-0.5" aria-label="Mục chính">
            {nav.map((item) => {
              const active = isActive(item.to)
              return (
                <NavLink key={item.to} to={item.to} title={item.label} aria-current={active ? 'page' : undefined}
                  className={`flex items-center justify-center lg:justify-start gap-3 rounded-xl h-11 px-3 font-semibold transition-colors ${
                    active ? 'bg-brand-50 text-brand-700' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'}`}>
                  <span className="text-[18px] leading-none">{item.icon}</span>
                  <span className="hidden lg:inline text-[15px]">{item.label}</span>
                </NavLink>
              )
            })}
          </nav>
          <div className="mt-auto pt-6 hidden lg:block"><ThemeSwitch full /></div>
          <div className="mt-auto pt-6 lg:hidden flex justify-center"><ThemeSwitch /></div>
        </aside>

        <div className="flex-1 flex flex-col min-w-0 relative z-[1]">
          <header className="h-14 md:h-16 flex items-center justify-between gap-2 px-3 md:px-6 bg-white border-b border-slate-200 sticky top-0 z-20">
            <NavLink to="/" className="md:hidden shrink-0"><Logo compact={!screens.sm} size={32} /></NavLink>
            <div className="flex-1" />
            <div className="flex items-center gap-1.5 sm:gap-2.5 text-sm">
              <Select
                value={languageValue}
                onChange={switchLanguage}
                variant="filled"
                style={{ width: screens.sm ? 230 : 72 }}
                popupMatchSelectWidth={false}
                aria-label="Ngôn ngữ đang học"
                labelRender={(o) => {
                  const item = LANGUAGES.find((l) => l.value === o.value)
                  return item ? <span className="inline-flex items-center gap-2 font-semibold">{item.glyph}{screens.sm && item.label}</span> : o.label
                }}
                optionRender={(o) => {
                  const item = LANGUAGES.find((l) => l.value === o.value)!
                  return <span className="inline-flex items-center gap-2">{item.glyph}{item.label}</span>
                }}
                options={LANGUAGES.map((l) => ({ value: l.value, label: l.label }))}
              />
              <Stat className="inline-flex" icon={<StreakIcon active={!!game.data?.studied_today} />} value={streak}
                title={game.data?.studied_today ? `Chuỗi ${streak} ngày – hôm nay bạn đã học!` : 'Học một bài hôm nay để giữ chuỗi ngày học'} />
              <Stat className="hidden sm:inline-flex" icon={<ScaleIcon />} value={game.data?.scales ?? user?.scales_balance ?? 0} title="Vảy – kiếm được khi học" />
              <Stat className="hidden sm:inline-flex" icon={<GemIcon />} value={game.data?.gems ?? user?.gems_balance ?? 0} title="Ngọc" />
              <span className="md:hidden"><ThemeSwitch /></span>
              <Badge count={unread} size="small" offset={[-4, 4]}>
                <button type="button" onClick={() => navigate('/notifications')} aria-label="Thông báo"
                  className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-600 hover:bg-slate-100 cursor-pointer transition">
                  <BellOutlined />
                </button>
              </Badge>
              <Dropdown menu={{ items: menu }} placement="bottomRight" trigger={['click']}>
                <button type="button" aria-label="Tài khoản" className="flex items-center gap-2 cursor-pointer rounded-full hover:bg-slate-100 p-0.5 lg:pr-3 transition">
                  <Avatar src={user?.avatar ?? undefined} icon={<UserOutlined />} className="!bg-brand-600" />
                  <span className="hidden lg:inline font-semibold text-slate-700 max-w-40 truncate">{user?.display_name}</span>
                </button>
              </Dropdown>
            </div>
          </header>
          <main className={`flex-1 p-3 sm:p-4 md:p-6 xl:p-8 md:pb-8 ${focus ? 'pb-4' : 'pb-28'}`}>
            <div className="mx-auto w-full max-w-7xl 2xl:max-w-[1600px]">
              <Outlet />
            </div>
          </main>

          {/* phone: the camera – the heart of the app – raised in the middle */}
          {!focus && <nav aria-label="Mục chính" className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-slate-200 grid grid-cols-5 items-end pt-1.5"
            style={{ paddingBottom: 'max(0.4rem, env(safe-area-inset-bottom))' }}>
            {bottom.map((item, i) => item ? (
              <NavLink key={item.to} to={item.to}
                className={`flex flex-col items-center gap-0.5 min-h-12 text-[11px] font-semibold ${isActive(item.to) ? 'text-brand-700' : 'text-slate-500'}`}>
                <span className={`text-xl px-4 py-0.5 rounded-full transition-colors ${isActive(item.to) ? 'bg-brand-50' : ''}`}>{item.icon}</span>
                {item.label}
              </NavLink>
            ) : (
              <NavLink key={`cam${i}`} to="/camera" aria-label="Chụp ảnh học từ" className="flex flex-col items-center -mt-7">
                <span className="h-14 w-14 rounded-2xl prism-bg grid place-items-center text-white text-2xl ring-4 ring-[var(--page-bg)] active:scale-95 transition-transform">
                  <CameraFilled />
                </span>
                <span className={`text-[11px] font-semibold mt-0.5 ${isActive('/camera') ? 'text-brand-700' : 'text-slate-500'}`}>Chụp ảnh</span>
              </NavLink>
            ))}
            <button type="button" onClick={() => setMoreOpen(true)}
              className={`flex flex-col items-center gap-0.5 min-h-12 text-[11px] font-semibold cursor-pointer ${onTab ? 'text-slate-500' : 'text-brand-700'}`}>
              <span className={`text-xl px-4 py-0.5 rounded-full ${onTab ? '' : 'bg-brand-50'}`}><AppstoreOutlined /></span>
              Thêm
            </button>
          </nav>}
          <Drawer open={moreOpen} onClose={() => setMoreOpen(false)} placement="bottom" height="auto" title="Tất cả mục"
            styles={{ body: { paddingBottom: 'max(16px, env(safe-area-inset-bottom))' } }}>
            <nav className="grid grid-cols-3 gap-2">
              {[...nav, { to: '/profile', label: 'Hồ sơ', icon: <UserOutlined /> }].map((item) => (
                <NavLink key={item.to} to={item.to}
                  className={`btn-3d flex flex-col items-center gap-1.5 py-3 px-1 text-xs font-semibold text-center ${isActive(item.to) ? '!border-brand-500 text-brand-700' : 'text-slate-700'}`}>
                  <span className="text-xl">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </nav>
            <div className="mt-5 text-sm font-semibold text-slate-500 mb-2">Giao diện</div>
            <ThemeSwitch full />
          </Drawer>
        </div>
      </div>
    </ConfigProvider>
  )
}
