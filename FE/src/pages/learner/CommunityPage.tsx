import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Form, Input, Modal, Select, Segmented, Skeleton, Switch, Upload } from 'antd'
import { DownOutlined, HeartFilled, HeartOutlined, MessageOutlined, SaveOutlined, FlagOutlined, PlusOutlined, CrownFilled, TeamOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/vi'
import { communityApi, gameApi, type Post, type StudyGroup } from '../../api/app'
import { errorMessage } from '../../api/client'
import { vocabApi } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import { langTag } from '../../components/TargetWord'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader, ShowMore, UserAvatar, useShowMore } from '../../components/ui'
import { StickerImage, StickerPicker } from '../../components/Stickers'

dayjs.extend(relativeTime)
dayjs.locale('vi')

/** A bookmark outline, filled when the post is in "Bài đã lưu". */
function BookmarkIcon({ filled }: { filled: boolean }) {
  return (
    <svg width="1em" height="1em" viewBox="0 0 24 24" aria-hidden className={filled ? 'text-brand-600' : ''}>
      <path d="M6 3.5h12a1 1 0 0 1 1 1V21l-7-4.5L5 21V4.5a1 1 0 0 1 1-1Z" fill={filled ? 'currentColor' : 'none'}
        stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  )
}

export function PostCard({ post, commentsOpen = false }: { post: Post; commentsOpen?: boolean }) {
  const { message, modal } = App.useApp()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const me = useAuth((s) => s.user)
  const [liked, setLiked] = useState(post.liked)
  const [likes, setLikes] = useState(post.like_count)
  const [saved, setSaved] = useState(post.saved)
  const [commentCount, setCommentCount] = useState(post.comment_count)
  const [open, setOpen] = useState(commentsOpen)
  const [text, setText] = useState('')
  const [allComments, setAllComments] = useState(commentsOpen) // the feed shows the last 3 comments
  const comments = useQuery({ queryKey: ['comments', post.id], queryFn: () => communityApi.comments(post.id), enabled: open })

  const toggleSave = async () => {
    setSaved(!saved)
    try {
      await communityApi.bookmark(post.id, !saved)
      message.success(saved ? 'Đã bỏ khỏi Bài đã lưu' : 'Đã lưu bài viết')
      queryClient.invalidateQueries({ queryKey: ['feed', 'saved'] })
    } catch (e) {
      setSaved(saved)
      message.error(errorMessage(e))
    }
  }
  const removeComment = (id: number) => modal.confirm({
    title: 'Xoá bình luận này?', okText: 'Xoá', okButtonProps: { danger: true }, cancelText: 'Huỷ',
    onOk: async () => {
      try {
        await communityApi.deleteComment(post.id, id)
        setCommentCount((n) => Math.max(0, n - 1))
        comments.refetch()
      } catch (e) {
        message.error(errorMessage(e))
      }
    },
  })

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
  const send = async (sticker?: string) => {
    if (!sticker && !text.trim()) return
    try {
      if (sticker) await communityApi.commentSticker(post.id, sticker)
      else {
        await communityApi.comment(post.id, text)
        setText('')
      }
      setCommentCount((n) => n + 1)
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
          <Button type="text" danger onClick={() => modal.confirm({
            title: 'Xoá bài viết này?', okText: 'Xoá', okButtonProps: { danger: true }, cancelText: 'Huỷ',
            onOk: async () => { await communityApi.remove(post.id); queryClient.invalidateQueries({ queryKey: ['feed'] }); if (commentsOpen) navigate('/community') },
          })}>Xoá</Button>
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
          <Button type="text" aria-expanded={open} aria-label="Bình luận" icon={<MessageOutlined />} onClick={() => setOpen(!open)}><span className="num">{commentCount}</span></Button>
          <Button type="text" aria-pressed={saved} aria-label={saved ? 'Bỏ lưu bài viết' : 'Lưu bài viết'} icon={<BookmarkIcon filled={saved} />} onClick={toggleSave}>
            {saved ? 'Đã lưu' : 'Lưu bài'}
          </Button>
          {post.words.length > 0 && (
            <Button type="text" icon={<SaveOutlined />} onClick={async () => {
              try { const r = await communityApi.saveWords(post.id); message.success(`Đã lưu ${r.added} từ`) } catch (e) { message.error(errorMessage(e)) }
            }}>Lưu từ vựng</Button>
          )}
        </div>
        {open && (
          <div className="flex flex-col gap-2.5 border-t border-slate-200 pt-3">
            {comments.isLoading && <Skeleton active paragraph={{ rows: 2 }} title={false} />}
            {comments.data?.length === 0 && <div className="text-sm text-slate-500">Chưa có bình luận. Hãy là người đầu tiên!</div>}
            {!allComments && (comments.data?.length ?? 0) > 3 && (
              <button type="button" onClick={() => setAllComments(true)}
                className="self-start inline-flex items-center gap-1.5 bg-transparent border-0 p-0 cursor-pointer text-sm font-semibold text-slate-500 hover:text-slate-800">
                Xem {comments.data!.length - 3} bình luận trước <DownOutlined className="text-xs" />
              </button>
            )}
            {(allComments ? comments.data : comments.data?.slice(-3))?.map((c) => (
              <div key={c.id} className="group flex gap-2 text-sm">
                <Link to={`/community/users/${c.author.id}`}><UserAvatar name={c.author.display_name} src={c.author.avatar} size={26} /></Link>
                <div className="flex-1 min-w-0">
                  <Link to={`/community/users/${c.author.id}`} className="font-semibold !text-slate-800">{c.author.display_name}</Link>{' '}
                  {c.kind === 'sticker' ? <StickerImage code={c.sticker} size={88} /> : <span className="text-slate-700 break-words">{c.content}</span>}
                  <span className="block text-xs text-slate-500 mt-0.5">
                    {dayjs(c.created_at).fromNow()}
                    {c.can_delete && <button type="button" className="ml-3 cursor-pointer font-semibold text-slate-500 hover:text-red-600" onClick={() => removeComment(c.id)}>Xoá</button>}
                  </span>
                </div>
              </div>
            ))}
            <div className="flex gap-2">
              <Input.Search placeholder="Viết bình luận…" enterButton="Gửi" value={text} onChange={(e) => setText(e.target.value)} onSearch={() => send()} />
              <StickerPicker onPick={(code) => send(code)} />
            </div>
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
  const [asking, setAsking] = useState<StudyGroup | null>(null)
  const [hello, setHello] = useState('')
  const join = useMutation({
    mutationFn: ({ id, message: m }: { id: number; message: string }) => communityApi.join(id, m),
    onSuccess: (r) => {
      message.success(r.status === 'pending' ? 'Đã gửi yêu cầu, trưởng nhóm sẽ nhận được thông báo' : 'Đã tham gia nhóm')
      setAsking(null)
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
    onError: (e) => message.error(errorMessage(e)),
  })
  const cancel = async (id: number) => {
    try {
      await communityApi.leave(id)
      message.success('Đã huỷ yêu cầu')
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const ask = (g: StudyGroup) => {
    if (!g.require_approval) return join.mutate({ id: g.id, message: '' })
    setHello('')
    setAsking(g)
  }
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
      <ShowMore items={groups.data} limit={6} label="Xem tất cả nhóm">{(shown) => (
      <ul className="m-0 p-0 list-none grid md:grid-cols-2 gap-3">
        {shown.map((g) => (
          <li key={g.id} className="lp-card p-5 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="font-bold text-lg text-slate-800">{g.name} {g.my_role === 'leader' && <CrownFilled className="text-amber-500" aria-label="Bạn là trưởng nhóm" />}</div>
              {g.description && <div className="text-slate-500 text-sm mt-0.5">{g.description}</div>}
              <div className="num text-sm text-slate-500 mt-1.5">{g.member_count} thành viên{g.require_approval && ' · cần trưởng nhóm duyệt'}</div>
            </div>
            {g.my_status === 'active' ? (
              <Button type="primary" onClick={() => navigate(`/community/groups/${g.id}`)}>Vào nhóm</Button>
            ) : g.my_status === 'pending' ? (
              <span className="flex flex-col items-end gap-1 shrink-0">
                <span className="text-sm font-semibold text-amber-700 whitespace-nowrap">Chờ duyệt</span>
                <Button size="small" type="text" onClick={() => cancel(g.id)}>Huỷ yêu cầu</Button>
              </span>
            ) : (
              <Button loading={join.isPending && join.variables?.id === g.id} onClick={() => ask(g)}>{g.require_approval ? 'Xin vào nhóm' : 'Tham gia'}</Button>
            )}
          </li>
        ))}
      </ul>
      )}</ShowMore>
      {groups.data?.length === 0 && (
        <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={88} />} title="Chưa có nhóm học nào" description="Tạo nhóm đầu tiên và rủ bạn bè cùng học." /></div>
      )}
      <Modal title={asking ? `Xin vào nhóm ${asking.name}` : ''} open={!!asking} okText="Gửi yêu cầu" cancelText="Huỷ"
        confirmLoading={join.isPending} onCancel={() => setAsking(null)}
        onOk={() => asking && join.mutate({ id: asking.id, message: hello.trim() })}>
        {asking?.description && (
          <div className="rounded-xl bg-slate-100 px-3 py-2 text-sm text-slate-700 mb-3">
            <b className="block text-slate-800">Giới thiệu / yêu cầu của nhóm</b>{asking.description}
          </div>
        )}
        <p className="text-slate-600 mt-0">Giới thiệu ngắn về bạn – trưởng nhóm đọc trong thông báo trước khi duyệt.</p>
        <Input.TextArea value={hello} onChange={(e) => setHello(e.target.value)} maxLength={200} showCount autoSize={{ minRows: 3, maxRows: 6 }}
          placeholder="VD: Mình đang ôn HSK 3, mỗi tối học 20 phút, muốn tìm bạn cùng luyện nói." aria-label="Giới thiệu bản thân" />
      </Modal>
      <Modal title="Tạo nhóm học" open={creating} onOk={create} onCancel={() => setCreating(false)} okText="Tạo nhóm" cancelText="Huỷ">
        <Form form={form} layout="vertical" initialValues={{ require_approval: false }}>
          <Form.Item name="name" label="Tên nhóm" rules={[{ required: true, message: 'Đặt tên cho nhóm' }]}><Input /></Form.Item>
          <Form.Item name="description" label="Giới thiệu / yêu cầu của nhóm"><Input.TextArea maxLength={300} showCount placeholder="Nhóm học gì, mỗi tuần làm gì, cần điều kiện gì để vào" /></Form.Item>
          <Form.Item name="require_approval" label="Cần trưởng nhóm duyệt" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

function LeaderboardTab() {
  const isKid = useAuth((s) => s.user?.learner_type === 'kid') // children follow nobody
  const [scope, setScope] = useState<'league' | 'friends' | 'global'>('league')
  const board = useQuery({ queryKey: ['leaderboard', scope], queryFn: () => gameApi.leaderboard(scope) })
  const zoneColor = { promotion: 'bg-emerald-50', safe: '', demotion: 'bg-red-50' } as const
  const medal = ['#ffb020', '#9aa8bb', '#e08a4f']
  const rows = useShowMore(board.data?.members, 10, 'Xem cả bảng xếp hạng')
  // my own row stays in sight even when I am below the top 10
  const meBelow = rows.open ? undefined : board.data?.members.find((m) => m.is_me && !rows.shown.includes(m))
  return (
    <div className="flex flex-col gap-4">
      <Segmented value={scope} onChange={(v) => setScope(v as typeof scope)} options={[
        { value: 'league', label: 'Giải đấu tuần' },
        ...(isKid ? [] : [{ value: 'friends', label: 'Bạn bè' }]),
        { value: 'global', label: 'Toàn hệ thống' },
      ]} />
      {scope === 'friends' && <div className="text-slate-600">XP tuần này của bạn và những người bạn đang theo dõi.</div>}
      {board.data?.tier && (
        <div className="text-slate-600"><b className="text-slate-800">{board.data.tier.name}</b> · kết thúc {dayjs(board.data.ends_at).fromNow()} ·
          <span className="text-emerald-700"> xanh: lên hạng</span> · <span className="text-red-600">đỏ: xuống hạng</span></div>
      )}
      <ol className="lp-card m-0 p-2 list-none">
        {scope === 'friends' && board.data?.members.length === 1 && (
          <li className="px-3 py-2 text-sm text-slate-500">Theo dõi bạn học trong Bảng tin để cùng thi đua mỗi tuần.</li>
        )}
        {board.data?.members.length === 0 && <li><EmptyState art={<Prismo mood="sleepy" size={80} />} title="Bảng xếp hạng tuần này còn trống" description="Học một bài để có tên đầu tiên." /></li>}
        {[...rows.shown, ...(meBelow ? [meBelow] : [])].map((m) => (
          <li key={m.user_id} className={`flex items-center gap-3 py-2 px-3 rounded-xl ${m.is_me ? 'bg-brand-50' : m.zone ? zoneColor[m.zone] : ''}`}>
            <span className="num w-8 text-center font-bold" style={m.rank <= 3 ? { color: medal[m.rank - 1] } : undefined}>{m.rank}</span>
            <UserAvatar name={m.display_name} src={m.avatar} />
            <span className={`flex-1 min-w-0 truncate ${m.is_me ? 'font-bold text-brand-700' : 'text-slate-800'}`}>{m.display_name}{m.is_me && ' (bạn)'}</span>
            <span className="num font-semibold text-slate-700">{m.xp} XP</span>
          </li>
        ))}
      </ol>
      {rows.toggle && <div className="-mt-3">{rows.toggle}</div>}
    </div>
  )
}

const LANG_NAME: Record<string, string> = { en: 'tiếng Anh', zh: 'tiếng Trung', vi: 'tiếng Việt' }

/** A row of people to follow: same language first. Following someone back opens private messages. */
function Suggestions() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const people = useQuery({ queryKey: ['follow-suggestions'], queryFn: communityApi.suggestions, staleTime: 300_000 })
  const [done, setDone] = useState<number[]>([])
  if (!people.data?.length) return null
  const follow = async (id: number) => {
    try {
      await communityApi.follow(id, true)
      setDone((d) => [...d, id])
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <section className="lp-card p-4" aria-label="Gợi ý bạn học">
      <h2 className="m-0 mb-3 text-base font-bold text-slate-800">Gợi ý bạn học</h2>
      <ul className="m-0 flex list-none gap-3 overflow-x-auto p-0 pb-1">
        {people.data.map((p) => (
          <li key={p.id} className="flex w-36 shrink-0 flex-col items-center gap-1.5 rounded-xl border border-slate-100 p-3 text-center">
            <Link to={`/community/users/${p.id}`} className="flex flex-col items-center gap-1.5 min-w-0 w-full">
              <UserAvatar name={p.display_name} src={p.avatar} size={48} />
              <span className="w-full truncate font-semibold text-slate-800">{p.display_name}</span>
            </Link>
            <span className="text-xs text-slate-500">{p.follows_me ? 'Đang theo dõi bạn' : `Học ${LANG_NAME[p.active_language] ?? p.active_language}`}</span>
            <Button size="small" type={done.includes(p.id) ? 'default' : 'primary'} disabled={done.includes(p.id)} onClick={() => follow(p.id)}>
              {done.includes(p.id) ? 'Đã theo dõi' : p.follows_me ? 'Theo dõi lại' : 'Theo dõi'}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function CommunityPage() {
  const user = useAuth((s) => s.user)
  const [params, setParams] = useSearchParams()
  const isKidUser = user?.learner_type === 'kid'
  const asked = params.get('tab') as 'feed' | 'saved' | 'groups' | 'leaderboard' | null
  const tab = isKidUser ? 'leaderboard' : asked && ['feed', 'saved', 'groups', 'leaderboard'].includes(asked) ? asked : 'feed'
  const setTab = (t: typeof tab) => setParams({ tab: t }, { replace: true })
  const feed = useQuery({ queryKey: ['feed'], queryFn: () => communityApi.feed(), enabled: tab === 'feed' })
  const saved = useQuery({ queryKey: ['feed', 'saved'], queryFn: () => communityApi.feed({ saved: 1 }), enabled: tab === 'saved' })
  const isKid = user?.learner_type === 'kid'
  const requests = useQuery({ queryKey: ['friend-requests', 'incoming'], queryFn: () => communityApi.friendRequests('incoming'), enabled: !isKid })
  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-5">
      <PageHeader title="Cộng đồng" description="Chia sẻ ảnh kèm từ vựng, học cùng nhóm và đua XP mỗi tuần."
        actions={!isKid && (
          <span className="flex gap-2">
            <Link to="/friends"><Button icon={<TeamOutlined />}>Bạn bè{requests.data?.length ? <span className="num ml-1 rounded-full bg-brand-600 text-white text-xs px-1.5">{requests.data.length}</span> : null}</Button></Link>
            {tab === 'feed' && <NewPost />}
          </span>
        )} />
      <Segmented value={tab} onChange={(v) => setTab(v as typeof tab)} options={[
        ...(isKid ? [] : [{ value: 'feed', label: 'Bảng tin' }, { value: 'saved', label: 'Đã lưu' }, { value: 'groups', label: 'Nhóm học' }]),
        { value: 'leaderboard', label: 'Bảng xếp hạng' },
      ]} />
      {tab === 'feed' && <Suggestions />}
      {tab === 'feed' && (feed.isLoading ? <Skeleton active /> : feed.data?.results.length ? feed.data.results.map((p) => <PostCard key={p.id} post={p} />) : (
        <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={88} />} title="Bảng tin còn trống" description="Chụp một đồ vật rồi đăng ảnh kèm từ vựng để mọi người cùng học." /></div>
      ))}
      {tab === 'saved' && (saved.isLoading ? <Skeleton active /> : saved.data?.results.length ? saved.data.results.map((p) => <PostCard key={p.id} post={p} />) : (
        <div className="lp-card"><EmptyState art={<Prismo mood="happy" size={88} />} title="Chưa lưu bài nào" description="Bấm “Lưu bài” dưới một bài viết để xem lại ở đây." /></div>
      ))}
      {tab === 'groups' && <Groups />}
      {tab === 'leaderboard' && <LeaderboardTab />}
    </div>
  )
}
