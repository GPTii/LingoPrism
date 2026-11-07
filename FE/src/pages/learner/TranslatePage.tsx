import { useMutation, useQuery } from '@tanstack/react-query'
import { App, Button, Input, Select, Tooltip } from 'antd'
import { AudioOutlined, CheckOutlined, CopyOutlined, PlusOutlined, SoundOutlined, SwapOutlined } from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { learnApi, type TranslateLang, type TranslatedWord, type Translation } from '../../api/app'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'
import { Prismo } from '../../components/brand/Brand'
import { langTag } from '../../components/TargetWord'
import { EmptyState, PageHeader } from '../../components/ui'
import { canRecognise, listen } from '../../lib/pronounce'
import { speak } from '../../lib/speech'

const MAX = 500
const LANGS: { value: TranslateLang; label: string; locale: string }[] = [
  { value: 'vi', label: 'Tiếng Việt', locale: 'vi-VN' },
  { value: 'en', label: 'Tiếng Anh', locale: 'en-US' },
  { value: 'zh-Hans', label: 'Tiếng Trung giản thể', locale: 'zh-CN' },
  { value: 'zh-Hant', label: 'Tiếng Trung phồn thể', locale: 'zh-TW' },
]
const locale = (l: TranslateLang) => LANGS.find((x) => x.value === l)!.locale
const isZh = (l: TranslateLang) => l.startsWith('zh')

/** "Dịch": type or speak a sentence, get a machine translation that can be heard, and save the verified words in it. */
export default function TranslatePage() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  // the language being learned (English for those learning Vietnamese itself)
  const learning: TranslateLang = user?.active_language === 'zh' ? (user.zh_script === 'hant' ? 'zh-Hant' : 'zh-Hans') : 'en'
  const [source, setSource] = useState<TranslateLang>(user?.active_language === 'vi' ? 'en' : 'vi')
  const [target, setTarget] = useState<TranslateLang>(user?.active_language === 'vi' ? 'vi' : learning)
  const [text, setText] = useState('')
  const [listening, setListening] = useState(false)
  const [saved, setSaved] = useState<Set<number>>(new Set())
  const stopRef = useRef<(() => void) | undefined>(undefined)
  const status = useQuery({ queryKey: ['ai-status'], queryFn: learnApi.aiStatus, staleTime: 5 * 60_000 })
  const run = useMutation({
    mutationFn: (v: { text: string; source: TranslateLang; target: TranslateLang }) => learnApi.translate(v.text, v.source, v.target),
  })
  const save = useMutation({
    mutationFn: learnApi.saveTranslatedWord,
    onSuccess: (_, w) => {
      setSaved((s) => new Set(s).add(w.word_id))
      message.success(`Đã lưu “${w.text}” vào Từ của tôi`)
    },
    onError: (e) => message.error(errorMessage(e)),
  })
  useEffect(() => () => stopRef.current?.(), [])

  const translate = (t = text, s = source, g = target) => {
    if (t.trim()) run.mutate({ text: t.trim(), source: s, target: g })
  }

  // A mic under each side: speaking the other side's language flips the direction, so two people can take turns.
  const talk = async (side: 'source' | 'target') => {
    if (listening) {
      stopRef.current?.()
      return
    }
    const s = side === 'source' ? source : target
    const g = side === 'source' ? target : source
    if (side === 'target') {
      setSource(s)
      setTarget(g)
    }
    const { result, stop } = listen(locale(s), 15000)
    stopRef.current = stop
    setListening(true)
    try {
      const heard = (await result).alternatives[0] ?? ''
      setText(heard)
      translate(heard, s, g)
    } catch (e) {
      message.warning((e as Error).message)
    } finally {
      setListening(false)
    }
  }

  const swap = () => {
    const out = run.data
    setSource(target)
    setTarget(source)
    if (out && out.source === source) {
      setText(out.translation)
      translate(out.translation, target, source)
    }
  }

  const header = (
    <PageHeader
      title="Dịch"
      description="Gõ hoặc nói một câu bằng tiếng Việt, tiếng Anh hay tiếng Trung, nghe bản dịch và lưu những từ đã được kiểm duyệt."
    />
  )
  if (status.data && !status.data.translate) {
    return (
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {header}
        <div className="lp-card">
          <EmptyState
            art={<Prismo mood="think" size={90} />}
            title="Tính năng dịch chưa được bật"
            description="Máy chủ chưa được cấu hình dịch vụ AI. Bạn quay lại sau nhé."
          />
        </div>
      </div>
    )
  }

  const options = (other: TranslateLang) =>
    LANGS.map((l) => ({
      value: l.value,
      label: l.label,
      // giản ↔ phồn is not a translation (the words differ by region), so the two are never paired
      disabled: l.value === other || (isZh(l.value) && isZh(other)),
    }))
  const pickSource = (v: TranslateLang) => {
    setSource(v)
    if (v === target || (isZh(v) && isZh(target))) setTarget(v === 'vi' ? learning : 'vi')
  }
  const pickTarget = (v: TranslateLang) => {
    setTarget(v)
    if (v === source || (isZh(v) && isZh(source))) setSource(v === 'vi' ? learning : 'vi')
  }
  const out: Translation | undefined = run.data
  const mic = canRecognise()

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      {header}
      <div className="flex items-center gap-2">
        <Select<TranslateLang>
          value={source}
          onChange={pickSource}
          options={options(target)}
          className="flex-1 min-w-0"
          size="large"
          aria-label="Dịch từ"
        />
        <Tooltip title="Đổi chiều">
          <Button size="large" shape="circle" icon={<SwapOutlined />} onClick={swap} aria-label="Đổi chiều dịch" />
        </Tooltip>
        <Select<TranslateLang>
          value={target}
          onChange={pickTarget}
          options={options(source)}
          className="flex-1 min-w-0"
          size="large"
          aria-label="Dịch sang"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="lp-card p-4 flex flex-col gap-3" aria-label="Câu cần dịch">
          <Input.TextArea
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={MAX}
            showCount
            autoSize={{ minRows: 4, maxRows: 10 }}
            lang={langTag(source)}
            variant="borderless"
            placeholder={listening ? 'Đang nghe…' : 'Nhập hoặc bấm mic để nói'}
            className="!text-lg !p-0"
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                translate()
              }
            }}
          />
          {out?.source_reading && out.text === text.trim() && <div className="text-sm text-slate-500">{out.source_reading}</div>}
          <div className="flex items-center gap-2">
            {mic && (
              <Button
                size="large"
                type={listening ? 'primary' : 'default'}
                danger={listening}
                shape="circle"
                icon={<AudioOutlined />}
                onClick={() => talk('source')}
                aria-label={listening ? 'Dừng nghe' : `Nói bằng ${LANGS.find((l) => l.value === source)!.label}`}
              />
            )}
            {text && (
              <Button
                type="text"
                shape="circle"
                icon={<SoundOutlined />}
                onClick={() => speak(text, locale(source))}
                aria-label="Nghe câu gốc"
              />
            )}
            <span className="flex-1" />
            <Button type="primary" size="large" loading={run.isPending} disabled={!text.trim()} onClick={() => translate()}>
              Dịch
            </Button>
          </div>
        </section>

        <section className="lp-card p-4 flex flex-col gap-3 bg-slate-50" aria-label="Bản dịch" aria-live="polite">
          {out ? (
            <>
              <div lang={langTag(out.target)} className="text-lg text-slate-900 whitespace-pre-wrap">
                {out.translation}
              </div>
              {out.reading && <div className="text-sm text-slate-500">{out.reading}</div>}
            </>
          ) : run.isError ? (
            <p className="m-0 text-red-600">{errorMessage(run.error)}</p>
          ) : (
            <p className="m-0 text-slate-400 text-lg">Bản dịch</p>
          )}
          <span className="flex-1" />
          <div className="flex items-center gap-2">
            {mic && (
              <Button
                size="large"
                shape="circle"
                icon={<AudioOutlined />}
                onClick={() => talk('target')}
                aria-label={`Người kia nói bằng ${LANGS.find((l) => l.value === target)!.label}`}
                title="Người kia nói (đổi chiều)"
              />
            )}
            {out && (
              <>
                <Button
                  type="text"
                  shape="circle"
                  icon={<SoundOutlined />}
                  onClick={() => speak(out.translation, out.target_tts)}
                  aria-label="Nghe bản dịch"
                />
                <Button
                  type="text"
                  shape="circle"
                  icon={<CopyOutlined />}
                  aria-label="Chép bản dịch"
                  onClick={() => navigator.clipboard?.writeText(out.translation).then(() => message.success('Đã chép'))}
                />
                <span className="flex-1" />
                <span className="rounded-md bg-slate-200/70 px-2 py-0.5 text-xs font-semibold text-slate-600">Bản dịch máy</span>
              </>
            )}
          </div>
        </section>
      </div>

      {out && (
        <p className="m-0 text-sm text-slate-500">
          Bản dịch do AI viết, có thể chưa chính xác và không được dùng làm bài học. Chỉ những từ đã kiểm duyệt bên dưới mới lưu được vào
          thẻ học.
        </p>
      )}

      {out && out.words.length > 0 && (
        <section className="flex flex-col gap-3" aria-label="Từ đã kiểm duyệt trong câu">
          <h2 className="m-0 text-lg font-bold text-slate-800">Từ đã kiểm duyệt trong câu</h2>
          <ul className="m-0 p-0 list-none grid gap-2 sm:grid-cols-2">
            {out.words.map((w: TranslatedWord) => (
              <li key={w.word_id} className="lp-card px-4 py-3 flex items-center gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span lang={langTag(w.language)} className="text-lg font-semibold text-slate-800">
                      {w.text}
                    </span>
                    <button
                      type="button"
                      onClick={() => speak(w.text, locale(w.language))}
                      aria-label={`Nghe “${w.text}”`}
                      className="text-brand-600 hover:text-brand-700 cursor-pointer"
                    >
                      <SoundOutlined />
                    </button>
                  </div>
                  <div className="text-sm text-slate-500 truncate">
                    {w.reading && <span>{w.language === 'en' ? `/${w.reading}/` : w.reading} · </span>}
                    {w.meaning_vi}
                  </div>
                </div>
                {saved.has(w.word_id) ? (
                  <Button icon={<CheckOutlined />} disabled>
                    Đã lưu
                  </Button>
                ) : (
                  <Button
                    icon={<PlusOutlined />}
                    loading={save.isPending && save.variables?.word_id === w.word_id}
                    onClick={() => save.mutate(w)}
                  >
                    Lưu
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
