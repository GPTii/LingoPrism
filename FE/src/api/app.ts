import { api } from './client'
import type { Paginated } from './types'
import type { WordCard } from './vocab'

// ---------------------------------------------------------------- gamification

export interface GameSummary {
  lifetime_xp: number
  level: number
  today_xp: number
  daily_xp_cap: number
  streak: number
  longest_streak: number
  studied_today: boolean
  scales: number
  gems: number
  streak_freezes: number
  freezes_used: number
  words_learned: number
  words_mastered: number
  today: { new_learned: number; new_target: number; reviews_done: number; review_target: number }
  active_boosts: { item: string; name: string; multiplier: number; expires_at: string }[]
  league: { tier: string; tier_code: string; weekly_xp: number } | null
}

export interface DailyQuest {
  id: number
  kind: string
  title: string
  target: number
  progress: number
  completed: boolean
  reward_claimed: boolean
  reward_scales: number
}

export interface MonthlyQuest {
  month: string
  completed_count: number
  target: number
  reward_gems: number
  reward_claimed: boolean
}

export interface Badge {
  id: number
  code: string
  name: string
  description: string
  icon: string
  owned: boolean
  awarded_at: string | null
}

export interface LeaderboardEntry {
  rank: number
  user_id: number
  display_name: string
  avatar: string | null
  xp: number
  zone?: 'promotion' | 'safe' | 'demotion'
  is_me: boolean
}

export interface Leaderboard {
  scope: 'league' | 'global'
  tier?: { code: string; name: string }
  ends_at?: string
  tiers: { code: string; name: string; order: number; icon: string }[]
  members: LeaderboardEntry[]
}

export interface ShopItem {
  id: number
  code: string
  name: string
  description: string
  image: string
  effect: string
  cost_scales: number | null
  cost_gems: number | null
  owned: number
}

export interface DayProgress {
  date: string
  xp: number
  new_learned: number
  reviews_done: number
  active: boolean
  freeze_used: boolean
}

export const gameApi = {
  summary: () => api.get<GameSummary>('/gamification/summary/').then((r) => r.data),
  progress: (start?: string, end?: string) => api.get<DayProgress[]>('/gamification/progress/', { params: { start, end } }).then((r) => r.data),
  quests: () => api.get<{ quests: DailyQuest[]; monthly: MonthlyQuest }>('/quests/today/').then((r) => r.data),
  claim: (id: number) => api.post<{ scales: number }>(`/quests/${id}/claim/`).then((r) => r.data),
  claimMonthly: () => api.post<{ gems: number }>('/quests/monthly/claim/').then((r) => r.data),
  badges: () => api.get<Badge[]>('/badges/').then((r) => r.data),
  leaderboard: (scope: 'league' | 'global' = 'league') => api.get<Leaderboard>('/leaderboard/', { params: { scope } }).then((r) => r.data),
  shop: () => api.get<ShopItem[]>('/shop/items/').then((r) => r.data),
  buy: (id: number) => api.post<{ scales: number; gems: number }>(`/shop/items/${id}/buy/`).then((r) => r.data),
  use: (id: number) => api.post<{ multiplier: number; expires_at: string }>(`/shop/items/${id}/use/`).then((r) => r.data),
}

// ---------------------------------------------------------------- notifications

export interface AppNotification {
  id: number
  kind: string
  title: string
  body: string
  image: string
  data: { route?: string; [k: string]: unknown }
  read: boolean
  created_at: string
}

export const notificationApi = {
  list: () => api.get<Paginated<AppNotification>>('/notifications/', { params: { page_size: 100 } }).then((r) => r.data.results),
  unread: () => api.get<{ unread: number }>('/notifications/unread-count/').then((r) => r.data.unread),
  read: (id: number) => api.post(`/notifications/${id}/read/`),
  readAll: () => api.post('/notifications/read-all/'),
}

// ---------------------------------------------------------------- community

export interface Author {
  id: number
  display_name: string
  avatar: string | null
}

export interface Post {
  id: number
  author: Author
  image: string
  caption: string
  topic_label: string
  like_count: number
  comment_count: number
  liked: boolean
  save_count: number
  words: WordCard[]
  created_at: string
}

export interface PostComment {
  id: number
  author: Author
  kind: 'text' | 'sticker'
  content: string
  sticker: string
  created_at: string
}

export interface StudyGroup {
  id: number
  name: string
  description: string
  icon: string
  require_approval: boolean
  member_count: number
  my_status: 'pending' | 'active' | null
  my_role: 'leader' | 'member' | null
  created_at: string
}

export interface GroupMember {
  id: number
  user: Author
  role: 'leader' | 'member'
  status: 'pending' | 'active'
  request_message: string
  weekly_xp: number
  lifetime_xp: number
}

export interface ChatMessage {
  id: number
  kind?: string
  content: string
  sticker?: string
  client_id: string
  created_at: string
  user?: { id: number; display_name: string }
  sender?: { id: number; display_name: string; is_staff: boolean }
  read_at?: string | null
}

export interface CommunityProfile extends Author {
  bio: string
  followers: number
  following: number
  posts: number
  is_following: boolean
  lifetime_xp: number
  streak: number
  recent_posts: { id: number; image: string }[]
  groups: { id: number; name: string }[]
}

export interface SupportConversation {
  id: number
  subject: string
  status: 'open' | 'closed'
  learner: { id: number; display_name: string; email: string }
  staff_name: string | null
  unread: number
  last_message: ChatMessage | null
  last_message_at: string
}

export const communityApi = {
  feed: (params?: Record<string, unknown>) => api.get<Paginated<Post>>('/posts/', { params }).then((r) => r.data),
  create: (image: File, caption: string, wordIds: number[]) => {
    const form = new FormData()
    form.append('image', image)
    form.append('caption', caption)
    wordIds.forEach((id) => form.append('word_ids', String(id)))
    return api.post<Post>('/posts/', form).then((r) => r.data)
  },
  remove: (id: number) => api.delete(`/posts/${id}/`),
  like: (id: number, like: boolean) => (like ? api.post(`/posts/${id}/like/`) : api.delete(`/posts/${id}/like/`)),
  comments: (id: number) => api.get<PostComment[]>(`/posts/${id}/comments/`).then((r) => r.data),
  comment: (id: number, content: string) => api.post<PostComment>(`/posts/${id}/comments/`, { kind: 'text', content }).then((r) => r.data),
  report: (id: number, reason: string, details: string) => api.post(`/posts/${id}/report/`, { reason, details }),
  saveWords: (id: number) => api.post<{ added: number }>(`/posts/${id}/save-words/`).then((r) => r.data),
  profile: (userId: number) => api.get<CommunityProfile>(`/community/users/${userId}/profile/`).then((r) => r.data),
  follow: (userId: number, follow: boolean) =>
    follow ? api.post(`/community/users/${userId}/follow/`) : api.delete(`/community/users/${userId}/follow/`),
  groups: (params?: Record<string, unknown>) => api.get<Paginated<StudyGroup>>('/groups/', { params: { page_size: 100, ...params } }).then((r) => r.data.results),
  createGroup: (data: Partial<StudyGroup>) => api.post<StudyGroup>('/groups/', data).then((r) => r.data),
  join: (id: number, message = '') => api.post<{ status: string }>(`/groups/${id}/join/`, { message }).then((r) => r.data),
  leave: (id: number) => api.post(`/groups/${id}/leave/`),
  members: (id: number) => api.get<GroupMember[]>(`/groups/${id}/members/`).then((r) => r.data),
  moderate: (groupId: number, memberId: number, decision: 'approve' | 'reject' | 'remove') =>
    api.post(`/groups/${groupId}/members/${memberId}/${decision}/`),
  messages: (groupId: number) => api.get<{ results: ChatMessage[]; has_more: boolean }>(`/groups/${groupId}/messages/`).then((r) => r.data),
  send: (groupId: number, content: string, client_id: string) =>
    api.post<ChatMessage>(`/groups/${groupId}/messages/`, { kind: 'text', content, client_id }).then((r) => r.data),
  openSupport: () => api.post<SupportConversation>('/support/conversations/', {}).then((r) => r.data),
  conversations: (params?: Record<string, unknown>) =>
    api.get<Paginated<SupportConversation>>('/support/conversations/', { params }).then((r) => r.data.results),
  supportMessages: (id: number) => api.get<ChatMessage[]>(`/support/conversations/${id}/messages/`).then((r) => r.data),
  sendSupport: (id: number, content: string, client_id: string) =>
    api.post<ChatMessage>(`/support/conversations/${id}/messages/`, { content, client_id }).then((r) => r.data),
  closeSupport: (id: number) => api.post(`/support/conversations/${id}/close/`),
}

// ---------------------------------------------------------------- detection, GIS, exams

export interface DetectedItem {
  id: number
  label: string
  confidence: number
  bbox: number[]
  top_k: { label: string; confidence: number }[]
  selected: boolean
  feedback: 'unknown' | 'correct' | 'wrong'
  card: WordCard | null
  /** model not sure: ask "is it A / B / C?" (other likely objects, each with its word card) */
  uncertain: boolean
  alternatives: { label: string; confidence: number; card: WordCard }[]
  /** object the learner picked instead of the model's answer ('' = none) */
  corrected_label: string
  corrected_card: WordCard | null
  /** relabelled automatically from an earlier learner's error report */
  learned: boolean
  not_object: boolean
}

export interface DetectionResult {
  id: number
  model: string
  device: 'server' | 'on_device'
  inference_ms: number | null
  image: string | null
  created_at: string
  confirmed: boolean
  items: DetectedItem[]
}

/** A practice dialogue an AI model wrote around the words of one photo (never part of the verified vocabulary). */
export interface PhotoDialogue {
  id: number
  detection: number
  language: string
  title_vi: string
  words: { word_id: number; text: string; meaning_vi: string }[]
  lines: { speaker: 'A' | 'B'; text: string; reading: string; translation: string }[]
  ai_generated: true
  model: string
  created_at: string
}

export interface Poi {
  id: number
  name: string
  category: string
  category_label: string
  lat: number
  lng: number
  radius_m: number
  address: string
  description: string
  topics: number[]
  topics_detail: { id: number; slug: string; name_vi: string; icon: string }[]
  is_active: boolean
  distance_m?: number
}

export interface ExamInfo {
  id: number
  title: string
  description: string
  language: string
  topic: number | null
  topic_name: string | null
  time_limit_minutes: number | null
  pass_percent: number
  question_count: number
  my_best: { percent: number; status: string; submission: number } | null
}

export interface ExamQuestion {
  id: number
  kind: 'mcq' | 'fill' | 'essay'
  language: string
  prompt: string
  image_url: string
  options: string[]
  points: string
}

export interface AnswerResult {
  id: number
  question: { id: number; kind: string; prompt: string; options: string[]; correct_option: number | null; accepted_answers: string[]; explanation: string; points: string }
  selected_option: number | null
  text: string
  is_correct: boolean | null
  score: string | null
  feedback: string
}

export interface Submission {
  id: number
  exam: number
  exam_title: string
  user_email: string
  status: 'in_progress' | 'submitted' | 'graded'
  started_at: string
  submitted_at: string | null
  score: string
  max_score: string
  percent: number
  passed: boolean
  feedback: string
  answers: AnswerResult[]
}

export const learnApi = {
  /** my earlier photos, newest first */
  detections: (page = 1) => api.get<Paginated<DetectionResult>>('/detections/', { params: { page } }).then((r) => r.data),
  /** which AI features the server has switched on */
  aiStatus: () => api.get<{ dialogue: boolean }>('/ai/status/').then((r) => r.data),
  /** the dialogue already written for a photo, or null */
  dialogue: (id: number) =>
    api.get<PhotoDialogue>(`/detections/${id}/dialogue/`).then((r) => r.data).catch((e) => {
      if (e?.response?.status === 404) return null
      throw e
    }),
  makeDialogue: (id: number) => api.post<PhotoDialogue>(`/detections/${id}/dialogue/`).then((r) => r.data),
  detect: (image: File) => {
    const form = new FormData()
    form.append('image', image)
    form.append('source', 'web')
    return api.post<DetectionResult>('/detect/', form).then((r) => r.data)
  },
  confirm: (id: number, items: { id: number; selected: boolean; feedback: string; corrected_label?: string; not_object?: boolean }[]) =>
    api.post<DetectionResult & { saved: number; reported: number }>(`/detections/${id}/confirm/`, { items }).then((r) => r.data),
  /** every object the detector knows, with its word card (error report: "it is something else") */
  detectLabels: () => api.get<{ label: string; card: WordCard }[]>('/detections/labels/').then((r) => r.data),
  nearby: (lat: number, lng: number, radius = 3000) =>
    api.get<{ results: Poi[]; query_ms: number }>('/pois-nearby/', { params: { lat, lng, radius } }).then((r) => r.data),
  pois: () => api.get<Poi[]>('/pois/').then((r) => r.data),
  exams: (language?: string) => api.get<Paginated<ExamInfo>>('/exams/', { params: { language, page_size: 100 } }).then((r) => r.data.results),
  startExam: (id: number) =>
    api.post<{ submission: number; title: string; language: string; time_limit_minutes: number | null; started_at: string; questions: ExamQuestion[] }>(`/exams/${id}/start/`).then((r) => r.data),
  submit: (submission: number, answers: { question: number; selected_option?: number | null; text?: string }[]) =>
    api.post<Submission>(`/submissions/${submission}/submit/`, { answers }).then((r) => r.data),
  result: (id: number) => api.get<Submission>(`/submissions/${id}/`).then((r) => r.data),
}

/** Target-language code for the current user (vi | en | zh-Hans | zh-Hant). */
export function targetCode(user: { active_language: string; zh_script: string } | null): string | undefined {
  if (!user) return undefined
  if (user.active_language === 'zh') return user.zh_script === 'hant' ? 'zh-Hant' : 'zh-Hans'
  return user.active_language
}
