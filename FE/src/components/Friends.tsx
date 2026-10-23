import { useQueryClient } from '@tanstack/react-query'
import { App, Button, Dropdown, Input, Modal } from 'antd'
import { CheckOutlined, CopyOutlined, DownOutlined, UserAddOutlined } from '@ant-design/icons'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { communityApi, type FriendStatus, type Person } from '../api/app'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/store'
import { UserAvatar } from './ui'

/** Everything that shows who is friends with whom is refetched after a change. */
function useRefreshFriends() {
  const queryClient = useQueryClient()
  return () => {
    for (const key of ['friends', 'friend-requests', 'people-search', 'profile', 'notifications']) {
      queryClient.invalidateQueries({ queryKey: [key] })
    }
  }
}

/**
 * The one friend button, in its four states: "Kết bạn" (asks for a short hello first), "Đã gửi lời mời" (can be
 * cancelled), "Đồng ý" / "Từ chối" when they asked me, and "Bạn bè" (can be ended).
 */
export function FriendButton({ userId, name, status, requestId, onChange, size = 'middle' }: {
  userId: number
  name: string
  status: FriendStatus
  requestId: number | null
  onChange?: (status: FriendStatus) => void
  size?: 'small' | 'middle' | 'large'
}) {
  const { message, modal } = App.useApp()
  const refresh = useRefreshFriends()
  const me = useAuth((s) => s.user)
  const [busy, setBusy] = useState(false)
  const [asking, setAsking] = useState(false)
  const [hello, setHello] = useState('')

  const run = async (work: () => Promise<FriendStatus>, done?: string) => {
    setBusy(true)
    try {
      const next = await work()
      onChange?.(next)
      refresh()
      if (done) message.success(done)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  const send = () => run(async () => {
    const r = await communityApi.addFriend(userId, hello.trim())
    setAsking(false)
    return r.friend_status
  }, `Đã gửi lời mời kết bạn tới ${name}`)
  const remove = (done: string) => run(async () => { await communityApi.removeFriend(userId); return 'none' }, done)
  const answer = (decision: 'accept' | 'decline') => run(async () => {
    const r = requestId ? await communityApi.answerFriend(requestId, decision) : await communityApi.addFriend(userId)
    return r.friend_status
  }, decision === 'accept' ? `Bạn và ${name} đã là bạn bè` : undefined)

  if (status === 'incoming') {
    return (
      <span className="inline-flex gap-2">
        <Button size={size} type="primary" loading={busy} onClick={() => answer('accept')}>Đồng ý kết bạn</Button>
        <Button size={size} disabled={busy} onClick={() => answer('decline')}>Từ chối</Button>
      </span>
    )
  }
  if (status === 'outgoing') {
    return (
      <Dropdown trigger={['click']} menu={{ items: [{ key: 'cancel', label: 'Huỷ lời mời', danger: true, onClick: () => remove('Đã huỷ lời mời') }] }}>
        <Button size={size} loading={busy}>Đã gửi lời mời <DownOutlined className="text-[10px]" /></Button>
      </Dropdown>
    )
  }
  if (status === 'friends') {
    return (
      <Dropdown trigger={['click']} menu={{
        items: [{
          key: 'unfriend', label: 'Huỷ kết bạn', danger: true,
          onClick: () => modal.confirm({
            title: `Huỷ kết bạn với ${name}?`, content: 'Hai bạn vẫn có thể kết bạn lại sau.',
            okText: 'Huỷ kết bạn', okButtonProps: { danger: true }, cancelText: 'Không', onOk: () => remove(`Đã huỷ kết bạn với ${name}`),
          }),
        }],
      }}>
        <Button size={size} loading={busy} icon={<CheckOutlined />}>Bạn bè <DownOutlined className="text-[10px]" /></Button>
      </Dropdown>
    )
  }
  return (
    <>
      <Button size={size} type="primary" icon={<UserAddOutlined />} loading={busy}
        onClick={() => { setHello(`Chào ${name}, mình là ${me?.display_name ?? ''}. Kết bạn cùng học nhé!`); setAsking(true) }}>
        Kết bạn
      </Button>
      <Modal open={asking} title={`Kết bạn với ${name}`} okText="Gửi lời mời" cancelText="Huỷ" confirmLoading={busy}
        onOk={send} onCancel={() => setAsking(false)}>
        <p className="text-slate-600 mt-0">Lời chào này sẽ gửi kèm thông báo tới {name}.</p>
        <Input.TextArea value={hello} onChange={(e) => setHello(e.target.value)} maxLength={200} showCount autoSize={{ minRows: 2, maxRows: 5 }}
          aria-label="Lời chào kèm lời mời" />
      </Modal>
    </>
  )
}

/** Copies an 8-digit ID; falls back to showing it when the browser blocks the clipboard. */
export function CopyIdButton({ id, label, size = 'middle' }: { id: string; label?: string; size?: 'small' | 'middle' | 'large' }) {
  const { message } = App.useApp()
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(id)
      message.success('Đã sao chép ID')
    } catch {
      message.info(`ID: ${id}`)
    }
  }
  return (
    <Button size={size} type={label ? 'default' : 'text'} icon={<CopyOutlined />} onClick={copy}
      aria-label="Sao chép ID" title="Sao chép ID">
      {label}
    </Button>
  )
}

/** "ID của tôi": the 8 digits friends search for, with a copy button. */
export function MyIdCard({ className = '' }: { className?: string }) {
  const id = useAuth((s) => s.user?.public_id)
  if (!id) return null
  return (
    <div className={`lp-card px-4 py-3 flex items-center gap-3 ${className}`}>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-slate-500">ID của tôi</div>
        <div className="num text-2xl font-extrabold tracking-[0.12em] text-slate-900">{id}</div>
      </div>
      <span className="ml-auto"><CopyIdButton id={id} label="Sao chép" /></span>
    </div>
  )
}

/** One learner in a list, with the friend button on the right. */
export function PersonRow({ person, extra, onChange }: { person: Person; extra?: ReactNode; onChange?: (s: FriendStatus) => void }) {
  return (
    <li className="flex items-center gap-3 py-3">
      <Link to={`/community/users/${person.id}`} className="flex items-center gap-3 min-w-0 flex-1">
        <UserAvatar name={person.display_name} src={person.avatar} size={44} />
        <span className="min-w-0">
          <span className="block font-semibold text-slate-800 truncate">{person.display_name}</span>
          <span className="num block text-xs text-slate-500">ID {person.public_id}</span>
          {extra}
        </span>
      </Link>
      <FriendButton userId={person.id} name={person.display_name} status={person.friend_status} requestId={person.friend_request_id}
        onChange={onChange} size="small" />
    </li>
  )
}
