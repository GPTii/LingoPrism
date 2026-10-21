import { useQuery } from '@tanstack/react-query'
import { App, Avatar, Button, Card, Skeleton, Statistic } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { communityApi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'

export default function MemberProfilePage() {
  const { id } = useParams()
  const me = useAuth((s) => s.user)
  const { message } = App.useApp()
  const profile = useQuery({ queryKey: ['profile', id], queryFn: () => communityApi.profile(Number(id)) })
  const p = profile.data
  if (!p) return <Skeleton active />
  const toggle = async () => {
    try {
      await communityApi.follow(p.id, !p.is_following)
      profile.refetch()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-4">
      <Card className="!rounded-2xl">
        <div className="flex items-center gap-4">
          <Avatar size={72} src={p.avatar?.startsWith('assets/') ? undefined : p.avatar} icon={<UserOutlined />} />
          <div className="flex-1">
            <div className="text-xl font-bold">{p.display_name}</div>
            <div className="text-slate-500">{p.bio}</div>
            {p.groups[0] && <div className="text-sm">Nhóm: {p.groups[0].name}</div>}
          </div>
          {p.id !== me?.id && <Button type={p.is_following ? 'default' : 'primary'} onClick={toggle}>{p.is_following ? 'Đang theo dõi' : 'Theo dõi'}</Button>}
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 mt-4">
          <Statistic title="XP" value={p.lifetime_xp} />
          <Statistic title="Streak" value={p.streak} />
          <Statistic title="Bài đăng" value={p.posts} />
          <Statistic title="Người theo dõi" value={p.followers} />
          <Statistic title="Đang theo dõi" value={p.following} />
        </div>
      </Card>
      <div className="grid grid-cols-3 gap-2">
        {p.recent_posts.map((r) => <img key={r.id} src={r.image} alt="" className="aspect-square object-cover rounded-xl" />)}
      </div>
    </div>
  )
}
