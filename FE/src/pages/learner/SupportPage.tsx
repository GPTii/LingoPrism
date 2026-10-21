import { App, Card, Input, Spin } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { communityApi, type ChatMessage } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { LiveSocket } from '../../lib/ws'

/** Chat used by learners (their own conversation) and staff (any conversation id from the admin inbox). */
export function SupportChatBox({ conversationId, title }: { conversationId: number; title?: string }) {
  const me = useAuth((s) => s.user)
  const { message } = App.useApp()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [text, setText] = useState('')
  const [typing, setTyping] = useState(false)
  const socket = useRef<LiveSocket | null>(null)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    communityApi.supportMessages(conversationId).then(setMessages).catch((e) => message.error(errorMessage(e)))
    const s = new LiveSocket(`/ws/support/${conversationId}/`)
    s.connect()
    let t: number | undefined
    const off = s.on((e) => {
      if (e.event === 'message') {
        const m = e.payload as unknown as ChatMessage
        setMessages((l) => {
          const i = l.findIndex((x) => x.client_id && x.client_id === m.client_id)
          if (i >= 0) return l.map((x, j) => (j === i ? m : x))
          return l.some((x) => x.id === m.id) ? l : [...l, m]
        })
        if (m.sender?.id !== me?.id) s.send({ action: 'read' })
      } else if (e.event === 'read') {
        const ids = new Set(e.payload.ids as number[])
        setMessages((l) => l.map((x) => (ids.has(x.id) ? { ...x, read_at: String(e.payload.read_at) } : x)))
      } else if (e.event === 'typing' && e.payload.user !== me?.id) {
        setTyping(true)
        window.clearTimeout(t)
        t = window.setTimeout(() => setTyping(false), 3000)
      }
    })
    socket.current = s
    return () => { off(); s.close() }
  }, [conversationId, me?.id, message])

  useEffect(() => bottom.current?.scrollIntoView({ behavior: 'smooth' }), [messages])

  const send = async () => {
    const content = text.trim()
    if (!content) return
    setText('')
    const client_id = `${me?.id}-${Date.now()}`
    setMessages((l) => [...l, { id: -Date.now(), content, client_id, created_at: new Date().toISOString(), sender: { id: me!.id, display_name: me!.display_name, is_staff: false } }])
    if (!socket.current?.send({ action: 'send', content, client_id })) {
      try { await communityApi.sendSupport(conversationId, content, client_id) } catch (e) { message.error(errorMessage(e)) }
    }
  }

  return (
    <Card title={title ?? 'Hỏi giáo viên'} className="!rounded-2xl" styles={{ body: { display: 'flex', flexDirection: 'column', height: 'min(520px, calc(100dvh - 180px))' } }}>
      <div className="flex-1 overflow-y-auto flex flex-col gap-2">
        {messages.map((m) => {
          const mine = m.sender?.id === me?.id
          return (
            <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-2xl px-3 py-2 ${mine ? 'bg-brand-600 text-white' : 'bg-slate-100'}`}>
                {!mine && <div className="text-xs font-semibold opacity-70">{m.sender?.display_name}{m.sender?.is_staff && ' · giáo viên'}</div>}
                <div>{m.content}</div>
                {mine && <div className="text-[10px] opacity-70 text-right">{m.id < 0 ? 'Đang gửi…' : m.read_at ? 'Đã xem' : 'Đã gửi'}</div>}
              </div>
            </div>
          )
        })}
        <div ref={bottom} />
      </div>
      {typing && <div className="text-xs text-slate-400">Đang nhập…</div>}
      <Input.Search className="mt-2" placeholder="Nhập tin nhắn…" enterButton="Gửi" value={text}
        onChange={(e) => { setText(e.target.value); socket.current?.send({ action: 'typing' }) }} onSearch={send} />
    </Card>
  )
}

export default function SupportPage() {
  const { message } = App.useApp()
  const [id, setId] = useState<number | null>(null)
  useEffect(() => { communityApi.openSupport().then((c) => setId(c.id)).catch((e) => message.error(errorMessage(e))) }, [message])
  return (
    <div className="max-w-3xl mx-auto">
      {id ? <SupportChatBox conversationId={id} /> : <Spin />}
    </div>
  )
}
