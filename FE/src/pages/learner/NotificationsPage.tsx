import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Empty, List } from 'antd'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { notificationApi } from '../../api/app'
import { useUnread } from '../../lib/useUserEvents'

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
      <div className="flex flex-wrap justify-between items-center gap-2">
        <h1 className="text-2xl font-bold m-0">Thông báo</h1>
        <Button onClick={async () => { await notificationApi.readAll(); useUnread.getState().set(0); list.refetch() }}>Đánh dấu tất cả đã đọc</Button>
      </div>
      <Card className="!rounded-2xl">
        {list.data?.length === 0 ? <Empty description="Chưa có thông báo" /> : (
          <List loading={list.isLoading} dataSource={list.data} renderItem={(n) => (
            <List.Item className={`cursor-pointer ${n.read ? '' : 'bg-brand-50'}`} onClick={() => open(n.id, n.data.route)}>
              <List.Item.Meta title={n.title} description={<>{n.body}<div className="text-xs text-slate-400">{dayjs(n.created_at).format('HH:mm DD/MM/YYYY')}</div></>} />
            </List.Item>
          )} />
        )}
      </Card>
    </div>
  )
}
