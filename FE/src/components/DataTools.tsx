import { App, Button, Checkbox, DatePicker, Popconfirm } from 'antd'
import { CheckSquareOutlined, CloseOutlined, DeleteOutlined } from '@ant-design/icons'
import type { TableRowSelection } from 'antd/es/table/interface'
import dayjs, { type Dayjs } from 'dayjs'
import { useEffect, useState, type ReactNode } from 'react'
import { api, errorMessage } from '../api/client'

/** Shared by every long list (admin tables and the learner's own lists): pick rows with ticks, delete them in one go
 * (`POST <list>/bulk-delete/`), and narrow the list by the day things were created. */

export type DateRange = [Dayjs, Dayjs] | null

/** ?created_from=&created_to= (both days included) – understood by every list whose rows have a creation date */
export const dateParams = (range: DateRange) =>
  range ? { created_from: range[0].format('YYYY-MM-DD'), created_to: range[1].format('YYYY-MM-DD') } : {}

const PRESETS: { label: string; value: [Dayjs, Dayjs] }[] = [
  { label: 'Hôm nay', value: [dayjs().startOf('day'), dayjs()] },
  { label: '7 ngày qua', value: [dayjs().subtract(6, 'day'), dayjs()] },
  { label: '30 ngày qua', value: [dayjs().subtract(29, 'day'), dayjs()] },
  { label: 'Tháng này', value: [dayjs().startOf('month'), dayjs()] },
  { label: 'Tháng trước', value: [dayjs().subtract(1, 'month').startOf('month'), dayjs().subtract(1, 'month').endOf('month')] },
  { label: 'Năm nay', value: [dayjs().startOf('year'), dayjs()] },
]

export function DateRangeFilter({ value, onChange, placeholder = ['Từ ngày', 'Đến ngày'], size }: {
  value: DateRange
  onChange: (range: DateRange) => void
  placeholder?: [string, string]
  size?: 'small' | 'middle' | 'large'
}) {
  return (
    <DatePicker.RangePicker value={value} onChange={(v) => onChange(v?.[0] && v[1] ? [v[0], v[1]] : null)}
      presets={PRESETS} format="DD/MM/YYYY" allowClear placeholder={placeholder} size={size}
      disabledDate={(d) => d.isAfter(dayjs(), 'day')} style={{ width: 250 }} aria-label="Lọc theo ngày tạo" />
  )
}

/** Ticked rows of an antd Table. Kept across pages; dropped when `resetOn` changes (a new filter shows other rows,
 * and nothing hidden should be deleted by surprise). */
export function useSelection<T>(resetOn: unknown[] = []) {
  const [keys, setKeys] = useState<number[]>([])
  const resetKey = JSON.stringify(resetOn)
  useEffect(() => setKeys([]), [resetKey])
  const rowSelection: TableRowSelection<T> = {
    selectedRowKeys: keys,
    onChange: (k) => setKeys(k as number[]),
    preserveSelectedRowKeys: true,
  }
  return { keys, setKeys, clear: () => setKeys([]), rowSelection }
}

export interface BulkResult {
  deleted: number
  skipped: { id: number; reason: string }[]
  not_found: number
}

/** Runs a bulk delete and tells the user what happened, including the rows kept back and why. */
export function useBulkDelete(url: string, onDone: () => void) {
  const { message, modal } = App.useApp()
  const [busy, setBusy] = useState(false)
  const run = async (ids: number[], label: (n: number) => string) => {
    setBusy(true)
    try {
      const r = (await api.post<BulkResult>(url, { ids })).data
      if (r.deleted) message.success(`Đã xoá ${label(r.deleted)}`)
      if (r.skipped.length) {
        const reasons = Object.entries(r.skipped.reduce<Record<string, number>>((acc, s) => ({ ...acc, [s.reason]: (acc[s.reason] ?? 0) + 1 }), {}))
        modal.warning({
          title: `${r.skipped.length} mục không xoá được`,
          content: <ul className="m-0 pl-5">{reasons.map(([reason, n]) => <li key={reason}>{n > 1 ? `${n} mục: ` : ''}{reason}</li>)}</ul>,
          okText: 'Đã hiểu',
        })
      }
      onDone()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return { run, busy }
}

/** "Đã chọn N · Bỏ chọn · Xoá N …" above an admin table; empty when nothing is ticked. */
export function BulkDeleteBar({ count, noun, busy, onDelete, onClear, warning }: {
  count: number
  /** "người dùng", "từ", "ảnh" … */
  noun: string
  busy?: boolean
  onDelete: () => void
  onClear: () => void
  /** what else goes with them, shown in the confirmation */
  warning?: string
}) {
  if (!count) return null
  return (
    <div role="status" className="flex flex-wrap items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 mb-3">
      <span className="font-semibold">Đã chọn <span className="num">{count}</span> {noun}</span>
      <Button size="small" type="text" icon={<CloseOutlined />} onClick={onClear}>Bỏ chọn</Button>
      <Popconfirm title={`Xoá ${count} ${noun}?`} description={warning ?? 'Không thể hoàn tác.'}
        okText="Xoá" okButtonProps={{ danger: true }} cancelText="Huỷ" onConfirm={onDelete}>
        <Button size="small" danger type="primary" icon={<DeleteOutlined />} loading={busy} className="ml-auto">
          Xoá {count} {noun}
        </Button>
      </Popconfirm>
    </div>
  )
}

/** Table pagination with a page-size choice, so up to 100 rows can be ticked on one page. */
export function pagination(page: number, total: number | undefined, pageSize: number, onChange: (page: number, size: number) => void) {
  return {
    current: page, total, pageSize, onChange, showSizeChanger: true, pageSizeOptions: [20, 50, 100],
    showTotal: (n: number) => <span className="num">{n} mục</span>,
  }
}

/* ---------- learner lists (cards, not tables) ---------- */

/** A card that can be ticked while the list is in "Chọn nhiều" mode: a tap ticks it instead of opening it. */
export function Selectable({ active, checked, onToggle, label, children }: {
  active: boolean
  checked: boolean
  onToggle: () => void
  /** what the tick box is for, for screen readers */
  label: string
  children: ReactNode
}) {
  if (!active) return <>{children}</>
  return (
    <div className={`relative rounded-2xl break-inside-avoid transition-shadow ${checked ? 'ring-[3px] ring-brand-500' : ''}`}
      onClickCapture={(e) => { e.preventDefault(); e.stopPropagation(); onToggle() }}>
      {/* top right: the top left of a card often holds a badge (level, "đã học xong") */}
      <Checkbox checked={checked} aria-label={label} className="absolute top-2.5 right-2.5 z-20 scale-125 origin-top-right" />
      <div className={checked ? '' : 'opacity-80'}>{children}</div>
    </div>
  )
}

/** The bar that stays at the bottom of the screen while picking cards. */
export function SelectionBar({ count, total, noun, busy, onSelectAll, onClear, onDelete, onDone }: {
  count: number
  /** cards shown right now */
  total: number
  noun: string
  busy?: boolean
  onSelectAll: () => void
  onClear: () => void
  onDelete: () => void
  onDone: () => void
}) {
  return (
    <div className="lp-card sticky bottom-24 md:bottom-4 z-20 flex flex-wrap items-center gap-2 px-4 py-3 shadow-lg">
      <span className="font-semibold">Đã chọn <span className="num">{count}</span> {noun}</span>
      {count < total
        ? <Button size="small" icon={<CheckSquareOutlined />} onClick={onSelectAll}>Chọn tất cả ({total})</Button>
        : <Button size="small" onClick={onClear}>Bỏ chọn</Button>}
      <span className="ml-auto flex gap-2">
        <Popconfirm title={`Xoá ${count} ${noun}?`} description="Không thể hoàn tác." okText="Xoá" okButtonProps={{ danger: true }}
          cancelText="Huỷ" onConfirm={onDelete} disabled={!count}>
          <Button danger type="primary" icon={<DeleteOutlined />} disabled={!count} loading={busy}>Xoá</Button>
        </Popconfirm>
        <Button onClick={onDone}>Xong</Button>
      </span>
    </div>
  )
}

/** "Chọn nhiều" state for a card list: the ticked ids, and leaving the mode clears them. */
export function usePicking() {
  const [active, setActive] = useState(false)
  const [ids, setIds] = useState<Set<number>>(new Set())
  const toggle = (id: number) => setIds((s) => {
    const next = new Set(s)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })
  return {
    active, ids, toggle,
    start: () => setActive(true),
    stop: () => { setActive(false); setIds(new Set()) },
    selectAll: (all: number[]) => setIds(new Set(all)),
    clear: () => setIds(new Set()),
  }
}
