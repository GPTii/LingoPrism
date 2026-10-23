import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Popover, Tooltip } from 'antd'
import { DownOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'
import { NavLink, useLocation } from 'react-router-dom'
import { Logo, LogoMark } from './brand/Brand'
import { AppIcon, type AppIconName } from './brand/AppIcon'

export type NavLeaf = { to: string; label: string; icon: AppIconName; only?: string; count?: number; adults?: boolean }
export type NavGroup = { key: string; label: string; icon: AppIconName; to?: string; children?: NavLeaf[] }

/** The whole app in groups; the counts make the work waiting inside each one visible. */
export function navGroups(counts: { due?: number; unread?: number; quests?: number; dm?: number; friends?: number }): NavGroup[] {
  return [
    { key: 'home', label: 'Hôm nay', icon: 'home', to: '/' },
    {
      key: 'learn', label: 'Học', icon: 'learn', children: [
        { to: '/learn?kind=learn', label: 'Học từ mới', icon: 'sparkle' },
        { to: '/learn?kind=review', label: 'Ôn từ đến hạn', icon: 'review', count: counts.due },
        { to: '/sentences', label: 'Luyện câu', icon: 'tiles' },
        { to: '/speak', label: 'Luyện phát âm', icon: 'mic' },
        { to: '/doc-viet', label: 'Học đọc – viết', icon: 'pencil', only: 'vi' },
        { to: '/exams', label: 'Đề thi', icon: 'exam' },
      ],
    },
    {
      key: 'vocab', label: 'Từ vựng', icon: 'vocab', children: [
        { to: '/vocab', label: 'Chủ đề', icon: 'shapes' },
        { to: '/vocab?tab=library', label: 'Từ của tôi', icon: 'bookmark' },
      ],
    },
    {
      key: 'snap', label: 'Chụp & khám phá', icon: 'camera', children: [
        { to: '/camera', label: 'Chụp ảnh học từ', icon: 'camera' },
        { to: '/camera/history', label: 'Lịch sử ảnh', icon: 'photo' },
        { to: '/map', label: 'Học theo vị trí', icon: 'pin' },
      ],
    },
    {
      key: 'community', label: 'Cộng đồng', icon: 'community', children: [
        { to: '/community?tab=feed', label: 'Bảng tin', icon: 'news' },
        { to: '/friends', label: 'Bạn bè', icon: 'community', count: counts.friends, adults: true },
        { to: '/community?tab=saved', label: 'Bài đã lưu', icon: 'bookmark', adults: true },
        { to: '/community?tab=groups', label: 'Nhóm học', icon: 'group' },
        { to: '/community?tab=leaderboard', label: 'Bảng xếp hạng', icon: 'podium' },
        { to: '/messages', label: 'Tin nhắn', icon: 'mail', count: counts.dm, adults: true },
      ],
    },
    {
      key: 'rewards', label: 'Thành tích', icon: 'trophy', children: [
        { to: '/stats', label: 'Thống kê học tập', icon: 'chart' },
        { to: '/achievements#quests', label: 'Nhiệm vụ', icon: 'target', count: counts.quests },
        { to: '/achievements#calendar', label: 'Lịch học', icon: 'calendar' },
        { to: '/achievements#badges', label: 'Huy hiệu', icon: 'medal' },
        { to: '/prismo', label: 'Tủ đồ Prismo', icon: 'sparkle' },
        { to: '/achievements#shop', label: 'Cửa hàng', icon: 'bag' },
      ],
    },
    {
      key: 'help', label: 'Hỗ trợ', icon: 'chat', children: [
        { to: '/support', label: 'Hỏi giáo viên', icon: 'cap' },
        { to: '/notifications', label: 'Thông báo', icon: 'bell', count: counts.unread },
        { to: '/profile', label: 'Hồ sơ & cài đặt', icon: 'profile' },
      ],
    },
  ]
}

/** How well a link matches where we are: path, then its ?query, then its #hash. -1 = not at all. */
function score(to: string, loc: { pathname: string; search: string; hash: string }) {
  const u = new URL(to, 'http://x')
  const pathOk = u.pathname === '/' ? loc.pathname === '/' : loc.pathname === u.pathname || loc.pathname.startsWith(`${u.pathname}/`)
  if (!pathOk) return -1
  let s = loc.pathname === u.pathname ? 2 : 1 // /camera/history beats /camera there
  const here = new URLSearchParams(loc.search)
  for (const [k, v] of u.searchParams) {
    if (here.get(k) === v) s += 2
    else return 0
  }
  if (u.hash) s += u.hash === loc.hash ? 2 : 0
  return s
}

/** The link that best matches the current address (one active item in the whole menu). */
export function useActiveLink(groups: NavGroup[]) {
  const loc = useLocation()
  // /review is an alias of the review session
  const where = loc.pathname === '/review' ? { ...loc, pathname: '/learn', search: '?kind=review' } : loc
  return useMemo(() => {
    let best: string | null = null
    let top = 0
    for (const g of groups) {
      for (const to of g.to ? [g.to] : (g.children ?? []).map((c) => c.to)) {
        const sc = score(to, where)
        if (sc > top) { top = sc; best = to }
      }
    }
    return best
  }, [groups, where.pathname, where.search, where.hash]) // eslint-disable-line react-hooks/exhaustive-deps
}

const Count = ({ n }: { n?: number }) =>
  n ? <span className="num ml-auto min-w-5 h-5 px-1.5 rounded-full bg-brand-600 text-white text-[11px] font-bold grid place-items-center">{n > 99 ? '99+' : n}</span> : null

const read = <T,>(key: string, fallback: T): T => {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) as T : fallback } catch { return fallback }
}
const write = (key: string, v: unknown) => { try { localStorage.setItem(key, JSON.stringify(v)) } catch { /* storage blocked */ } }

function Leaves({ items, active, onPick }: { items: NavLeaf[]; active: string | null; onPick?: () => void }) {
  return (
    <ul className="m-0 p-0 list-none flex flex-col">
      {items.map((c) => {
        const on = c.to === active
        return (
          <li key={c.to}>
            <NavLink to={c.to} onClick={onPick} aria-current={on ? 'page' : undefined}
              className={`flex items-center gap-2.5 rounded-xl h-10 pl-2 pr-2 text-sm font-semibold border-2 transition-colors ${
                on ? 'text-brand-700 bg-brand-50 border-brand-200' : 'text-slate-500 border-transparent hover:text-slate-900 hover:bg-slate-100'}`}>
              <AppIcon name={c.icon} size={22} />
              <span className="truncate">{c.label}</span>
              <Count n={c.count} />
            </NavLink>
          </li>
        )
      })}
    </ul>
  )
}

/**
 * Left navigation: groups that fold open like a dropdown, each with its own small links.
 * Folded down to a rail, a group's links fly out beside its icon instead.
 */
export default function SideNav({ groups, footer }: { groups: NavGroup[]; footer?: (collapsed: boolean) => ReactNode }) {
  const active = useActiveLink(groups)
  const activeGroup = groups.find((g) => g.to === active || g.children?.some((c) => c.to === active))?.key
  const [collapsed, setCollapsed] = useState<boolean>(() => read('lingoprism-nav-collapsed', false))
  const [open, setOpen] = useState<string[]>(() => read('lingoprism-nav-open', ['learn']))
  useEffect(() => {
    if (activeGroup && !open.includes(activeGroup)) setOpen((o) => [...o, activeGroup])
  }, [activeGroup]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => write('lingoprism-nav-open', open), [open])
  useEffect(() => {
    write('lingoprism-nav-collapsed', collapsed)
    // fixed bars (the lesson's answer bar) start where the menu ends
    document.documentElement.style.setProperty('--nav-w', collapsed ? '76px' : '256px')
  }, [collapsed])
  const toggle = (key: string) => setOpen((o) => (o.includes(key) ? o.filter((k) => k !== key) : [...o, key]))
  const total = (g: NavGroup) => (g.children ?? []).reduce((n, c) => n + (c.count ?? 0), 0)

  if (collapsed) {
    return (
      <aside className="hidden md:flex w-[76px] shrink-0 flex-col items-center border-r border-slate-200 py-4 sticky top-0 h-screen overflow-y-auto z-10">
        <NavLink to="/" aria-label="LingoPrism – trang chủ" className="mb-5"><LogoMark size={38} /></NavLink>
        <nav className="flex flex-col items-center gap-1.5" aria-label="Mục chính">
          {groups.map((g) => {
            const on = g.key === activeGroup
            const icon = (
              <span className={`relative h-12 w-12 rounded-xl grid place-items-center border-2 transition-colors ${
                on ? 'bg-brand-50 border-brand-200' : 'border-transparent hover:bg-slate-100'}`}>
                <AppIcon name={g.icon} size={30} />
                {total(g) > 0 && <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#ff6b81]" />}
              </span>
            )
            return g.to ? (
              <Tooltip key={g.key} title={g.label} placement="right">
                <NavLink to={g.to} aria-label={g.label} aria-current={on ? 'page' : undefined}>{icon}</NavLink>
              </Tooltip>
            ) : (
              <Popover key={g.key} placement="rightTop" arrow={false} trigger={['hover', 'click']}
                title={<span className="font-bold">{g.label}</span>}
                content={<div className="w-56 -mx-1"><Leaves items={g.children!} active={active} /></div>}>
                <button type="button" aria-label={g.label} className="cursor-pointer">{icon}</button>
              </Popover>
            )
          })}
        </nav>
        <div className="mt-auto pt-4 flex flex-col items-center gap-2">
          {footer?.(true)}
          <Tooltip title="Mở rộng menu" placement="right">
            <button type="button" onClick={() => setCollapsed(false)} aria-label="Mở rộng menu"
              className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-500 hover:bg-slate-100 cursor-pointer"><MenuUnfoldOutlined /></button>
          </Tooltip>
        </div>
      </aside>
    )
  }

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-slate-200 px-3 py-4 sticky top-0 h-screen overflow-y-auto z-10">
      <div className="flex items-center justify-between px-2 mb-5">
        <NavLink to="/" aria-label="LingoPrism – trang chủ"><Logo size={34} /></NavLink>
        <Tooltip title="Thu gọn menu" placement="right">
          <button type="button" onClick={() => setCollapsed(true)} aria-label="Thu gọn menu"
            className="h-9 w-9 rounded-lg grid place-items-center text-slate-500 hover:bg-slate-100 cursor-pointer"><MenuFoldOutlined /></button>
        </Tooltip>
      </div>
      <nav className="flex flex-col gap-0.5" aria-label="Mục chính">
        {groups.map((g) => {
          const on = g.key === activeGroup
          if (g.to) {
            return (
              <NavLink key={g.key} to={g.to} aria-current={g.to === active ? 'page' : undefined}
                className={`flex items-center gap-3 rounded-xl h-12 px-2.5 font-bold border-2 transition-colors ${
                  on ? 'text-brand-700 bg-brand-50 border-brand-200' : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-900'}`}>
                <AppIcon name={g.icon} size={30} />{g.label}
              </NavLink>
            )
          }
          const isOpen = open.includes(g.key)
          return (
            <div key={g.key}>
              <button type="button" onClick={() => toggle(g.key)} aria-expanded={isOpen}
                className={`w-full flex items-center gap-3 rounded-xl h-12 px-2.5 font-bold border-2 border-transparent cursor-pointer transition-colors ${
                  on ? 'text-slate-900' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}>
                <AppIcon name={g.icon} size={30} />
                <span className="flex-1 text-left">{g.label}</span>
                {!isOpen && total(g) > 0 && <Count n={total(g)} />}
                <DownOutlined className={`text-[10px] text-slate-400 transition-transform duration-200 ${isOpen ? '' : '-rotate-90'}`} />
              </button>
              {/* folds open with its own height: grid rows 0fr → 1fr */}
              <div className="grid transition-[grid-template-rows] duration-200 ease-out" style={{ gridTemplateRows: isOpen ? '1fr' : '0fr' }}>
                <div className="overflow-hidden" inert={!isOpen}>
                  <div className="ml-[26px] pl-2 border-l-2 border-slate-200 my-1">
                    <Leaves items={g.children!} active={active} />
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </nav>
      {footer && <div className="mt-auto pt-5">{footer(false)}</div>}
    </aside>
  )
}
