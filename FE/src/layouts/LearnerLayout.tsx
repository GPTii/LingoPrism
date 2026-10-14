import { App, Avatar, Dropdown, Select } from 'antd'
import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { authApi } from '../api/auth'
import {
  BookOutlined, CameraOutlined, EnvironmentOutlined, FileDoneOutlined, HomeOutlined,
  LogoutOutlined, RedoOutlined, SettingOutlined, ShopOutlined, TeamOutlined, UserOutlined,
} from '@ant-design/icons'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { isStaffRole, useAuth } from '../auth/store'
import { useLogout } from '../auth/useLogout'
import type { User } from '../api/types'

const NAV = [
  { to: '/', label: 'Trang chủ', icon: <HomeOutlined /> },
  { to: '/vocab', label: 'Từ vựng', icon: <BookOutlined /> },
  { to: '/review', label: 'Ôn tập', icon: <RedoOutlined /> },
  { to: '/camera', label: 'Nhận diện', icon: <CameraOutlined /> },
  { to: '/exams', label: 'Đề thi', icon: <FileDoneOutlined /> },
  { to: '/community', label: 'Cộng đồng', icon: <TeamOutlined /> },
  { to: '/map', label: 'Bản đồ', icon: <EnvironmentOutlined /> },
  { to: '/shop', label: 'Cửa hàng', icon: <ShopOutlined /> },
]

export default function LearnerLayout() {
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const logout = useLogout()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { message } = App.useApp()

  useEffect(() => {
    const onNoVoice = (e: Event) =>
      message.warning(`Trình duyệt chưa có giọng đọc ${(e as CustomEvent).detail}. Hãy cài thêm giọng đọc trong cài đặt hệ điều hành hoặc dùng Chrome/Edge.`)
    window.addEventListener('lingoprism:no-voice', onNoVoice)
    return () => window.removeEventListener('lingoprism:no-voice', onNoVoice)
  }, [message])

  const switchLanguage = async (value: string) => {
    const [active_language, zh_script] = value.split(':') as [User['active_language'], User['zh_script'] | undefined]
    const updated = await authApi.updateMe({ active_language, ...(zh_script ? { zh_script } : {}) })
    setUser(updated)
    queryClient.invalidateQueries()
  }
  const languageValue = user?.active_language === 'zh' ? `zh:${user.zh_script}` : user?.active_language

  const menu = [
    { key: 'profile', icon: <UserOutlined />, label: 'Hồ sơ & cài đặt', onClick: () => navigate('/profile') },
    ...(isStaffRole(user) ? [{ key: 'admin', icon: <SettingOutlined />, label: 'Trang quản trị', onClick: () => navigate('/admin') }] : []),
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', danger: true, onClick: logout },
  ]

  return (
    <div className="min-h-screen flex">
      <aside className="hidden md:flex w-60 flex-col border-r border-slate-200 bg-white px-3 py-5">
        <div className="flex items-center gap-2 px-3 mb-8">
          <img src="/logo.png" alt="" className="h-9 w-9 rounded-xl" />
          <span className="text-lg font-bold text-slate-800">LingoPrism</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 font-medium transition ${
                  isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-50'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 flex items-center justify-between px-6 bg-white/80 backdrop-blur border-b border-slate-200 sticky top-0 z-10">
          <div className="md:hidden font-bold text-slate-800">LingoPrism</div>
          <div className="flex-1" />
          <div className="flex items-center gap-5 text-sm font-semibold">
            <Select
              value={languageValue}
              onChange={switchLanguage}
              variant="borderless"
              style={{ width: 190 }}
              options={[
                { value: 'en', label: '🇬🇧 Tiếng Anh' },
                { value: 'zh:hans', label: '🇨🇳 Tiếng Trung giản thể' },
                { value: 'zh:hant', label: '🇹🇼 Tiếng Trung phồn thể' },
                { value: 'vi', label: '🇻🇳 Tiếng Việt' },
              ]}
            />
            <span title="Vảy">🐟 {user?.scales_balance ?? 0}</span>
            <span title="Ngọc">💎 {user?.gems_balance ?? 0}</span>
            <Dropdown menu={{ items: menu }} placement="bottomRight" trigger={['click']}>
              <button className="flex items-center gap-2 cursor-pointer">
                <Avatar src={user?.avatar ?? undefined} icon={<UserOutlined />} />
                <span className="hidden sm:inline text-slate-700">{user?.display_name}</span>
              </button>
            </Dropdown>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8 pb-24 md:pb-8">
          <Outlet />
        </main>
        <nav className="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-slate-200 flex justify-around py-2">
          {NAV.slice(0, 5).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => `flex flex-col items-center text-xs ${isActive ? 'text-brand-600' : 'text-slate-500'}`}
            >
              <span className="text-xl">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}
