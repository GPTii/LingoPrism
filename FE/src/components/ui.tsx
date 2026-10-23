import { useState, type ReactNode } from 'react'
import { ArrowLeftOutlined, DownOutlined, UpOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import type { MascotLook } from '../api/types'
import { PrismoAvatar } from './brand/Brand'

/**
 * The few building blocks every learner page is made of, so all pages share one rhythm:
 * a page header, plain sections (one hairline, no shadow) and facts set as a row of numbers
 * rather than a grid of look-alike tiles.
 */

export function PageHeader({ title, description, back, actions }: {
  title: ReactNode
  description?: ReactNode
  back?: { to: string; label: string }
  actions?: ReactNode
}) {
  return (
    <header className="flex flex-col gap-3">
      {back && (
        <Link to={back.to} className="inline-flex items-center gap-1.5 self-start text-sm font-semibold !text-slate-500 hover:!text-slate-800">
          <ArrowLeftOutlined className="text-xs" /> {back.label}
        </Link>
      )}
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div className="min-w-0">
          <h1 className="text-[2rem] sm:text-5xl font-extrabold text-slate-900 m-0 leading-[1.05] tracking-[-0.03em]">{title}</h1>
          {description && <p className="text-lg text-slate-500 mt-3 mb-0 max-w-[60ch]">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </header>
  )
}

export function Section({ id, title, extra, children, className = '', bodyClassName = '' }: {
  id?: string
  title?: ReactNode
  extra?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}) {
  return (
    <section id={id} className={`lp-card scroll-mt-20 ${className}`}>
      {(title || extra) && (
        <div className="flex flex-wrap items-center justify-between gap-2 px-5 pt-4 sm:px-6 sm:pt-5">
          {title && <h2 className="text-lg font-bold text-slate-800 m-0">{title}</h2>}
          {extra}
        </div>
      )}
      <div className={`p-5 sm:p-6 ${title || extra ? 'pt-3 sm:pt-4' : ''} ${bodyClassName}`}>{children}</div>
    </section>
  )
}

/** Numbers that belong together, read left to right: big value, small label, optional icon. */
export function Facts({ items, className = '' }: {
  items: { label: string; value: ReactNode; icon?: ReactNode; hint?: ReactNode }[]
  className?: string
}) {
  return (
    <dl className={`m-0 flex flex-wrap gap-x-8 gap-y-4 ${className}`}>
      {items.map((f) => (
        <div key={f.label} className="flex flex-col min-w-0">
          <dt className="order-last text-sm text-slate-500">{f.label}</dt>
          <dd className="m-0 num flex items-center gap-1.5 text-2xl font-bold text-slate-800 leading-tight">
            {f.icon}{f.value}{f.hint && <span className="text-sm font-medium text-slate-400">{f.hint}</span>}
          </dd>
        </div>
      ))}
    </dl>
  )
}

/** Empty / error state that always says what to do next. */
export function EmptyState({ title, description, action, art }: {
  title: ReactNode
  description?: ReactNode
  action?: ReactNode
  art?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center text-center gap-2 py-10 px-4">
      {art}
      <div className="text-lg font-bold text-slate-800">{title}</div>
      {description && <p className="text-slate-500 m-0 max-w-[48ch]">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

/**
 * A person: their photo, or their own Prismo dressed as they left it (also when they chose Prismo over the photo).
 * Preset avatars ("assets/…") are mobile app artwork, so the web shows their Prismo for them.
 */
export function UserAvatar({ src, size = 36, mascot }: {
  name?: string | null
  src?: string | null
  size?: number
  mascot?: MascotLook | null
}) {
  const photo = src && !src.startsWith('assets/') && !mascot?.as_avatar ? src : null
  return photo ? (
    <img src={photo} alt="" width={size} height={size} className="rounded-full object-cover shrink-0 bg-slate-100" style={{ width: size, height: size }} />
  ) : (
    <PrismoAvatar look={mascot} size={size} />
  )
}

/**
 * A long list shows its first `limit` entries and a "Xem tất cả (N)" toggle below, never everything at once.
 * `shown` goes into the list; `toggle` goes under it (null when nothing is hidden).
 */
export function useShowMore<T>(items: readonly T[] | undefined, limit: number, label = 'Xem tất cả') {
  const [open, setOpen] = useState(false)
  const list = items ?? []
  const hidden = list.length > limit
  return {
    shown: open || !hidden ? list : list.slice(0, limit),
    open,
    toggle: hidden ? <MoreToggle open={open} count={list.length} label={label} onClick={() => setOpen((o) => !o)} /> : null,
  }
}

export function MoreToggle({ open, count, label = 'Xem tất cả', onClick, className = '' }: {
  open: boolean
  count?: number
  label?: string
  onClick: () => void
  className?: string
}) {
  return (
    <button type="button" onClick={onClick} aria-expanded={open}
      className={`mt-3 mx-auto flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-semibold text-brand-600 hover:bg-brand-50 bg-transparent border-0 cursor-pointer ${className}`}>
      {open ? <>Thu gọn <UpOutlined className="text-xs" /></> : <>{label}{count != null && ` (${count})`} <DownOutlined className="text-xs" /></>}
    </button>
  )
}

/** The same, for lists rendered inside conditionals: `<ShowMore items={x} limit={6}>{(shown) => <ul>…</ul>}</ShowMore>`. */
export function ShowMore<T>({ items, limit, label, children }: {
  items: readonly T[] | undefined
  limit: number
  label?: string
  children: (shown: readonly T[]) => ReactNode
}) {
  const { shown, toggle } = useShowMore(items, limit, label)
  return <>{children(shown)}{toggle}</>
}
