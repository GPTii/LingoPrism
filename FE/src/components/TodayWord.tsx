import { useQuery } from '@tanstack/react-query'
import { Skeleton } from 'antd'
import { SoundOutlined } from '@ant-design/icons'
import { vocabApi, type TargetText } from '../api/vocab'
import { useAuth } from '../auth/store'
import { speak } from '../lib/speech'
import { LANG_BEAM, LangGlyph } from './brand/Brand'
import { langTag } from './TargetWord'
import WordPicture from './WordPicture'

/** Same word for everyone on the same day: days since 1 Jan 2026, local time. */
const dayNumber = () => Math.floor((Date.now() - new Date(2026, 0, 1).getTime() - new Date().getTimezoneOffset() * 60_000) / 86_400_000)

/**
 * "Từ của hôm nay": one verified word seen through all three beams at once –
 * English, Chinese (in the learner's chosen script) and Vietnamese, side by side.
 */
export default function TodayWord() {
  const script = useAuth((s) => s.user?.zh_script) ?? 'hans'
  const q = useQuery({
    queryKey: ['today-word', script, dayNumber()],
    staleTime: 3_600_000,
    queryFn: async () => {
      // a page of 50 verified words, chosen by the day; prefer one with a real photo
      const head = await vocabApi.wordPage('zh', script, 1)
      if (!head.count) return null
      const pages = Math.ceil(head.count / 50)
      const list = (await vocabApi.wordPage('zh', script, (dayNumber() % pages) + 1, 50)).results
      const start = dayNumber() % list.length
      const ordered = [...list.slice(start), ...list.slice(0, start)]
      const zh = ordered.find((w) => w.image && w.part_of_speech === 'noun') ?? ordered.find((w) => w.image) ?? ordered[0]
      const en = await vocabApi.word(zh.id, 'en').catch(() => null)
      return { zh, en }
    },
  })
  if (q.isLoading) return <Skeleton active paragraph={{ rows: 3 }} />
  if (!q.data) return null
  const { zh, en } = q.data
  const cols: { lang: 'en' | 'zh' | 'vi'; name: string; target?: TargetText | null; text: string; reading?: string }[] = [
    { lang: 'en', name: 'Tiếng Anh', target: en?.target, text: en?.target?.text ?? zh.english ?? '', reading: en?.target?.ipa ? `/${en.target.ipa}/` : undefined },
    { lang: 'zh', name: script === 'hant' ? 'Tiếng Trung phồn thể' : 'Tiếng Trung giản thể', target: zh.target, text: zh.target?.text ?? '', reading: zh.target?.pinyin },
    { lang: 'vi', name: 'Tiếng Việt', text: zh.meaning_vi },
  ]

  return (
    <section aria-labelledby="today-word" className="grid lg:grid-cols-[minmax(200px,280px)_1fr] gap-6 lg:gap-10 items-center">
      <div className="rounded-2xl bg-[var(--surface)] border border-slate-200 p-3">
        <WordPicture image={zh.image} emoji={zh.emoji || '—'} credit={zh.image_credit} source={zh.image_source} alt={zh.meaning_vi} height="h-44" />
      </div>
      <div className="min-w-0">
        <h2 id="today-word" className="text-lg font-bold text-slate-500 m-0 mb-4">Từ của hôm nay</h2>
        <ul className="m-0 p-0 list-none grid sm:grid-cols-3 gap-x-8 gap-y-6">
          {cols.map((c) => (
            <li key={c.lang} className="min-w-0 pt-4" style={{ borderTop: `3px solid ${LANG_BEAM[c.lang]}` }}>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                <LangGlyph lang={c.lang} script={script} size={18} />{c.name}
              </div>
              <div className="flex items-baseline gap-2 flex-wrap">
                <span lang={c.lang === 'zh' ? langTag(zh.target?.language ?? 'zh-Hans') : c.lang}
                  className="text-4xl xl:text-5xl font-bold text-slate-900 leading-tight break-words">
                  {c.text || '—'}
                </span>
                {(c.target || c.lang === 'vi') && c.text && (
                  <button type="button" aria-label={`Nghe ${c.name}`} onClick={() => (c.target ? speak(c.target.text, c.target.tts_locale) : speak(c.text, 'vi-VN'))}
                    className="text-xl text-slate-500 hover:text-slate-900 cursor-pointer transition-colors">
                    <SoundOutlined />
                  </button>
                )}
              </div>
              {c.reading && <div className="mt-1 text-slate-500">{c.reading}</div>}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
