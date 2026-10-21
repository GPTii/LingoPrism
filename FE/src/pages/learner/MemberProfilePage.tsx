import { useQuery } from '@tanstack/react-query'
import { App, Button, Skeleton } from 'antd'
import { useParams } from 'react-router-dom'
import { communityApi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { StreakIcon, XpIcon } from '../../components/brand/Brand'
import { Facts, PageHeader, Section, UserAvatar } from '../../components/ui'

export default function MemberProfilePage() {
  const { id } = useParams()
  const me = useAuth((s) => s.user)
  const { message } = App.useApp()
  const profile = useQuery({ queryKey: ['profile', id], queryFn: () => communityApi.profile(Number(id)) })
  const p = profile.data
  if (!p) return <div className="max-w-3xl mx-auto lp-card p-6"><Skeleton active avatar /></div>
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
              {p.groups[0] && <span className="block text-base font-medium text-slate-500 mt-0.5">Nhóm {p.groups[0].name}</span>}
            </span>
          </span>
        }
        description={p.bio || undefined}
        actions={p.id !== me?.id && (
          <Button size="large" type={p.is_following ? 'default' : 'primary'} onClick={toggle}>{p.is_following ? 'Đang theo dõi' : 'Theo dõi'}</Button>
        )} />
      <Section>
        <Facts items={[
          { label: 'tổng XP', value: p.lifetime_xp.toLocaleString('vi-VN'), icon: <XpIcon size={22} /> },
          { label: 'ngày liên tiếp', value: p.streak, icon: <StreakIcon size={22} /> },
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
