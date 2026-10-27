import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth, RequireStaff } from './auth/guards'
import LearnerLayout from './layouts/LearnerLayout'
import AdminLayout from './layouts/AdminLayout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import HomePage from './pages/learner/HomePage'

// pages load on demand: a first visit downloads only the shell, sign-in and home, not every screen
const WelcomePage = lazy(() => import('./pages/auth/WelcomePage'))
const ProfilePage = lazy(() => import('./pages/learner/ProfilePage'))
const VocabPage = lazy(() => import('./pages/learner/VocabPage'))
const TopicPage = lazy(() => import('./pages/learner/TopicPage'))
const SessionPage = lazy(() => import('./pages/learner/SessionPage'))
const SentencePage = lazy(() => import('./pages/learner/SentencePage'))
const LiteracyLessonPage = lazy(() => import('./pages/learner/LiteracyPages').then((m) => ({ default: m.LiteracyLessonPage })))
const LiteracyMapPage = lazy(() => import('./pages/learner/LiteracyPages').then((m) => ({ default: m.LiteracyMapPage })))
const LevelTestPage = lazy(() => import('./pages/learner/LevelTestPage'))
const CameraPage = lazy(() => import('./pages/learner/CameraPage'))
const DetectionHistoryPage = lazy(() => import('./pages/learner/DetectionHistoryPage'))
const CommunityPage = lazy(() => import('./pages/learner/CommunityPage'))
const GroupPage = lazy(() => import('./pages/learner/GroupPage'))
const MemberProfilePage = lazy(() => import('./pages/learner/MemberProfilePage'))
const FriendsPage = lazy(() => import('./pages/learner/FriendsPage'))
const PostPage = lazy(() => import('./pages/learner/PostPage'))
const ExamListPage = lazy(() => import('./pages/learner/ExamsPages').then((m) => ({ default: m.ExamListPage })))
const ExamResultPage = lazy(() => import('./pages/learner/ExamsPages').then((m) => ({ default: m.ExamResultPage })))
const ExamTakePage = lazy(() => import('./pages/learner/ExamsPages').then((m) => ({ default: m.ExamTakePage })))
const MapPage = lazy(() => import('./pages/learner/MapPage'))
const AchievementsPage = lazy(() => import('./pages/learner/AchievementsPage'))
const WardrobePage = lazy(() => import('./pages/learner/WardrobePage'))
const StatsPage = lazy(() => import('./pages/learner/StatsPage'))
const SpeakPage = lazy(() => import('./pages/learner/SpeakPage'))
const SupportPage = lazy(() => import('./pages/learner/SupportPage'))
const MessagesPage = lazy(() => import('./pages/learner/MessagesPage'))
const NotificationsPage = lazy(() => import('./pages/learner/NotificationsPage'))
const DashboardPage = lazy(() => import('./pages/admin/DashboardPage'))
const UsersPage = lazy(() => import('./pages/admin/UsersPage'))
const VocabAdminPage = lazy(() => import('./pages/admin/VocabAdminPage'))
const LanguageReviewPage = lazy(() => import('./pages/admin/LanguageReviewPage'))
const ExamsAdminPage = lazy(() => import('./pages/admin/ExamsAdminPage'))
const PoisAdminPage = lazy(() => import('./pages/admin/PoisAdminPage'))
const BroadcastPage = lazy(() => import('./pages/admin/OperationsPages').then((m) => ({ default: m.BroadcastPage })))
const DetectionsAdminPage = lazy(() => import('./pages/admin/OperationsPages').then((m) => ({ default: m.DetectionsAdminPage })))
const GamificationAdminPage = lazy(() => import('./pages/admin/OperationsPages').then((m) => ({ default: m.GamificationAdminPage })))
const ModerationPage = lazy(() => import('./pages/admin/OperationsPages').then((m) => ({ default: m.ModerationPage })))
const SupportAdminPage = lazy(() => import('./pages/admin/OperationsPages').then((m) => ({ default: m.SupportAdminPage })))
const AlgorithmsPage = lazy(() => import('./pages/admin/AlgorithmsPage'))
const AuditLogPage = lazy(() => import('./pages/admin/AuditLogPage'))
export default function App() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />

        <Route element={<RequireAuth />}>
          <Route path="/welcome" element={<WelcomePage />} />
          <Route element={<LearnerLayout />}>
            <Route index element={<HomePage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="vocab" element={<VocabPage />} />
            <Route path="vocab/topics/:id" element={<TopicPage />} />
            <Route path="learn" element={<SessionPage />} />
            <Route path="sentences" element={<SentencePage />} />
            <Route path="doc-viet" element={<LiteracyMapPage />} />
            <Route path="doc-viet/:n" element={<LiteracyLessonPage />} />
            <Route path="levels/:n/test" element={<LevelTestPage />} />
            <Route path="review" element={<Navigate to="/learn?kind=review" replace />} />
            <Route path="camera" element={<CameraPage />} />
            <Route path="camera/history" element={<DetectionHistoryPage />} />
            <Route path="community" element={<CommunityPage />} />
            <Route path="community/groups/:id" element={<GroupPage />} />
            <Route path="community/users/:id" element={<MemberProfilePage />} />
            <Route path="community/posts/:id" element={<PostPage />} />
            <Route path="friends" element={<FriendsPage />} />
            <Route path="exams" element={<ExamListPage />} />
            <Route path="exams/:id" element={<ExamTakePage />} />
            <Route path="exams/results/:id" element={<ExamResultPage />} />
            <Route path="map" element={<MapPage />} />
            <Route path="shop" element={<AchievementsPage />} />
            <Route path="achievements" element={<AchievementsPage />} />
            <Route path="prismo" element={<WardrobePage />} />
            <Route path="stats" element={<StatsPage />} />
            <Route path="speak" element={<SpeakPage />} />
            <Route path="support" element={<SupportPage />} />
            <Route path="messages" element={<MessagesPage />} />
            <Route path="messages/:id" element={<MessagesPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
          </Route>

          <Route path="admin" element={<RequireStaff />}>
            <Route element={<AdminLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="vocab" element={<VocabAdminPage />} />
              <Route path="language-review" element={<LanguageReviewPage />} />
              <Route path="exams" element={<ExamsAdminPage />} />
              <Route path="pois" element={<PoisAdminPage />} />
              <Route path="moderation" element={<ModerationPage />} />
              <Route path="support" element={<SupportAdminPage />} />
              <Route path="notifications" element={<BroadcastPage />} />
              <Route path="gamification" element={<GamificationAdminPage />} />
              <Route path="detections" element={<DetectionsAdminPage />} />
              <Route path="algorithms" element={<AlgorithmsPage />} />
              <Route path="audit" element={<AuditLogPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
