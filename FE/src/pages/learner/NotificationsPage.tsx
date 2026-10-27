import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Checkbox, Segmented, Select, Skeleton } from 'antd'
import { CheckSquareOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { communityApi, notificationApi, type AppNotification } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useUnread } from '../../lib/useUserEvents'
import { Prismo } from '../../components/brand/Brand'
import { AppIcon, type AppIconName } from '../../components/brand/AppIcon'
import { rewardUrl } from '../../components/Stickers'
import { EmptyState, PageHeader, ShowMore } from '../../components/ui'
import { DateRangeFilter, dateParams, SelectionBar, useBulkDelete, usePicking, type DateRange } from '../../components/DataTools'

/** Maps server routes (shared with the mobile app) to web pages. */
export function webRoute(route?: string): string | null {
  if (!route) return null
  if (route.startsWith('/support')) return '/support'
  return route
}

const KIND_ICON: Record<string, AppIconName> = {
  friend_request: 'community', friend_accept: 'community', follow: 'profile', group_request: 'group', group: 'group',
  like: 'medal', comment: 'chat', message: 'mail', achievement: 'trophy', league: 'podium', xp_milestone: 'chart',
  reminder: 'calendar', exam: 'exam', location: 'pin', broadcast: 'bell', system: 'bell',
}

/** Accept / decline a friend request, or approve / refuse someone asking into my group, without leaving the list. */
function Answer({ n, onDone }: { n: AppNotification; onDone: () => void }) {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [busy, setBusy] = useState<string | null>(null)
  const { action, request_id, group_id, member_id } = n.data
  if (n.action_state === 'accepted') {
    return <span className="text-sm font-semibold text-emerald-700">{action === 'friend_request' ? 'Đã là bạn bè' : 'Đã duyệt vào nhóm'}</span>
  }
  if (n.action_state === 'gone') {
    return <span className="text-sm text-slate-500">{action === 'friend_request' ? 'Lời mời không còn' : 'Yêu cầu đã được xử lý'}</span>
  }
  const run = async (yes: boolean) => {
    setBusy(yes ? 'yes' : 'no')
    try {
      if (action === 'friend_request' && request_id) {
        await communityApi.answerFriend(request_id, yes ? 'accept' : 'decline')
        message.success(yes ? 'Hai bạn đã là bạn bè' : 'Đã từ chối lời mời')
        queryClient.invalidateQueries({ queryKey: ['friends'] })
        queryClient.invalidateQueries({ queryKey: ['friend-requests'] })
      } else if (action === 'group_request' && group_id && member_id) {
        await communityApi.moderate(group_id, member_id, yes ? 'approve' : 'reject')
        message.success(yes ? 'Đã duyệt vào nhóm' : 'Đã từ chối yêu cầu')
        queryClient.invalidateQueries({ queryKey: ['members', group_id] })
      }
      if (!n.read) {
        await notificationApi.read(n.id).catch(() => undefined)
        useUnread.getState().set(Math.max(0, useUnread.getState().unread - 1))
      }
      onDone()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }
  return (
    <span className="flex gap-2">
      <Button type="primary" size="small" loading={busy === 'yes'} disabled={!!busy} onClick={() => run(true)}>
        {action === 'friend_request' ? 'Đồng ý' : 'Duyệt'}
      </Button>
      <Button size="small" loading={busy === 'no'} disabled={!!busy} onClick={() => run(false)}>Từ chối</Button>
    </span>
  )
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [group, setGroup] = useState('all')
  const [read, setRead] = useState<string | undefined>()
  const [received, setReceived] = useState<DateRange>(null)
  const filters = { group: group === 'all' ? undefined : group, read, ...dateParams(received) }
  const filtering = Object.values(filters).some(Boolean)
  const list = useQuery({ queryKey: ['notifications', filters], queryFn: () => notificationApi.list(filters) })
  const picking = usePicking()
  const bulk = useBulkDelete('/notifications/bulk-delete/', async () => {
    picking.stop()
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
    useUnread.getState().set(await notificationApi.unread().catch(() => useUnread.getState().unread))
  })
  const open = async (n: AppNotification) => {
    if (!n.read) {
      await notificationApi.read(n.id).catch(() => undefined)
      useUnread.getState().set(Math.max(0, useUnread.getState().unread - 1))
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    }
    const to = webRoute(n.data.route)
    if (to) navigate(to)
  }
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4">
      <PageHeader title="Thông báo"
        actions={!picking.active && (
          <div className="flex flex-wrap gap-2">
            {list.data?.some((n) => !n.read) && (
              <Button onClick={async () => { await notificationApi.readAll(); useUnread.getState().set(0); list.refetch() }}>Đánh dấu tất cả đã đọc</Button>
            )}
            {!!list.data?.length && <Button icon={<CheckSquareOutlined />} onClick={picking.start}>Chọn nhiều</Button>}
          </div>
        )} />
      <div className="flex flex-wrap gap-2 -mt-2">
        <Segmented value={group} onChange={(v) => setGroup(String(v))} options={[
          { value: 'all', label: 'Tất cả' }, { value: 'social', label: 'Bạn bè & nhóm' }, { value: 'learning', label: 'Học tập' }, { value: 'system', label: 'Hệ thống' },
        ]} />
        <Select allowClear placeholder="Đã đọc?" value={read} onChange={setRead} style={{ width: 130 }}
          options={[{ value: '0', label: 'Chưa đọc' }, { value: '1', label: 'Đã đọc' }]} />
        <DateRangeFilter value={received} onChange={setReceived} placeholder={['Nhận từ ngày', 'đến ngày']} />
      </div>
      <div className="lp-card p-2">
        {list.isLoading ? <div className="p-4"><Skeleton active /></div> : list.data?.length === 0 ? (
          filtering
            ? <EmptyState art={<Prismo mood="think" size={88} />} title="Không có thông báo nào khớp bộ lọc"
                action={<Button onClick={() => { setGroup('all'); setRead(undefined); setReceived(null) }}>Bỏ lọc</Button>} />
            : <EmptyState art={<Prismo mood="sleepy" size={88} />} title="Chưa có thông báo" description="Lời mời kết bạn, yêu cầu vào nhóm, lời nhắc học và tin nhóm sẽ hiện ở đây." />
        ) : (
          <ShowMore items={list.data} limit={picking.active ? 100 : 20} label="Xem thông báo cũ hơn">{(shown) => (
          <ul className="m-0 p-0 list-none flex flex-col">
            {shown.map((n) => (
              <li key={n.id} className={`flex flex-col sm:flex-row gap-2 sm:gap-3 rounded-xl p-3 transition-colors hover:bg-slate-50 ${n.read ? '' : 'bg-brand-50/70'}`}>
                {picking.active && (
                  <Checkbox checked={picking.ids.has(n.id)} onChange={() => picking.toggle(n.id)} className="self-start sm:self-center"
                    aria-label={`Chọn thông báo: ${n.title}`} />
                )}
                <button type="button" onClick={() => (picking.active ? picking.toggle(n.id) : open(n))} className="flex gap-3 flex-1 min-w-0 text-left cursor-pointer">
                  <span className="mt-0.5 h-10 w-10 shrink-0 rounded-full grid place-items-center bg-slate-100">
                    {rewardUrl(n.image) ? <img src={rewardUrl(n.image)!} alt="" width={34} height={34} />
                      : <AppIcon name={KIND_ICON[n.kind] ?? 'bell'} size={26} />}
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className={`block ${n.read ? 'font-medium text-slate-700' : 'font-bold text-slate-800'}`}>{n.title}</span>
                    {n.body && <span className="block text-sm text-slate-600 mt-0.5 whitespace-pre-wrap">{n.data.action ? `“${n.body}”` : n.body}</span>}
                    <span className="num block text-xs text-slate-500 mt-1">{dayjs(n.created_at).format('HH:mm · DD/MM/YYYY')}</span>
                  </span>
                  {!n.read && <span className="sr-only">chưa đọc</span>}
                </button>
                {!picking.active && n.data.action && n.action_state && (
                  <div className="shrink-0 pl-[52px] sm:pl-0 sm:self-center"><Answer n={n} onDone={() => list.refetch()} /></div>
                )}
              </li>
            ))}
          </ul>
          )}</ShowMore>
        )}
      </div>
      {picking.active && (
        <SelectionBar count={picking.ids.size} total={list.data?.length ?? 0} noun="thông báo" busy={bulk.busy}
          onSelectAll={() => picking.selectAll(list.data?.map((n) => n.id) ?? [])} onClear={picking.clear} onDone={picking.stop}
          onDelete={() => bulk.run([...picking.ids], (n) => `${n} thông báo`)} />
      )}
    </div>
  )
}
