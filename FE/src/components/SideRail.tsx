import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Progress, Skeleton } from 'antd'
import { Link } from 'react-router-dom'
import { gameApi, type DailyQuest } from '../api/app'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/store'
import { AppIcon, type AppIconName } from './brand/AppIcon'
import { GemIcon, ScaleIcon, StreakIcon } from './brand/Brand'
import { QuestGo } from './QuestGo'

/** what each daily quest is about (gamification DailyQuest.Kind) */
const QUEST_ICON: Record<string, AppIconName> = {
  save_words: 'camera',
  reach_learn_goal: 'sparkle',
  reach_review_goal: 'review',
  win_games: 'game',
  post_community_image: 'photo',
  engage_community: 'community',
}

const rank = (q: DailyQuest) => (q.completed && !q.reward_claimed ? 0 : !q.completed ? 1 : 2)

function Card({ title, link, children }: { title: string; link?: { to: string; label: string }; children: React.ReactNode }) {
  return (
    <section className="lp-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="m-0 text-base font-extrabold text-slate-900">{title}</h2>
        {link && (
          <Link to={link.to} className="text-xs font-bold uppercase tracking-wide">
            {link.label}
          </Link>
        )}
      </div>
      {children}
    </section>
  )
}

function Quest({ q }: { q: DailyQuest }) {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const claim = useMutation({
    mutationFn: () => gameApi.claim(q.id),
    onSuccess: (r) => {
      message.success(`+${r.scales} vảy${r.gems ? `, +${r.gems} ngọc` : ''}`)
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      queryClient.invalidateQueries({ queryKey: ['game-summary'] })
    },
    onError: (e) => message.error(errorMessage(e)),
  })
  const pct = Math.round((Math.min(q.progress, q.target) / Math.max(q.target, 1)) * 100)
  return (
    <li className="flex items-center gap-3">
      <AppIcon name={QUEST_ICON[q.kind] ?? 'target'} size={36} className="shrink-0" />
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-bold leading-snug ${q.reward_claimed ? 'text-slate-400' : 'text-slate-800'}`}>{q.title}</div>
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Progress
              percent={pct}
              showInfo={false}
              size={['100%', 14]}
              strokeColor={q.completed ? '#10c79a' : '#ffc800'}
              className="!m-0"
            />
            <span className="num absolute inset-0 grid place-items-center text-[10px] font-bold text-slate-600">
              {Math.min(q.progress, q.target)} / {q.target}
            </span>
          </div>
          {/* the reward: a chest that opens when the quest is done */}
          {q.completed && !q.reward_claimed ? (
            <Button size="small" type="primary" loading={claim.isPending} onClick={() => claim.mutate()} className="!px-2">
              Nhận
            </Button>
          ) : (
            <span title={`${q.reward_scales} vảy`} className={q.reward_claimed ? 'opacity-40' : ''}>
              <AppIcon name="chest" size={26} />
            </span>
          )}
        </div>
      </div>
      {!q.completed && <QuestGo kind={q.kind} title={q.title} />}
    </li>
  )
}

/**
 * Right-hand column of the wide screens (like Duolingo's): the day's streak, the league, the daily quests with their
 * chests, the month's challenge. Shown from the xl breakpoint; the same things are on Home / Thành tích on phones.
 */
export default function SideRail() {
  const user = useAuth((s) => s.user)
  const game = useQuery({ queryKey: ['game-summary'], queryFn: gameApi.summary, enabled: !!user })
  const quests = useQuery({ queryKey: ['quests'], queryFn: gameApi.quests, enabled: !!user })
  const g = game.data
  const league = g?.league
  const monthly = quests.data?.monthly

  return (
    <aside className="hidden xl:flex flex-col gap-4 w-80 shrink-0 sticky top-20 self-start" aria-label="Nhiệm vụ và tiến độ">
      <Card title="Hôm nay">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-xl bg-slate-50 py-2">
            <div className="flex justify-center">
              <StreakIcon active={!!g?.studied_today} size={26} />
            </div>
            <div className="num font-extrabold text-slate-800">{g?.streak ?? 0}</div>
            <div className="text-[11px] text-slate-500">ngày liên tiếp</div>
          </div>
          <div className="rounded-xl bg-slate-50 py-2">
            <div className="flex justify-center">
              <AppIcon name="sparkle" size={26} />
            </div>
            <div className="num font-extrabold text-slate-800">{g?.today_xp ?? 0}</div>
            <div className="text-[11px] text-slate-500">XP hôm nay</div>
          </div>
          <div className="rounded-xl bg-slate-50 py-2">
            <div className="flex justify-center gap-1">
              <ScaleIcon size={22} />
              <GemIcon size={22} />
            </div>
            <div className="num font-extrabold text-slate-800">
              {g?.scales ?? 0} · {g?.gems ?? 0}
            </div>
            <div className="text-[11px] text-slate-500">vảy · ngọc</div>
          </div>
        </div>
        {g && !g.studied_today && (
          <Link
            to="/learn?kind=learn"
            className="mt-3 block text-center rounded-xl bg-amber-50 text-amber-700 text-sm font-semibold py-2 !no-underline"
          >
            Học một bài để giữ chuỗi {g.streak > 0 ? `${g.streak} ngày` : 'ngày học'}!
          </Link>
        )}
      </Card>

      <Card title={league ? `Giải ${league.tier}` : 'Bảng xếp hạng'} link={{ to: '/community?tab=leaderboard', label: 'Xem' }}>
        {league ? (
          <div className="flex items-center gap-3">
            <AppIcon name="podium" size={44} />
            <div className="text-sm text-slate-600">
              Tuần này bạn có <b className="num text-slate-900">{league.weekly_xp} XP</b>. Học và chơi thêm để lên hạng!
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <AppIcon name="medal" size={44} className="opacity-70" />
            <div className="text-sm text-slate-600">Hoàn thành vài bài học để bắt đầu thi đấu cùng mọi người.</div>
          </div>
        )}
      </Card>

      <Card title="Nhiệm vụ hằng ngày" link={{ to: '/achievements#quests', label: 'Xem tất cả' }}>
        {quests.isLoading ? (
          <Skeleton active paragraph={{ rows: 3 }} title={false} />
        ) : (
          <ul className="m-0 p-0 list-none flex flex-col gap-4">
            {/* a reward to collect first, then what is left to do, the collected ones last */}
            {[...(quests.data?.quests ?? [])]
              .sort((a, b) => rank(a) - rank(b))
              .map((q) => (
                <Quest key={q.id} q={q} />
              ))}
            {!quests.data?.quests.length && <li className="text-sm text-slate-500">Học một bài để mở nhiệm vụ hôm nay.</li>}
          </ul>
        )}
      </Card>

      {monthly && (
        <Card title="Thử thách tháng">
          <div className="flex items-center gap-3">
            <AppIcon name="calendar" size={40} />
            <div className="flex-1">
              <div className="text-sm font-semibold text-slate-700">Hoàn thành {monthly.target} nhiệm vụ trong tháng</div>
              <Progress
                percent={Math.round((Math.min(monthly.completed_count, monthly.target) / Math.max(monthly.target, 1)) * 100)}
                format={() => `${monthly.completed_count}/${monthly.target}`}
                size="small"
                strokeColor="#a78bfa"
              />
            </div>
            <span className="num inline-flex items-center gap-1 text-sm font-bold text-slate-600">
              <GemIcon size={16} />
              {monthly.reward_gems}
            </span>
          </div>
        </Card>
      )}
    </aside>
  )
}
