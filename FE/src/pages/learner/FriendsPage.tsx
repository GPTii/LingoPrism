import { useQuery } from '@tanstack/react-query'
import { Input, Segmented, Skeleton } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/vi'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { communityApi } from '../../api/app'
import { Prismo } from '../../components/brand/Brand'
import { MyIdCard, PersonRow } from '../../components/Friends'
import { EmptyState, PageHeader } from '../../components/ui'

dayjs.extend(relativeTime)
dayjs.locale('vi')

type Tab = 'friends' | 'incoming' | 'outgoing' | 'find'

/** Friends: the list, requests waiting for my answer, the ones I sent, and finding people by ID or name. */
export default function FriendsPage() {
  const [params, setParams] = useSearchParams()
  const asked = params.get('tab') as Tab | null
  const tab: Tab = asked && ['friends', 'incoming', 'outgoing', 'find'].includes(asked) ? asked : 'friends'
  const setTab = (t: Tab) => setParams({ tab: t }, { replace: true })
  const [q, setQ] = useState('')
  const [term, setTerm] = useState('')

  const friends = useQuery({ queryKey: ['friends'], queryFn: communityApi.friends })
  const incoming = useQuery({ queryKey: ['friend-requests', 'incoming'], queryFn: () => communityApi.friendRequests('incoming') })
  const outgoing = useQuery({ queryKey: ['friend-requests', 'outgoing'], queryFn: () => communityApi.friendRequests('outgoing'), enabled: tab === 'outgoing' })
  const found = useQuery({ queryKey: ['people-search', term], queryFn: () => communityApi.search(term), enabled: tab === 'find' && term.length >= 2 })

  const waiting = incoming.data?.length ?? 0
  const loading = <div className="p-4"><Skeleton active avatar /></div>

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-5">
      <PageHeader back={{ to: '/community', label: 'Cộng đồng' }} title="Bạn bè"
        description="Kết bạn để nhắn tin, cùng đua XP và xem bài của nhau. Bạn bè tìm bạn bằng ID bên dưới." />
      <MyIdCard />
      <Segmented value={tab} onChange={(v) => setTab(v as Tab)} block options={[
        { value: 'friends', label: `Bạn bè${friends.data?.length ? ` (${friends.data.length})` : ''}` },
        { value: 'incoming', label: `Lời mời${waiting ? ` (${waiting})` : ''}` },
        { value: 'outgoing', label: 'Đã gửi' },
        { value: 'find', label: 'Tìm bạn' },
      ]} />

      {tab === 'find' && (
        <div className="flex flex-col gap-3">
          <Input.Search size="large" placeholder="Nhập ID 8 số hoặc tên bạn học" enterButton="Tìm" allowClear value={q}
            onChange={(e) => setQ(e.target.value)} onSearch={(v) => setTerm(v.trim().replace(/^#/, ''))} aria-label="Tìm bạn theo ID hoặc tên" />
          <div className="lp-card px-4">
            {term.length < 2 ? <p className="text-slate-500 py-4 m-0">Hỏi ID của bạn mình (trong mục Bạn bè hoặc Hồ sơ) rồi nhập vào đây.</p>
              : found.isLoading ? loading : found.data?.length ? (
                <ul className="m-0 p-0 list-none divide-y divide-slate-100">
                  {found.data.map((p) => <PersonRow key={p.id} person={p} />)}
                </ul>
              ) : <EmptyState art={<Prismo mood="think" size={80} />} title="Không tìm thấy ai" description="Kiểm tra lại ID 8 số, hoặc thử tìm theo tên." />}
          </div>
        </div>
      )}

      {tab === 'friends' && (
        <div className="lp-card px-4">
          {friends.isLoading ? loading : friends.data?.length ? (
            <ul className="m-0 p-0 list-none divide-y divide-slate-100">
              {friends.data.map((p) => (
                <PersonRow key={p.id} person={p} extra={p.since && <span className="block text-xs text-slate-500">Bạn bè từ {dayjs(p.since).format('DD/MM/YYYY')}</span>} />
              ))}
            </ul>
          ) : <EmptyState art={<Prismo mood="wow" size={80} />} title="Chưa có bạn bè" description="Vào Tìm bạn, nhập ID hoặc tên để gửi lời mời kết bạn." />}
        </div>
      )}

      {tab === 'incoming' && (
        <div className="lp-card px-4">
          {incoming.isLoading ? loading : incoming.data?.length ? (
            <ul className="m-0 p-0 list-none divide-y divide-slate-100">
              {incoming.data.map((r) => (
                <PersonRow key={r.id} person={r.user} extra={
                  <>
                    {r.message && <span className="block text-sm text-slate-700 mt-1 whitespace-pre-wrap">“{r.message}”</span>}
                    <span className="block text-xs text-slate-500 mt-0.5">{dayjs(r.created_at).fromNow()}</span>
                  </>
                } />
              ))}
            </ul>
          ) : <EmptyState art={<Prismo mood="sleepy" size={80} />} title="Không có lời mời nào" description="Khi ai đó muốn kết bạn, lời mời sẽ hiện ở đây và trong Thông báo." />}
        </div>
      )}

      {tab === 'outgoing' && (
        <div className="lp-card px-4">
          {outgoing.isLoading ? loading : outgoing.data?.length ? (
            <ul className="m-0 p-0 list-none divide-y divide-slate-100">
              {outgoing.data.map((r) => (
                <PersonRow key={r.id} person={r.user} extra={<span className="block text-xs text-slate-500">Gửi {dayjs(r.created_at).fromNow()}</span>} />
              ))}
            </ul>
          ) : <EmptyState art={<Prismo mood="happy" size={80} />} title="Bạn chưa gửi lời mời nào" description="Lời mời đang chờ trả lời sẽ hiện ở đây, bạn có thể huỷ nếu muốn." />}
        </div>
      )}
    </div>
  )
}
