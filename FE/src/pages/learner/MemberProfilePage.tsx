import { useQuery } from '@tanstack/react-query'
import { App, Button, Skeleton } from 'antd'
import { useParams } from 'react-router-dom'
import { communityApi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { StreakIcon, XpIcon } from '../../components/brand/Brand'
import { Facts, PageHeader, Section, UserAvatar } from '../../components/ui'
import { FriendButton } from '../../components/Friends'
import { MessageButton } from './MessagesPage'
import { ReportUserButton } from './ReportUser'

export default function MemberProfilePage() {
  const { id } = useParams()
  const me = useAuth((s) => s.user)
  const { message, modal } = App.useApp()
  const profile = useQuery({ queryKey: ['profile', id], queryFn: () => communityApi.profile(Number(id)) })
  const p = profile.data
  if (!p) return <div className="max-w-3xl mx-auto lp-card p-6"><Skeleton active avatar /></div>
  const toggleBlock = () => {
    const run = async () => {
      try {
        await communityApi.block(p.id, !p.blocked)
        message.success(p.blocked ? `Đã bỏ chặn ${p.display_name}` : `Đã chặn ${p.display_name}`)
        profile.refetch()
      } catch (e) {
        message.error(errorMessage(e))
      }
    }
    if (p.blocked) return run()
    modal.confirm({
      title: `Chặn ${p.display_name}?`,
      content: 'Hai bạn sẽ bỏ theo dõi nhau, không nhắn tin cho nhau được và không thấy bài đăng của nhau. Người kia không nhận được thông báo.',
      okText: 'Chặn', okButtonProps: { danger: true }, cancelText: 'Huỷ', onOk: run,
    })
  }
  const toggle = async () => {
    try {
      await communityApi.follow(p.id, !p.is_following)
      profile.refetch()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <PageHeader back={{ to: '/community', label: 'Cộng đồng' }}
        title={
          <span className="flex items-center gap-4">
            <UserAvatar name={p.display_name} src={p.avatar} size={64} />
            <span className="min-w-0">
              {p.display_name}
              <span className="num block text-sm font-semibold text-slate-500 mt-0.5 tracking-normal">ID {p.public_id}</span>
              {p.groups[0] && <span className="block text-base font-medium text-slate-500 mt-0.5">Nhóm {p.groups[0].name}</span>}
            </span>
          </span>
        }
        description={p.bio || undefined}
        actions={p.id !== me?.id && (
          <span className="flex gap-2">
            {!p.blocked && p.friend_status !== 'incoming' && (
              <FriendButton userId={p.id} name={p.display_name} status={p.friend_status} requestId={p.friend_request_id} size="large" />
            )}
            {p.can_message && <MessageButton userId={p.id} />}
            {!p.blocked && <Button size="large" type="default" onClick={toggle}>{p.is_following ? 'Đang theo dõi' : 'Theo dõi'}</Button>}
            <Button size="large" type="text" danger={!p.blocked} onClick={toggleBlock}>{p.blocked ? 'Bỏ chặn' : 'Chặn'}</Button>
            <ReportUserButton userId={p.id} name={p.display_name} blocked={p.blocked} onDone={() => profile.refetch()} />
          </span>
        )} />
      {p.friend_status === 'incoming' && !p.blocked && (
        <section className="lp-card p-5 border-brand-200 bg-brand-50 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1 min-w-0">
            <div className="font-bold text-slate-800">{p.display_name} muốn kết bạn với bạn</div>
            {p.friend_message && <div className="text-slate-700 mt-1 whitespace-pre-wrap">“{p.friend_message}”</div>}
          </div>
          <FriendButton userId={p.id} name={p.display_name} status="incoming" requestId={p.friend_request_id} />
        </section>
      )}
      <Section>
        <Facts items={[
          { label: 'tổng XP', value: p.lifetime_xp.toLocaleString('vi-VN'), icon: <XpIcon size={22} /> },
          { label: 'ngày liên tiếp', value: p.streak, icon: <StreakIcon size={22} /> },
          { label: 'bạn bè', value: p.friends },
          { label: 'bài đăng', value: p.posts },
          { label: 'người theo dõi', value: p.followers },
          { label: 'đang theo dõi', value: p.following },
        ]} />
      </Section>
      {p.recent_posts.length > 0 && (
        <Section title="Ảnh gần đây">
          <div className="grid grid-cols-3 gap-2">
            {p.recent_posts.map((r) => <img key={r.id} src={r.image} alt="" loading="lazy" className="aspect-square w-full object-cover rounded-xl bg-slate-100" />)}
          </div>
        </Section>
      )}
    </div>
  )
}
