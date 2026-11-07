import type React from 'react'
import { App, Badge, ConfigProvider, Drawer, Dropdown, Grid, Select, Tooltip } from 'antd'
import { Suspense, useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { communityApi, gameApi, messagesApi } from '../api/app'
import { authApi } from '../api/auth'
import { CameraFilled, LogoutOutlined, MoonOutlined, SettingOutlined, SunOutlined } from '@ant-design/icons'
import { Navigate, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { isStaffRole, useAuth } from '../auth/store'
import { useLogout } from '../auth/useLogout'
import type { User } from '../api/types'
import { useUnread, useUserEvents } from '../lib/useUserEvents'
import { GemIcon, LangGlyph, Logo, ScaleIcon, StreakIcon } from '../components/brand/Brand'
import { AppIcon, type AppIconName } from '../components/brand/AppIcon'
import { useThemeMode, type ThemeMode } from '../theme/store'
import SideNav, { navGroups, type NavLeaf } from '../components/SideNav'
import ErrorBoundary from '../components/ErrorBoundary'
import TranslateBubble from '../components/TranslateBubble'
import SideRail from '../components/SideRail'
import { VerifyEmailBanner, WhatsNew } from '../components/AccountGates'
import { vocabApi } from '../api/vocab'
import { ProfilePrompt } from '../components/ProfileSetup'
import { UserAvatar } from '../components/ui'

/** Learning pages that get the right-hand rail on wide screens (not lessons, games being played, the camera, chats,
 * the community, the profile or Thành tích – which shows the quests itself). */
const RAIL_PAGES = ['/', '/tro-choi', '/vocab', '/sentences', '/speak', '/doc-viet', '/exams', '/camera/history']

const THEMES: { mode: ThemeMode; label: string; icon: React.ReactNode }[] = [
  { mode: 'light', label: 'Sáng', icon: <SunOutlined /> },
  { mode: 'dark', label: 'Tối', icon: <MoonOutlined /> },
]

const LANGUAGES = [
  { value: 'en', label: 'Tiếng Anh', glyph: <LangGlyph lang="en" /> },
  { value: 'zh:hans', label: 'Tiếng Trung giản thể', glyph: <LangGlyph lang="zh" script="hans" /> },
  { value: 'zh:hant', label: 'Tiếng Trung phồn thể', glyph: <LangGlyph lang="zh" script="hant" /> },
  { value: 'vi', label: 'Tiếng Việt', glyph: <LangGlyph lang="vi" /> },
]

/** Light / dark. Full: two side-by-side choices; compact: one button that flips to the other. */
function ThemeSwitch({ full = false }: { full?: boolean }) {
  const { mode, setMode, toggle } = useThemeMode()
  if (full) {
    return (
      <div role="radiogroup" aria-label="Giao diện" className="grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1">
        {THEMES.map((t) => (
          <button
            key={t.mode}
            type="button"
            role="radio"
            aria-checked={mode === t.mode}
            onClick={() => setMode(t.mode)}
            className={`h-9 rounded-lg inline-flex items-center justify-center gap-2 text-sm font-semibold cursor-pointer transition-colors ${
              mode === t.mode
                ? 'bg-[var(--surface)] text-slate-900 shadow-[0_1px_2px_rgb(0_0_0/0.12)]'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>
    )
  }
  const other = THEMES.find((t) => t.mode !== mode)!
  return (
    <Tooltip title={`Chuyển sang giao diện ${other.label.toLowerCase()}`}>
      <button
        type="button"
        onClick={toggle}
        aria-label={`Chuyển sang giao diện ${other.label.toLowerCase()}`}
        className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-600 hover:bg-slate-100 cursor-pointer transition"
      >
        {other.icon}
      </button>
    </Tooltip>
  )
}

function Stat({ icon, value, title, className = '' }: { icon: React.ReactNode; value: number; title: string; className?: string }) {
  return (
    <Tooltip title={title}>
      <span
        className={`num items-center gap-1 rounded-lg pl-1 pr-2 py-1 font-bold text-slate-700 hover:bg-slate-100 transition ${className}`}
      >
        {icon}
        {value}
      </span>
    </Tooltip>
  )
}

export default function LearnerLayout() {
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const logout = useLogout()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const unread = useUnread((s) => s.unread)
  useUserEvents()
  const game = useQuery({ queryKey: ['game-summary'], queryFn: gameApi.summary, enabled: !!user })
  const library = useQuery({ queryKey: ['summary', user?.active_language, user?.zh_script], queryFn: vocabApi.summary, enabled: !!user })
  const quests = useQuery({ queryKey: ['quests'], queryFn: gameApi.quests, enabled: !!user })
  const isKid = user?.learner_type === 'kid'
  const dmThreads = useQuery({ queryKey: ['dm-threads'], queryFn: messagesApi.threads, enabled: !!user && !isKid })
  const friendRequests = useQuery({
    queryKey: ['friend-requests', 'incoming'],
    queryFn: () => communityApi.friendRequests('incoming'),
    enabled: !!user && !isKid,
  })
  const groups = navGroups({
    due: library.data?.due,
    unread,
    quests: quests.data?.quests.filter((q) => !q.completed).length,
    dm: dmThreads.data?.reduce((n, t) => n + t.unread, 0),
    friends: friendRequests.data?.length,
  }).map((g) => ({ ...g, children: g.children?.filter((c) => (!c.only || c.only === user?.active_language) && !(c.adults && isKid)) }))

  useEffect(() => {
    const onNoVoice = (e: Event) =>
      message.warning(
        `Trình duyệt chưa có giọng đọc ${(e as CustomEvent).detail}. Hãy cài thêm giọng đọc trong cài đặt hệ điều hành hoặc dùng Chrome/Edge.`,
      )
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
  const [sheet, setSheet] = useState<'learn' | 'me' | null>(null)
  const location = useLocation()
  useEffect(() => setSheet(null), [location.pathname])
  const focus = location.pathname.startsWith('/learn') // during a lesson: no tab bar on the phone
  const railOn = RAIL_PAGES.includes(location.pathname) || location.pathname.startsWith('/vocab/topics/')
  const isActive = (to: string) => (to === '/' ? location.pathname === '/' : location.pathname.startsWith(to))

  const menu = [
    ...(groups.find((g) => g.key === 'me')?.children ?? []).map((c) => ({
      key: c.to,
      icon: <AppIcon name={c.icon} size={20} />,
      onClick: () => navigate(c.to),
      label: (
        <span className="flex items-center gap-3 justify-between min-w-44">
          {c.label}
          {c.count ? <Badge count={c.count} size="small" /> : null}
        </span>
      ),
    })),
    ...(isStaffRole(user) ? [{ key: 'admin', icon: <SettingOutlined />, label: 'Trang quản trị', onClick: () => navigate('/admin') }] : []),
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', danger: true, onClick: logout },
  ]
  const streak = game.data?.streak ?? 0
  // the phone's "Học" sheet: the learning group, games, the word library extras; "Tôi": the learner's own corner
  const byKey = (k: string) => groups.find((g) => g.key === k)
  const learnSheet: NavLeaf[] = [
    ...(byKey('learn')?.children ?? []),
    { to: '/tro-choi', label: 'Trò chơi', icon: 'game' },
    ...(byKey('vocab')?.children ?? []).filter((c) => c.to !== '/vocab'),
  ]
  const meGroup = byKey('me')?.children ?? []
  const sumCounts = (items: NavLeaf[]) => items.reduce((n, c) => n + (c.count ?? 0), 0)
  const learnCount = sumCounts(learnSheet)
  const meCount = sumCounts(meGroup)
  const activeIn = (items: NavLeaf[]) =>
    items.some((c) => c.to.split(/[?#]/)[0] !== '/' && location.pathname.startsWith(c.to.split(/[?#]/)[0]))
  const learnActive = activeIn(learnSheet) || location.pathname === '/review'
  const meActive = activeIn(meGroup)

  // first visit: the short survey comes before anything else (the app does the same)
  if (user && !user.onboarding_completed && !isStaffRole(user)) return <Navigate to="/welcome" replace />

  return (
    <ConfigProvider
      theme={{
        token: { borderRadius: 10, controlHeightLG: 48, fontSizeLG: 16 },
        components: { Card: { borderRadiusLG: 16, headerFontSize: 17 } },
      }}
    >
      <div className="learner min-h-screen flex relative">
        <SideNav groups={groups} footer={(collapsed) => <ThemeSwitch full={!collapsed} />} />

        <div className="flex-1 flex flex-col min-w-0 relative z-[1]">
          <header className="h-14 md:h-16 flex items-center justify-between gap-2 px-3 md:px-8 bg-[var(--page-bg)] sticky top-0 z-20">
            <NavLink to="/" className="md:hidden shrink-0">
              <Logo compact={!screens.sm} size={32} />
            </NavLink>
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
                  return item ? (
                    <span className="inline-flex items-center gap-2 font-semibold">
                      {item.glyph}
                      {screens.sm && item.label}
                    </span>
                  ) : (
                    o.label
                  )
                }}
                optionRender={(o) => {
                  const item = LANGUAGES.find((l) => l.value === o.value)!
                  return (
                    <span className="inline-flex items-center gap-2">
                      {item.glyph}
                      {item.label}
                    </span>
                  )
                }}
                options={LANGUAGES.map((l) => ({ value: l.value, label: l.label }))}
              />
              <Stat
                className="inline-flex"
                icon={<StreakIcon active={!!game.data?.studied_today} />}
                value={streak}
                title={
                  game.data?.studied_today ? `Chuỗi ${streak} ngày – hôm nay bạn đã học!` : 'Học một bài hôm nay để giữ chuỗi ngày học'
                }
              />
              <Stat
                className="hidden sm:inline-flex"
                icon={<ScaleIcon />}
                value={game.data?.scales ?? user?.scales_balance ?? 0}
                title="Vảy – kiếm được khi học"
              />
              <Stat className="hidden sm:inline-flex" icon={<GemIcon />} value={game.data?.gems ?? user?.gems_balance ?? 0} title="Ngọc" />
              <span className="md:hidden">
                <ThemeSwitch />
              </span>
              <Badge count={unread} size="small" offset={[-4, 4]}>
                <button
                  type="button"
                  onClick={() => navigate('/notifications')}
                  aria-label="Thông báo"
                  className="h-10 w-10 rounded-xl grid place-items-center hover:bg-slate-100 cursor-pointer transition"
                >
                  <AppIcon name="bell" size={26} />
                </button>
              </Badge>
              <Dropdown menu={{ items: menu }} placement="bottomRight" trigger={['click']}>
                <button
                  type="button"
                  aria-label="Tài khoản"
                  className="flex items-center gap-2 cursor-pointer rounded-full hover:bg-slate-100 p-0.5 lg:pr-3 transition"
                >
                  <UserAvatar name={user?.display_name} src={user?.avatar} mascot={user?.mascot} size={32} />
                  <span className="hidden lg:inline font-semibold text-slate-700 max-w-40 truncate">{user?.display_name}</span>
                </button>
              </Dropdown>
            </div>
          </header>
          <main className={`flex-1 px-3 sm:px-4 md:px-8 xl:px-12 pt-2 md:pt-4 md:pb-12 ${focus ? 'pb-4' : 'pb-28'}`}>
            <div className="mx-auto w-full max-w-7xl 2xl:max-w-[1600px]">
              <VerifyEmailBanner />
              <WhatsNew />
              <ProfilePrompt />
              {/* the right-hand rail (quests, streak, league) beside the learning pages, on wide screens */}
              <div className="flex gap-8 items-start">
                <div key={location.pathname} className="animate-page flex-1 min-w-0">
                  <ErrorBoundary>
                    <Suspense fallback={null}>
                      <Outlet />
                    </Suspense>
                  </ErrorBoundary>
                </div>
                {railOn && <SideRail />}
              </div>
              {!focus && <TranslateBubble />}
            </div>
          </main>

          {/* phone: Hôm nay · Học · [camera, raised: the heart of the app] · Từ vựng · Tôi */}
          {!focus && (
            <nav
              aria-label="Mục chính"
              className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-[var(--surface)] border-t border-slate-200 grid grid-cols-5 items-end pt-1.5"
              style={{ paddingBottom: 'max(0.4rem, env(safe-area-inset-bottom))' }}
            >
              <TabLink to="/" icon="home" label="Hôm nay" on={isActive('/')} />
              <TabButton
                icon="learn"
                label="Học"
                on={sheet === 'learn' || learnActive}
                count={learnCount}
                onClick={() => setSheet('learn')}
              />
              <NavLink to="/camera" aria-label="Chụp ảnh học từ" className="flex flex-col items-center -mt-7">
                <span className="h-14 w-14 rounded-2xl prism-bg grid place-items-center text-white text-2xl ring-4 ring-[var(--page-bg)] active:scale-95 transition-transform">
                  <CameraFilled />
                </span>
                <span className={`text-[11px] font-semibold mt-0.5 ${isActive('/camera') ? 'text-brand-700' : 'text-slate-500'}`}>
                  Chụp ảnh
                </span>
              </NavLink>
              <TabLink to="/vocab" icon="vocab" label="Từ vựng" on={isActive('/vocab')} />
              <TabButton icon="profile" label="Tôi" on={sheet === 'me' || meActive} count={meCount} onClick={() => setSheet('me')} />
            </nav>
          )}
          <Drawer
            open={!!sheet}
            onClose={() => setSheet(null)}
            placement="bottom"
            size="auto"
            title={
              sheet === 'me' ? (
                <span className="flex items-center gap-2">
                  <UserAvatar name={user?.display_name} src={user?.avatar} mascot={user?.mascot} size={28} />
                  {user?.display_name}
                </span>
              ) : (
                'Học'
              )
            }
            styles={{ body: { paddingBottom: 'max(16px, env(safe-area-inset-bottom))' } }}
          >
            <nav aria-label={sheet === 'me' ? 'Tôi' : 'Học'} className="grid grid-cols-3 gap-2">
              {(sheet === 'me' ? meGroup : learnSheet).map((c) => (
                <NavLink
                  key={c.to}
                  to={c.to}
                  onClick={() => setSheet(null)}
                  className="relative rounded-2xl bg-slate-100 px-1 py-3 flex flex-col items-center gap-1 text-center text-xs font-semibold !text-slate-700 active:scale-95 transition-transform"
                >
                  <AppIcon name={c.icon} size={30} />
                  {c.label}
                  {c.count ? (
                    <span className="num absolute top-1.5 right-1.5 rounded-full bg-brand-600 text-white text-[10px] font-bold px-1.5">
                      {c.count > 99 ? '99+' : c.count}
                    </span>
                  ) : null}
                </NavLink>
              ))}
            </nav>
            {sheet === 'me' && (
              <>
                <div className="mt-5 text-sm font-semibold text-slate-500 mb-2">Giao diện</div>
                <ThemeSwitch full />
                <button
                  type="button"
                  onClick={logout}
                  className="mt-4 w-full h-11 rounded-xl text-red-600 font-semibold bg-red-50 cursor-pointer"
                >
                  Đăng xuất
                </button>
              </>
            )}
          </Drawer>
        </div>
      </div>
    </ConfigProvider>
  )
}

function TabLink({ to, icon, label, on }: { to: string; icon: AppIconName; label: string; on: boolean }) {
  return (
    <NavLink
      to={to}
      className={`flex flex-col items-center gap-0.5 min-h-12 text-[11px] font-semibold ${on ? 'text-brand-700' : 'text-slate-500'}`}
    >
      <span className={`px-3.5 py-0.5 rounded-xl border-2 transition-colors ${on ? 'bg-brand-50 border-brand-200' : 'border-transparent'}`}>
        <AppIcon name={icon} size={28} />
      </span>
      {label}
    </NavLink>
  )
}

function TabButton({
  icon,
  label,
  on,
  count,
  onClick,
}: {
  icon: AppIconName
  label: string
  on: boolean
  count: number
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-haspopup="dialog"
      className={`flex flex-col items-center gap-0.5 min-h-12 text-[11px] font-semibold cursor-pointer ${on ? 'text-brand-700' : 'text-slate-500'}`}
    >
      <Badge count={count} size="small" offset={[-6, 4]}>
        <span
          className={`block px-3.5 py-0.5 rounded-xl border-2 transition-colors ${on ? 'bg-brand-50 border-brand-200' : 'border-transparent'}`}
        >
          <AppIcon name={icon} size={28} />
        </span>
      </Badge>
      {label}
    </button>
  )
}
