import { Avatar, Button, Drawer, Dropdown, Grid, Layout, Menu } from 'antd'
import { Suspense, useEffect, useState } from 'react'
import {
  AlertOutlined, AuditOutlined, BookOutlined, CameraOutlined, DashboardOutlined, EnvironmentOutlined,
  FileDoneOutlined, LogoutOutlined, MessageOutlined, NotificationOutlined, TrophyOutlined,
  UserOutlined, HomeOutlined,
  ExperimentOutlined, MenuOutlined, MoonOutlined, SunOutlined, HistoryOutlined,
} from '@ant-design/icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/store'
import { useLogout } from '../auth/useLogout'
import { LogoMark } from '../components/brand/Brand'
import { useThemeMode } from '../theme/store'
import { WhatsNew } from '../components/AccountGates'

const ITEMS = [
  { key: '/admin', icon: <DashboardOutlined />, label: 'Tổng quan' },
  { key: '/admin/users', icon: <UserOutlined />, label: 'Người dùng' },
  { key: '/admin/vocab', icon: <BookOutlined />, label: 'Từ vựng & chủ đề' },
  { key: '/admin/language-review', icon: <AuditOutlined />, label: 'Kiểm tra dữ liệu' },
  { key: '/admin/exams', icon: <FileDoneOutlined />, label: 'Câu hỏi & đề thi' },
  { key: '/admin/pois', icon: <EnvironmentOutlined />, label: 'Bản đồ POI' },
  { key: '/admin/moderation', icon: <AlertOutlined />, label: 'Kiểm duyệt' },
  { key: '/admin/support', icon: <MessageOutlined />, label: 'Chat hỗ trợ' },
  { key: '/admin/notifications', icon: <NotificationOutlined />, label: 'Thông báo' },
  { key: '/admin/gamification', icon: <TrophyOutlined />, label: 'Game hóa' },
  { key: '/admin/detections', icon: <CameraOutlined />, label: 'Nhận diện YOLO' },
  { key: '/admin/algorithms', icon: <ExperimentOutlined />, label: 'Thuật toán AI' },
  { key: '/admin/audit', icon: <HistoryOutlined />, label: 'Nhật ký thao tác', adminOnly: true },
]

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuth((s) => s.user)
  const logout = useLogout()
  const { mode, toggle: toggleTheme } = useThemeMode()
  const dark = mode === 'dark'
  // the audit log is for admins only (the API answers 403 to staff)
  const items = ITEMS.filter((i) => !('adminOnly' in i) || user?.role === 'admin').map(({ key, icon, label }) => ({ key, icon, label }))
  const selected = ITEMS.map((i) => i.key).filter((k) => location.pathname.startsWith(k)).sort((a, b) => b.length - a.length)[0]

  const screens = Grid.useBreakpoint()
  const wide = screens.lg ?? true // laptop and larger: fixed sidebar; tablet / phone: menu in a drawer
  const [open, setOpen] = useState(false)
  useEffect(() => setOpen(false), [location.pathname])
  const logo = (
    <div className="flex items-center gap-2 px-5 h-16">
      <LogoMark size={32} />
      <span className="font-extrabold tracking-[-0.02em] text-slate-800">LingoPrism <span className="font-semibold text-slate-500">Quản trị</span></span>
    </div>
  )
  const menu = <Menu mode="inline" selectedKeys={[selected]} items={items} onClick={(e) => navigate(e.key)} className="!border-e-0" />

  return (
    <Layout className="min-h-screen">
      {wide ? (
        <Layout.Sider width={232} theme="light" className="border-r border-slate-200 !sticky top-0 h-screen overflow-y-auto">
          {logo}
          {menu}
        </Layout.Sider>
      ) : (
        <Drawer open={open} onClose={() => setOpen(false)} placement="left" width={260} styles={{ body: { padding: 0 } }}
          title={null} closable={false}>
          {logo}
          {menu}
        </Drawer>
      )}
      <Layout className="min-w-0">
        <Layout.Header className="!px-3 md:!px-6 flex items-center justify-between gap-2 border-b border-slate-200 sticky top-0 z-10">
          {wide ? <span /> : (
            <div className="flex items-center gap-2">
              <Button type="text" icon={<MenuOutlined />} onClick={() => setOpen(true)} aria-label="Menu" />
              <span className="font-bold text-slate-800 hidden min-[400px]:inline">LingoPrism Admin</span>
            </div>
          )}
          <div className="flex items-center gap-2">
          <Button type="text" onClick={toggleTheme} aria-label={dark ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
            icon={dark ? <SunOutlined /> : <MoonOutlined />} />
          <Dropdown
            trigger={['click']}
            menu={{
              items: [
                { key: 'learn', icon: <HomeOutlined />, label: 'Về trang học', onClick: () => navigate('/') },
                { key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', danger: true, onClick: logout },
              ],
            }}
          >
            <button className="flex items-center gap-2 cursor-pointer">
              <Avatar src={user?.avatar ?? undefined} icon={<UserOutlined />} />
              <span className="hidden sm:inline max-w-48 truncate">{user?.display_name}</span>
            </button>
          </Dropdown>
          </div>
        </Layout.Header>
        <Layout.Content className="p-3 md:p-6">
          <div className="mx-auto w-full max-w-[1600px]">
            <WhatsNew />
            <Suspense fallback={null}><Outlet /></Suspense>
          </div>
        </Layout.Content>
      </Layout>
    </Layout>
  )
}
