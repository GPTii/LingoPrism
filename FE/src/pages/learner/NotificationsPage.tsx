import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Skeleton } from 'antd'
import dayjs from 'dayjs'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { communityApi, notificationApi, type AppNotification } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useUnread } from '../../lib/useUserEvents'
import { Prismo } from '../../components/brand/Brand'
import { AppIcon, type AppIconName } from '../../components/brand/AppIcon'
import { EmptyState, PageHeader } from '../../components/ui'

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
  const list = useQuery({ queryKey: ['notifications'], queryFn: notificationApi.list })
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
        actions={list.data?.some((n) => !n.read) && (
          <Button onClick={async () => { await notificationApi.readAll(); useUnread.getState().set(0); list.refetch() }}>Đánh dấu tất cả đã đọc</Button>
        )} />
      <div className="lp-card p-2">
        {list.isLoading ? <div className="p-4"><Skeleton active /></div> : list.data?.length === 0 ? (
          <EmptyState art={<Prismo mood="sleepy" size={88} />} title="Chưa có thông báo" description="Lời mời kết bạn, yêu cầu vào nhóm, lời nhắc học và tin nhóm sẽ hiện ở đây." />
        ) : (
          <ul className="m-0 p-0 list-none flex flex-col">
            {list.data?.map((n) => (
              <li key={n.id} className={`flex flex-col sm:flex-row gap-2 sm:gap-3 rounded-xl p-3 transition-colors hover:bg-slate-50 ${n.read ? '' : 'bg-brand-50/70'}`}>
                <button type="button" onClick={() => open(n)} className="flex gap-3 flex-1 min-w-0 text-left cursor-pointer">
                  <span className="mt-0.5 h-10 w-10 shrink-0 rounded-full grid place-items-center bg-slate-100">
                    <AppIcon name={KIND_ICON[n.kind] ?? 'bell'} size={26} />
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className={`block ${n.read ? 'font-medium text-slate-700' : 'font-bold text-slate-800'}`}>{n.title}</span>
                    {n.body && <span className="block text-sm text-slate-600 mt-0.5 whitespace-pre-wrap">{n.data.action ? `“${n.body}”` : n.body}</span>}
                    <span className="num block text-xs text-slate-500 mt-1">{dayjs(n.created_at).format('HH:mm · DD/MM/YYYY')}</span>
                  </span>
                  {!n.read && <span className="sr-only">chưa đọc</span>}
                </button>
                {n.data.action && n.action_state && (
                  <div className="shrink-0 pl-[52px] sm:pl-0 sm:self-center"><Answer n={n} onDone={() => list.refetch()} /></div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
