import { api } from './client'
import type { Paginated } from './types'
import type { Poi, Submission, SupportConversation } from './app'

export interface DashboardData {
  users: { total: number; learners: number; kids: number; new_7d: number; active_today: number; by_language: { active_language: string; zh_script: string; n: number }[] }
  learning: { sessions_per_day: { date: string; count: number }[]; answers_today: number }
  detection: { per_day: { date: string; count: number }[]; top_labels: { label: string; n: number }[] }
  content: { translations: { language_id: string; status: string; n: number }[]; open_error_reports: number; pending_post_reports: number; pending_user_reports: number; posts_7d: number }
  exams: { waiting_for_grading: number }
  support: { open_conversations: number }
}

export interface AdminQuestion {
  id: number
  kind: 'mcq' | 'fill' | 'essay'
  language: string
  topic: number | null
  prompt: string
  options: { text: string; correct: boolean }[]
  accepted_answers: string[]
  explanation: string
  difficulty: number
}

export interface AdminExam {
  id: number
  title: string
  description: string
  language: string
  topic: number | null
  audience: string
  time_limit_minutes: number | null
  pass_percent: number
  is_published: boolean
  questions: { id: number; points: string; order: number; kind: string; prompt: string }[]
  submission_count: number
}

export interface PostReport {
  id: number
  post: number
  post_caption: string
  post_image: string
  post_author: string
  post_status: string
  reporter_email: string
  reason: string
  details: string
  status: 'pending' | 'resolved' | 'dismissed'
  created_at: string
}

/** A learner reported another learner; `evidence` is the conversation as it was when reported. */
export interface UserReport {
  id: number
  reporter: number
  reporter_name: string
  reporter_email: string
  reported: number
  reported_name: string
  reported_email: string
  reported_status: 'active' | 'locked'
  /** distinct people who ever reported this learner */
  reports_against: number
  reason: string
  details: string
  evidence: { sender: string; sender_id: number; content: string; created_at: string }[]
  status: 'pending' | 'resolved' | 'dismissed'
  created_at: string
}

export interface DetectionLog {
  id: number
  user: string
  model: string
  device: string
  inference_ms: number | null
  image: string | null
  created_at: string
  items: { label: string; confidence: number; feedback: string; corrected_label: string }[]
}

/** A learner's detection error report, remembered by what the object looks like (correction memory). */
export interface DetectionReport {
  id: number
  user: string
  wrong_label: string
  /** '' = "not an object" */
  correct_label: string
  status: 'pending' | 'approved' | 'rejected'
  disputes: number
  /** times the server already fixed a detection with it */
  applied: number
  /** distinct learners who reported the same mistake */
  same_reports: number
  crop: string | null
  photo: string | null
  reviewed_by: string | null
  exported_at: string | null
  created_at: string
}

export interface DetectionReportSummary {
  pending: number
  approved: number
  rejected: number
  approved_not_exported: number
  applied: number
  memory_enabled: boolean
  consensus_users: number
}

export interface DetectionStats {
  per_label: { label: string; count: number; avg_confidence: number; wrong: number; correct: number }[]
  confusion: { label: string; corrected_label: string; count: number }[]
  by_device: { device: string; count: number; avg_ms: number | null }[]
}

export interface ModelVersion {
  id: number
  name: string
  file: string
  classes: string[]
  precision: number | null
  recall: number | null
  map50: number | null
  map50_95: number | null
  is_active: boolean
  created_at: string
}

export const adminApi = {
  dashboard: () => api.get<DashboardData>('/admin/dashboard/').then((r) => r.data),
  // exams
  questions: (params?: Record<string, unknown>) => api.get<Paginated<AdminQuestion>>('/admin/questions/', { params }).then((r) => r.data),
  createQuestion: (data: Partial<AdminQuestion>) => api.post<AdminQuestion>('/admin/questions/', data).then((r) => r.data),
  exams: (params?: Record<string, unknown>) => api.get<Paginated<AdminExam>>('/admin/exams/', { params }).then((r) => r.data),
  updateExam: (id: number, data: Partial<AdminExam> & { question_ids?: number[] }) => api.patch<AdminExam>(`/admin/exams/${id}/`, data).then((r) => r.data),
  createExam: (data: Partial<AdminExam> & { question_ids?: number[] }) => api.post<AdminExam>('/admin/exams/', data).then((r) => r.data),
  submissions: (params?: Record<string, unknown>) => api.get<Paginated<Submission>>('/admin/submissions/', { params }).then((r) => r.data),
  grade: (id: number, grades: { answer: number; score: string; feedback?: string }[], feedback: string) =>
    api.post<Submission>(`/admin/submissions/${id}/grade/`, { grades, feedback }).then((r) => r.data),
  // pois
  pois: () => api.get<Poi[]>('/pois/').then((r) => r.data),
  savePoi: (poi: Partial<Poi>) => (poi.id ? api.patch<Poi>(`/pois/${poi.id}/`, poi) : api.post<Poi>('/pois/', poi)).then((r) => r.data),
  deletePoi: (id: number) => api.delete(`/pois/${id}/`),
  poiStats: () => api.get<{ id: number; name: string; category: string; visits: number }[]>('/pois/stats/').then((r) => r.data),
  // moderation
  postReports: (status = 'pending') => api.get<Paginated<PostReport>>('/admin/post-reports/', { params: { status } }).then((r) => r.data),
  resolveReport: (id: number, hide: boolean) => api.post(`/admin/post-reports/${id}/resolve/`, { hide_post: hide }),
  userReports: (status = 'pending') => api.get<Paginated<UserReport>>('/admin/user-reports/', { params: { status } }).then((r) => r.data),
  resolveUserReport: (id: number, lock: boolean) => api.post(`/admin/user-reports/${id}/resolve/`, { lock }),
  // notifications
  broadcast: (data: { title: string; body: string; role: string; learner_type: string }) => api.post<{ sent: number }>('/admin/broadcast/', data).then((r) => r.data),
  // support
  conversations: (status?: string) => api.get<Paginated<SupportConversation>>('/support/conversations/', { params: { status } }).then((r) => r.data.results),
  // detections
  detections: (page = 1) => api.get<Paginated<DetectionLog>>('/admin/detections/', { params: { page } }).then((r) => r.data),
  detectionStats: () => api.get<DetectionStats>('/admin/detections/stats/').then((r) => r.data),
  detectionReports: (status: string | undefined, page = 1) =>
    api.get<Paginated<DetectionReport>>('/admin/detection-reports/', { params: { status, page } }).then((r) => r.data),
  detectionReportSummary: () => api.get<DetectionReportSummary>('/admin/detection-reports/summary/').then((r) => r.data),
  reviewDetectionReport: (id: number, approve: boolean) => api.post(`/admin/detection-reports/${id}/${approve ? 'approve' : 'reject'}/`),
  exportDetectionReports: () => api.get<Blob>('/admin/detection-reports/export/', { responseType: 'blob' }).then((r) => r.data),
  modelVersions: () => api.get<Paginated<ModelVersion>>('/admin/model-versions/').then((r) => r.data.results),
  activateModel: (id: number) => api.patch(`/admin/model-versions/${id}/`, { is_active: true }),
  // gamification
  items: () => api.get<Paginated<Record<string, unknown>>>('/admin/items/').then((r) => r.data.results),
  badges: () => api.get<Paginated<Record<string, unknown>>>('/admin/badges/').then((r) => r.data.results),
  tiers: () => api.get<Paginated<Record<string, unknown>>>('/admin/league-tiers/').then((r) => r.data.results),
  closeWeek: () => api.post<{ closed: number }>('/admin/league-tiers/close-week/').then((r) => r.data),
  patch: (resource: string, id: number, data: Record<string, unknown>) => api.patch(`/admin/${resource}/${id}/`, data),
}
