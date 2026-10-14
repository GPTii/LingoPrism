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
import DashboardPage from './pages/admin/DashboardPage'
import UsersPage from './pages/admin/UsersPage'
import VocabAdminPage from './pages/admin/VocabAdminPage'
import LanguageReviewPage from './pages/admin/LanguageReviewPage'

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
          <Route path="review" element={<Navigate to="/learn?kind=review" replace />} />
        </Route>

        <Route path="admin" element={<RequireStaff />}>
          <Route element={<AdminLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="vocab" element={<VocabAdminPage />} />
            <Route path="language-review" element={<LanguageReviewPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
