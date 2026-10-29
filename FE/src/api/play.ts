import { api } from './client'
import type { MascotLook } from './types'

/** Trò chơi: the game map (BE apps/games). Rounds open once their words / reading lesson were learned. */

export interface GameLock {
  reason: 'previous' | 'learn' | 'lesson'
  need?: number
  level?: number
  lesson?: number
  title?: string
}

export interface GameStop {
  id: string
  kind: 'round' | 'chest' | 'boss'
  index: number
  title: string
  lesson: number | null
  status: 'done' | 'open' | 'locked'
  stars: number
  lock: GameLock | null
}

export interface GameLevel {
  level: number
  name: string
  description: string
  unlocked: boolean
  done: number
  total: number
  nodes: GameStop[]
}

/** A friend on the same map: they stand at the stop they play next (the last stop once they passed everything). */
export interface MapFriend {
  id: number
  display_name: string
  avatar: string | null
  mascot: MascotLook
  node: string
  finished: boolean
}

export interface GameMap {
  language: string
  track: 'words' | 'reading'
  current: string | null
  pass_percent: number
  levels: GameLevel[]
  friends: MapFriend[]
}

export interface Audio { text: string; locale: string }
export interface Prompt { text?: string; sub?: string; audio?: Audio; image?: string | null; emoji?: string }
export interface Option { t: string; s?: string; image?: string | null; emoji?: string }

export type ChooseKind = 'pop' | 'fish' | 'tone' | 'picture' | 'meaning' | 'gate'
/** hint: the word's meaning / how the syllable is spelt out, shown when the learner pays vảy for it */
export interface ChooseItem { prompt: Prompt; options: Option[]; answer: string; hint?: string }
export interface TrainItem {
  audio: Audio
  text: string
  onsets: string[]
  rhymes: string[]
  tones: { code: string; label: string; symbol: string }[]
  answer: { onset: string; rhyme: string; tone: string }
  hint?: string
}
export interface SortItem { t: string; audio: Audio; answer: string; hint?: string }
export interface MatchItem { a: Option; b: Option }
export interface TilesItem { prompt: Prompt; tiles: string[]; joiner: string; answer: string; hint?: string }
export interface TypeItem { prompt: Prompt; answer: string; accepted: string[]; hint?: string }

export type HelperKind = 'hint' | 'retry'
export interface GameHelpers { cost: Record<HelperKind, number>; per_round: number; scales: number }

export type MiniGame =
  | { game: ChooseKind; title: string; items: ChooseItem[] }
  | { game: 'train'; title: string; items: TrainItem[] }
  | { game: 'sort'; title: string; baskets: string[]; items: SortItem[] }
  | { game: 'match'; title: string; items: MatchItem[] }
  | { game: 'spell' | 'order'; title: string; items: TilesItem[] }
  | { game: 'type'; title: string; items: TypeItem[] }

export interface GameRound {
  node: string
  kind: 'round' | 'boss'
  level: number
  title: string
  track: 'words' | 'reading'
  pass_percent: number
  games: MiniGame[]
  token: string
  helpers: GameHelpers
}

export interface GameFinish {
  correct: number
  total: number
  percent: number
  stars: number
  passed: boolean
  best_stars: number
  xp: number
  gems: number
  review: { kind: 'words'; word_ids: number[] } | { kind: 'lesson'; lesson: number } | null
  next: GameStop | null
}

export const playApi = {
  map: () => api.get<GameMap>('/games/map/').then((r) => r.data),
  round: (node: string) => api.get<GameRound>(`/games/rounds/${node}/`).then((r) => r.data),
  finish: (node: string, token: string, results: boolean[][]) =>
    api.post<GameFinish>(`/games/rounds/${node}/finish/`, { token, results }).then((r) => r.data),
  help: (node: string, token: string, kind: HelperKind) =>
    api.post<{ kind: HelperKind; cost: number; scales: number; left: number }>(`/games/rounds/${node}/help/`, { token, kind }).then((r) => r.data),
  openChest: (node: string) => api.post<{ gems: number; scales: number }>(`/games/chests/${node}/open/`).then((r) => r.data),
}
