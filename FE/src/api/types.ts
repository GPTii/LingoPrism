export type Role = 'admin' | 'staff' | 'learner'
export type LanguageCode = 'vi' | 'en' | 'zh'

export interface UserGoal {
  daily_new_target: number
  daily_review_target: number
  remind_morning: string | null
  remind_evening: string | null
  smart_remind: boolean
}

/** What someone's Prismo wears (one outfit code per slot, "" for nothing) and whether it stands in for their photo. */
export interface MascotLook {
  name: string
  as_avatar: boolean
  background: string
  hat: string
  glasses: string
  neck: string
  hand: string
}

export interface User {
  id: number
  /** 8 digits, shown as "ID của tôi" – friends find each other by it */
  public_id: string
  email: string
  display_name: string
  avatar: string | null
  bio: string
  role: Role
  status: 'active' | 'locked'
  learner_type: 'kid' | 'adult'
  learning_languages: LanguageCode[]
  active_language: LanguageCode
  zh_script: 'hans' | 'hant'
  show_zhuyin: boolean
  birth_date: string | null
  gender: string
  purpose: string
  daily_minutes: number
  onboarding_completed: boolean
  timezone: string
  scales_balance: number
  gems_balance: number
  goal: UserGoal | null
  /** null until they open their wardrobe: a plain Prismo */
  mascot?: MascotLook | null
  /** admin lists only */
  last_login?: string | null
  created_at: string
}

export interface Tokens {
  access: string
  refresh: string
}

export interface AuthResponse {
  user: User
  tokens: Tokens
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiError {
  detail: string
  errors: Record<string, string[] | string>
}
