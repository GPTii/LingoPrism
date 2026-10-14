import { SoundOutlined } from '@ant-design/icons'
import type { TargetText } from '../api/vocab'
import { useAuth } from '../auth/store'
import { speak } from '../lib/speech'

/** HTML lang tag for a translation, so the browser picks the right glyphs (Han unification). */
export function langTag(language: string): string {
  if (language === 'zh-Hant') return 'zh-Hant-TW'
  return language
}

export default function TargetWord({ target, size = 'lg', showReading = true }: { target: TargetText; size?: 'md' | 'lg' | 'xl'; showReading?: boolean }) {
  const showZhuyin = useAuth((s) => s.user?.show_zhuyin)
  const isZh = target.language.startsWith('zh')
  const textSize = { md: 'text-2xl', lg: 'text-4xl', xl: 'text-6xl' }[size]
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="flex items-center gap-3">
        <span lang={langTag(target.language)} className={`${textSize} font-semibold text-slate-800`}>
          {target.text}
        </span>
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); speak(target.text, target.tts_locale) }}
          className="text-brand-600 hover:text-brand-700 text-xl cursor-pointer"
          title="Nghe phát âm"
        >
          <SoundOutlined />
        </button>
      </div>
      {showReading && (
        <div className="text-slate-500 text-base flex flex-wrap justify-center gap-x-3">
          {target.ipa && <span>/{target.ipa}/</span>}
          {isZh && target.pinyin && <span>{target.pinyin}</span>}
          {isZh && target.zhuyin && showZhuyin && <span lang="zh-Hant-TW">{target.zhuyin}</span>}
          {isZh && target.measure_word && (
            <span className="text-slate-400">
              lượng từ: <span lang={langTag(target.language)}>{target.measure_word}</span>
            </span>
          )}
        </div>
      )}
      {target.unverified && <span className="text-xs text-amber-600">Chưa được kiểm tra</span>}
    </div>
  )
}
