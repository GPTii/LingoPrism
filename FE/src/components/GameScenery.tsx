import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

/**
 * Scenery of the game map (Trò chơi): every level is a little world – a meadow, the seaside, the desert, a volcano
 * at night – with a winding trail through its stops, things growing and moving beside it and clouds drifting
 * above. Hand-drawn SVG in the LingoPrism palette (no third-party art), CSS animations that stop when the learner
 * asks for reduced motion (index.css, .sc-*).
 */

type Theme = 'meadow' | 'sea' | 'desert' | 'night'
const THEMES: Theme[] = ['meadow', 'sea', 'desert', 'night']
export const themeOf = (level: number): Theme => THEMES[(level - 1) % THEMES.length]

// ------------------------------------------------------------------------------------------------- sprites

type Sprite = (p: { size: number }) => ReactNode

const Tree: Sprite = ({ size }) => (
  <svg width={size} height={size * 1.2} viewBox="0 0 60 72" className="sc-sway">
    <rect x="26" y="44" width="8" height="26" rx="3" fill="#8a5a3b" />
    <circle cx="30" cy="30" r="22" fill="#2fbf71" />
    <circle cx="18" cy="38" r="13" fill="#27a862" />
    <circle cx="42" cy="38" r="13" fill="#27a862" />
    <circle cx="24" cy="22" r="6" fill="#5bd994" opacity=".8" />
  </svg>
)
const Pine: Sprite = ({ size }) => (
  <svg width={size * 0.8} height={size * 1.2} viewBox="0 0 48 72" className="sc-sway">
    <rect x="21" y="56" width="6" height="14" rx="2" fill="#7a4e33" />
    <path d="M24 2 44 30H32L46 50H30L42 62H6L18 50H2L16 30H4Z" fill="#1d9a5b" />
  </svg>
)
const Flower: Sprite = ({ size }) => (
  <svg width={size * 0.6} height={size * 0.8} viewBox="0 0 30 40" className="sc-sway">
    <path d="M15 40V18" stroke="#2fbf71" strokeWidth="3" />
    <path d="M15 30c-6-2-8-6-8-9 4 0 7 3 8 9z" fill="#2fbf71" />
    {[0, 72, 144, 216, 288].map((a) => (
      <ellipse key={a} cx="15" cy="8" rx="4.5" ry="7" fill="#ff8fab" transform={`rotate(${a} 15 14)`} />
    ))}
    <circle cx="15" cy="14" r="4" fill="#ffd23f" />
  </svg>
)
const Mushroom: Sprite = ({ size }) => (
  <svg width={size * 0.7} height={size * 0.7} viewBox="0 0 40 40">
    <rect x="15" y="20" width="10" height="16" rx="4" fill="#fff4e0" />
    <path d="M2 22C2 10 10 3 20 3s18 7 18 19z" fill="#ff5d73" />
    <circle cx="13" cy="12" r="3" fill="#fff" />
    <circle cx="26" cy="9" r="2.5" fill="#fff" />
    <circle cx="29" cy="17" r="2" fill="#fff" />
  </svg>
)
const Butterfly: Sprite = ({ size }) => (
  <svg width={size * 0.7} height={size * 0.6} viewBox="0 0 40 34" className="sc-float">
    <g className="sc-flap" style={{ transformOrigin: '20px 17px' }}>
      <path d="M20 17C12 2 2 4 4 14s10 6 16 3z" fill="#a78bfa" />
      <path d="M20 17c8-15 18-13 16-3s-10 6-16 3z" fill="#a78bfa" />
      <path d="M20 18c-8 2-12 10-8 13s8-6 8-13zM20 18c8 2 12 10 8 13s-8-6-8-13z" fill="#c4b5fd" />
    </g>
    <rect x="19" y="10" width="2" height="16" rx="1" fill="#3b2f63" />
  </svg>
)
const Palm: Sprite = ({ size }) => (
  <svg width={size} height={size * 1.3} viewBox="0 0 60 78" className="sc-sway">
    <path d="M30 76c2-20 0-36-4-50" stroke="#a0703f" strokeWidth="6" fill="none" strokeLinecap="round" />
    <path
      d="M27 24C17 12 4 14 2 22c10-6 18-4 25 2zM27 24c4-14 18-20 26-14-11 0-20 6-26 14zM27 24c10-6 24-2 30 8-10-6-20-8-30-8zM27 24C18 20 8 28 6 38c6-8 13-12 21-14z"
      fill="#22b573"
    />
    <circle cx="27" cy="26" r="3" fill="#7a4e33" />
    <circle cx="31" cy="27" r="3" fill="#7a4e33" />
  </svg>
)
const Boat: Sprite = ({ size }) => (
  <svg width={size} height={size * 0.8} viewBox="0 0 60 48" className="sc-bob">
    <path d="M30 4v30" stroke="#5b6b7f" strokeWidth="2" />
    <path d="M31 6l18 24H31z" fill="#fff" />
    <path d="M29 10L14 30h15z" fill="#ffd23f" />
    <path d="M6 34h48l-8 10H14z" fill="#e0445e" />
  </svg>
)
const Wave: Sprite = ({ size }) => (
  <svg width={size * 1.4} height={size * 0.4} viewBox="0 0 70 20" className="sc-wave">
    <path
      d="M0 12c6-8 12-8 18 0s12 8 18 0 12-8 18 0 12 8 16 0"
      stroke="#fff"
      strokeOpacity=".8"
      strokeWidth="3"
      fill="none"
      strokeLinecap="round"
    />
  </svg>
)
const Fish: Sprite = ({ size }) => (
  <svg width={size * 0.8} height={size * 0.5} viewBox="0 0 40 24" className="sc-jump">
    <path d="M4 12C10 2 26 2 32 12 26 22 10 22 4 12z" fill="#ff9f43" />
    <path d="M32 12l8-8v16z" fill="#ff9f43" />
    <circle cx="11" cy="10" r="2" fill="#243447" />
  </svg>
)
const Shell: Sprite = ({ size }) => (
  <svg width={size * 0.6} height={size * 0.5} viewBox="0 0 30 24">
    <path d="M15 2C6 2 1 12 3 20h24c2-8-3-18-12-18z" fill="#ffc6d3" />
    {[8, 12, 15, 18, 22].map((x) => (
      <path key={x} d={`M15 20L${x} 4`} stroke="#ff8fab" strokeWidth="1.4" />
    ))}
  </svg>
)
const Cactus: Sprite = ({ size }) => (
  <svg width={size * 0.8} height={size * 1.1} viewBox="0 0 48 66" className="sc-sway">
    <rect x="18" y="6" width="12" height="58" rx="6" fill="#2fa36b" />
    <path d="M18 34H10a4 4 0 0 1-4-4V18a4 4 0 0 1 8 0v8h4zM30 26h8V14a4 4 0 0 1 8 0v12a8 8 0 0 1-8 8h-8z" fill="#2fa36b" />
    <circle cx="24" cy="6" r="4" fill="#ff8fab" />
  </svg>
)
const Pyramid: Sprite = ({ size }) => (
  <svg width={size * 1.3} height={size} viewBox="0 0 64 50">
    <path d="M32 2l30 46H2z" fill="#e7b25c" />
    <path d="M32 2l30 46H32z" fill="#c98f35" />
  </svg>
)
const Rock: Sprite = ({ size }) => (
  <svg width={size * 0.8} height={size * 0.5} viewBox="0 0 40 24">
    <path d="M2 22l6-12 10-6 12 4 8 14z" fill="#b9a38a" />
    <path d="M18 4l12 4 8 14H22z" fill="#a08a72" />
  </svg>
)
const Star: Sprite = ({ size }) => (
  <svg width={size * 0.4} height={size * 0.4} viewBox="0 0 20 20" className="sc-twinkle">
    <path d="M10 0l2.6 7.4L20 10l-7.4 2.6L10 20l-2.6-7.4L0 10l7.4-2.6z" fill="#ffe28a" />
  </svg>
)
const Crystal: Sprite = ({ size }) => (
  <svg width={size * 0.7} height={size} viewBox="0 0 34 48" className="sc-glow">
    <path d="M10 46L4 20 12 4l6 16-2 26z" fill="#c084fc" />
    <path d="M18 46l2-28 8-12 4 18-6 22z" fill="#f472b6" />
  </svg>
)
const Volcano: Sprite = ({ size }) => (
  <svg width={size * 1.4} height={size * 1.2} viewBox="0 0 70 60">
    <circle cx="38" cy="10" r="6" fill="#9ca3af" opacity=".6" className="sc-smoke" />
    <circle cx="32" cy="14" r="5" fill="#9ca3af" opacity=".5" className="sc-smoke" style={{ animationDelay: '1.2s' }} />
    <path d="M2 58L26 20h18l24 38z" fill="#5b3a4a" />
    <path d="M26 20h18l-4 8-5-3-4 6-5-5z" fill="#ff7a45" />
  </svg>
)
const Lantern: Sprite = ({ size }) => (
  <svg width={size * 0.5} height={size * 0.8} viewBox="0 0 24 40" className="sc-bob">
    <path d="M12 0v6" stroke="#ffd23f" strokeWidth="2" />
    <rect x="3" y="6" width="18" height="24" rx="9" fill="#ff5d73" />
    <rect x="8" y="30" width="8" height="4" rx="1" fill="#ffd23f" />
    <path d="M12 34v6" stroke="#ffd23f" strokeWidth="2" />
  </svg>
)

const DECOR: Record<Theme, Sprite[]> = {
  meadow: [Tree, Flower, Butterfly, Pine, Mushroom, Flower, Tree],
  sea: [Palm, Wave, Boat, Fish, Shell, Wave, Palm],
  desert: [Cactus, Pyramid, Rock, Cactus, Star, Rock],
  night: [Star, Crystal, Volcano, Lantern, Star, Crystal],
}

/** Small art for the level banner. */
export function BannerArt({ level }: { level: number }) {
  const S = { meadow: Tree, sea: Boat, desert: Pyramid, night: Volcano }[themeOf(level)]
  // left of the "done / total" count, so it never covers it
  return (
    <span aria-hidden className="pointer-events-none absolute right-28 bottom-0 opacity-25">
      <S size={64} />
    </span>
  )
}

// ------------------------------------------------------------------------------------------------- the trail

type Pt = { x: number; y: number }

function curve(points: Pt[]) {
  if (!points.length) return ''
  let d = `M${points[0].x},${points[0].y}`
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1],
      b = points[i],
      my = (a.y + b.y) / 2
    d += ` C${a.x},${my} ${b.x},${my} ${b.x},${b.y}`
  }
  return d
}

/**
 * Wraps the column of stops of one level: measures where each stop button is, then draws the trail through them
 * (solid up to `progress`, the last stop reached) and the scenery beside it. `ids`: the stops, in order; each has
 * an element #stop-<id> with a button inside.
 */
export function LevelScene({ level, ids, progress, children }: { level: number; ids: string[]; progress: number; children: ReactNode }) {
  const box = useRef<HTMLDivElement>(null)
  const [pts, setPts] = useState<Pt[]>([])
  const [width, setWidth] = useState(0)
  const theme = themeOf(level)

  useLayoutEffect(() => {
    const el = box.current
    if (!el) return
    const measure = () => {
      const r = el.getBoundingClientRect()
      setWidth(r.width)
      setPts(
        ids.map((id) => {
          const b = document.getElementById(`stop-${id}`)?.querySelector('button')?.getBoundingClientRect()
          return b ? { x: b.left - r.left + b.width / 2, y: b.top - r.top + b.height / 2 } : { x: r.width / 2, y: 0 }
        }),
      )
    }
    measure()
    // the stops settle after the box resizes (rotation, window size): measure again a moment later
    let timer = 0
    const later = () => {
      window.clearTimeout(timer)
      timer = window.setTimeout(measure, 60)
    }
    const ro = new ResizeObserver(later)
    ro.observe(el)
    window.addEventListener('resize', later)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', later)
      window.clearTimeout(timer)
    }
  }, [ids.join('|')]) // eslint-disable-line react-hooks/exhaustive-deps

  const sprites = DECOR[theme]
  const decor = pts
    .flatMap((p, i) => {
      const left = p.x > width / 2 // the stop leans right: scenery on the left, and the other way round
      const x = Math.min(Math.max(28, left ? p.x - 150 : p.x + 150), width - 28)
      const S = sprites[i % sprites.length]
      const T = sprites[(i + 3) % sprites.length]
      return [
        { key: `${i}a`, x, y: p.y + 10, S, size: 46 + ((i * 7) % 18) },
        ...(i % 2
          ? [{ key: `${i}b`, x: Math.min(Math.max(20, left ? p.x - 95 : p.x + 95), width - 20), y: p.y + 44, S: T, size: 30 }]
          : []),
      ]
    })
    .filter((d) =>
      pts.every((p) => {
        // never on top of a stop (sprites stand on (x, y), about size wide and tall)
        const half = d.size * 0.7
        return d.x + half < p.x - 52 || d.x - half > p.x + 52 || d.y < p.y - 52 || d.y - d.size * 1.3 > p.y + 52
      }),
    )

  return (
    <div ref={box} className={`relative overflow-hidden scene-${theme}`}>
      <div aria-hidden className="pointer-events-none absolute inset-0">
        {theme === 'night' ? <div className="sc-moon absolute right-6 top-5" /> : <div className="sc-sun absolute right-6 top-5" />}
        <div className="sc-cloud sc-drift absolute top-6" style={{ animationDuration: '38s' }} />
        <div className="sc-cloud sc-drift absolute top-24 scale-75" style={{ animationDuration: '52s', animationDelay: '-20s' }} />
        <svg className="absolute inset-0" width="100%" height="100%">
          <path d={curve(pts)} fill="none" stroke="var(--sc-trail)" strokeWidth="14" strokeLinecap="round" />
          <path d={curve(pts)} fill="none" stroke="var(--sc-dash)" strokeWidth="3" strokeDasharray="2 12" strokeLinecap="round" />
          {progress > 0 && (
            <path d={curve(pts.slice(0, progress + 1))} fill="none" stroke="#ffc800" strokeWidth="6" strokeLinecap="round" opacity=".85" />
          )}
        </svg>
        {decor.map(({ key, x, y, S, size }) => (
          <span key={key} className="absolute -translate-x-1/2 -translate-y-full" style={{ left: x, top: y }}>
            <S size={size} />
          </span>
        ))}
      </div>
      <div className="relative">{children}</div>
    </div>
  )
}
