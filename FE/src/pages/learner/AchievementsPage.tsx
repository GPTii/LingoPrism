import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Calendar, Progress, Skeleton } from 'antd'
import { CheckOutlined, ThunderboltFilled } from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { gameApi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { BadgeMedal, FreezeIcon, GemIcon, Prismo, ScaleIcon, StreakIcon, XpIcon } from '../../components/brand/Brand'
import { Facts, PageHeader, Section } from '../../components/ui'
import { QuestGo } from '../../components/QuestGo'

/** the item drawn from the brand set: ice block, Prismo sticker, or the XP star */
const itemIcon = (i: { code: string; effect: string }) =>
  i.effect === 'streak_freeze' ? <FreezeIcon size={26} />
    : i.effect === 'sticker' ? <Prismo size={30} mood={i.code.includes('sad') ? 'sad' : i.code.includes('love') ? 'celebrate' : 'happy'} />
      : <XpIcon size={26} />

const price = (i: { cost_scales: number | null; cost_gems: number | null }) =>
  i.cost_scales ? <>{i.cost_scales} <ScaleIcon size={16} /></> : <>{i.cost_gems} <GemIcon size={16} /></>

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
  const refresh = () => ['game-summary', 'quests', 'shop', 'badges'].forEach((k) => queryClient.invalidateQueries({ queryKey: [k] }))
  const act = useMutation({
    mutationFn: ({ fn }: { fn: () => Promise<unknown>; done: string }) => fn(),
    onSuccess: (_, v) => { message.success(v.done); refresh() },
    onError: (e) => message.error(errorMessage(e)),
  })
  // menu links like /achievements#shop land on their section (and highlight it briefly)
  const { hash } = useLocation()
  useEffect(() => {
    if (!hash) return
    const t = window.setTimeout(() => {
      const el = document.getElementById(hash.slice(1))
      el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 60)
    return () => window.clearTimeout(t)
  }, [hash, badges.isSuccess, shop.isSuccess])
  const s = summary.data
  const owned = badges.data?.filter((b) => b.owned).length ?? 0

  const cell = (d: Dayjs) => {
    const p = days.get(d.format('YYYY-MM-DD'))
    if (!p) return null
    return <div className="flex justify-center">{p.freeze_used ? <FreezeIcon size={18} /> : p.active ? <StreakIcon size={18} /> : null}</div>
  }

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <PageHeader title="Thành tích" description="Chuỗi ngày học, nhiệm vụ, huy hiệu và cửa hàng đổi vảy, ngọc." />

      <Section>
        <Facts items={[
          { label: 'ngày học liên tiếp', value: s?.streak ?? 0, icon: <StreakIcon size={24} active={!!s?.studied_today} /> },
          { label: 'tổng kinh nghiệm', value: (s?.lifetime_xp ?? 0).toLocaleString('vi-VN'), icon: <XpIcon size={24} /> },
          { label: 'XP hôm nay', value: s?.today_xp ?? 0, hint: `/ ${s?.daily_xp_cap ?? 500}` },
          { label: 'vảy', value: s?.scales ?? 0, icon: <ScaleIcon size={24} /> },
          { label: 'ngọc', value: s?.gems ?? 0, icon: <GemIcon size={24} /> },
        ]} />
        {s?.active_boosts.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {s.active_boosts.map((b) => (
              <span key={b.item} className="inline-flex items-center gap-1.5 rounded-lg bg-amber-50 text-amber-700 px-2.5 py-1 text-sm font-semibold">
                <ThunderboltFilled /> {b.name} ×{b.multiplier} đến {dayjs(b.expires_at).format('HH:mm DD/MM')}
              </span>
            ))}
          </div>
        ) : null}
      </Section>

      <div className="grid lg:grid-cols-2 gap-6">
        <Section id="quests" title="Nhiệm vụ hằng ngày">
          {quests.isLoading ? <Skeleton active /> : (
            <ul className="m-0 p-0 list-none flex flex-col gap-4">
              {quests.data?.quests.map((q) => (
                <li key={q.id}>
                  <div className="flex justify-between items-center gap-3">
                    <span className={`font-medium ${q.reward_claimed ? 'text-slate-400' : 'text-slate-700'}`}>{q.title}</span>
                    {q.completed && !q.reward_claimed ? (
                      <Button size="small" type="primary" loading={act.isPending}
                        onClick={() => act.mutate({ fn: () => gameApi.claim(q.id), done: `Đã nhận ${q.reward_scales} vảy` })}>
                        Nhận {q.reward_scales} <ScaleIcon size={14} />
                      </Button>
                    ) : q.reward_claimed ? <span className="text-sm font-semibold text-emerald-600"><CheckOutlined /> Đã nhận</span>
                      : !q.completed ? <QuestGo kind={q.kind} title={q.title} /> : null}
                  </div>
                  <Progress percent={Math.round((q.progress / Math.max(q.target, 1)) * 100)} format={() => `${q.progress}/${q.target}`}
                    strokeColor={q.completed ? '#10c79a' : undefined} />
                </li>
              ))}
            </ul>
          )}
          {quests.data && (
            <div className="mt-5 pt-5 border-t border-slate-200">
              <div className="flex justify-between items-center gap-3">
                <span className="font-semibold text-slate-700">Nhiệm vụ tháng: hoàn thành {quests.data.monthly.target} nhiệm vụ</span>
                {quests.data.monthly.completed_count >= quests.data.monthly.target && !quests.data.monthly.reward_claimed && (
                  <Button size="small" type="primary"
                    onClick={() => act.mutate({ fn: gameApi.claimMonthly, done: `Đã nhận ${quests.data!.monthly.reward_gems} ngọc` })}>
                    Nhận {quests.data.monthly.reward_gems} <GemIcon size={14} />
                  </Button>
                )}
              </div>
              <Progress percent={Math.round((quests.data.monthly.completed_count / Math.max(quests.data.monthly.target, 1)) * 100)}
                format={() => `${quests.data!.monthly.completed_count}/${quests.data!.monthly.target}`} />
            </div>
          )}
        </Section>

        <Section id="calendar" title="Lịch học">
          <Calendar fullscreen={false} value={month} onPanelChange={(d) => setMonth(d)} cellRender={(d, info) => (info.type === 'date' ? cell(d) : null)} />
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500">
            <span className="inline-flex items-center gap-1"><StreakIcon size={14} /> ngày có học</span>
            <span className="inline-flex items-center gap-1"><FreezeIcon size={14} /> dùng Đá băng giữ chuỗi</span>
            <span>Đá băng còn: <b className="num text-slate-700">{s?.streak_freezes ?? 0}</b></span>
          </div>
        </Section>
      </div>

      <Section id="badges" title="Huy hiệu" extra={badges.data && <span className="num text-sm text-slate-500">{owned}/{badges.data.length} đã có</span>}>
        <ul className="m-0 p-0 list-none grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-4 gap-y-6">
          {badges.data?.map((b, i) => (
            <li key={b.code} className={`flex flex-col items-center text-center gap-1 ${b.owned ? '' : 'opacity-60'}`}>
              <BadgeMedal owned={b.owned} seed={i} size={52} />
              <div className={`font-semibold leading-snug ${b.owned ? 'text-slate-800' : 'text-slate-500'}`}>{b.name}</div>
              <div className="text-xs text-slate-500 max-w-[22ch]">{b.description}</div>
              {b.owned && b.awarded_at && <div className="text-xs text-emerald-600 font-medium">{dayjs(b.awarded_at).format('DD/MM/YYYY')}</div>}
            </li>
          ))}
        </ul>
      </Section>

      <Section id="shop" title="Cửa hàng" extra={<span className="text-sm text-slate-500">Đổi vảy và ngọc lấy vật phẩm hỗ trợ</span>}>
        <ul className="m-0 p-0 list-none grid md:grid-cols-3 gap-3">
          {shop.data?.map((i) => (
            <li key={i.id} className="rounded-xl bg-slate-50 p-4 flex flex-col gap-2">
              <div className="flex items-center gap-2 font-semibold text-slate-800">
                {itemIcon(i)}
                <span className="flex-1">{i.name}</span>
                {i.owned > 0 && <span className="num text-sm font-medium text-slate-500">đang có {i.owned}</span>}
              </div>
              <div className="text-sm text-slate-500 flex-1">{i.description}</div>
              <div className="flex gap-2 pt-1">
                <Button type="primary" onClick={() => act.mutate({ fn: () => gameApi.buy(i.id), done: `Đã mua ${i.name}` })}>
                  Mua · {price(i)}
                </Button>
                {i.owned > 0 && (i.effect === 'xp_double_15m' || i.effect === 'xp_plus25_24h') && (
                  <Button onClick={() => act.mutate({ fn: () => gameApi.use(i.id), done: `Đã dùng ${i.name}` })}>Dùng ngay</Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  )
}
