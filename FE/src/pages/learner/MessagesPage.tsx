import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Grid, Input, Skeleton } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { messagesApi, type DirectMessage, type DirectThread } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader, UserAvatar } from '../../components/ui'
import { ReportUserButton } from './ReportUser'

const when = (iso: string) => (dayjs(iso).isSame(dayjs(), 'day') ? dayjs(iso).format('HH:mm') : dayjs(iso).format('DD/MM'))

function ThreadList({ threads, active }: { threads: DirectThread[]; active?: number }) {
  if (!threads.length)
    return (
      <EmptyState art={<Prismo mood="happy" size={80} />} title="Chưa có cuộc trò chuyện"
        description="Hai bạn theo dõi nhau là nhắn tin được. Mở hồ sơ một bạn học trong Cộng đồng và bấm “Nhắn tin”." />
    )
  return (
    <ul className="flex flex-col">
      {threads.map((t) => (
        <li key={t.id}>
          <Link to={`/messages/${t.id}`}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 ${t.id === active ? 'bg-brand-50' : 'hover:bg-slate-50'}`}>
            <UserAvatar name={t.other.display_name} src={t.other.avatar} size={40} />
            <span className="min-w-0 flex-1">
              <span className="flex items-baseline justify-between gap-2">
                <span className={`truncate text-slate-800 ${t.unread ? 'font-bold' : 'font-semibold'}`}>{t.other.display_name}</span>
                {t.last_message && <span className="num text-xs text-slate-500 shrink-0">{when(t.last_message.created_at)}</span>}
              </span>
              <span className="flex items-center justify-between gap-2">
                <span className={`truncate text-sm ${t.unread ? 'text-slate-800' : 'text-slate-500'}`}>{t.last_message?.content}</span>
                {t.unread > 0 && <span className="num shrink-0 rounded-full bg-brand-600 px-1.5 text-xs font-bold text-white">{t.unread}</span>}
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

function Conversation({ id }: { id: number }) {
  const me = useAuth((s) => s.user)
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const thread = useQuery({ queryKey: ['dm-thread', id], queryFn: () => messagesApi.thread(id) })
  const [messages, setMessages] = useState<DirectMessage[] | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [text, setText] = useState('')
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMessages(null)
    messagesApi.list(id).then((r) => {
      setMessages(r.results)
      setHasMore(r.has_more)
      queryClient.invalidateQueries({ queryKey: ['dm-threads'] }) // opening it marked them read
    }).catch((e) => message.error(errorMessage(e)))
  }, [id, message, queryClient])

  // realtime: new messages (also the ones I sent from another tab) and "seen"
  useEffect(() => {
    const on = (ev: Event) => {
      const { event, payload } = (ev as CustomEvent).detail as { event: string; payload: DirectMessage & { thread: number } }
      if (payload.thread !== id) return
      if (event === 'dm_read') {
        setMessages((l) => l?.map((m) => (m.sender === me?.id && !m.read_at ? { ...m, read_at: new Date().toISOString() } : m)) ?? l)
        return
      }
      setMessages((l) => {
        if (!l) return l
        const i = l.findIndex((m) => m.client_id && m.client_id === payload.client_id)
        if (i >= 0) return l.map((m, j) => (j === i ? payload : m))
        return l.some((m) => m.id === payload.id) ? l : [...l, payload]
      })
      if (payload.sender !== me?.id) messagesApi.read(id).catch(() => undefined)
    }
    window.addEventListener('lingoprism:dm', on)
    return () => window.removeEventListener('lingoprism:dm', on)
  }, [id, me?.id])

  useEffect(() => { bottom.current?.scrollIntoView({ block: 'end' }) }, [messages?.length])

  const older = async () => {
    if (!messages?.length) return
    const r = await messagesApi.list(id, messages[0].id)
    setMessages((l) => [...r.results, ...(l ?? [])])
    setHasMore(r.has_more)
  }

  const send = async () => {
    const content = text.trim()
    if (!content || !me) return
    setText('')
    const client_id = `${me.id}-${Date.now()}`
    setMessages((l) => [...(l ?? []), { id: -Date.now(), thread: id, sender: me.id, content, client_id, read_at: null, created_at: new Date().toISOString() }])
    try {
      const m = await messagesApi.send(id, content, client_id)
      setMessages((l) => l?.map((x) => (x.client_id === client_id ? m : x)) ?? l)
    } catch (e) {
      setMessages((l) => l?.filter((x) => x.client_id !== client_id) ?? l)
      setText(content)
      message.error(errorMessage(e))
    }
  }

  const t = thread.data
  return (
    <div className="lp-card min-w-0 flex flex-col h-[calc(100dvh-320px)] min-h-[340px] md:h-[min(640px,calc(100dvh-200px))]">
      <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
        {t ? (
          <Link to={`/community/users/${t.other.id}`} className="flex items-center gap-3 min-w-0">
            <UserAvatar name={t.other.display_name} src={t.other.avatar} size={36} />
            <span className="truncate font-bold text-slate-800">{t.other.display_name}</span>
          </Link>
        ) : <Skeleton.Input active size="small" />}
        {t && (
          <span className="ml-auto">
            <ReportUserButton compact userId={t.other.id} name={t.other.display_name} threadId={t.id}
              onDone={() => { queryClient.invalidateQueries({ queryKey: ['dm-threads'] }); thread.refetch() }} />
          </span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-2 p-4" aria-live="polite">
        {messages === null && <Skeleton active />}
        {hasMore && <Button size="small" className="self-center" onClick={older}>Tin cũ hơn</Button>}
        {messages?.length === 0 && (
          <div className="m-auto text-center text-slate-500 max-w-[36ch]">Gửi lời chào đầu tiên. Thử viết một câu bằng ngôn ngữ hai bạn đang học!</div>
        )}
        {messages?.map((m, i) => {
          const mine = m.sender === me?.id
          const lastMine = mine && !messages.slice(i + 1).some((x) => x.sender === me?.id)
          return (
            <div key={m.id} className={`flex flex-col ${mine ? 'items-end' : 'items-start'}`}>
              <div title={dayjs(m.created_at).format('HH:mm DD/MM/YYYY')}
                className={`max-w-[75%] whitespace-pre-wrap break-words rounded-2xl px-3 py-2 ${mine ? 'bg-brand-600 text-white rounded-br-md' : 'bg-slate-100 text-slate-800 rounded-bl-md'}`}>
                {m.content}
              </div>
              {lastMine && <span className="text-[11px] text-slate-500 mt-0.5">{m.id < 0 ? 'Đang gửi…' : m.read_at ? 'Đã xem' : 'Đã gửi'}</span>}
            </div>
          )
        })}
        <div ref={bottom} />
      </div>
      <div className="border-t border-slate-100 p-3">
        {t && !t.can_message ? (
          <div className="text-center text-sm text-slate-500">Hai bạn không còn theo dõi nhau nên không gửi thêm tin được.</div>
        ) : (
          <Input.Search placeholder="Nhập tin nhắn…" enterButton="Gửi" aria-label="Tin nhắn" maxLength={1000}
            value={text} onChange={(e) => setText(e.target.value)} onSearch={send} />
        )}
      </div>
    </div>
  )
}

/** Private messages between two learners who follow each other. */
export default function MessagesPage() {
  const { id } = useParams()
  const active = id ? Number(id) : undefined
  const isKid = useAuth((s) => s.user?.learner_type === 'kid')
  const wide = Grid.useBreakpoint().md
  const threads = useQuery({ queryKey: ['dm-threads'], queryFn: messagesApi.threads, enabled: !isKid })
  if (isKid)
    return (
      <div className="max-w-3xl mx-auto lp-card p-6">
        <EmptyState art={<Prismo mood="think" size={80} />} title="Tin nhắn dành cho người lớn"
          description="Bạn vẫn có thể hỏi giáo viên trong mục Hỏi giáo viên." />
      </div>
    )
  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <PageHeader title="Tin nhắn" back={active && !wide ? { to: '/messages', label: 'Tất cả tin nhắn' } : undefined}
        description="Nhắn riêng với bạn học đã theo dõi nhau." />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-[300px_minmax(0,1fr)]">
        {(wide || !active) && (
          <div className="lp-card p-2 md:h-[min(640px,calc(100dvh-200px))] md:overflow-y-auto">
            {threads.isLoading ? <Skeleton active avatar className="p-3" /> : <ThreadList threads={threads.data ?? []} active={active} />}
          </div>
        )}
        {active ? <Conversation id={active} /> : wide && (
          <div className="lp-card grid place-items-center p-6 text-slate-500">Chọn một cuộc trò chuyện</div>
        )}
      </div>
    </div>
  )
}

/** "Nhắn tin" on a member's profile: opens (or creates) the conversation. */
export function MessageButton({ userId }: { userId: number }) {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [busy, setBusy] = useState(false)
  return (
    <Button size="large" loading={busy} onClick={async () => {
      setBusy(true)
      try {
        navigate(`/messages/${(await messagesApi.open(userId)).id}`)
      } catch (e) {
        message.error(errorMessage(e))
      } finally {
        setBusy(false)
      }
    }}>Nhắn tin</Button>
  )
}
