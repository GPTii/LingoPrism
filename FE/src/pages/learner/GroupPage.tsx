import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Input, Popconfirm } from 'antd'
import { CrownFilled } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { communityApi, type ChatMessage } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { LiveSocket } from '../../lib/ws'
import { PageHeader, Section, ShowMore, UserAvatar } from '../../components/ui'
import { StickerImage, StickerPicker } from '../../components/Stickers'

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

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

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

  const sendSticker = async (sticker: string) => {
    const client_id = `${me?.id}-${Date.now()}`
    setMessages((l) => [...l, { id: -Date.now(), kind: 'sticker', sticker, content: '', client_id, created_at: new Date().toISOString(),
      user: { id: me!.id, display_name: me!.display_name } }])
    if (!socket.current?.send({ action: 'send', kind: 'sticker', sticker, client_id })) {
      try { await communityApi.sendSticker(groupId, sticker, client_id) } catch (e) { message.error(errorMessage(e)) }
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
      <PageHeader back={{ to: '/community', label: 'Cộng đồng' }} title={group?.name ?? 'Nhóm học'} description={group?.description || undefined}
        actions={
          <Popconfirm title="Rời nhóm này?" description="Bạn có thể xin vào lại sau." okText="Rời nhóm" cancelText="Ở lại" onConfirm={leave}>
            <Button danger>Rời nhóm</Button>
          </Popconfirm>
        } />
      <div className="grid md:grid-cols-3 gap-4">
        <Section title="Trò chuyện" className="md:col-span-2" bodyClassName="flex flex-col h-[min(520px,calc(100dvh-200px))]">
          <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1" aria-live="polite">
            {messages.map((m) => {
              const mine = m.user?.id === me?.id
              return (
                <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                  <div className={m.kind === 'sticker' ? 'max-w-[75%]'
                    : `max-w-[75%] rounded-2xl px-3 py-2 ${mine ? 'bg-brand-600 text-white rounded-br-md' : 'bg-slate-100 text-slate-800 rounded-bl-md'}`}>
                    {!mine && <div className="text-xs font-semibold text-slate-500">{m.user?.display_name}{m.user && leaderIds.has(m.user.id) && <CrownFilled className="text-amber-500 ml-1" aria-label="trưởng nhóm" />}</div>}
                    {m.kind === 'sticker' && m.sticker ? <StickerImage code={m.sticker} size={112} /> : <div>{m.content}</div>}
                  </div>
                </div>
              )
            })}
            <div ref={bottom} />
          </div>
          <div className="mt-3 flex gap-2">
            <Input.Search placeholder="Nhập tin nhắn…" enterButton="Gửi" aria-label="Tin nhắn" value={text} onChange={(e) => setText(e.target.value)} onSearch={send} />
            <StickerPicker onPick={sendSticker} />
          </div>
        </Section>
        <div className="flex flex-col gap-4">
          <Section title="XP tuần này" extra={<span className="num text-sm text-slate-500">{active.length} thành viên</span>}>
            <ShowMore items={active} limit={10} label="Xem tất cả thành viên">{(shown) => (
            <ol className="m-0 p-0 list-none flex flex-col gap-2.5">
              {shown.map((m, i) => (
                <li key={m.id} className="flex items-center gap-2.5">
                  <span className="num w-5 text-sm font-bold text-slate-500">{i + 1}</span>
                  <UserAvatar name={m.user.display_name} src={m.user.avatar} size={30} />
                  <span className="flex-1 min-w-0 truncate text-slate-800">
                    {m.user.display_name}{m.role === 'leader' && <CrownFilled className="text-amber-500 ml-1" aria-label="trưởng nhóm" />}
                  </span>
                  <span className="num text-sm font-semibold text-slate-600">{m.weekly_xp} XP</span>
                </li>
              ))}
            </ol>
            )}</ShowMore>
          </Section>
          {pending.length > 0 && (
            <Section title="Yêu cầu tham gia">
              <ShowMore items={pending} limit={5}>{(shown) => shown.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-1">
                  <div><div className="font-medium">{m.user.display_name}</div><div className="text-xs text-slate-500">{m.request_message}</div></div>
                  <div className="flex gap-1">
                    <Button size="small" type="primary" onClick={async () => { await communityApi.moderate(groupId, m.id, 'approve'); members.refetch() }}>Duyệt</Button>
                    <Button size="small" onClick={async () => { await communityApi.moderate(groupId, m.id, 'reject'); members.refetch() }}>Từ chối</Button>
                  </div>
                </div>
              ))}</ShowMore>
            </Section>
          )}
        </div>
      </div>
    </div>
  )
}
