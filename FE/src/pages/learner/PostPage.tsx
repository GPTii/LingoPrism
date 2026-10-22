import { useQuery } from '@tanstack/react-query'
import { Skeleton } from 'antd'
import { useParams } from 'react-router-dom'
import { communityApi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader } from '../../components/ui'
import { PostCard } from './CommunityPage'

/** One post with its comments open – where a "liked / commented on your post" notification leads. */
export default function PostPage() {
  const { id } = useParams()
  const post = useQuery({ queryKey: ['post', id], queryFn: () => communityApi.post(Number(id)), retry: false })
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-5">
      <PageHeader back={{ to: '/community', label: 'Cộng đồng' }} title="Bài viết" />
      {post.isLoading ? <div className="lp-card p-6"><Skeleton active avatar /></div>
        : post.data ? <PostCard post={post.data} commentsOpen />
          : <div className="lp-card"><EmptyState art={<Prismo mood="sad" size={88} />} title="Không xem được bài viết này" description={post.error ? errorMessage(post.error) : 'Bài có thể đã bị xoá.'} /></div>}
    </div>
  )
}
