import { useQuery } from '@tanstack/react-query'
import { App, Button, Dropdown, Space, Tooltip } from 'antd'
import { AudioOutlined, DownOutlined, TranslationOutlined, UndoOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { learnApi, type TranslateLang } from '../api/app'
import { errorMessage } from '../api/client'
import { canRecognise, listen } from '../lib/pronounce'

const LANGS: { value: TranslateLang; label: string; locale: string }[] = [
  { value: 'vi', label: 'Tiếng Việt', locale: 'vi-VN' },
  { value: 'en', label: 'Tiếng Anh', locale: 'en-US' },
  { value: 'zh-Hans', label: 'Tiếng Trung giản thể', locale: 'zh-CN' },
  { value: 'zh-Hant', label: 'Tiếng Trung phồn thể', locale: 'zh-TW' },
]
const label = (l: TranslateLang) => LANGS.find((x) => x.value === l)!.label

function remembered(key: string, fallback: TranslateLang): TranslateLang {
  try {
    const v = localStorage.getItem(key) as TranslateLang | null
    return v && LANGS.some((l) => l.value === v) ? v : fallback
  } catch {
    return fallback
  }
}
function remember(key: string, v: string) {
  try {
    localStorage.setItem(key, v)
  } catch {
    /* private window */
  }
}

/**
 * Above a chat box: speak instead of typing (the words land in the box), and turn what is in the box into
 * another language before sending it (machine translation, shown as such to the sender, with pinyin).
 */
export default function ChatVoiceTools({ text, setText, disabled }: { text: string; setText: (t: string) => void; disabled?: boolean }) {
  const { message } = App.useApp()
  const status = useQuery({ queryKey: ['ai-status'], queryFn: learnApi.aiStatus, staleTime: 5 * 60_000 })
  const [micLang, setMicLang] = useState<TranslateLang>(() => remembered('lp-chat-mic', 'vi'))
  const [listening, setListening] = useState(false)
  const [busy, setBusy] = useState(false)
  // the last translation, so it can be undone; forgotten as soon as the box no longer holds it
  const [done, setDone] = useState<{ original: string; result: string; target: TranslateLang; reading: string } | null>(null)
  const stop = useRef<(() => void) | undefined>(undefined)
  useEffect(() => () => stop.current?.(), [])
  const shown = done && done.result === text ? done : null

  const talk = async () => {
    if (listening) {
      stop.current?.()
      return
    }
    const { result, stop: s } = listen(LANGS.find((l) => l.value === micLang)!.locale, 15000)
    stop.current = s
    setListening(true)
    try {
      const heard = (await result).alternatives[0]?.trim() ?? ''
      if (heard) setText(text.trim() ? `${text.trim()} ${heard}` : heard)
    } catch (e) {
      message.warning((e as Error).message)
    } finally {
      setListening(false)
    }
  }

  const translate = async (target: TranslateLang) => {
    remember('lp-chat-to', target)
    const original = text.trim()
    if (!original) {
      message.info('Nhập hoặc nói một câu trước rồi hãy dịch.')
      return
    }
    setBusy(true)
    try {
      const out = await learnApi.translate(original, 'auto', target)
      setText(out.translation)
      setDone({ original, result: out.translation, target, reading: out.reading })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const mic = canRecognise()
  const canTranslate = !!status.data?.translate
  if (!mic && !canTranslate) return null
  const lastTarget = remembered('lp-chat-to', 'en')

  return (
    <div className="flex flex-col gap-1.5">
      {shown && (
        <div className="flex flex-wrap items-center gap-x-2 text-xs text-slate-500" aria-live="polite">
          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-semibold text-slate-600">Bản dịch máy</span>
          <span>sang {label(shown.target)}</span>
          {shown.reading && <span className="text-slate-600">· {shown.reading}</span>}
          <button
            type="button"
            className="inline-flex items-center gap-1 font-semibold text-brand-600 hover:text-brand-700 cursor-pointer"
            onClick={() => {
              setText(shown.original)
              setDone(null)
            }}
          >
            <UndoOutlined /> Hoàn tác
          </button>
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2">
        {mic && (
          <Space.Compact size="small">
            <Tooltip title={listening ? 'Chạm để dừng' : `Nói bằng ${label(micLang)}`}>
              <Button
                size="small"
                type={listening ? 'primary' : 'default'}
                danger={listening}
                icon={<AudioOutlined />}
                disabled={disabled}
                onClick={talk}
                aria-label={listening ? 'Dừng nghe' : `Nói bằng ${label(micLang)}`}
              >
                {listening ? 'Đang nghe…' : 'Nói'}
              </Button>
            </Tooltip>
            <Dropdown
              disabled={disabled || listening}
              trigger={['click']}
              menu={{
                selectable: true,
                selectedKeys: [micLang],
                items: LANGS.map((l) => ({ key: l.value, label: `Nói bằng ${l.label}` })),
                onClick: ({ key }) => {
                  setMicLang(key as TranslateLang)
                  remember('lp-chat-mic', key)
                },
              }}
            >
              <Button size="small" icon={<DownOutlined className="text-[10px]" />} aria-label="Chọn ngôn ngữ nói" />
            </Dropdown>
          </Space.Compact>
        )}
        {canTranslate && (
          <Dropdown
            disabled={disabled || busy || !text.trim()}
            trigger={['click']}
            menu={{
              selectable: true,
              selectedKeys: [lastTarget],
              items: LANGS.map((l) => ({ key: l.value, label: `Dịch sang ${l.label}` })),
              onClick: ({ key }) => translate(key as TranslateLang),
            }}
          >
            <Button size="small" icon={<TranslationOutlined />} loading={busy} aria-label="Dịch tin nhắn trước khi gửi">
              Dịch <DownOutlined className="text-[10px]" />
            </Button>
          </Dropdown>
        )}
      </div>
    </div>
  )
}
