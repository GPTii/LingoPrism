import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Avatar, Button, Card, Empty, Form, Input, Modal, Select, Segmented, Skeleton, Switch, Tag, Upload } from 'antd'
import { HeartFilled, HeartOutlined, MessageOutlined, SaveOutlined, FlagOutlined, PlusOutlined, UserOutlined, CrownOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/vi'
import { communityApi, gameApi, type Post } from '../../api/app'
import { errorMessage } from '../../api/client'
import { vocabApi } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import { langTag } from '../../components/TargetWord'

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
    <Card className="!rounded-2xl" styles={{ body: { padding: 0 } }}>
      <div className="flex items-center gap-3 p-4">
        <Avatar src={post.author.avatar?.startsWith('assets/') ? undefined : post.author.avatar} icon={<UserOutlined />} />
        <button type="button" className="text-left cursor-pointer" onClick={() => navigate(`/community/users/${post.author.id}`)}>
          <div className="font-semibold">{post.author.display_name}</div>
          <div className="text-xs text-slate-400">{dayjs(post.created_at).fromNow()}</div>
        </button>
        <div className="flex-1" />
        {post.author.id === me?.id ? (
          <Button type="text" danger onClick={async () => { await communityApi.remove(post.id); queryClient.invalidateQueries({ queryKey: ['feed'] }) }}>Xoá</Button>
        ) : (
          <Button type="text" icon={<FlagOutlined />} onClick={report} />
        )}
      </div>
      <img src={post.image} alt="" className="w-full max-h-[480px] object-cover" />
      <div className="p-4 flex flex-col gap-3">
        {post.caption && <div>{post.caption}</div>}
        <div className="flex flex-wrap gap-2">
          {post.words.map((w) => w.target && (
            <Tag key={w.id} color={w.personal ? 'green' : 'blue'} className="!text-sm !py-1">
              <span lang={langTag(w.target.language)}>{w.target.text}</span> · {w.meaning_vi}
            </Tag>
          ))}
        </div>
        <div className="flex gap-2">
          <Button type="text" icon={liked ? <HeartFilled className="text-red-500" /> : <HeartOutlined />} onClick={toggleLike}>{likes}</Button>
          <Button type="text" icon={<MessageOutlined />} onClick={() => setOpen(!open)}>{post.comment_count}</Button>
          {post.words.length > 0 && (
            <Button type="text" icon={<SaveOutlined />} onClick={async () => {
              try { const r = await communityApi.saveWords(post.id); message.success(`Đã lưu ${r.added} từ`) } catch (e) { message.error(errorMessage(e)) }
            }}>Lưu từ vựng</Button>
          )}
        </div>
        {open && (
          <div className="flex flex-col gap-2 border-t pt-3">
            {comments.data?.map((c) => (
              <div key={c.id} className="text-sm"><b>{c.author.display_name}</b> {c.content}</div>
            ))}
            <Input.Search placeholder="Viết bình luận…" enterButton="Gửi" value={text} onChange={(e) => setText(e.target.value)} onSearch={send} />
          </div>
        )}
      </div>
    </Card>
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
      <Modal title="Chia sẻ ảnh & từ vựng" open={open} onOk={submit} onCancel={() => setOpen(false)} okText="Đăng">
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
      <div className="grid md:grid-cols-2 gap-4">
        {groups.data?.map((g) => (
          <Card key={g.id} className="!rounded-2xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-semibold text-lg">{g.name} {g.my_role === 'leader' && <CrownOutlined className="text-amber-500" />}</div>
                <div className="text-slate-500 text-sm">{g.description}</div>
                <div className="text-xs text-slate-400 mt-1">{g.member_count} thành viên {g.require_approval && '· cần duyệt'}</div>
              </div>
              {g.my_status === 'active' ? (
                <Button type="primary" onClick={() => navigate(`/community/groups/${g.id}`)}>Vào nhóm</Button>
              ) : g.my_status === 'pending' ? <Tag>Chờ duyệt</Tag> : (
                <Button loading={join.isPending} onClick={() => join.mutate(g.id)}>Tham gia</Button>
              )}
            </div>
          </Card>
        ))}
      </div>
      <Modal title="Tạo nhóm học" open={creating} onOk={create} onCancel={() => setCreating(false)} okText="Tạo">
        <Form form={form} layout="vertical" initialValues={{ require_approval: false }}>
          <Form.Item name="name" label="Tên nhóm" rules={[{ required: true }]}><Input /></Form.Item>
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
  return (
    <div className="flex flex-col gap-4">
      <Segmented value={scope} onChange={(v) => setScope(v as typeof scope)} options={[{ value: 'league', label: 'Giải đấu tuần' }, { value: 'global', label: 'Toàn hệ thống' }]} />
      {board.data?.tier && <div className="font-semibold">{board.data.tier.name} · kết thúc {dayjs(board.data.ends_at).fromNow()}</div>}
      <Card className="!rounded-2xl">
        {board.data?.members.length === 0 && <Empty description="Chưa có ai trong bảng xếp hạng tuần này" />}
        {board.data?.members.map((m) => (
          <div key={m.user_id} className={`flex items-center gap-3 py-2 px-2 rounded-lg ${m.zone ? zoneColor[m.zone] : ''} ${m.is_me ? 'ring-2 ring-brand-500' : ''}`}>
            <span className="w-8 text-center font-bold">{m.rank}</span>
            <Avatar src={m.avatar?.startsWith('assets/') ? undefined : m.avatar} icon={<UserOutlined />} />
            <span className="flex-1">{m.display_name}{m.is_me && ' (bạn)'}</span>
            <span className="font-semibold">{m.xp} XP</span>
          </div>
        ))}
      </Card>
    </div>
  )
}

export default function CommunityPage() {
  const user = useAuth((s) => s.user)
  const [tab, setTab] = useState<'feed' | 'groups' | 'leaderboard'>(user?.learner_type === 'kid' ? 'leaderboard' : 'feed')
  const feed = useQuery({ queryKey: ['feed'], queryFn: () => communityApi.feed(), enabled: tab === 'feed' })
  const isKid = user?.learner_type === 'kid'
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold text-slate-800 m-0">Cộng đồng</h1>
        {tab === 'feed' && !isKid && <NewPost />}
      </div>
      <Segmented value={tab} onChange={(v) => setTab(v as typeof tab)} options={[
        ...(isKid ? [] : [{ value: 'feed', label: 'Bảng tin' }, { value: 'groups', label: 'Nhóm học' }]),
        { value: 'leaderboard', label: 'Bảng xếp hạng' },
      ]} />
      {tab === 'feed' && (feed.isLoading ? <Skeleton active /> : feed.data?.results.length ? feed.data.results.map((p) => <PostCard key={p.id} post={p} />) : <Empty description="Chưa có bài đăng" />)}
      {tab === 'groups' && <Groups />}
      {tab === 'leaderboard' && <LeaderboardTab />}
    </div>
  )
}
