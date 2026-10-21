import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth, RequireStaff } from './auth/guards'
import LearnerLayout from './layouts/LearnerLayout'
import AdminLayout from './layouts/AdminLayout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import HomePage from './pages/learner/HomePage'
import ProfilePage from './pages/learner/ProfilePage'
import VocabPage from './pages/learner/VocabPage'
import TopicPage from './pages/learner/TopicPage'
import SessionPage from './pages/learner/SessionPage'
import SentencePage from './pages/learner/SentencePage'
import { LiteracyLessonPage, LiteracyMapPage } from './pages/learner/LiteracyPages'
import LevelTestPage from './pages/learner/LevelTestPage'
import CameraPage from './pages/learner/CameraPage'
import CommunityPage from './pages/learner/CommunityPage'
import GroupPage from './pages/learner/GroupPage'
import MemberProfilePage from './pages/learner/MemberProfilePage'
import { ExamListPage, ExamResultPage, ExamTakePage } from './pages/learner/ExamsPages'
import MapPage from './pages/learner/MapPage'
import AchievementsPage from './pages/learner/AchievementsPage'
import SupportPage from './pages/learner/SupportPage'
import NotificationsPage from './pages/learner/NotificationsPage'
import DashboardPage from './pages/admin/DashboardPage'
import UsersPage from './pages/admin/UsersPage'
import VocabAdminPage from './pages/admin/VocabAdminPage'
import LanguageReviewPage from './pages/admin/LanguageReviewPage'
import ExamsAdminPage from './pages/admin/ExamsAdminPage'
import PoisAdminPage from './pages/admin/PoisAdminPage'
import { BroadcastPage, DetectionsAdminPage, GamificationAdminPage, ModerationPage, SupportAdminPage } from './pages/admin/OperationsPages'
import AlgorithmsPage from './pages/admin/AlgorithmsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />

      <Route element={<RequireAuth />}>
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
          <Route path="community" element={<CommunityPage />} />
          <Route path="community/groups/:id" element={<GroupPage />} />
          <Route path="community/users/:id" element={<MemberProfilePage />} />
          <Route path="exams" element={<ExamListPage />} />
          <Route path="exams/:id" element={<ExamTakePage />} />
          <Route path="exams/results/:id" element={<ExamResultPage />} />
          <Route path="map" element={<MapPage />} />
          <Route path="shop" element={<AchievementsPage />} />
          <Route path="achievements" element={<AchievementsPage />} />
          <Route path="support" element={<SupportPage />} />
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
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
