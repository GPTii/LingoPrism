import { useQuery } from '@tanstack/react-query'
import { Button, Popover } from 'antd'
import { SmileOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { gameApi } from '../api/app'

/** Rewards artwork stored as an app asset path ("assets/rewards/…") → the same picture on the web ("/rewards/…"). */
export function rewardUrl(path: string | null | undefined): string | null {
  return path?.startsWith('assets/rewards/') ? `/${path.slice('assets/'.length)}` : null
}

export const stickerUrl = (code: string) => `/rewards/stickers/${code}.png`

/** A sent sticker, in a comment or a chat bubble. */
export function StickerImage({ code, size = 96 }: { code: string; size?: number }) {
  return <img src={stickerUrl(code)} alt="Sticker" width={size} height={Math.round(size * 294 / 282)} loading="lazy" className="block select-none" draggable={false} />
}

/** The smiley button next to a message box: my stickers in a grid, or the way to the shop when I have none. */
export function StickerPicker({ onPick, disabled }: { onPick: (code: string) => void; disabled?: boolean }) {
  const [open, setOpen] = useState(false)
  const mine = useQuery({ queryKey: ['my-stickers'], queryFn: gameApi.stickers, enabled: open, staleTime: 60_000 })
  const content = (
    <div className="w-[300px] max-w-[calc(100vw-48px)]">
      {mine.data && mine.data.length === 0 ? (
        <div className="text-center py-3 px-2">
          <img src={stickerUrl('hello')} alt="" width={84} className="mx-auto" />
          <p className="text-sm text-slate-600 mt-2 mb-3">Bạn chưa có sticker nào. Mua gói sticker Prismo trong cửa hàng nhé!</p>
          <Link to="/achievements#stickers" onClick={() => setOpen(false)}><Button type="primary">Đến cửa hàng</Button></Link>
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-1 max-h-[280px] overflow-y-auto">
          {(mine.data ?? []).map((s) => (
            <button key={s.code} type="button" title={s.caption} aria-label={s.caption}
              className="rounded-xl p-1 cursor-pointer bg-transparent border-0 hover:bg-slate-100 transition-transform active:scale-95"
              onClick={() => { onPick(s.code); setOpen(false) }}>
              <img src={stickerUrl(s.code)} alt={s.caption} className="w-full h-auto block" loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
  return (
    <Popover trigger="click" open={open} onOpenChange={setOpen} content={content} placement="topRight">
      <Button icon={<SmileOutlined />} aria-label="Gửi sticker" title="Sticker" disabled={disabled} />
    </Popover>
  )
}
