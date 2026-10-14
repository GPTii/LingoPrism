import { Avatar, Dropdown, Layout, Menu } from 'antd'
import {
  AlertOutlined, AuditOutlined, BookOutlined, CameraOutlined, DashboardOutlined, EnvironmentOutlined,
  FileDoneOutlined, LogoutOutlined, MessageOutlined, NotificationOutlined, TeamOutlined, TrophyOutlined,
  UserOutlined, HomeOutlined,
} from '@ant-design/icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/store'
import { useLogout } from '../auth/useLogout'

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
  { key: '/admin/groups', icon: <TeamOutlined />, label: 'Nhóm học' },
  { key: '/admin/detections', icon: <CameraOutlined />, label: 'Nhận diện YOLO' },
]

export default function AdminLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuth((s) => s.user)
  const logout = useLogout()
  const selected = ITEMS.map((i) => i.key).filter((k) => location.pathname.startsWith(k)).sort((a, b) => b.length - a.length)[0]

  return (
    <Layout className="min-h-screen">
      <Layout.Sider width={232} theme="light" breakpoint="lg" collapsedWidth={64} className="border-r border-slate-200">
        <div className="flex items-center gap-2 px-5 h-16">
          <img src="/logo.png" alt="" className="h-8 w-8 rounded-lg" />
          <span className="font-bold text-slate-800">LingoPrism Admin</span>
        </div>
        <Menu mode="inline" selectedKeys={[selected]} items={ITEMS} onClick={(e) => navigate(e.key)} />
      </Layout.Sider>
      <Layout>
        <Layout.Header className="!bg-white !px-6 flex items-center justify-end border-b border-slate-200">
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
              <span>{user?.display_name}</span>
            </button>
          </Dropdown>
        </Layout.Header>
        <Layout.Content className="p-6">
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  )
}
