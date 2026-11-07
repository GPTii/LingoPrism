import { useQuery } from '@tanstack/react-query'
import { App, Dropdown } from 'antd'
import { HeartFilled, HeartOutlined, MoreOutlined, TranslationOutlined } from '@ant-design/icons'
import { useState, type ReactNode } from 'react'
import { learnApi } from '../api/app'
import { errorMessage } from '../api/client'

/**
 * One chat bubble with a small "⋯" menu: put a heart on it, or translate it into Vietnamese (a machine
 * translation shown under the bubble, only to me). The hearts are shown under the bubble; tapping them toggles mine.
 */
export default function MessageActions({
  children,
  text,
  hearts = [],
  meId,
  mine,
  onHeart,
}: {
  children: ReactNode
  /** the text of the message ('' for a sticker: nothing to translate) */
  text: string
  hearts?: number[]
  meId?: number
  mine: boolean
  onHeart?: () => void
}) {
  const { message } = App.useApp()
  const status = useQuery({ queryKey: ['ai-status'], queryFn: learnApi.aiStatus, staleTime: 5 * 60_000 })
  const [translation, setTranslation] = useState<{ text: string; reading: string } | null>(null)
  const [shown, setShown] = useState(false)
  const [busy, setBusy] = useState(false)
  const hearted = !!meId && hearts.includes(meId)

  const translate = async () => {
    if (translation) {
      setShown(!shown)
      return
    }
    setBusy(true)
    try {
      const out = await learnApi.translate(text, 'auto', 'vi')
      setTranslation({ text: out.translation, reading: out.source_reading })
      setShown(true)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const items = [
    onHeart && {
      key: 'heart',
      icon: hearted ? <HeartFilled className="text-rose-500" /> : <HeartOutlined />,
      label: hearted ? 'Bỏ tim' : 'Thả tim',
    },
    text.trim() &&
      status.data?.translate && {
        key: 'translate',
        icon: <TranslationOutlined />,
        label: busy ? 'Đang dịch…' : translation && shown ? 'Ẩn bản dịch' : 'Dịch sang tiếng Việt',
      },
  ].filter(Boolean) as { key: string; icon: ReactNode; label: string }[]

  return (
    <div className={`group flex flex-col max-w-[75%] ${mine ? 'items-end' : 'items-start'}`}>
      <div className={`flex items-center gap-1 max-w-full ${mine ? 'flex-row-reverse' : ''}`}>
        <div className="min-w-0">{children}</div>
        {items.length > 0 && (
          <Dropdown
            trigger={['click']}
            placement={mine ? 'bottomRight' : 'bottomLeft'}
            menu={{
              items,
              onClick: ({ key }) => (key === 'heart' ? onHeart?.() : translate()),
            }}
          >
            <button
              type="button"
              aria-label="Tuỳ chọn tin nhắn"
              className="shrink-0 h-7 w-7 grid place-items-center rounded-full text-slate-500 hover:bg-slate-100 hover:text-slate-800 cursor-pointer sm:opacity-0 sm:group-hover:opacity-100 focus-visible:opacity-100 aria-expanded:opacity-100"
            >
              <MoreOutlined className="rotate-90" />
            </button>
          </Dropdown>
        )}
      </div>
      {translation && shown && (
        <div className="mt-1 max-w-full rounded-xl border border-slate-200 bg-[var(--surface)] px-3 py-1.5 text-sm text-slate-700">
          {translation.reading && <div className="text-xs text-slate-500">{translation.reading}</div>}
          <div lang="vi" className="whitespace-pre-wrap break-words">
            {translation.text}
          </div>
          <div className="text-[11px] text-slate-400">Bản dịch máy</div>
        </div>
      )}
      {hearts.length > 0 && (
        <button
          type="button"
          onClick={onHeart}
          disabled={!onHeart}
          aria-label={`${hearts.length} lượt thả tim${hearted ? ', có bạn' : ''}. Bấm để ${hearted ? 'bỏ tim' : 'thả tim'}`}
          className={`-mt-1.5 z-[1] inline-flex items-center gap-1 rounded-full border px-1.5 py-px text-xs cursor-pointer shadow-sm bg-[var(--surface)] ${
            hearted ? 'border-rose-200 text-rose-600' : 'border-slate-200 text-slate-500'
          }`}
        >
          <HeartFilled className="text-rose-500" />
          {hearts.length > 1 && <span className="num font-semibold">{hearts.length}</span>}
        </button>
      )}
    </div>
  )
}
