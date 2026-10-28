import { Button, Input } from 'antd'
import { CheckCircleFilled, CloseCircleFilled, SoundOutlined } from '@ant-design/icons'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { Audio, ChooseItem, ChooseKind, MatchItem, MiniGame, Option, Prompt, SortItem, TilesItem, TrainItem, TypeItem } from '../api/play'
import { speak } from '../lib/speech'
import { VietInput } from '../pages/learner/LiteracyPages'
import WordPicture from './WordPicture'

/** The mini games of the game map (Trò chơi). Every game reports, item by item, whether the first answer was right.
 * Answers come with the round, so a game reacts at once; the server scores the round from these results. */

type Done = (results: boolean[]) => void
const RIGHT_MS = 850
const WRONG_MS = 1700

const sayAudio = (a?: Audio) => { if (a) speak(a.text, a.locale) }

function shuffle<T>(xs: T[]): T[] {
  const out = xs.slice()
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

export function normalize(text: string): string {
  return text.normalize('NFC').toLowerCase().replace(/[.,!?;:"“”'’…。，！？]/g, '').replace(/\s+/g, ' ').trim()
}

/** Steps through the items of one game: `answer(ok)` records the first answer, then moves on after a moment. */
function useSteps(count: number, onDone: Done) {
  const [i, setI] = useState(0)
  const [answered, setAnswered] = useState<boolean | null>(null)
  const results = useRef<boolean[]>([])
  const answer = (ok: boolean) => {
    if (answered !== null) return
    setAnswered(ok)
    results.current.push(ok)
    setTimeout(() => {
      if (results.current.length >= count) onDone(results.current)
      else { setI((x) => x + 1); setAnswered(null) }
    }, ok ? RIGHT_MS : WRONG_MS)
  }
  return { i, answered, answer }
}

function Dots({ count, at }: { count: number; at: number }) {
  return (
    <div className="flex justify-center gap-1.5" aria-label={`Câu ${at + 1}/${count}`}>
      {Array.from({ length: count }, (_, k) => (
        <span key={k} className={`h-2 rounded-full transition-all ${k < at ? 'w-2 bg-[#58cc02]' : k === at ? 'w-6 bg-brand-500' : 'w-2 bg-slate-200'}`} />
      ))}
    </div>
  )
}

function Feedback({ ok, answer }: { ok: boolean | null; answer?: string }) {
  if (ok === null) return <div className="h-12" />
  return (
    <div className={`h-12 rounded-2xl px-4 flex items-center justify-center gap-2 text-lg font-semibold animate-rise ${ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
      {ok ? <><CheckCircleFilled /> Giỏi lắm!</> : <><CloseCircleFilled /> Đáp án đúng: <span className="font-bold">{answer}</span></>}
    </div>
  )
}

function SpeakBig({ audio, size = 64 }: { audio?: Audio; size?: number }) {
  if (!audio) return null
  return (
    <button type="button" onClick={() => sayAudio(audio)} aria-label="Nghe lại"
      style={{ width: size, height: size }}
      className="rounded-full bg-brand-500 text-white text-2xl grid place-items-center shadow-[0_4px_0_var(--color-brand-700)] active:translate-y-1 active:shadow-none transition cursor-pointer">
      <SoundOutlined />
    </button>
  )
}

function PromptView({ prompt, lang, big = true }: { prompt: Prompt; lang: string; big?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-3">
      {(prompt.image || prompt.emoji) && <WordPicture image={prompt.image ?? null} emoji={prompt.emoji ?? ''} height="h-32" />}
      {prompt.text && (
        <button type="button" onClick={() => sayAudio(prompt.audio)} lang={lang}
          className={`${big ? 'text-6xl' : 'text-4xl'} font-bold text-slate-800 cursor-pointer`}>{prompt.text}</button>
      )}
      {prompt.sub && <div className="text-lg text-slate-500 text-center">{prompt.sub}</div>}
      {!prompt.text && <SpeakBig audio={prompt.audio} />}
    </div>
  )
}

function OptionFace({ o, lang }: { o: Option; lang: string }) {
  if (o.image || o.emoji) return <WordPicture image={o.image ?? null} emoji={o.emoji ?? ''} height="h-24" />
  return (
    <span className="flex flex-col items-center leading-tight" lang={lang}>
      <span>{o.t}</span>
      {o.s && <span className="text-sm font-normal text-slate-500">{o.s}</span>}
    </span>
  )
}

// ====================================================================== choose games

const BUBBLES = ['#ff86c8', '#1cb0f6', '#ffc800', '#58cc02', '#ce82ff', '#ff9600']

function ChooseGame({ kind, items, lang, onDone }: { kind: ChooseKind; items: ChooseItem[]; lang: string; onDone: Done }) {
  const { i, answered, answer } = useSteps(items.length, onDone)
  const [picked, setPicked] = useState<string | null>(null)
  const item = items[i]
  useEffect(() => {
    setPicked(null)
    const t = setTimeout(() => sayAudio(item.prompt.audio), 350)
    return () => clearTimeout(t)
  }, [item])
  const pick = (o: Option) => {
    if (answered !== null) return
    setPicked(o.t)
    answer(o.t === item.answer)
  }
  const state = (o: Option) => answered === null ? '' : o.t === item.answer ? 'is-right' : o.t === picked ? 'is-wrong' : 'opacity-50'
  const right = item.options.find((o) => o.t === item.answer)

  let options
  if (kind === 'pop') {
    options = (
      <div className="flex flex-wrap justify-center gap-5 py-4">
        {item.options.map((o, k) => {
          const popped = answered !== null && o.t === picked && o.t === item.answer
          return (
            <button key={o.t} type="button" data-opt={o.t} onClick={() => pick(o)} lang={lang}
              style={{
                background: `radial-gradient(circle at 32% 28%, #ffffffb0 0 11%, transparent 12%), ${BUBBLES[k % BUBBLES.length]}`,
                animationDuration: `${2.2 + k * 0.35}s`,
              }}
              className={`relative h-28 w-28 sm:h-32 sm:w-32 rounded-full text-2xl font-bold text-white [text-shadow:0_2px_0_#0003] cursor-pointer transition duration-300
                ${popped ? 'scale-150 opacity-0' : 'lp-float'}
                ${answered !== null && o.t === picked && o.t !== item.answer ? 'animate-[lp-shake_420ms]' : ''}
                ${answered !== null && o.t === item.answer && o.t !== picked ? 'ring-4 ring-[#58cc02]' : ''}`}>
              <OptionFace o={o} lang={lang} />
              <span className="absolute left-1/2 -bottom-3 h-4 w-0.5 bg-slate-300" />
            </button>
          )
        })}
      </div>
    )
  } else if (kind === 'fish') {
    options = (
      <div className="w-full rounded-3xl bg-gradient-to-b from-sky-200 to-sky-400 p-4 flex flex-col gap-3 overflow-hidden">
        {item.options.map((o, k) => (
          <motion.button key={o.t} type="button" data-opt={o.t} onClick={() => pick(o)} lang={lang}
            animate={{ x: k % 2 ? [-14, 14, -14] : [14, -14, 14] }} transition={{ duration: 3 + k * 0.4, repeat: Infinity, ease: 'easeInOut' }}
            className={`btn-3d self-center flex items-center gap-3 pl-4 pr-8 py-2 text-2xl font-bold cursor-pointer ${state(o)}`}
            style={{ borderRadius: '999px 60% 60% 999px' }}>
            <span aria-hidden>🐟</span><OptionFace o={o} lang={lang} />
          </motion.button>
        ))}
      </div>
    )
  } else if (kind === 'gate') {
    options = (
      <div className="flex justify-center gap-6">
        {item.options.map((o) => (
          <button key={o.t} type="button" data-opt={o.t} onClick={() => pick(o)} style={{ perspective: 600 }} className="cursor-pointer">
            <motion.div animate={answered !== null && o.t === item.answer ? { rotateY: -55 } : { rotateY: 0 }}
              transition={{ duration: 0.5 }} style={{ transformOrigin: 'left center' }}
              className={`h-44 w-28 rounded-t-[56px] rounded-b-lg border-4 border-[#a0662f] bg-[#c98546] grid place-items-center relative
                ${answered !== null && o.t === picked && o.t !== item.answer ? 'animate-[lp-shake_420ms]' : ''}`}>
              <span className="text-4xl font-bold text-white [text-shadow:0_2px_0_#0004]">{o.t}</span>
              <span className="absolute right-3 top-1/2 h-3 w-3 rounded-full bg-[#ffc800]" />
            </motion.div>
          </button>
        ))}
      </div>
    )
  } else {
    options = (
      <div className="grid grid-cols-2 gap-3 w-full">
        {item.options.map((o) => (
          <button key={o.t} type="button" data-opt={o.t} onClick={() => pick(o)} disabled={answered !== null}
            className={`btn-3d py-4 px-2 ${kind === 'tone' ? 'text-4xl' : 'text-xl'} font-semibold text-slate-800 cursor-pointer disabled:cursor-default ${state(o)}`}>
            <OptionFace o={o} lang={lang} />
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-5 w-full">
      <Dots count={items.length} at={i} />
      <PromptView prompt={item.prompt} lang={lang} big={kind !== 'meaning'} />
      {kind === 'tone' && lang === 'vi' && <div className="text-slate-500">Thêm dấu nào thì thành tiếng vừa nghe?</div>}
      {options}
      <Feedback ok={answered} answer={right && (right.image || right.emoji ? undefined : right.t)} />
    </div>
  )
}

// ====================================================================== train (onset + rhyme + tone)

function TrainGame({ items, onDone }: { items: TrainItem[]; onDone: Done }) {
  const { i, answered, answer } = useSteps(items.length, onDone)
  const item = items[i]
  const [pick, setPick] = useState<{ onset?: string; rhyme?: string; tone?: string }>({})
  useEffect(() => {
    setPick({})
    const t = setTimeout(() => sayAudio(item.audio), 350)
    return () => clearTimeout(t)
  }, [item])
  const toneLabel = (code?: string) => item.tones.find((t) => t.code === code)
  const cars: [string, string | undefined][] = [
    ['Âm đầu', pick.onset === '∅' ? '–' : pick.onset], ['Vần', pick.rhyme], ['Dấu', toneLabel(pick.tone)?.symbol || (pick.tone ? 'ngang' : undefined)],
  ]
  const check = () => answer(pick.onset === item.answer.onset && pick.rhyme === item.answer.rhyme && pick.tone === item.answer.tone)
  const rows = [
    ['onset', 'Âm đầu', item.onsets.map((o) => ({ v: o, l: o === '∅' ? '(không có)' : o }))],
    ['rhyme', 'Vần', item.rhymes.map((r) => ({ v: r, l: r }))],
    ['tone', 'Dấu', item.tones.map((t) => ({ v: t.code, l: t.symbol ? `${t.symbol} ${t.label}` : t.label }))],
  ] as const
  return (
    <div className="flex flex-col items-center gap-5 w-full">
      <Dots count={items.length} at={i} />
      <SpeakBig audio={item.audio} />
      <motion.div className="flex items-end gap-1" animate={answered ? { x: [0, 260] } : { x: 0 }} transition={{ duration: 0.9, ease: 'easeIn' }}>
        <span className="text-5xl" aria-hidden>🚂</span>
        {cars.map(([label, value]) => (
          <div key={label} className="flex flex-col items-center">
            <div className={`h-16 min-w-16 px-3 rounded-xl border-b-4 grid place-items-center text-2xl font-bold
              ${value ? 'bg-brand-500 border-brand-700 text-white' : 'bg-slate-100 border-slate-300 text-slate-300'}`}>{value ?? '?'}</div>
            <div className="flex gap-3 -mt-1"><span className="h-3 w-3 rounded-full bg-slate-600" /><span className="h-3 w-3 rounded-full bg-slate-600" /></div>
            <div className="text-xs text-slate-400">{label}</div>
          </div>
        ))}
      </motion.div>
      {rows.map(([key, label, opts]) => (
        <div key={key} className="w-full">
          <div className="text-sm text-slate-400 mb-1">{label}</div>
          <div className="flex flex-wrap gap-2">
            {opts.map((o) => (
              <button key={o.v} type="button" data-part={`${key}:${o.v}`} disabled={answered !== null} onClick={() => setPick({ ...pick, [key]: o.v })}
                className={`btn-3d px-4 py-2 text-xl cursor-pointer ${pick[key] === o.v ? '!border-brand-500 !bg-brand-50 text-brand-700' : 'text-slate-700'}`}>
                {o.l}
              </button>
            ))}
          </div>
        </div>
      ))}
      {answered === null
        ? <Button type="primary" size="large" disabled={!pick.onset || !pick.rhyme || !pick.tone} onClick={check}>Cho tàu chạy</Button>
        : <Feedback ok={answered} answer={item.text} />}
    </div>
  )
}

// ====================================================================== sort (fruit into rhyme baskets)

function SortGame({ baskets, items, onDone }: { baskets: string[]; items: SortItem[]; onDone: Done }) {
  const { i, answered, answer } = useSteps(items.length, onDone)
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [target, setTarget] = useState<string | null>(null)
  const item = items[i]
  useEffect(() => {
    setTarget(null)
    const t = setTimeout(() => sayAudio(item.audio), 300)
    return () => clearTimeout(t)
  }, [item])
  const drop = (b: string) => {
    if (answered !== null) return
    setTarget(b)
    const ok = b === item.answer
    if (ok) setCounts((c) => ({ ...c, [b]: (c[b] ?? 0) + 1 }))
    answer(ok)
  }
  return (
    <div className="flex flex-col items-center gap-6 w-full">
      <Dots count={items.length} at={i} />
      <AnimatePresence mode="wait">
        <motion.button key={i} type="button" onClick={() => sayAudio(item.audio)}
          initial={{ y: -30, opacity: 0 }}
          animate={answered && target ? { y: 140, x: baskets.indexOf(target) ? 90 : -90, scale: 0.6, opacity: 0 } : { y: 0, opacity: 1 }}
          exit={{ opacity: 0 }} transition={{ duration: answered ? 0.6 : 0.3 }}
          className="relative h-32 w-32 grid place-items-center cursor-pointer">
          <span className="absolute inset-0 text-[110px] leading-none" aria-hidden>🍎</span>
          <span className="relative mt-4 text-2xl font-bold text-white [text-shadow:0_2px_0_#0006]" lang="vi">{item.t}</span>
        </motion.button>
      </AnimatePresence>
      <div className="flex gap-6">
        {baskets.map((b) => (
          <button key={b} type="button" data-basket={b} onClick={() => drop(b)}
            className={`btn-3d w-36 py-3 flex flex-col items-center cursor-pointer ${answered !== null && b === item.answer ? 'is-right' : answered !== null && b === target ? 'is-wrong' : ''}`}>
            <span className="text-5xl" aria-hidden>🧺</span>
            <span className="text-2xl font-bold text-brand-700">vần {b}</span>
            <span className="text-xs text-slate-400">{counts[b] ?? 0} quả</span>
          </button>
        ))}
      </div>
      <Feedback ok={answered} answer={`vần ${item.answer}`} />
    </div>
  )
}

// ====================================================================== match (memory cards)

type Card = { key: string; pair: number; face: Option }

function MatchGame({ items, lang, onDone }: { items: MatchItem[]; lang: string; onDone: Done }) {
  const cards = useMemo<Card[]>(() => shuffle(items.flatMap((p, k) => [
    { key: `a${k}`, pair: k, face: p.a }, { key: `b${k}`, pair: k, face: p.b }])), [items])
  const [open, setOpen] = useState<string[]>([])
  const [found, setFound] = useState<Set<number>>(new Set())
  const missed = useRef<Set<number>>(new Set())
  const flip = (c: Card) => {
    if (open.length === 2 || open.includes(c.key) || found.has(c.pair)) return
    const now = [...open, c.key]
    setOpen(now)
    if (now.length < 2) return
    const [x, y] = now.map((k) => cards.find((cc) => cc.key === k)!)
    setTimeout(() => {
      if (x.pair === y.pair) {
        const next = new Set(found).add(x.pair)
        setFound(next)
        if (next.size === items.length) setTimeout(() => onDone(items.map((_, k) => !missed.current.has(k))), 500)
      } else {
        missed.current.add(x.pair)
        missed.current.add(y.pair)
      }
      setOpen([])
    }, x.pair === y.pair ? 350 : 900)
  }
  return (
    <div className="flex flex-col items-center gap-4 w-full">
      <div className="text-slate-500">Đã tìm được {found.size}/{items.length} cặp</div>
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 w-full">
        {cards.map((c) => {
          const shown = open.includes(c.key) || found.has(c.pair)
          return (
            <button key={c.key} type="button" data-pair={c.pair} onClick={() => flip(c)} style={{ perspective: 600 }} className="h-28 cursor-pointer">
              <motion.div animate={{ rotateY: shown ? 0 : 180 }} transition={{ duration: 0.35 }}
                className={`relative h-full w-full rounded-2xl border-2 border-b-4 grid place-items-center text-xl font-semibold
                  ${found.has(c.pair) ? 'border-[#10c79a] bg-green-50' : shown ? 'border-brand-400 bg-white' : 'border-brand-700 bg-brand-500'}`}
                style={{ transformStyle: 'preserve-3d' }}>
                {shown ? <span style={{ transform: 'rotateY(0deg)' }}><OptionFace o={c.face} lang={lang} /></span>
                  : <span className="text-3xl text-white" style={{ transform: 'rotateY(180deg)' }}>?</span>}
              </motion.div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ====================================================================== tiles (spell a word / order a sentence)

function TilesGame({ items, lang, onDone }: { items: TilesItem[]; lang: string; onDone: Done }) {
  const { i, answered, answer } = useSteps(items.length, onDone)
  const item = items[i]
  const [used, setUsed] = useState<number[]>([])
  useEffect(() => {
    setUsed([])
    const t = setTimeout(() => sayAudio(item.prompt.audio), 350)
    return () => clearTimeout(t)
  }, [item])
  const built = used.map((k) => item.tiles[k]).join(item.joiner)
  const sentence = item.joiner === ' '
  return (
    <div className="flex flex-col items-center gap-5 w-full">
      <Dots count={items.length} at={i} />
      <div className="flex items-center gap-4">
        {(item.prompt.image || item.prompt.emoji) && <WordPicture image={item.prompt.image ?? null} emoji={item.prompt.emoji ?? ''} height="h-24" />}
        <SpeakBig audio={item.prompt.audio} size={56} />
      </div>
      {item.prompt.sub && <div className="text-lg text-slate-500 text-center">“{item.prompt.sub}”</div>}
      <div className={`min-h-16 w-full rounded-2xl border-2 border-dashed px-3 py-2 flex flex-wrap items-center justify-center gap-2
        ${answered === null ? 'border-slate-300' : answered ? 'border-[#10c79a] bg-green-50' : 'border-red-300 bg-red-50'}`} lang={lang}>
        {used.map((k, pos) => (
          <button key={`${k}-${pos}`} type="button" disabled={answered !== null} onClick={() => setUsed(used.filter((_, p) => p !== pos))}
            className={`btn-3d ${sentence ? 'px-3' : 'w-12'} py-2 text-2xl font-semibold cursor-pointer animate-pop`}>{item.tiles[k]}</button>
        ))}
      </div>
      <div className="flex flex-wrap justify-center gap-2" lang={lang}>
        {item.tiles.map((t, k) => (
          <button key={k} type="button" data-tile={k} disabled={used.includes(k) || answered !== null} onClick={() => setUsed([...used, k])}
            className={`btn-3d ${sentence ? 'px-3' : 'w-12'} py-2 text-2xl font-semibold cursor-pointer disabled:opacity-25 disabled:cursor-default`}>{t}</button>
        ))}
      </div>
      {answered === null
        ? <Button type="primary" size="large" disabled={!used.length} onClick={() => answer(normalize(built) === normalize(item.answer))}>Kiểm tra</Button>
        : <Feedback ok={answered} answer={item.answer} />}
    </div>
  )
}

// ====================================================================== type (picture -> write the word)

function TypeGame({ items, lang, onDone }: { items: TypeItem[]; lang: string; onDone: Done }) {
  const { i, answered, answer } = useSteps(items.length, onDone)
  const item = items[i]
  const [typed, setTyped] = useState('')
  useEffect(() => {
    setTyped('')
    const t = setTimeout(() => sayAudio(item.prompt.audio), 350)
    return () => clearTimeout(t)
  }, [item])
  const check = () => typed.trim() && answer(item.accepted.some((a) => normalize(a) === normalize(typed)))
  return (
    <div className="flex flex-col items-center gap-5 w-full">
      <Dots count={items.length} at={i} />
      <WordPicture image={item.prompt.image ?? null} emoji={item.prompt.emoji ?? ''} height="h-40" />
      <SpeakBig audio={item.prompt.audio} size={52} />
      {lang === 'vi'
        ? <VietInput value={typed} onChange={setTyped} onEnter={check} disabled={answered !== null} />
        : <Input size="large" value={typed} onChange={(e) => setTyped(e.target.value)} onPressEnter={check} disabled={answered !== null}
            className="max-w-md text-center text-2xl" autoFocus />}
      {answered === null
        ? <Button type="primary" size="large" disabled={!typed.trim()} onClick={check}>Kiểm tra</Button>
        : <Feedback ok={answered} answer={item.answer} />}
    </div>
  )
}

// ====================================================================== one mini game

export function MiniGameView({ game, lang, onDone }: { game: MiniGame; lang: string; onDone: Done }) {
  switch (game.game) {
    case 'train': return <TrainGame items={game.items} onDone={onDone} />
    case 'sort': return <SortGame baskets={game.baskets} items={game.items} onDone={onDone} />
    case 'match': return <MatchGame items={game.items} lang={lang} onDone={onDone} />
    case 'spell': case 'order': return <TilesGame items={game.items} lang={lang} onDone={onDone} />
    case 'type': return <TypeGame items={game.items} lang={lang} onDone={onDone} />
    default: return <ChooseGame kind={game.game} items={game.items} lang={lang} onDone={onDone} />
  }
}

export const GAME_NAMES: Record<MiniGame['game'], string> = {
  pop: 'Bắt bong bóng', fish: 'Câu cá', tone: 'Thả dấu', picture: 'Chọn hình', meaning: 'Chọn nghĩa', gate: 'Chọn cửa',
  train: 'Ghép toa tàu', sort: 'Hái quả', match: 'Lật thẻ', spell: 'Ghép chữ', order: 'Xếp câu', type: 'Đuổi hình bắt chữ',
}
