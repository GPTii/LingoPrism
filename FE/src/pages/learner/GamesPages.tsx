import { App, Button, Modal, Progress, Result, Spin, Tooltip } from 'antd'
import { CloseOutlined, LockFilled, StarFilled } from '@ant-design/icons'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { errorMessage } from '../../api/client'
import { playApi, type GameFinish, type GameRound, type GameStop, type HelperKind, type MapFriend } from '../../api/play'
import { useAuth } from '../../auth/store'
import { AppIcon } from '../../components/brand/AppIcon'
import { Prismo, ScaleIcon } from '../../components/brand/Brand'
import { GAME_NAMES, HelpContext, MiniGameView, type GameHelp } from '../../components/MiniGames'
import { langTag } from '../../components/TargetWord'
import { PageHeader, UserAvatar } from '../../components/ui'

const LANG_NAME: Record<string, string> = { en: 'tiếng Anh', zh: 'tiếng Trung', vi: 'tiếng Việt' }
const LEVEL_COLORS = ['#0E9F7B', '#1F7ED0', '#B26F00', '#E0445E']  // same as the learning path (LevelPath)

function useLang() {
  const user = useAuth((s) => s.user)
  const lang = user?.active_language ?? 'en'
  return { lang, tag: lang === 'zh' ? langTag(user?.zh_script === 'hant' ? 'zh-Hant' : 'zh-Hans') : lang }
}

function Stars({ n, size = 'text-sm' }: { n: number; size?: string }) {
  return (
    <span className={`flex gap-0.5 ${size}`} aria-label={`${n} sao`}>
      {[1, 2, 3].map((s) => <StarFilled key={s} style={{ color: s <= n ? '#ffc800' : 'var(--color-slate-300)' }} />)}
    </span>
  )
}

// ====================================================================== map

function StopButton({ stop, color, current, onClick }: { stop: GameStop; color: string; current: boolean; onClick: () => void }) {
  const big = stop.kind === 'boss'
  const size = big ? 92 : 72
  const face = stop.status === 'locked' ? '#d5dce6' : stop.status === 'done' ? '#58cc02' : color
  const lip = stop.status === 'locked' ? '#aab6c4' : stop.status === 'done' ? '#43a000' : `color-mix(in oklab, ${color} 70%, black)`
  return (
    <div className="relative flex flex-col items-center">
      {current && (
        <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 1.4, repeat: Infinity }}
          className="absolute -top-10 whitespace-nowrap rounded-xl bg-white border-2 border-slate-200 px-3 py-1 text-sm font-bold text-brand-600 shadow-sm">
          {stop.kind === 'chest' ? 'Mở rương!' : 'Chơi nào!'}
        </motion.div>
      )}
      <button type="button" onClick={onClick} aria-label={`${stop.title}${stop.status === 'locked' ? ' (chưa mở)' : ''}`}
        style={{ width: size, height: size, background: face, boxShadow: `0 6px 0 ${lip}` }}
        className={`rounded-full grid place-items-center text-white text-2xl font-extrabold cursor-pointer transition active:translate-y-1.5 active:!shadow-none
          ${current ? 'ring-8 ring-brand-200' : ''}`}>
        {stop.kind === 'chest' ? <AppIcon name="chest" size={big ? 56 : 44} className={stop.status === 'done' ? 'opacity-60' : ''} />
          : stop.kind === 'boss' ? <AppIcon name="trophy" size={52} className={stop.status === 'locked' ? 'grayscale opacity-60' : ''} />
            : stop.status === 'locked' ? <LockFilled className="text-slate-400" /> : stop.index}
      </button>
      {stop.kind !== 'chest' && stop.status === 'done' && <div className="mt-2"><Stars n={stop.stars} /></div>}
      {stop.kind === 'boss' && <div className="mt-1 text-xs font-semibold text-slate-500">Màn trùm</div>}
    </div>
  )
}

/** Friends standing at a stop: up to 3 faces, then "+N"; their names on hover. */
function FriendsHere({ friends, size = 34, className = '' }: { friends: MapFriend[]; size?: number; className?: string }) {
  if (!friends.length) return null
  const names = friends.map((f) => f.display_name || 'Bạn bè')
  return (
    <Tooltip title={names.length > 6 ? `${names.slice(0, 6).join(', ')} và ${names.length - 6} bạn khác` : names.join(', ')}>
      <div className={`flex items-center ${className}`} aria-label={`Bạn bè ở đây: ${names.join(', ')}`}>
        {friends.slice(0, 3).map((f, i) => (
          <motion.span key={f.id} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.15 + i * 0.08, type: 'spring', stiffness: 400, damping: 18 }}
            className={`rounded-full ring-[3px] ring-white shadow-sm ${i ? '-ml-3' : ''}`} style={{ zIndex: 3 - i }}>
            <UserAvatar name={f.display_name} src={f.avatar} mascot={f.mascot} size={size} />
          </motion.span>
        ))}
        {friends.length > 3 && (
          <span className="-ml-3 rounded-full ring-[3px] ring-white bg-slate-200 text-slate-600 text-xs font-bold grid place-items-center"
            style={{ width: size, height: size }}>+{friends.length - 3}</span>
        )}
      </div>
    </Tooltip>
  )
}

export function GameMapPage() {
  const { message, modal } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { lang } = useLang()
  const kid = useAuth((s) => s.user?.learner_type === 'kid')  // children stay out of the social side
  const { data, isLoading, error } = useQuery({ queryKey: ['game-map', lang], queryFn: playApi.map })
  const [chest, setChest] = useState<{ gems: number; scales: number } | null>(null)

  useEffect(() => {  // bring the stop to play into view
    if (data?.current) document.getElementById(`stop-${data.current}`)?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [data?.current])

  if (isLoading) return <div className="flex justify-center py-20"><Spin size="large" /></div>
  if (error || !data) return <Result status="warning" title={errorMessage(error)} />

  const friendsAt = new Map<string, MapFriend[]>()
  for (const f of data.friends ?? []) friendsAt.set(f.node, [...(friendsAt.get(f.node) ?? []), f])
  const levelOf = (node: string) => Number(node.split('-')[0].slice(1))
  const showFriend = (f: MapFriend) => {
    const el = document.getElementById(`stop-${f.node}`)
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
    else message.info(`${f.display_name} đang ở cấp ${levelOf(f.node)} – thắng màn trùm để theo kịp nhé!`)
  }

  const tapLocked = (stop: GameStop) => {
    const lock = stop.lock
    if (lock?.reason === 'learn') {
      modal.confirm({
        title: 'Học trước rồi chơi nhé!', okText: 'Đi học từ mới', cancelText: 'Để sau',
        content: `Màn này dùng những từ bạn đã học. Hãy học thêm ${lock.need} từ ở cấp ${lock.level} để mở.`,
        onOk: () => navigate('/learn?kind=learn'),
      })
    } else if (lock?.reason === 'lesson') {
      modal.confirm({
        title: 'Học bài trước rồi chơi nhé!', okText: `Học bài ${lock.lesson}`, cancelText: 'Để sau',
        content: `Màn này mở khi con học xong bài “${lock.title}”.`, onOk: () => navigate(`/doc-viet/${lock.lesson}`),
      })
    } else {
      message.info('Hãy qua màn trước đã!')
    }
  }
  const tap = async (stop: GameStop) => {
    if (stop.status === 'locked') return tapLocked(stop)
    if (stop.kind !== 'chest') return navigate(`/tro-choi/${stop.id}`)
    if (stop.status === 'done') return message.info('Rương này đã mở rồi')
    try {
      setChest(await playApi.openChest(stop.id))
      queryClient.invalidateQueries({ queryKey: ['game-map'] })
      queryClient.invalidateQueries({ queryKey: ['game-summary'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <PageHeader title="Trò chơi" description={data.track === 'reading'
        ? 'Học xong bài ở mục Học đọc – viết rồi vào đây chơi. Qua mỗi màn, mở rương nhận ngọc!'
        : `Chơi với những từ ${LANG_NAME[data.language] ?? ''} bạn đã học. Học thêm ở mục Học để mở màn mới.`} />
      {data.track === 'words' && !kid && (
        <section className="lp-card p-4 flex flex-col gap-3" aria-label="Bạn bè trên bản đồ">
          <div className="flex items-center justify-between gap-3">
            <div className="font-bold text-slate-800">Bạn bè đang chơi</div>
            {!!data.friends?.length && <span className="text-sm text-slate-500">Chạm để xem họ ở màn nào</span>}
          </div>
          {data.friends?.length ? (
            <div className="flex gap-3 overflow-x-auto pb-1 -mx-1 px-1">
              {data.friends.map((f) => (
                <button key={f.id} type="button" onClick={() => showFriend(f)}
                  className="shrink-0 w-20 flex flex-col items-center gap-1 rounded-xl p-1.5 hover:bg-slate-100 cursor-pointer transition">
                  <UserAvatar name={f.display_name} src={f.avatar} mascot={f.mascot} size={44} />
                  <span className="text-xs font-semibold text-slate-700 w-full truncate text-center">{f.display_name || 'Bạn bè'}</span>
                  <span className="text-[11px] text-slate-500">{f.finished ? 'Đã phá đảo!' : `Cấp ${levelOf(f.node)}`}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">
              Chưa có bạn nào chơi {LANG_NAME[data.language] ?? ''} ở đây. <Link to="/friends">Rủ bạn bè</Link> cùng chơi để thấy họ trên bản đồ!
            </div>
          )}
        </section>
      )}
      {data.levels.map((level) => {
        const color = LEVEL_COLORS[level.level - 1]
        return (
          <section key={level.level} className="lp-card overflow-hidden">
            <div className="p-5 text-white flex items-center gap-4" style={{ background: color }}>
              <div className="flex-1 min-w-0">
                <div className="text-sm opacity-90">Cấp {level.level}</div>
                <div className="text-2xl font-extrabold">{level.name}</div>
                <div className="text-sm opacity-90">{level.description}</div>
              </div>
              <div className="text-right flex flex-col items-end gap-1">
                <div className="num text-xl font-bold">{level.done}/{level.total}</div>
                {!level.unlocked && <LockFilled className="text-2xl opacity-80" />}
                {!level.unlocked && <FriendsHere size={28}
                  friends={(data.friends ?? []).filter((f) => levelOf(f.node) === level.level)} />}
              </div>
            </div>
            {level.unlocked ? (
              <div className="pt-16 pb-10 flex flex-col items-center gap-9">
                {level.nodes.map((stop, k) => {
                  const shift = Math.round(Math.sin(k * 0.85) * 80)
                  return (
                    <div key={stop.id} id={`stop-${stop.id}`} className="relative" style={{ transform: `translateX(${shift}px)` }}>
                      <StopButton stop={stop} color={color} current={stop.id === data.current} onClick={() => tap(stop)} />
                      {/* friends stand beside the stop, on the side facing the middle of the path */}
                      <FriendsHere friends={friendsAt.get(stop.id) ?? []}
                        className={`absolute top-4 ${shift > 0 ? 'right-full mr-3' : 'left-full ml-3'}`} />
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="p-6 flex items-center gap-4 text-slate-500">
                <Prismo mood="sleepy" size={56} className="shrink-0" />
                Thắng màn trùm của cấp trước để mở cấp này.
              </div>
            )}
          </section>
        )
      })}
      <Modal open={!!chest} footer={null} onCancel={() => setChest(null)} centered>
        {chest && (
          <div className="flex flex-col items-center gap-4 py-4">
            <motion.div initial={{ rotate: 0, scale: 0.8 }} animate={{ rotate: [0, -8, 8, -6, 6, 0], scale: [0.8, 1, 1.15, 1] }}
              transition={{ duration: 0.9 }}>
              <AppIcon name="chest" size={120} />
            </motion.div>
            <div className="text-2xl font-extrabold text-slate-800">Rương đã mở!</div>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }}
              className="flex gap-6 text-xl font-bold">
              <span className="text-pink-500">+{chest.gems} ngọc</span>
              <span className="text-teal-600">+{chest.scales} vảy</span>
            </motion.div>
            <Button type="primary" size="large" onClick={() => setChest(null)}>Tuyệt quá!</Button>
          </div>
        )}
      </Modal>
    </div>
  )
}

// ====================================================================== play

export function GamePlayPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const node = useParams().node ?? ''
  const { tag } = useLang()
  const [round, setRound] = useState<GameRound | null>(null)
  const [error, setError] = useState('')
  const [at, setAt] = useState(0)
  const [intro, setIntro] = useState(true)
  const [results, setResults] = useState<boolean[][]>([])
  const [finish, setFinish] = useState<GameFinish | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [scales, setScales] = useState(0)
  const [left, setLeft] = useState<Record<HelperKind, number>>({ hint: 0, retry: 0 })

  useEffect(() => {
    setRound(null); setAt(0); setIntro(true); setResults([]); setFinish(null); setError('')
    playApi.round(node).then((r) => {
      setRound(r)
      setScales(r.helpers.scales)
      setLeft({ hint: r.helpers.per_round, retry: r.helpers.per_round })
    }).catch((e) => setError(errorMessage(e)))
  }, [node, attempt])

  const help: GameHelp | null = round && {
    scales, left, cost: round.helpers.cost, hintLabel: round.track === 'reading' ? 'Gợi ý' : 'Dịch nghĩa',
    buy: async (kind) => {
      try {
        const r = await playApi.help(node, round.token, kind)
        setScales(r.scales)
        setLeft((x) => ({ ...x, [kind]: r.left }))
        queryClient.invalidateQueries({ queryKey: ['game-summary'] })
        return true
      } catch (e) {
        message.error(errorMessage(e))
        return false
      }
    },
  }

  const done = async (r: boolean[]) => {
    if (!round) return
    const all = [...results, r]
    setResults(all)
    if (at + 1 < round.games.length) { setAt(at + 1); setIntro(true); return }
    try {
      setFinish(await playApi.finish(node, round.token, all))
      queryClient.invalidateQueries({ queryKey: ['game-map'] })
      queryClient.invalidateQueries({ queryKey: ['game-summary'] })
    } catch (e) {
      setError(errorMessage(e))
    }
  }

  if (error) {
    return <Result status="info" title={error} extra={[
      <Button key="map" onClick={() => navigate('/tro-choi')}>Về bản đồ</Button>,
      <Button key="learn" type="primary" onClick={() => navigate('/learn?kind=learn')}>Đi học</Button>]} />
  }
  if (!round) return <div className="flex justify-center py-20"><Spin size="large" /></div>

  if (finish) {
    const review = finish.review
    const learnAgain = review?.kind === 'words' ? `/learn?kind=review&words=${review.word_ids.join(',')}`
      : review?.kind === 'lesson' ? `/doc-viet/${review.lesson}` : null
    return (
      <Result
        icon={<div className="flex justify-center"><Prismo mood={finish.passed ? 'celebrate' : 'sad'} size={150} className="animate-pop" /></div>}
        title={!finish.passed ? 'Chưa qua màn này' : round.kind !== 'boss' ? 'Qua màn rồi!'
          : round.level === 4 ? 'Thắng màn trùm cuối! Bạn đã hoàn thành cả 4 cấp.' : 'Thắng màn trùm! Cấp mới đã mở.'}
        subTitle={
          <div className="flex flex-col items-center gap-2">
            <Stars n={finish.stars} size="text-4xl" />
            <span>Đúng {finish.correct}/{finish.total} câu ({finish.percent}%) · cần {round.pass_percent}% để qua màn</span>
            {(finish.xp > 0 || finish.gems > 0) && (
              <span className="font-bold text-lg">
                {finish.xp > 0 && <span className="text-amber-500">+{finish.xp} XP </span>}
                {finish.gems > 0 && <span className="text-pink-500">+{finish.gems} ngọc</span>}
              </span>
            )}
            {!finish.passed && <span className="text-slate-600">Học lại những phần còn sai rồi quay lại chơi nhé!</span>}
          </div>
        }
        extra={finish.passed ? [
          <Button key="map" size="large" onClick={() => navigate('/tro-choi')}>Về bản đồ</Button>,
          finish.next && finish.next.kind !== 'chest' && finish.next.status === 'open'
            ? <Button key="next" size="large" type="primary" onClick={() => navigate(`/tro-choi/${finish.next!.id}`)}>Màn tiếp theo</Button>
            : <Button key="go" size="large" type="primary" onClick={() => navigate('/tro-choi')}>
                {finish.next?.kind === 'chest' ? 'Đi mở rương' : 'Tiếp tục'}
              </Button>,
        ] : [
          <Button key="again" size="large" onClick={() => setAttempt((x) => x + 1)}>Chơi lại</Button>,
          learnAgain && <Button key="learn" size="large" type="primary" onClick={() => navigate(learnAgain)}>
            {review?.kind === 'lesson' ? `Học lại bài ${review.lesson}` : 'Ôn lại những từ còn sai'}
          </Button>,
        ]}
      />
    )
  }

  const game = round.games[at]
  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-5">
      <div className="flex items-center gap-3">
        <button type="button" onClick={() => navigate('/tro-choi')} aria-label="Thoát màn chơi"
          className="h-10 w-10 rounded-xl grid place-items-center text-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 cursor-pointer transition">
          <CloseOutlined />
        </button>
        <Progress percent={Math.round((at / round.games.length) * 100)} showInfo={false} className="flex-1 m-0" />
        <span className="num text-sm text-slate-500">{at + 1}/{round.games.length}</span>
        <Tooltip title={`Vảy để mua trợ giúp: ${help!.hintLabel.toLowerCase()} ${round.helpers.cost.hint} vảy, làm lại câu sai ${round.helpers.cost.retry} vảy`}>
          <span className="num flex items-center gap-1 rounded-xl bg-teal-50 px-2.5 py-1 text-sm font-bold text-teal-700" aria-label={`${scales} vảy`}>
            <ScaleIcon size={18} />{scales}
          </span>
        </Tooltip>
      </div>
      <AnimatePresence mode="wait">
        {intro ? (
          <motion.div key={`intro-${at}`} initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
            className="lp-card p-8 min-h-96 flex flex-col items-center justify-center gap-5 text-center">
            <div className="text-sm font-semibold text-slate-500">
              {round.kind === 'boss' ? 'Màn trùm' : round.title} · Trò chơi {at + 1}/{round.games.length}
            </div>
            <AppIcon name="game" size={84} />
            <div className="text-3xl font-extrabold text-slate-800">{GAME_NAMES[game.game]}</div>
            <div className="text-lg text-slate-600 max-w-md">{game.title}</div>
            <Button type="primary" size="large" onClick={() => setIntro(false)}>Bắt đầu</Button>
          </motion.div>
        ) : (
          <motion.div key={`game-${at}`} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }}
            className="lp-card p-6 sm:p-8 min-h-96 flex flex-col items-center gap-4">
            <div className="text-center text-slate-500 font-medium">{game.title}</div>
            <HelpContext.Provider value={help}>
              <MiniGameView game={game} lang={tag} onDone={done} />
            </HelpContext.Provider>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
