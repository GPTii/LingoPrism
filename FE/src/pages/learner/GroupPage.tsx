import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Avatar, Button, Card, Input, List, Tag } from 'antd'
import { ArrowLeftOutlined, UserOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { communityApi, type ChatMessage } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { LiveSocket } from '../../lib/ws'

/** Study group: realtime chat (WebSocket) + members ranked by this week's XP. */
export default function GroupPage() {
  const { id } = useParams()
  const groupId = Number(id)
  const me = useAuth((s) => s.user)
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [text, setText] = useState('')
  const socket = useRef<LiveSocket | null>(null)
  const bottom = useRef<HTMLDivElement>(null)
  const members = useQuery({ queryKey: ['members', groupId], queryFn: () => communityApi.members(groupId) })
  const groups = useQuery({ queryKey: ['groups'], queryFn: () => communityApi.groups() })
  const group = groups.data?.find((g) => g.id === groupId)
  const leaderIds = new Set(members.data?.filter((m) => m.role === 'leader').map((m) => m.user.id))

  useEffect(() => {
    communityApi.messages(groupId).then((r) => setMessages(r.results)).catch((e) => message.error(errorMessage(e)))
    const s = new LiveSocket(`/ws/groups/${groupId}/`)
    s.connect()
    const off = s.on((e) => {
      if (e.event === 'message') {
        const m = e.payload as unknown as ChatMessage
        setMessages((list) => {
          const i = list.findIndex((x) => x.client_id && x.client_id === m.client_id)
          if (i >= 0) return list.map((x, j) => (j === i ? m : x))
          return list.some((x) => x.id === m.id) ? list : [...list, m]
        })
      } else if (e.event === 'error') {
        message.error(String(e.payload.detail))
      }
    })
    socket.current = s
    return () => { off(); s.close() }
  }, [groupId, message])

  useEffect(() => bottom.current?.scrollIntoView({ behavior: 'smooth' }), [messages])

  const send = async () => {
    const content = text.trim()
    if (!content) return
    setText('')
    const client_id = `${me?.id}-${Date.now()}`
    setMessages((l) => [...l, { id: -Date.now(), content, client_id, created_at: new Date().toISOString(), user: { id: me!.id, display_name: me!.display_name } }])
    if (!socket.current?.send({ action: 'send', content, client_id })) {
      try { await communityApi.send(groupId, content, client_id) } catch (e) { message.error(errorMessage(e)) }
    }
  }

  const leave = async () => {
    await communityApi.leave(groupId)
    queryClient.invalidateQueries({ queryKey: ['groups'] })
    navigate('/community')
  }

  const pending = members.data?.filter((m) => m.status === 'pending') ?? []
  const active = (members.data?.filter((m) => m.status === 'active') ?? []).sort((a, b) => b.weekly_xp - a.weekly_xp)

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-4">
      <Link to="/community" className="text-slate-500"><ArrowLeftOutlined /> Cộng đồng</Link>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold m-0">{group?.name ?? 'Nhóm học'}</h1>
        <Button danger onClick={leave}>Rời nhóm</Button>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="md:col-span-2 !rounded-2xl" title="Trò chuyện" styles={{ body: { display: 'flex', flexDirection: 'column', height: 520 } }}>
          <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
            {messages.map((m) => {
              const mine = m.user?.id === me?.id
              return (
                <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] rounded-2xl px-3 py-2 ${mine ? 'bg-brand-600 text-white' : 'bg-slate-100'}`}>
                    {!mine && <div className="text-xs font-semibold opacity-70">{m.user?.display_name}{m.user && leaderIds.has(m.user.id) && ' 👑'}</div>}
                    <div>{m.kind === 'sticker' ? `[sticker ${m.sticker}]` : m.content}</div>
                  </div>
                </div>
              )
            })}
            <div ref={bottom} />
          </div>
          <Input.Search className="mt-3" placeholder="Nhập tin nhắn…" enterButton="Gửi" value={text} onChange={(e) => setText(e.target.value)} onSearch={send} />
        </Card>
        <div className="flex flex-col gap-4">
          <Card className="!rounded-2xl" title={`Thành viên (${active.length})`}>
            <List dataSource={active} renderItem={(m, i) => (
              <List.Item>
                <span className="w-6 font-bold">{i + 1}</span>
                <Avatar size="small" src={m.user.avatar?.startsWith('assets/') ? undefined : m.user.avatar} icon={<UserOutlined />} />
                <span className="flex-1 ml-2">{m.user.display_name} {m.role === 'leader' && <Tag color="gold">Trưởng nhóm</Tag>}</span>
                <span className="text-sm">{m.weekly_xp} XP</span>
              </List.Item>
            )} />
          </Card>
          {pending.length > 0 && (
            <Card className="!rounded-2xl" title="Yêu cầu tham gia">
              {pending.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-1">
                  <div><div className="font-medium">{m.user.display_name}</div><div className="text-xs text-slate-500">{m.request_message}</div></div>
                  <div className="flex gap-1">
                    <Button size="small" type="primary" onClick={async () => { await communityApi.moderate(groupId, m.id, 'approve'); members.refetch() }}>Duyệt</Button>
                    <Button size="small" onClick={async () => { await communityApi.moderate(groupId, m.id, 'reject'); members.refetch() }}>Từ chối</Button>
                  </div>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
