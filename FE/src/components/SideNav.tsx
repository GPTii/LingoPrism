import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Popover, Tooltip } from 'antd'
import {
  BookOutlined, CameraOutlined, DownOutlined, HomeOutlined, MenuFoldOutlined, MenuUnfoldOutlined, MessageOutlined,
  ReadOutlined, TeamOutlined, TrophyOutlined,
} from '@ant-design/icons'
import { NavLink, useLocation } from 'react-router-dom'
import { Logo, LogoMark } from './brand/Brand'

export type NavLeaf = { to: string; label: string; only?: string; count?: number }
export type NavGroup = { key: string; label: string; icon: ReactNode; to?: string; children?: NavLeaf[] }

/** The whole app in groups; the counts make the work waiting inside each one visible. */
export function navGroups(counts: { due?: number; unread?: number; quests?: number }): NavGroup[] {
  return [
    { key: 'home', label: 'Hôm nay', icon: <HomeOutlined />, to: '/' },
    {
      key: 'learn', label: 'Học', icon: <ReadOutlined />, children: [
        { to: '/learn?kind=learn', label: 'Học từ mới' },
        { to: '/learn?kind=review', label: 'Ôn từ đến hạn', count: counts.due },
        { to: '/sentences', label: 'Luyện câu' },
        { to: '/doc-viet', label: 'Học đọc – viết', only: 'vi' },
        { to: '/exams', label: 'Đề thi' },
      ],
    },
    {
      key: 'vocab', label: 'Từ vựng', icon: <BookOutlined />, children: [
        { to: '/vocab', label: 'Chủ đề' },
        { to: '/vocab?tab=library', label: 'Từ của tôi' },
      ],
    },
    {
      key: 'snap', label: 'Chụp & khám phá', icon: <CameraOutlined />, children: [
        { to: '/camera', label: 'Chụp ảnh học từ' },
        { to: '/map', label: 'Học theo vị trí' },
      ],
    },
    {
      key: 'community', label: 'Cộng đồng', icon: <TeamOutlined />, children: [
        { to: '/community?tab=feed', label: 'Bảng tin' },
        { to: '/community?tab=groups', label: 'Nhóm học' },
        { to: '/community?tab=leaderboard', label: 'Bảng xếp hạng' },
      ],
    },
    {
      key: 'rewards', label: 'Thành tích', icon: <TrophyOutlined />, children: [
        { to: '/achievements#quests', label: 'Nhiệm vụ', count: counts.quests },
        { to: '/achievements#calendar', label: 'Lịch học' },
        { to: '/achievements#badges', label: 'Huy hiệu' },
        { to: '/achievements#shop', label: 'Cửa hàng' },
      ],
    },
    {
      key: 'help', label: 'Hỗ trợ', icon: <MessageOutlined />, children: [
        { to: '/support', label: 'Hỏi giáo viên' },
        { to: '/notifications', label: 'Thông báo', count: counts.unread },
        { to: '/profile', label: 'Hồ sơ & cài đặt' },
      ],
    },
  ]
}

/** How well a link matches where we are: path, then its ?query, then its #hash. -1 = not at all. */
function score(to: string, loc: { pathname: string; search: string; hash: string }) {
  const u = new URL(to, 'http://x')
  const pathOk = u.pathname === '/' ? loc.pathname === '/' : loc.pathname === u.pathname || loc.pathname.startsWith(`${u.pathname}/`)
  if (!pathOk) return -1
  let s = 1
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
  n ? <span className="num ml-auto min-w-5 h-5 px-1.5 rounded-full bg-[#6d4aff] text-white text-[11px] font-bold grid place-items-center">{n > 99 ? '99+' : n}</span> : null

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
              className={`flex items-center gap-2.5 rounded-lg h-9 pl-3 pr-2 text-sm transition-colors ${
                on ? 'text-slate-900 font-semibold bg-slate-100' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'}`}>
              <span aria-hidden className={`h-1.5 w-1.5 rounded-full shrink-0 transition-colors ${on ? 'bg-[#6d4aff]' : 'bg-slate-300'}`} />
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
              <span className={`relative h-11 w-11 rounded-xl grid place-items-center text-[18px] transition-colors ${
                on ? 'bg-[#6d4aff] text-white' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'}`}>
                {g.icon}
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
                className={`flex items-center gap-3 rounded-xl h-11 px-3 font-semibold transition-colors ${
                  on ? 'bg-[#6d4aff] text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}>
                <span className="text-[18px] leading-none">{g.icon}</span>{g.label}
              </NavLink>
            )
          }
          const isOpen = open.includes(g.key)
          return (
            <div key={g.key}>
              <button type="button" onClick={() => toggle(g.key)} aria-expanded={isOpen}
                className={`w-full flex items-center gap-3 rounded-xl h-11 px-3 font-semibold cursor-pointer transition-colors ${
                  on ? 'text-slate-900' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}>
                <span className={`text-[18px] leading-none ${on ? 'text-[#8f75ff]' : ''}`}>{g.icon}</span>
                <span className="flex-1 text-left">{g.label}</span>
                {!isOpen && total(g) > 0 && <Count n={total(g)} />}
                <DownOutlined className={`text-[10px] text-slate-400 transition-transform duration-200 ${isOpen ? '' : '-rotate-90'}`} />
              </button>
              {/* folds open with its own height: grid rows 0fr → 1fr */}
              <div className="grid transition-[grid-template-rows] duration-200 ease-out" style={{ gridTemplateRows: isOpen ? '1fr' : '0fr' }}>
                <div className="overflow-hidden" inert={!isOpen}>
                  <div className="ml-[22px] pl-2 border-l border-slate-200 my-1">
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
