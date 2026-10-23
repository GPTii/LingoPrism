/**
 * LingoPrism's own visual identity, drawn here as SVG (no third-party artwork):
 *   * the mark: a prism splitting one beam of light into three colours – one snap, three languages;
 *   * Prismo, the mascot: that prism with a face, in a few moods;
 *   * the game icons: streak flame, scales (vảy), gems (ngọc), XP.
 */
import { useId } from 'react'
import type { MascotLook } from '../../api/types'
import { useAuth } from '../../auth/store'

/** useId() contains ':' / '«', which breaks url(#id) references in some browsers */
const useSvgId = () => 'lp' + useId().replace(/[^a-zA-Z0-9]/g, '')

/** The app icon: Prismo's big-eyed face on the brand blue (same drawing as FE/scripts/make-brand-mark.py). */
export function LogoMark({ size = 36, className = '' }: { size?: number; className?: string }) {
  const tri = 'M80 22 L138 124 L22 124 Z'
  return (
    <svg width={size} height={size} viewBox="0 0 160 160" className={className} aria-hidden>
      <rect width="160" height="160" rx="40" fill="#1899f0" />
      <g transform="translate(4.8 4.8) scale(0.94)">
        <g strokeWidth="7" strokeLinecap="round">
          <path d="M131 95 L152 84" stroke="#ffb020" /><path d="M134 104 L157 104" stroke="#10c79a" /><path d="M131 113 L152 124" stroke="#ff6b81" />
        </g>
        <path d={tri} transform="translate(0 7)" fill="#0f78c8" stroke="#0f78c8" strokeWidth="22" strokeLinejoin="round" />
        <path d={tri} fill="#5cc6ff" stroke="#5cc6ff" strokeWidth="22" strokeLinejoin="round" />
        {[60, 100].map((x) => (
          <g key={x}>
            <ellipse cx={x} cy="89" rx="17.5" ry="21" fill="#fff" />
            <ellipse cx={x + 3} cy="93" rx="8.5" ry="10.5" fill="#15233b" />
            <circle cx={x + 6.5} cy="87.5" r="3.4" fill="#fff" />
          </g>
        ))}
        <path d="M73 113 Q80 120 87 113" fill="none" stroke="#15233b" strokeWidth="4" strokeLinecap="round" />
      </g>
    </svg>
  )
}

export function Logo({ compact = false, size = 36, inverse = false }: { compact?: boolean; size?: number; inverse?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark size={size} />
      {!compact && (
        <span className={`text-xl font-extrabold tracking-[-0.03em] ${inverse ? 'text-white' : 'text-slate-800'}`}>
          Lingo<span className={inverse ? 'text-[#6fc0f8]' : 'prism-text'}>Prism</span>
        </span>
      )}
    </span>
  )
}

export type Mood = 'happy' | 'celebrate' | 'sleepy' | 'think' | 'sad' | 'wow'

const INK = '#15233b'

/** Each learner's Prismo is dressed from layers drawn on this frame: Prismo's grid with room for hats and held things. */
const FRAME = '-10 -24 180 180'
/** layers in front of Prismo, back to front (the background goes behind) */
const FRONT = ['neck', 'hand', 'glasses', 'hat'] as const
export const outfitUrl = (code: string) => `/outfits/${code}.svg`

/**
 * Prismo – the LingoPrism mascot. By default it wears what the signed-in learner dressed it in
 * (`look="mine"`); pass another learner's look, or null for the plain mascot.
 */
export function Prismo({ mood = 'happy', size = 120, className = '', look = 'mine' }: {
  mood?: Mood
  size?: number
  className?: string
  look?: MascotLook | null | 'mine'
}) {
  const mine = useAuth((s) => s.user?.mascot)
  const wear = look === 'mine' ? mine : look
  const front = wear ? FRONT.filter((slot) => wear[slot]) : []
  if (!front.length) {
    return (
      <svg width={size} height={size * 0.94} viewBox="0 0 160 150" className={className} role="img" aria-label="Prismo">
        <PrismoBody mood={mood} />
      </svg>
    )
  }
  // dressed: drawn on the larger frame, with negative margins so it takes the same room as plain Prismo
  // and the hat (or what it holds) reaches outside that room
  const k = size / 160
  return (
    <svg width={180 * k} height={180 * k} viewBox={FRAME} className={className} role="img" aria-label="Prismo"
      style={{ margin: `${-24 * k}px ${-10 * k}px ${-6 * k}px ${-10 * k}px`, overflow: 'visible' }}>
      <PrismoBody mood={mood} />
      {front.map((slot) => <image key={slot} href={outfitUrl(wear![slot])} x="-10" y="-24" width="180" height="180" />)}
    </svg>
  )
}

/** Someone's Prismo as their picture: the whole frame, background included, in a circle (or a rounded square). */
export function PrismoAvatar({ look, size = 36, mood = 'happy', square = false, className = '' }: {
  look?: MascotLook | null
  size?: number
  mood?: Mood
  square?: boolean
  className?: string
}) {
  return (
    <svg width={size} height={size} viewBox={FRAME} className={`shrink-0 ${square ? 'rounded-[22%]' : 'rounded-full'} ${className}`}
      role="img" aria-label={look?.name || 'Prismo'} style={{ width: size, height: size, overflow: 'hidden' }}>
      <rect x="-10" y="-24" width="180" height="180" fill="#dff1ff" />
      {look?.background && <image href={outfitUrl(look.background)} x="-10" y="-24" width="180" height="180" />}
      <PrismoBody mood={mood} />
      {look && FRONT.filter((slot) => look[slot]).map((slot) => (
        <image key={slot} href={outfitUrl(look[slot])} x="-10" y="-24" width="180" height="180" />
      ))}
    </svg>
  )
}

/** Prismo's body and face on its 160 × 150 grid. */
function PrismoBody({ mood }: { mood: Mood }) {
  const id = useSvgId()
  const eye = (x: number) => {
    switch (mood) {
      case 'celebrate':
        return <path d={`M${x - 7} 90 Q${x} 81 ${x + 7} 90`} stroke={INK} strokeWidth="4.5" fill="none" strokeLinecap="round" />
      case 'sleepy':
        return <path d={`M${x - 7} 88 Q${x} 94 ${x + 7} 88`} stroke={INK} strokeWidth="4" fill="none" strokeLinecap="round" />
      default: {
        const big = mood === 'wow'
        const dy = mood === 'sad' ? 3 : mood === 'think' ? -2 : 1
        return (
          <g>
            <ellipse cx={x} cy="88" rx={big ? 9 : 7.5} ry={big ? 10 : 8.5} fill="#fff" />
            <circle cx={x + (mood === 'think' ? 2 : 1)} cy={88 + dy} r={big ? 5 : 4.4} fill={INK} />
            <circle cx={x + 2.5} cy={85 + dy} r="1.6" fill="#fff" />
          </g>
        )
      }
    }
  }
  const mouth = {
    happy: <path d="M70 104 Q80 114 90 104" stroke={INK} strokeWidth="4" fill="none" strokeLinecap="round" />,
    celebrate: (
      <g>
        <path d="M67 101 Q80 122 93 101 Z" fill={INK} />
        <path d="M74 110 Q80 116 86 110 Q80 107 74 110 Z" fill="#ff6b81" />
      </g>
    ),
    sleepy: <ellipse cx="80" cy="106" rx="4" ry="3" fill={INK} />,
    think: <path d="M72 107 L88 104" stroke={INK} strokeWidth="4" strokeLinecap="round" />,
    sad: <path d="M70 110 Q80 101 90 110" stroke={INK} strokeWidth="4" fill="none" strokeLinecap="round" />,
    wow: <ellipse cx="80" cy="107" rx="5.5" ry="6.5" fill={INK} />,
  }[mood]

  return (
    <>
      <defs>
        <linearGradient id={`${id}b`} x1="0.2" y1="0" x2="0.8" y2="1">
          <stop offset="0" stopColor="#62c6ff" />
          <stop offset="0.6" stopColor="#1899f0" />
          <stop offset="1" stopColor="#0f6fb0" />
        </linearGradient>
      </defs>
      <ellipse cx="80" cy="141" rx="44" ry="6" fill="#000" opacity="0.12" />
      {/* light leaving the prism: the three languages */}
      <g strokeLinecap="round" strokeWidth="6">
        <path d="M128 92 L151 80" stroke="#ffb020" />
        <path d="M131 100 L155 99" stroke="#10c79a" />
        <path d="M128 108 L150 118" stroke="#ff6b81" />
      </g>
      <ellipse cx="62" cy="132" rx="11" ry="6" fill="#0b5a94" />
      <ellipse cx="98" cy="132" rx="11" ry="6" fill="#0b5a94" />
      <path d="M80 16 L140 122 L20 122 Z" fill={`url(#${id}b)`} stroke={`url(#${id}b)`} strokeWidth="18" strokeLinejoin="round" />
      <path d="M80 24 L80 124 L26 124 Z" fill="#fff" opacity="0.12" />
      <path d="M66 46 L56 64" stroke="#fff" strokeWidth="5" strokeLinecap="round" opacity="0.65" />
      <ellipse cx="55" cy="101" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.55" />
      <ellipse cx="105" cy="101" rx="7" ry="4.5" fill="#ff8fa3" opacity="0.55" />
      {eye(64)}
      {eye(96)}
      {mouth}
      {mood === 'sad' && <path d="M101 97 q4 7 0 9 q-4 -2 0 -9 Z" fill="#7dd3fc" />}
      {mood === 'sleepy' && <text x="112" y="58" fontSize="20" fontWeight="800" fill="#3dabf4" fontFamily="Be Vietnam Pro, sans-serif">z</text>}
      {mood === 'think' && <text x="114" y="60" fontSize="26" fontWeight="800" fill="#ffb020" fontFamily="Be Vietnam Pro, sans-serif">?</text>}
      {mood === 'celebrate' && (
        <g fill="#ffb020">
          <path d="M26 40 l3 7 7 3 -7 3 -3 7 -3 -7 -7 -3 7 -3 Z" />
          <path d="M132 34 l2 5 5 2 -5 2 -2 5 -2 -5 -5 -2 5 -2 Z" fill="#10c79a" />
        </g>
      )}
    </>
  )
}

type IconProps = { size?: number; className?: string }

export function StreakIcon({ size = 22, active = true, className = '' }: IconProps & { active?: boolean }) {
  const id = useSvgId()
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <defs>
        <linearGradient id={`${id}f`} x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0" stopColor={active ? '#ffb020' : '#c4ccd8'} />
          <stop offset="1" stopColor={active ? '#ff5a3c' : '#95a1b3'} />
        </linearGradient>
      </defs>
      <path d="M12 2.5C13.2 6 17.5 8 17.5 13.2C17.5 17.4 15 20.5 12 20.5C9 20.5 6.5 17.4 6.5 13.6C6.5 10.8 8 9.3 9 8.2C9.2 10 10 11 11 11.3C10.6 8 11 5 12 2.5Z"
        fill={`url(#${id}f)`} />
      <path d="M12 12C13.4 13.4 14.6 14.6 14.6 16.4C14.6 18 13.4 19.2 12 19.2C10.6 19.2 9.4 18 9.4 16.6C9.4 15 10.6 14 12 12Z"
        fill={active ? '#ffe08a' : '#e3e8ef'} />
    </svg>
  )
}

export function GemIcon({ size = 22, className = '' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <path d="M12 2 L20.5 8.5 L12 22 L3.5 8.5 Z" fill="#1899f0" />
      <path d="M12 2 L20.5 8.5 L12 10.5 L3.5 8.5 Z" fill="#a6d8fb" />
      <path d="M3.5 8.5 L12 10.5 L12 22 Z" fill="#3dabf4" />
      <path d="M12 2 L8 8.9 L12 10.5 L16 8.9 Z" fill="#d0ebfd" opacity="0.9" />
      <path d="M12 10.5 L20.5 8.5 L12 22 Z" fill="#06b6d4" opacity="0.55" />
    </svg>
  )
}

export function ScaleIcon({ size = 22, className = '' }: IconProps) {
  const id = useSvgId()
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <defs>
        <linearGradient id={`${id}s`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#34e3b5" />
          <stop offset="1" stopColor="#0891b2" />
        </linearGradient>
      </defs>
      <circle cx="12" cy="12" r="9.5" fill={`url(#${id}s)`} />
      <circle cx="12" cy="12" r="9.5" fill="none" stroke="#0e7490" strokeWidth="1.2" opacity="0.5" />
      <g fill="none" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" opacity="0.9">
        <path d="M6.5 11 a2.75 2.75 0 0 1 5.5 0" />
        <path d="M12 11 a2.75 2.75 0 0 1 5.5 0" />
        <path d="M9.25 15 a2.75 2.75 0 0 1 5.5 0" />
      </g>
    </svg>
  )
}

export function XpIcon({ size = 22, className = '' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <path d="M12 2.2 L14.7 8.4 L21.4 9 L16.3 13.4 L17.9 20 L12 16.5 L6.1 20 L7.7 13.4 L2.6 9 L9.3 8.4 Z"
        fill="#ffb020" stroke="#f08a00" strokeWidth="1" strokeLinejoin="round" />
      <path d="M12.8 7.5 L10.3 12.4 L12.4 12.4 L11.3 16.4 L14.2 11.3 L12.1 11.3 Z" fill="#fff" />
    </svg>
  )
}

/**
 * Each language is one beam leaving the prism – the same colour everywhere it is named
 * (the language switch, the sign-in page, the camera result).
 */
export const LANG_BEAM = { en: '#ffb020', zh: '#ff6b81', vi: '#10c79a' } as const

/** The language's own letters on its beam colour: "EN", 简 / 繁, "VI" – no flags, no emoji. */
export function LangGlyph({ lang, script = 'hans', size = 22 }: { lang: 'en' | 'zh' | 'vi'; script?: 'hans' | 'hant'; size?: number }) {
  const text = lang === 'zh' ? (script === 'hant' ? '繁' : '简') : lang.toUpperCase()
  return (
    <span aria-hidden lang={lang === 'zh' ? (script === 'hant' ? 'zh-Hant' : 'zh-Hans') : undefined}
      className="inline-grid place-items-center shrink-0 rounded-md font-bold text-[#15233b]"
      style={{ width: size, height: size, background: LANG_BEAM[lang], fontSize: size * (lang === 'zh' ? 0.6 : 0.45), lineHeight: 1 }}>
      {text}
    </span>
  )
}

/** An earned badge: a faceted medal in the prism colours; greyed out while still locked. */
export function BadgeMedal({ size = 44, owned = true, seed = 0 }: { size?: number; owned?: boolean; seed?: number }) {
  const beams = ['#ffb020', '#10c79a', '#ff6b81', '#239ff2']
  const c = owned ? beams[seed % beams.length] : '#c8d0db'
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden>
      <path d="M16 4h16l-4 12h-8z" fill={owned ? '#0f7ac4' : '#b2bccb'} />
      <path d="M24 13l11.3 6.5v13L24 39l-11.3-6.5v-13z" fill={c} />
      <path d="M24 13l11.3 6.5L24 26l-11.3-6.5z" fill="#fff" opacity="0.35" />
      <path d="M24 26v13l-11.3-6.5v-13z" fill="#000" opacity="0.08" />
      <path d="M24 19.5l1.9 3.9 4.3.6-3.1 3 .7 4.3-3.8-2-3.8 2 .7-4.3-3.1-3 4.3-.6z" fill="#fff" opacity={owned ? 0.95 : 0.6} />
    </svg>
  )
}

/** Đá băng (streak freeze): a small ice block. */
export function FreezeIcon({ size = 22, className = '' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden>
      <rect x="3.5" y="3.5" width="17" height="17" rx="4" fill="#7dd3fc" />
      <path d="M3.5 9 L20.5 9 M9 3.5 L9 20.5" stroke="#e0f6ff" strokeWidth="1.4" opacity="0.8" />
      <path d="M13 6.5 l3.5 3.5" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}
