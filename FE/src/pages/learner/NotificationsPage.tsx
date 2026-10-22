import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Skeleton } from 'antd'
import { BellOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { notificationApi } from '../../api/app'
import { useUnread } from '../../lib/useUserEvents'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader } from '../../components/ui'

/** Maps server routes (shared with the mobile app) to web pages. */
export function webRoute(route?: string): string | null {
  if (!route) return null
  if (route.startsWith('/community/posts/')) return '/community'
  if (route.startsWith('/support')) return '/support'
  return route
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const list = useQuery({ queryKey: ['notifications'], queryFn: notificationApi.list })
  const open = async (id: number, route?: string) => {
    await notificationApi.read(id).catch(() => undefined)
    useUnread.getState().set(Math.max(0, useUnread.getState().unread - 1))
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
    const to = webRoute(route)
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
          <EmptyState art={<Prismo mood="sleepy" size={88} />} title="Chưa có thông báo" description="Lời nhắc học, phản hồi của giáo viên và tin nhóm sẽ hiện ở đây." />
        ) : (
          <ul className="m-0 p-0 list-none flex flex-col">
            {list.data?.map((n) => (
              <li key={n.id}>
                <button type="button" onClick={() => open(n.id, n.data.route)}
                  className={`w-full text-left flex gap-3 rounded-xl p-3 cursor-pointer transition-colors hover:bg-slate-50 ${n.read ? '' : 'bg-brand-50/70'}`}>
                  <span className={`mt-0.5 h-9 w-9 shrink-0 rounded-full grid place-items-center ${n.read ? 'bg-slate-100 text-slate-500' : 'bg-brand-600 text-white'}`}>
                    <BellOutlined />
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className={`block ${n.read ? 'font-medium text-slate-700' : 'font-bold text-slate-800'}`}>{n.title}</span>
                    {n.body && <span className="block text-sm text-slate-600 mt-0.5">{n.body}</span>}
                    <span className="num block text-xs text-slate-500 mt-1">{dayjs(n.created_at).format('HH:mm · DD/MM/YYYY')}</span>
                  </span>
                  {!n.read && <span className="sr-only">chưa đọc</span>}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
