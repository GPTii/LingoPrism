import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Calendar, Card, Progress, Statistic, Tag } from 'antd'
import dayjs, { type Dayjs } from 'dayjs'
import { useState } from 'react'
import { gameApi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { GemIcon, ScaleIcon, StreakIcon, XpIcon } from '../../components/brand/Brand'

const Ice = () => <span className="inline-block h-4 w-4 rounded-[5px] bg-sky-300/80 border border-sky-400 align-middle" />

/** Thành tích: streak calendar, quests, badges and the shop (Vảy / Ngọc). */
export default function AchievementsPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [month, setMonth] = useState(dayjs())
  const summary = useQuery({ queryKey: ['game-summary'], queryFn: gameApi.summary })
  const quests = useQuery({ queryKey: ['quests'], queryFn: gameApi.quests })
  const badges = useQuery({ queryKey: ['badges'], queryFn: gameApi.badges })
  const shop = useQuery({ queryKey: ['shop'], queryFn: gameApi.shop })
  const progress = useQuery({
    queryKey: ['progress', month.format('YYYY-MM')],
    queryFn: () => gameApi.progress(month.startOf('month').format('YYYY-MM-DD'), month.endOf('month').format('YYYY-MM-DD')),
  })
  const days = new Map(progress.data?.map((d) => [d.date, d]))
  const refresh = () => ['game-summary', 'quests', 'shop'].forEach((k) => queryClient.invalidateQueries({ queryKey: [k] }))
  const act = useMutation({
    mutationFn: (fn: () => Promise<unknown>) => fn(),
    onSuccess: () => { message.success('Thành công'); refresh() },
    onError: (e) => message.error(errorMessage(e)),
  })
  const s = summary.data

  const cell = (d: Dayjs) => {
    const p = days.get(d.format('YYYY-MM-DD'))
    if (!p) return null
    return <div className="flex justify-center">{p.freeze_used ? <Ice /> : p.active ? <StreakIcon size={20} /> : null}</div>
  }

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <h1 className="text-3xl font-black text-slate-800 m-0">Thành tích</h1>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="lp-card !border-0"><Statistic title="Chuỗi ngày học" value={s?.streak ?? 0} prefix={<StreakIcon size={26} active={!!s?.studied_today} />} suffix="ngày" /></Card>
        <Card className="lp-card !border-0"><Statistic title="Tổng XP" value={s?.lifetime_xp ?? 0} prefix={<XpIcon size={26} />} /></Card>
        <Card className="lp-card !border-0"><Statistic title="XP hôm nay" value={s?.today_xp ?? 0} suffix={`/ ${s?.daily_xp_cap ?? 500}`} /></Card>
        <Card className="lp-card !border-0"><Statistic title="Vảy" value={s?.scales ?? 0} prefix={<ScaleIcon size={26} />} /></Card>
        <Card className="lp-card !border-0"><Statistic title="Ngọc" value={s?.gems ?? 0} prefix={<GemIcon size={26} />} /></Card>
      </div>
      {s?.active_boosts.length ? <div>{s.active_boosts.map((b) => <Tag key={b.item} color="gold">⚡ {b.name} x{b.multiplier} đến {dayjs(b.expires_at).format('HH:mm DD/MM')}</Tag>)}</div> : null}

      <div className="grid lg:grid-cols-2 gap-6">
        <Card title="Nhiệm vụ hằng ngày" className="!rounded-2xl">
          <div className="flex flex-col gap-4">
            {quests.data?.quests.map((q) => (
              <div key={q.id}>
                <div className="flex justify-between items-center">
                  <span>{q.title}</span>
                  {q.completed && !q.reward_claimed ? (
                    <Button size="small" type="primary" onClick={() => act.mutate(() => gameApi.claim(q.id))}>Nhận {q.reward_scales} <ScaleIcon size={16} /></Button>
                  ) : q.reward_claimed ? <Tag color="green">Đã nhận</Tag> : null}
                </div>
                <Progress percent={Math.round((q.progress / q.target) * 100)} format={() => `${q.progress}/${q.target}`} />
              </div>
            ))}
            {quests.data && (
              <div className="border-t pt-3">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Nhiệm vụ tháng: hoàn thành {quests.data.monthly.target} nhiệm vụ</span>
                  {quests.data.monthly.completed_count >= quests.data.monthly.target && !quests.data.monthly.reward_claimed && (
                    <Button size="small" type="primary" onClick={() => act.mutate(gameApi.claimMonthly)}>Nhận {quests.data.monthly.reward_gems} <GemIcon size={16} /></Button>
                  )}
                </div>
                <Progress percent={Math.round((quests.data.monthly.completed_count / quests.data.monthly.target) * 100)}
                  format={() => `${quests.data!.monthly.completed_count}/${quests.data!.monthly.target}`} strokeColor="#8b5cf6" />
              </div>
            )}
          </div>
        </Card>

        <Card title="Lịch học" className="!rounded-2xl">
          <Calendar fullscreen={false} value={month} onPanelChange={(d) => setMonth(d)} cellRender={(d, info) => (info.type === 'date' ? cell(d) : null)} />
          <div className="text-xs text-slate-500"><StreakIcon size={14} /> ngày có học · <Ice /> dùng Đá băng giữ streak · Đá băng còn: {s?.streak_freezes ?? 0}</div>
        </Card>
      </div>

      <Card title="Huy hiệu" className="!rounded-2xl">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {badges.data?.map((b) => (
            <div key={b.code} className={`text-center p-3 rounded-xl ${b.owned ? 'bg-amber-50' : 'opacity-40 grayscale'}`}>
              <div className="text-3xl">🏅</div>
              <div className="font-medium">{b.name}</div>
              <div className="text-xs text-slate-500">{b.description}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Cửa hàng" className="!rounded-2xl">
        <div className="grid md:grid-cols-3 gap-4">
          {shop.data?.map((i) => (
            <div key={i.id} className="rounded-xl border border-slate-200 p-4 flex flex-col gap-2">
              <div className="font-semibold">{i.name} {i.owned > 0 && <Tag>x{i.owned}</Tag>}</div>
              <div className="text-sm text-slate-500 flex-1">{i.description}</div>
              <div className="flex gap-2">
                <Button type="primary" onClick={() => act.mutate(() => gameApi.buy(i.id))}>
                  {i.cost_scales ? <>{i.cost_scales} <ScaleIcon size={16} /></> : <>{i.cost_gems} <GemIcon size={16} /></>}
                </Button>
                {i.owned > 0 && (i.effect === 'xp_double_15m' || i.effect === 'xp_plus25_24h') && (
                  <Button onClick={() => act.mutate(() => gameApi.use(i.id))}>Dùng</Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
