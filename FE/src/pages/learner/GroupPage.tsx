import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, App, Button, Dropdown, Input, Modal, Popconfirm, Tabs, Tag } from 'antd'
import { CrownFilled, MoreOutlined, UserAddOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { communityApi, type ChatMessage, type GroupMember } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { LiveSocket } from '../../lib/ws'
import { PageHeader, Section, ShowMore, UserAvatar } from '../../components/ui'
import { StickerImage, StickerPicker } from '../../components/Stickers'
import ChatVoiceTools from '../../components/ChatVoiceTools'
import MessageActions from '../../components/MessageActions'
import GroupAssignments from './GroupAssignments'

/** Study group: realtime chat (WebSocket), assignments (tab "Bài tập", ?tab=assignments) and members ranked by this
 * week's XP. Leaders add people by their 8-digit ID and promote members to leaders (who also give and mark work). */
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
  const joined = group?.my_status === 'active'
  const isLeader = group?.my_role === 'leader' && joined
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') === 'assignments' ? 'assignments' : 'chat'
  const [adding, setAdding] = useState(false)
  const [newId, setNewId] = useState('')

  useEffect(() => {
    if (!joined) return
    communityApi
      .messages(groupId)
      .then((r) => setMessages(r.results))
      .catch((e) => message.error(errorMessage(e)))
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
      } else if (e.event === 'heart') {
        const h = e.payload as unknown as { id: number; hearts: number[] }
        setMessages((list) => list.map((x) => (x.id === h.id ? { ...x, hearts: h.hearts } : x)))
      } else if (e.event === 'error') {
        message.error(String(e.payload.detail))
      }
    })
    socket.current = s
    return () => {
      off()
      s.close()
    }
  }, [groupId, message, joined])

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const content = text.trim()
    if (!content) return
    setText('')
    const client_id = `${me?.id}-${Date.now()}`
    setMessages((l) => [
      ...l,
      { id: -Date.now(), content, client_id, created_at: new Date().toISOString(), user: { id: me!.id, display_name: me!.display_name } },
    ])
    if (!socket.current?.send({ action: 'send', content, client_id })) {
      try {
        await communityApi.send(groupId, content, client_id)
      } catch (e) {
        message.error(errorMessage(e))
      }
    }
  }

  const sendSticker = async (sticker: string) => {
    const client_id = `${me?.id}-${Date.now()}`
    setMessages((l) => [
      ...l,
      {
        id: -Date.now(),
        kind: 'sticker',
        sticker,
        content: '',
        client_id,
        created_at: new Date().toISOString(),
        user: { id: me!.id, display_name: me!.display_name },
      },
    ])
    if (!socket.current?.send({ action: 'send', kind: 'sticker', sticker, client_id })) {
      try {
        await communityApi.sendSticker(groupId, sticker, client_id)
      } catch (e) {
        message.error(errorMessage(e))
      }
    }
  }

  const heart = async (messageId: number) => {
    try {
      const r = await communityApi.heart(groupId, messageId)
      setMessages((list) => list.map((x) => (x.id === r.id ? { ...x, hearts: r.hearts } : x)))
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  const leave = async () => {
    await communityApi.leave(groupId)
    queryClient.invalidateQueries({ queryKey: ['groups'] })
    navigate('/community')
  }

  const accept = async () => {
    try {
      await communityApi.join(groupId)
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      members.refetch()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const add = async () => {
    try {
      const m = await communityApi.addMember(groupId, newId.trim())
      message.success(m.status === 'active' ? `Đã thêm ${m.user.display_name} vào nhóm` : `Đã gửi lời mời tới ${m.user.display_name}`)
      setNewId('')
      setAdding(false)
      members.refetch()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const manage = async (m: GroupMember, decision: 'promote' | 'demote' | 'remove') => {
    try {
      await communityApi.moderate(groupId, m.id, decision)
      members.refetch()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  const pending = members.data?.filter((m) => m.status === 'pending') ?? []
  const invited = members.data?.filter((m) => m.status === 'invited') ?? []
  const active = (members.data?.filter((m) => m.status === 'active') ?? []).sort((a, b) => b.weekly_xp - a.weekly_xp)

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-4">
      <PageHeader
        back={{ to: '/community', label: 'Cộng đồng' }}
        title={group?.name ?? 'Nhóm học'}
        description={group?.description || undefined}
        actions={
          <Popconfirm
            title="Rời nhóm này?"
            description="Bạn có thể xin vào lại sau."
            okText="Rời nhóm"
            cancelText="Ở lại"
            onConfirm={leave}
          >
            <Button danger>Rời nhóm</Button>
          </Popconfirm>
        }
      />
      {group?.my_status === 'invited' && (
        <Alert
          type="info"
          showIcon
          message={`Bạn được mời vào nhóm ${group.name}`}
          action={
            <span className="flex gap-2">
              <Button type="primary" onClick={accept}>
                Nhận lời
              </Button>
              <Button onClick={leave}>Từ chối</Button>
            </span>
          }
        />
      )}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2 lp-card px-4 pb-4">
          <Tabs
            activeKey={tab}
            onChange={(k) => {
              const p = new URLSearchParams(params)
              if (k === 'chat') {
                p.delete('tab')
                p.delete('a')
                p.delete('s')
              } else p.set('tab', k)
              setParams(p)
            }}
            items={[
              {
                key: 'chat',
                label: 'Trò chuyện',
                children: !joined ? (
                  <div className="text-slate-500 py-6 text-center">Vào nhóm để trò chuyện.</div>
                ) : (
                  <div className="flex flex-col h-[min(520px,calc(100dvh-260px))]">
                    <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1" aria-live="polite">
                      {messages.map((m) => {
                        const mine = m.user?.id === me?.id
                        return (
                          <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                            <MessageActions
                              text={m.kind === 'text' || !m.kind ? m.content : ''}
                              hearts={m.hearts}
                              meId={me?.id}
                              mine={mine}
                              onHeart={m.id > 0 && m.kind !== 'system' ? () => heart(m.id) : undefined}
                            >
                              <div
                                className={
                                  m.kind === 'sticker'
                                    ? ''
                                    : `rounded-2xl px-3 py-2 break-words ${mine ? 'bg-brand-600 text-white rounded-br-md' : 'bg-slate-100 text-slate-800 rounded-bl-md'}`
                                }
                              >
                                {!mine && (
                                  <div className="text-xs font-semibold text-slate-500">
                                    {m.user?.display_name}
                                    {m.user && leaderIds.has(m.user.id) && (
                                      <CrownFilled className="text-amber-500 ml-1" aria-label="trưởng nhóm" />
                                    )}
                                  </div>
                                )}
                                {m.kind === 'sticker' && m.sticker ? <StickerImage code={m.sticker} size={112} /> : <div>{m.content}</div>}
                              </div>
                            </MessageActions>
                          </div>
                        )
                      })}
                      <div ref={bottom} />
                    </div>
                    <div className="mt-3 flex flex-col gap-2">
                      <ChatVoiceTools text={text} setText={setText} />
                      <div className="flex gap-2">
                        <Input.Search
                          placeholder="Nhập tin nhắn…"
                          enterButton="Gửi"
                          aria-label="Tin nhắn"
                          value={text}
                          onChange={(e) => setText(e.target.value)}
                          onSearch={send}
                        />
                        <StickerPicker onPick={sendSticker} />
                      </div>
                    </div>
                  </div>
                ),
              },
              {
                key: 'assignments',
                label: 'Bài tập',
                children: joined ? (
                  <GroupAssignments groupId={groupId} isLeader={isLeader} />
                ) : (
                  <div className="text-slate-500 py-6 text-center">Vào nhóm để xem bài tập.</div>
                ),
              },
            ]}
          />
        </div>
        <div className="flex flex-col gap-4">
          {isLeader && (
            <Button icon={<UserAddOutlined />} onClick={() => setAdding(true)}>
              Thêm thành viên
            </Button>
          )}
          <Section title="XP tuần này" extra={<span className="num text-sm text-slate-500">{active.length} thành viên</span>}>
            <ShowMore items={active} limit={10} label="Xem tất cả thành viên">
              {(shown) => (
                <ol className="m-0 p-0 list-none flex flex-col gap-2.5">
                  {shown.map((m, i) => (
                    <li key={m.id} className="flex items-center gap-2.5">
                      <span className="num w-5 text-sm font-bold text-slate-500">{i + 1}</span>
                      <UserAvatar name={m.user.display_name} src={m.user.avatar} mascot={m.user.mascot} size={30} />
                      <span className="flex-1 min-w-0 truncate text-slate-800">
                        {m.user.display_name}
                        {m.role === 'leader' && <CrownFilled className="text-amber-500 ml-1" aria-label="trưởng nhóm" />}
                      </span>
                      <span className="num text-sm font-semibold text-slate-600">{m.weekly_xp} XP</span>
                      {isLeader && m.user.id !== me?.id && (
                        <Dropdown
                          trigger={['click']}
                          menu={{
                            items: [
                              m.role === 'leader'
                                ? { key: 'demote', label: 'Bỏ quyền trưởng nhóm' }
                                : { key: 'promote', label: 'Cho làm trưởng nhóm (giao, chấm bài)' },
                              { key: 'remove', danger: true, label: 'Xoá khỏi nhóm', disabled: m.role === 'leader' },
                            ],
                            onClick: ({ key }) => manage(m, key as 'promote' | 'demote' | 'remove'),
                          }}
                        >
                          <Button size="small" type="text" icon={<MoreOutlined />} aria-label={`Quản lý ${m.user.display_name}`} />
                        </Dropdown>
                      )}
                    </li>
                  ))}
                </ol>
              )}
            </ShowMore>
          </Section>
          {isLeader && invited.length > 0 && (
            <Section title="Đã mời, chờ nhận lời">
              {invited.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-1">
                  <span>
                    {m.user.display_name} <Tag className="ml-1">#{m.user.public_id}</Tag>
                  </span>
                  <Button size="small" type="text" onClick={() => manage(m, 'remove')}>
                    Huỷ mời
                  </Button>
                </div>
              ))}
            </Section>
          )}
          {pending.length > 0 && (
            <Section title="Yêu cầu tham gia">
              <ShowMore items={pending} limit={5}>
                {(shown) =>
                  shown.map((m) => (
                    <div key={m.id} className="flex items-center justify-between py-1">
                      <div>
                        <div className="font-medium">{m.user.display_name}</div>
                        <div className="text-xs text-slate-500">{m.request_message}</div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          size="small"
                          type="primary"
                          onClick={async () => {
                            await communityApi.moderate(groupId, m.id, 'approve')
                            members.refetch()
                          }}
                        >
                          Duyệt
                        </Button>
                        <Button
                          size="small"
                          onClick={async () => {
                            await communityApi.moderate(groupId, m.id, 'reject')
                            members.refetch()
                          }}
                        >
                          Từ chối
                        </Button>
                      </div>
                    </div>
                  ))
                }
              </ShowMore>
            </Section>
          )}
        </div>
      </div>
      <Modal
        title="Thêm thành viên"
        open={adding}
        onCancel={() => setAdding(false)}
        onOk={add}
        okText="Thêm"
        cancelText="Huỷ"
        okButtonProps={{ disabled: !/^\d{8}$/.test(newId.trim()) }}
      >
        <p className="mt-0 text-slate-600">
          Nhập ID 8 số của người muốn thêm (xem trong Hồ sơ của họ). Bạn bè được thêm ngay, người khác nhận lời mời.
        </p>
        <Input
          value={newId}
          onChange={(e) => setNewId(e.target.value.replace(/\D/g, '').slice(0, 8))}
          placeholder="VD: 12345678"
          inputMode="numeric"
          onPressEnter={add}
          autoFocus
          aria-label="ID 8 số"
        />
      </Modal>
    </div>
  )
}
