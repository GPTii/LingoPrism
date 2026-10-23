import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Input, Segmented, Skeleton, Switch } from 'antd'
import { CheckOutlined, LockFilled } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { gameApi, type Outfit, type OutfitSlot, type Wardrobe } from '../../api/app'
import { errorMessage } from '../../api/client'
import type { MascotLook } from '../../api/types'
import { useAuth } from '../../auth/store'
import { GemIcon, PrismoAvatar } from '../../components/brand/Brand'
import { PageHeader, Section } from '../../components/ui'
import { prismoMood } from '../../lib/prismoMood'

const lookOf = (w: Wardrobe, wearing = w.wearing): MascotLook => ({ name: w.name, as_avatar: w.as_avatar, ...wearing })

/** Tủ đồ Prismo: try any piece on, buy it with ngọc, wear or take off what you own, name your Prismo. */
export default function WardrobePage() {
  const { message, modal } = App.useApp()
  const queryClient = useQueryClient()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const wardrobe = useQuery({ queryKey: ['wardrobe'], queryFn: gameApi.wardrobe })
  const summary = useQuery({ queryKey: ['game-summary'], queryFn: gameApi.summary })
  const quests = useQuery({ queryKey: ['quests'], queryFn: gameApi.quests })
  const [slot, setSlot] = useState<OutfitSlot>('hat')
  const [trying, setTrying] = useState<Outfit | null>(null)
  const [name, setName] = useState('')
  const w = wardrobe.data
  useEffect(() => { if (w) setName(w.name) }, [w?.name]) // eslint-disable-line react-hooks/exhaustive-deps

  // what everyone else sees follows every change
  const saved = (next: Wardrobe) => {
    queryClient.setQueryData(['wardrobe'], next)
    if (user) setUser({ ...user, mascot: lookOf(next) })
  }
  const change = useMutation({
    mutationFn: (fn: () => Promise<Wardrobe>) => fn(),
    onSuccess: saved,
    onError: (e) => message.error(errorMessage(e)),
  })

  const shown = useMemo(() => {
    if (!w) return null
    return lookOf(w, trying ? { ...w.wearing, [trying.slot]: trying.code } : w.wearing)
  }, [w, trying])
  const questsDone = !!quests.data?.quests.length && quests.data.quests.every((q) => q.completed)
  const { mood, line } = prismoMood(summary.data, questsDone, w?.name)

  if (wardrobe.isLoading || !w || !shown) return <div className="max-w-6xl mx-auto"><Skeleton active /></div>

  const pieces = w.outfits.filter((o) => o.slot === slot)
  const ownedCount = w.outfits.filter((o) => o.owned).length
  const wearing = trying && w.wearing[trying.slot] === trying.code

  const buy = (o: Outfit) => modal.confirm({
    title: `Mua ${o.name}?`,
    content: <span className="inline-flex items-center gap-1">Giá {o.cost_gems} <GemIcon size={16} />. Bạn đang có {w.gems} ngọc.</span>,
    okText: 'Mua', cancelText: 'Huỷ',
    onOk: () => change.mutateAsync(() => gameApi.buyOutfit(o.code)).then(() => message.success(`Prismo đã mặc ${o.name}!`)),
  })

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <PageHeader title="Tủ đồ Prismo"
        description="Mặc đồ cho Prismo của bạn. Đồ mua bằng ngọc; có món chỉ mở được bằng huy hiệu, có món chỉ bán trong dịp lễ."
        actions={<span className="num inline-flex items-center gap-1.5 rounded-xl bg-brand-50 px-3 py-1.5 text-lg font-bold text-brand-700">
          {w.gems} <GemIcon size={22} /></span>} />

      <div className="grid lg:grid-cols-[360px_1fr] gap-6 items-start">
        <Section className="lg:sticky lg:top-20">
          <div className="flex flex-col items-center gap-4">
            <PrismoAvatar look={shown} size={260} mood={mood} square />
            {line && <p className="m-0 text-center text-slate-600">{line}</p>}

            {trying ? (
              <div className="w-full rounded-2xl bg-slate-50 p-4 flex flex-col gap-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-bold text-slate-800">{trying.name}</span>
                  {trying.owned ? <span className="text-sm font-semibold text-emerald-600"><CheckOutlined /> Đã có</span>
                    : trying.cost_gems && !trying.badge ? <span className="num inline-flex items-center gap-1 font-bold text-brand-700">{trying.cost_gems} <GemIcon size={16} /></span> : null}
                </div>
                {trying.how && <div className="text-sm text-slate-500">{trying.how}</div>}
                <div className="flex gap-2">
                  {trying.owned ? (
                    <Button type="primary" block loading={change.isPending}
                      onClick={() => change.mutate(() => gameApi.dress({ wearing: { [trying.slot]: wearing ? '' : trying.code } }))}>
                      {wearing ? 'Tháo ra' : 'Mặc vào'}
                    </Button>
                  ) : trying.for_sale ? (
                    <Button type="primary" block disabled={w.gems < (trying.cost_gems ?? 0)} onClick={() => buy(trying)}>
                      {w.gems < (trying.cost_gems ?? 0) ? 'Chưa đủ ngọc' : <span className="inline-flex items-center gap-1">Mua · {trying.cost_gems} <GemIcon size={16} /></span>}
                    </Button>
                  ) : trying.badge ? (
                    <Link to="/achievements#badges" className="flex-1"><Button block icon={<LockFilled />}>Xem huy hiệu</Button></Link>
                  ) : <Button block disabled icon={<LockFilled />}>Chưa bán lúc này</Button>}
                  <Button onClick={() => setTrying(null)}>Bỏ thử</Button>
                </div>
              </div>
            ) : (
              <div className="w-full flex flex-col gap-3">
                <label className="flex flex-col gap-1">
                  <span className="text-sm font-semibold text-slate-600">Tên linh vật</span>
                  <Input value={name} maxLength={20} onChange={(e) => setName(e.target.value)} aria-label="Tên linh vật"
                    onBlur={() => name.trim() && name.trim() !== w.name && change.mutate(() => gameApi.dress({ name: name.trim() }))}
                    onPressEnter={(e) => (e.target as HTMLInputElement).blur()} />
                </label>
                <label className="flex items-center justify-between gap-3 cursor-pointer">
                  <span>
                    <span className="block font-semibold text-slate-700">Dùng làm ảnh đại diện</span>
                    <span className="block text-sm text-slate-500">Mọi người thấy {w.name} thay cho ảnh của bạn</span>
                  </span>
                  <Switch checked={w.as_avatar} onChange={(v) => change.mutate(() => gameApi.dress({ as_avatar: v }))} />
                </label>
                <p className="m-0 text-sm text-slate-500">Đã có {ownedCount}/{w.outfits.length} món. Chọn một món bên cạnh để thử.</p>
              </div>
            )}
          </div>
        </Section>

        <Section>
          <Segmented<OutfitSlot> block value={slot} onChange={(v) => setSlot(v)}
            options={w.slots.map((s) => ({ value: s.code, label: s.label }))} />
          <ul className="m-0 mt-5 p-0 list-none grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
            {pieces.map((o) => {
              const on = w.wearing[o.slot] === o.code
              const locked = !o.owned && !o.for_sale
              // each piece shown on a plain Prismo (a background on its own)
              const preview: MascotLook = { name: w.name, as_avatar: false, background: '', hat: '', glasses: '', neck: '', hand: '', [o.slot]: o.code }
              return (
                <li key={o.code}>
                  <button type="button" onClick={() => setTrying(o)} aria-pressed={trying?.code === o.code}
                    className={`w-full cursor-pointer rounded-2xl border-2 bg-white p-2.5 flex flex-col items-center gap-1.5 text-center transition-colors ${
                      trying?.code === o.code ? 'border-brand-500' : on ? 'border-emerald-400' : 'border-slate-100 hover:border-slate-300'}`}>
                    <span className="relative">
                      <PrismoAvatar look={preview} size={112} square className={locked ? 'opacity-60' : ''} />
                      {locked && <LockFilled className="absolute right-1.5 bottom-1.5 rounded-full bg-white p-1 text-slate-500" />}
                    </span>
                    <span className="font-semibold text-slate-800 leading-tight">{o.name}</span>
                    {on ? <span className="text-xs font-semibold text-emerald-600">Đang mặc</span>
                      : o.owned ? <span className="text-xs font-semibold text-slate-500">Đã có</span>
                        : o.for_sale ? <span className="num inline-flex items-center gap-1 text-sm font-bold text-brand-700">{o.cost_gems} <GemIcon size={14} /></span>
                          : <span className="text-xs text-slate-500 leading-snug">{o.badge ? 'Mở bằng huy hiệu' : 'Dịp lễ'}</span>}
                    {o.event && !o.owned && o.for_sale && <span className="text-[11px] font-semibold text-amber-600">Chỉ bán dịp lễ</span>}
                  </button>
                </li>
              )
            })}
          </ul>
        </Section>
      </div>
    </div>
  )
}
