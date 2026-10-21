import { Button } from 'antd'
import { MessageOutlined, SoundOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { learnApi } from '../api/app'
import { errorMessage } from '../api/client'
import { speak } from '../lib/speech'
import { langTag } from './TargetWord'

/**
 * "Hội thoại từ ảnh": a short dialogue an AI model writes around the words found in a photo.
 * Clearly marked as AI-made – the words in it are verified, the sentences are not.
 */
export default function PhotoDialogue({ detectionId, locale }: { detectionId: number; locale: string }) {
  const qc = useQueryClient()
  const status = useQuery({ queryKey: ['ai-status'], queryFn: learnApi.aiStatus, staleTime: 5 * 60_000 })
  const key = ['photo-dialogue', detectionId]
  const kept = useQuery({ queryKey: key, queryFn: () => learnApi.dialogue(detectionId), enabled: !!status.data?.dialogue })
  const make = useMutation({
    mutationFn: () => learnApi.makeDialogue(detectionId),
    onSuccess: (d) => qc.setQueryData(key, d),
  })
  if (!status.data?.dialogue) return null
  const d = kept.data
  if (!d) {
    return (
      <div className="flex flex-col gap-1.5">
        <Button icon={<MessageOutlined />} loading={make.isPending || kept.isLoading} onClick={() => make.mutate()}>
          Tạo hội thoại với các từ này
        </Button>
        {make.isError && <p className="m-0 text-sm text-red-600">{errorMessage(make.error)}</p>}
      </div>
    )
  }
  return (
    <section className="rounded-xl border border-slate-200 p-4 flex flex-col gap-3" aria-label="Hội thoại do AI tạo">
      <div className="flex items-center justify-between gap-2">
        <h3 className="m-0 text-base font-semibold text-slate-800">{d.title_vi || 'Hội thoại'}</h3>
        <span className="shrink-0 whitespace-nowrap rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">AI tạo</span>
      </div>
      <ol className="m-0 p-0 list-none flex flex-col gap-2.5">
        {d.lines.map((l, n) => (
          <li key={n} className="flex gap-3">
            <span className={`num mt-0.5 h-6 w-6 shrink-0 rounded-full text-xs font-bold grid place-items-center ${l.speaker === 'A' ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-600'}`}>
              {l.speaker}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-start gap-2">
                <span lang={langTag(d.language)} className="text-slate-800 font-medium">{l.text}</span>
                <button type="button" onClick={() => speak(l.text, locale)} aria-label="Nghe câu này" title="Nghe câu này"
                  className="text-brand-600 hover:text-brand-700 cursor-pointer shrink-0">
                  <SoundOutlined />
                </button>
              </div>
              {l.reading && <div className="text-sm text-slate-500">{l.reading}</div>}
              <div className="text-sm text-slate-600">{l.translation}</div>
            </div>
          </li>
        ))}
      </ol>
      <p className="m-0 text-xs text-slate-500">
        Câu do AI viết, chưa được kiểm duyệt như từ vựng. Từ trong ảnh: {d.words.map((w) => w.text).join(', ')}.
      </p>
    </section>
  )
}
