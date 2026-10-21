import { SoundOutlined } from '@ant-design/icons'
import type { Sentence, SentenceToken } from '../api/sentences'
import { useAuth } from '../auth/store'
import { speak } from '../lib/speech'
import { langTag } from './TargetWord'

/** A sentence with its reading above each word (pinyin, optionally zhuyin) – never generated per character on the client. */
export function TokenLine({ tokens, language, highlight = [], showReading = true, size = 'text-2xl' }: {
  tokens: SentenceToken[]
  language: string
  highlight?: number[]
  showReading?: boolean
  size?: string
}) {
  const showZhuyin = useAuth((s) => s.user?.show_zhuyin)
  const isZh = language.startsWith('zh')
  return (
    <p lang={langTag(language)} className={`${size} leading-relaxed text-slate-800 flex flex-wrap items-end justify-center ${isZh ? 'gap-x-1' : 'gap-x-2'}`}>
      {tokens.map((tok, i) => {
        if (tok.blank) return <span key={i} className="inline-block min-w-16 border-b-4 border-brand-400 mx-1">&nbsp;</span>
        if (tok.x) return <span key={i} className={isZh ? '' : '-ml-2'}>{tok.t}</span>
        const hl = highlight.includes(i) ? 'text-brand-700 font-semibold' : ''
        const reading = showReading && isZh && tok.p ? (showZhuyin && tok.z ? tok.z : tok.p) : ''
        return reading ? (
          <ruby key={i} className={hl}>
            {tok.t}
            <rt className="text-xs text-slate-500 font-normal" lang={showZhuyin && tok.z ? 'zh-Hant-TW' : 'en'}>{reading}</rt>
          </ruby>
        ) : (
          <span key={i} className={hl}>{tok.t}</span>
        )
      })}
    </p>
  )
}

export default function SentenceView({ sentence, showTranslation = true }: { sentence: Sentence; showTranslation?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <div className="flex items-center gap-3">
        <TokenLine tokens={sentence.tokens} language={sentence.language} highlight={sentence.target_tokens} />
        <button type="button" title="Nghe câu" aria-label="Nghe câu" className="text-brand-600 hover:text-brand-700 text-xl cursor-pointer"
          onClick={() => speak(sentence.text, sentence.tts_locale)}>
          <SoundOutlined />
        </button>
      </div>
      {showTranslation && sentence.translation && (
        <div className="text-slate-600">
          {sentence.translation.text}
        </div>
      )}
      {sentence.source.url && (
        <a href={sentence.source.url} target="_blank" rel="noreferrer" className="text-xs !text-slate-500 hover:!text-slate-700">
          Câu #{sentence.source.id} · {sentence.source.name} · {sentence.source.license}
        </a>
      )}
    </div>
  )
}
