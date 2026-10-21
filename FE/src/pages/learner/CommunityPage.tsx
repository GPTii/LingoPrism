import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Form, Input, Modal, Select, Segmented, Skeleton, Switch, Upload } from 'antd'
import { HeartFilled, HeartOutlined, MessageOutlined, SaveOutlined, FlagOutlined, PlusOutlined, CrownFilled } from '@ant-design/icons'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/vi'
import { communityApi, gameApi, type Post } from '../../api/app'
import { errorMessage } from '../../api/client'
import { vocabApi } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import { langTag } from '../../components/TargetWord'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader, UserAvatar } from '../../components/ui'

dayjs.extend(relativeTime)
dayjs.locale('vi')

function PostCard({ post }: { post: Post }) {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const me = useAuth((s) => s.user)
  const [liked, setLiked] = useState(post.liked)
  const [likes, setLikes] = useState(post.like_count)
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const comments = useQuery({ queryKey: ['comments', post.id], queryFn: () => communityApi.comments(post.id), enabled: open })

  const toggleLike = async () => {
    setLiked(!liked)
    setLikes((n) => n + (liked ? -1 : 1))
    try {
      await communityApi.like(post.id, !liked)
    } catch (e) {
      setLiked(liked)
      setLikes(post.like_count)
      message.error(errorMessage(e))
    }
  }
  const send = async () => {
    if (!text.trim()) return
    try {
      await communityApi.comment(post.id, text)
      setText('')
      comments.refetch()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const report = () => {
    let reason = 'spam'
    let details = ''
    Modal.confirm({
      title: 'Báo cáo vi phạm',
      content: (
        <div className="flex flex-col gap-2">
          <Select defaultValue="spam" onChange={(v) => (reason = v)} options={[
            { value: 'spam', label: 'Spam' }, { value: 'inappropriate', label: 'Nội dung không phù hợp' },
            { value: 'wrong_vocab', label: 'Từ vựng sai' }, { value: 'harassment', label: 'Quấy rối' }, { value: 'other', label: 'Khác' },
          ]} />
          <Input.TextArea placeholder="Mô tả chi tiết…" onChange={(e) => (details = e.target.value)} />
        </div>
      ),
      onOk: async () => {
        try {
          await communityApi.report(post.id, reason, details)
          message.success('Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.')
        } catch (e) {
          message.error(errorMessage(e))
        }
      },
    })
  }

  return (
    <article className="lp-card overflow-hidden">
      <div className="flex items-center gap-3 p-4">
        <UserAvatar name={post.author.display_name} src={post.author.avatar} size={40} />
        <button type="button" className="text-left cursor-pointer" onClick={() => navigate(`/community/users/${post.author.id}`)}>
          <div className="font-semibold text-slate-800">{post.author.display_name}</div>
          <div className="text-xs text-slate-500">{dayjs(post.created_at).fromNow()}</div>
        </button>
        <div className="flex-1" />
        {post.author.id === me?.id ? (
          <Button type="text" danger onClick={async () => { await communityApi.remove(post.id); queryClient.invalidateQueries({ queryKey: ['feed'] }) }}>Xoá</Button>
        ) : (
          <Button type="text" icon={<FlagOutlined />} onClick={report} aria-label="Báo cáo bài đăng" />
        )}
      </div>
      <img src={post.image} alt="" className="w-full max-h-[480px] object-cover" />
      <div className="p-4 flex flex-col gap-3">
        {post.caption && <p className="m-0 text-slate-800">{post.caption}</p>}
        {post.words.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {post.words.map((w) => w.target && (
              <span key={w.id} className={`rounded-lg px-2.5 py-1 text-sm ${w.personal ? 'bg-green-50 text-green-700' : 'bg-brand-50 text-brand-700'}`}>
                <b lang={langTag(w.target.language)} className="font-semibold">{w.target.text}</b> · {w.meaning_vi}
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <Button type="text" aria-pressed={liked} aria-label={liked ? 'Bỏ thích' : 'Thích'} icon={liked ? <HeartFilled className="text-red-500" /> : <HeartOutlined />} onClick={toggleLike}><span className="num">{likes}</span></Button>
          <Button type="text" aria-expanded={open} aria-label="Bình luận" icon={<MessageOutlined />} onClick={() => setOpen(!open)}><span className="num">{post.comment_count}</span></Button>
          {post.words.length > 0 && (
            <Button type="text" icon={<SaveOutlined />} onClick={async () => {
              try { const r = await communityApi.saveWords(post.id); message.success(`Đã lưu ${r.added} từ`) } catch (e) { message.error(errorMessage(e)) }
            }}>Lưu từ vựng</Button>
          )}
        </div>
        {open && (
          <div className="flex flex-col gap-2.5 border-t border-slate-200 pt-3">
            {comments.data?.map((c) => (
              <div key={c.id} className="flex gap-2 text-sm">
                <UserAvatar name={c.author.display_name} src={c.author.avatar} size={26} />
                <div><b className="font-semibold text-slate-800">{c.author.display_name}</b> <span className="text-slate-700">{c.content}</span></div>
              </div>
            ))}
            <Input.Search placeholder="Viết bình luận…" enterButton="Gửi" value={text} onChange={(e) => setText(e.target.value)} onSearch={send} />
          </div>
        )}
      </div>
    </article>
  )
}

function NewPost() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [form] = Form.useForm()
  const myWords = useQuery({ queryKey: ['my-words-all'], queryFn: () => vocabApi.myWords(), enabled: open })
  const submit = async () => {
    const v = await form.validateFields()
    if (!file) return message.warning('Hãy chọn ảnh')
    try {
      await communityApi.create(file, v.caption ?? '', v.words ?? [])
      message.success('Đã đăng bài')
      setOpen(false)
      form.resetFields()
      setFile(null)
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>Đăng ảnh</Button>
      <Modal title="Chia sẻ ảnh & từ vựng" open={open} onOk={submit} onCancel={() => setOpen(false)} okText="Đăng bài" cancelText="Huỷ">
        <Form form={form} layout="vertical">
          <Upload beforeUpload={(f) => { setFile(f); return false }} maxCount={1} accept="image/*" listType="picture">
            <Button>Chọn ảnh</Button>
          </Upload>
          <Form.Item name="caption" label="Chú thích" className="mt-4"><Input.TextArea maxLength={500} /></Form.Item>
          <Form.Item name="words" label="Gắn từ vựng (từ thư viện của bạn)">
            <Select mode="multiple" options={myWords.data?.results.map((w) => ({ value: w.id, label: `${w.target?.text} – ${w.meaning_vi}` }))} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

function Groups() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const groups = useQuery({ queryKey: ['groups'], queryFn: () => communityApi.groups() })
  const [creating, setCreating] = useState(false)
  const [form] = Form.useForm()
  const join = useMutation({
    mutationFn: (id: number) => communityApi.join(id),
    onSuccess: (r) => { message.success(r.status === 'pending' ? 'Đã gửi yêu cầu, chờ trưởng nhóm duyệt' : 'Đã tham gia nhóm'); queryClient.invalidateQueries({ queryKey: ['groups'] }) },
    onError: (e) => message.error(errorMessage(e)),
  })
  const create = async () => {
    const v = await form.validateFields()
    try {
      await communityApi.createGroup(v)
      setCreating(false)
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  if (groups.isLoading) return <Skeleton active />
  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end"><Button icon={<PlusOutlined />} onClick={() => setCreating(true)}>Tạo nhóm</Button></div>
      <ul className="m-0 p-0 list-none grid md:grid-cols-2 gap-3">
        {groups.data?.map((g) => (
          <li key={g.id} className="lp-card p-5 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="font-bold text-lg text-slate-800">{g.name} {g.my_role === 'leader' && <CrownFilled className="text-amber-500" aria-label="Bạn là trưởng nhóm" />}</div>
              {g.description && <div className="text-slate-500 text-sm mt-0.5">{g.description}</div>}
              <div className="num text-sm text-slate-500 mt-1.5">{g.member_count} thành viên{g.require_approval && ' · cần trưởng nhóm duyệt'}</div>
            </div>
            {g.my_status === 'active' ? (
              <Button type="primary" onClick={() => navigate(`/community/groups/${g.id}`)}>Vào nhóm</Button>
            ) : g.my_status === 'pending' ? <span className="text-sm font-semibold text-amber-700 whitespace-nowrap">Chờ duyệt</span> : (
              <Button loading={join.isPending} onClick={() => join.mutate(g.id)}>Tham gia</Button>
            )}
          </li>
        ))}
      </ul>
      {groups.data?.length === 0 && (
        <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={88} />} title="Chưa có nhóm học nào" description="Tạo nhóm đầu tiên và rủ bạn bè cùng học." /></div>
      )}
      <Modal title="Tạo nhóm học" open={creating} onOk={create} onCancel={() => setCreating(false)} okText="Tạo nhóm" cancelText="Huỷ">
        <Form form={form} layout="vertical" initialValues={{ require_approval: false }}>
          <Form.Item name="name" label="Tên nhóm" rules={[{ required: true, message: 'Đặt tên cho nhóm' }]}><Input /></Form.Item>
          <Form.Item name="description" label="Yêu cầu / mô tả"><Input.TextArea /></Form.Item>
          <Form.Item name="require_approval" label="Cần trưởng nhóm duyệt" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function LeaderboardTab() {
  const [scope, setScope] = useState<'league' | 'global'>('league')
  const board = useQuery({ queryKey: ['leaderboard', scope], queryFn: () => gameApi.leaderboard(scope) })
  const zoneColor = { promotion: 'bg-emerald-50', safe: '', demotion: 'bg-red-50' } as const
  const medal = ['#ffb020', '#a8a3c4', '#e08a4f']
  return (
    <div className="flex flex-col gap-4">
      <Segmented value={scope} onChange={(v) => setScope(v as typeof scope)} options={[{ value: 'league', label: 'Giải đấu tuần' }, { value: 'global', label: 'Toàn hệ thống' }]} />
      {board.data?.tier && (
        <div className="text-slate-600"><b className="text-slate-800">{board.data.tier.name}</b> · kết thúc {dayjs(board.data.ends_at).fromNow()} ·
          <span className="text-emerald-700"> xanh: lên hạng</span> · <span className="text-red-600">đỏ: xuống hạng</span></div>
      )}
      <ol className="lp-card m-0 p-2 list-none">
        {board.data?.members.length === 0 && <li><EmptyState art={<Prismo mood="sleepy" size={80} />} title="Bảng xếp hạng tuần này còn trống" description="Học một bài để có tên đầu tiên." /></li>}
        {board.data?.members.map((m) => (
          <li key={m.user_id} className={`flex items-center gap-3 py-2 px-3 rounded-xl ${m.is_me ? 'bg-brand-50' : m.zone ? zoneColor[m.zone] : ''}`}>
            <span className="num w-8 text-center font-bold" style={m.rank <= 3 ? { color: medal[m.rank - 1] } : undefined}>{m.rank}</span>
            <UserAvatar name={m.display_name} src={m.avatar} />
            <span className={`flex-1 min-w-0 truncate ${m.is_me ? 'font-bold text-brand-700' : 'text-slate-800'}`}>{m.display_name}{m.is_me && ' (bạn)'}</span>
            <span className="num font-semibold text-slate-700">{m.xp} XP</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

export default function CommunityPage() {
  const user = useAuth((s) => s.user)
  const [params, setParams] = useSearchParams()
  const isKidUser = user?.learner_type === 'kid'
  const asked = params.get('tab') as 'feed' | 'groups' | 'leaderboard' | null
  const tab = isKidUser ? 'leaderboard' : asked && ['feed', 'groups', 'leaderboard'].includes(asked) ? asked : 'feed'
  const setTab = (t: typeof tab) => setParams({ tab: t }, { replace: true })
  const feed = useQuery({ queryKey: ['feed'], queryFn: () => communityApi.feed(), enabled: tab === 'feed' })
  const isKid = user?.learner_type === 'kid'
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-5">
      <PageHeader title="Cộng đồng" description="Chia sẻ ảnh kèm từ vựng, học cùng nhóm và đua XP mỗi tuần."
        actions={tab === 'feed' && !isKid ? <NewPost /> : undefined} />
      <Segmented value={tab} onChange={(v) => setTab(v as typeof tab)} options={[
        ...(isKid ? [] : [{ value: 'feed', label: 'Bảng tin' }, { value: 'groups', label: 'Nhóm học' }]),
        { value: 'leaderboard', label: 'Bảng xếp hạng' },
      ]} />
      {tab === 'feed' && (feed.isLoading ? <Skeleton active /> : feed.data?.results.length ? feed.data.results.map((p) => <PostCard key={p.id} post={p} />) : (
        <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={88} />} title="Bảng tin còn trống" description="Chụp một đồ vật rồi đăng ảnh kèm từ vựng để mọi người cùng học." /></div>
      ))}
      {tab === 'groups' && <Groups />}
      {tab === 'leaderboard' && <LeaderboardTab />}
    </div>
  )
}
