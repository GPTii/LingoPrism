import { useQuery } from '@tanstack/react-query'
import { App, Button, Checkbox, Form, Input, InputNumber, Radio, Switch, TimePicker, Upload } from 'antd'
import { ArrowRightOutlined, CameraOutlined } from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi, type NotificationSettings } from '../../api/auth'
import { errorMessage } from '../../api/client'
import type { User, UserGoal } from '../../api/types'
import { useAuth } from '../../auth/store'
import { useLogout } from '../../auth/useLogout'
import { AppIcon, type AppIconName } from '../../components/brand/AppIcon'
import { LangGlyph, PrismoAvatar } from '../../components/brand/Brand'
import { MyIdCard } from '../../components/Friends'
import { PageHeader, Section, UserAvatar } from '../../components/ui'
import { DeleteAccountSection } from '../../components/AccountGates'

const LANGS = [
  { value: 'en', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="en" size={18} />Tiếng Anh</span> },
  { value: 'zh', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="zh" size={18} />Tiếng Trung</span> },
  { value: 'vi', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="vi" size={18} />Tiếng Việt</span> },
]

/** "HH:mm:ss" from the API ⇄ the time picker */
const toTime = (v: string | null | undefined) => (v ? dayjs(v, 'HH:mm:ss') : null)
const fromTime = (v: Dayjs | null | undefined) => (v ? v.format('HH:mm:00') : null)

function Shortcut({ to, icon, label }: { to: string; icon: AppIconName; label: string }) {
  return (
    <Link to={to} className="lift lp-card flex items-center gap-3 px-4 py-3 !text-slate-800 font-semibold">
      <AppIcon name={icon} size={30} />{label}
    </Link>
  )
}

/** Avatar: click to pick a photo; the server keeps it and every screen shows it. */
function AvatarPicker({ user }: { user: User }) {
  const { message } = App.useApp()
  const setUser = useAuth((s) => s.setUser)
  const [busy, setBusy] = useState(false)
  return (
    <Upload accept="image/*" showUploadList={false} beforeUpload={(file) => {
      if (file.size > 5 * 1024 * 1024) {
        message.error('Ảnh tối đa 5 MB')
        return false
      }
      setBusy(true)
      authApi.uploadAvatar(file).then((u) => { setUser(u); message.success('Đã đổi ảnh đại diện') })
        .catch((e) => message.error(errorMessage(e))).finally(() => setBusy(false))
      return false
    }}>
      <button type="button" aria-label="Đổi ảnh đại diện" className="relative cursor-pointer rounded-full">
        <UserAvatar name={user.display_name} src={user.avatar} mascot={user.mascot} size={72} />
        <span className={`absolute -bottom-1 -right-1 h-8 w-8 rounded-full grid place-items-center bg-brand-600 text-white ring-4 ring-[var(--page-bg)] ${busy ? 'animate-pulse' : ''}`}>
          <CameraOutlined />
        </span>
      </button>
    </Upload>
  )
}

function GoalSection() {
  const { message } = App.useApp()
  const goal = useQuery({ queryKey: ['goal'], queryFn: authApi.goal })
  const [saving, setSaving] = useState(false)
  if (!goal.data) return null
  const save = async (v: UserGoal & { morning?: Dayjs | null; evening?: Dayjs | null }) => {
    setSaving(true)
    try {
      await authApi.updateGoal({
        daily_new_target: v.daily_new_target, daily_review_target: v.daily_review_target, smart_remind: v.smart_remind,
        remind_morning: fromTime(v.morning), remind_evening: fromTime(v.evening),
      })
      goal.refetch()
      message.success('Đã lưu mục tiêu')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }
  return (
    <Section title="Mục tiêu mỗi ngày">
      <Form layout="vertical" requiredMark={false} onFinish={save}
        initialValues={{ ...goal.data, morning: toTime(goal.data.remind_morning), evening: toTime(goal.data.remind_evening) }}>
        <div className="grid sm:grid-cols-2 gap-x-4">
          <Form.Item name="daily_new_target" label="Từ mới mỗi ngày" rules={[{ required: true }]}>
            <InputNumber min={1} max={100} size="large" className="!w-full" addonAfter="từ" />
          </Form.Item>
          <Form.Item name="daily_review_target" label="Từ ôn mỗi ngày" rules={[{ required: true }]}>
            <InputNumber min={1} max={300} size="large" className="!w-full" addonAfter="từ" />
          </Form.Item>
          <Form.Item name="morning" label="Nhắc học buổi sáng">
            <TimePicker format="HH:mm" minuteStep={5} size="large" className="!w-full" placeholder="Không nhắc" />
          </Form.Item>
          <Form.Item name="evening" label="Nhắc học buổi tối">
            <TimePicker format="HH:mm" minuteStep={5} size="large" className="!w-full" placeholder="Không nhắc" />
          </Form.Item>
        </div>
        <Form.Item name="smart_remind" label="Nhắc thông minh (chọn giờ bạn hay học)" valuePropName="checked"><Switch /></Form.Item>
        <Button htmlType="submit" type="primary" loading={saving}>Lưu mục tiêu</Button>
      </Form>
    </Section>
  )
}

function NotificationSection() {
  const { message } = App.useApp()
  const settings = useQuery({ queryKey: ['notification-settings'], queryFn: authApi.notificationSettings })
  if (!settings.data) return null
  const change = async (data: Partial<NotificationSettings>) => {
    try {
      await authApi.updateNotificationSettings(data)
      settings.refetch()
      message.success('Đã lưu')
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const rows: { key: keyof NotificationSettings; label: string; hint: string }[] = [
    { key: 'push_enabled', label: 'Thông báo đẩy', hint: 'Nhắc học và tin mới trên điện thoại' },
    { key: 'social_enabled', label: 'Cộng đồng', hint: 'Lời mời kết bạn, thả tim, bình luận, người theo dõi mới' },
    { key: 'contextual_allowed', label: 'Gợi ý theo vị trí', hint: 'Gợi ý từ vựng khi bạn tới một địa điểm' },
  ]
  return (
    <Section title="Thông báo">
      <ul className="m-0 p-0 list-none divide-y divide-slate-100">
        {rows.map((r) => (
          <li key={r.key} className="flex items-center gap-4 py-3">
            <div className="flex-1 min-w-0"><div className="font-semibold text-slate-800">{r.label}</div><div className="text-sm text-slate-500">{r.hint}</div></div>
            <Switch checked={!!settings.data![r.key]} onChange={(v) => change({ [r.key]: v })} aria-label={r.label} />
          </li>
        ))}
      </ul>
    </Section>
  )
}

function PasswordSection() {
  const { message } = App.useApp()
  const logout = useLogout()
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const save = async (v: { old_password: string; new_password: string }) => {
    setSaving(true)
    try {
      await authApi.changePassword(v.old_password, v.new_password)
      message.success('Đã đổi mật khẩu. Hãy đăng nhập lại bằng mật khẩu mới.')
      await logout()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }
  return (
    <Section title="Đổi mật khẩu">
      <Form form={form} layout="vertical" requiredMark={false} onFinish={save} autoComplete="off">
        <Form.Item name="old_password" label="Mật khẩu hiện tại" rules={[{ required: true, message: 'Nhập mật khẩu hiện tại' }]}>
          <Input.Password size="large" autoComplete="current-password" />
        </Form.Item>
        <Form.Item name="new_password" label="Mật khẩu mới" rules={[{ required: true, min: 8, message: 'Ít nhất 8 ký tự' }]}>
          <Input.Password size="large" autoComplete="new-password" />
        </Form.Item>
        <Form.Item name="confirm" label="Nhập lại mật khẩu mới" dependencies={['new_password']}
          rules={[{ required: true, message: 'Nhập lại mật khẩu mới' }, ({ getFieldValue }) => ({
            validator: (_, v) => (!v || v === getFieldValue('new_password') ? Promise.resolve() : Promise.reject(new Error('Hai mật khẩu chưa khớp'))),
          })]}>
          <Input.Password size="large" autoComplete="new-password" />
        </Form.Item>
        <p className="text-sm text-slate-500 mt-0">Sau khi đổi, mọi thiết bị đang đăng nhập sẽ phải đăng nhập lại.</p>
        <Button htmlType="submit" loading={saving}>Đổi mật khẩu</Button>
      </Form>
    </Section>
  )
}

export default function ProfilePage() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const [saving, setSaving] = useState(false)
  const isKid = user?.learner_type === 'kid'

  const onFinish = async (values: Partial<User>) => {
    setSaving(true)
    try {
      setUser(await authApi.updateMe(values))
      message.success('Đã lưu hồ sơ')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  if (!user) return null
  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <PageHeader
        title={
          <span className="flex items-center gap-4">
            <AvatarPicker user={user} />
            <span className="min-w-0">
              {user.display_name}
              <span className="block text-base font-medium text-slate-500 mt-0.5">{user.email}</span>
            </span>
          </span>
        } />
      <Link to="/prismo" className="lift lp-card p-4 flex items-center gap-4 group">
        <PrismoAvatar look={user.mascot} size={76} square />
        <span className="flex-1 min-w-0">
          <span className="block font-bold text-slate-800 text-lg">{user.mascot?.name || 'Prismo'} của bạn</span>
          <span className="block text-sm text-slate-500">Mở tủ đồ: mũ, kính, đồ cầm tay và nền cho linh vật của bạn</span>
        </span>
        <ArrowRightOutlined className="text-slate-400 transition-transform duration-150 group-hover:translate-x-0.5" />
      </Link>
      {!isKid && (
        <>
          <MyIdCard />
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <Shortcut to="/friends" icon="community" label="Bạn bè" />
            <Shortcut to="/community?tab=saved" icon="bookmark" label="Bài đã lưu" />
            <Shortcut to="/notifications" icon="bell" label="Thông báo" />
          </div>
        </>
      )}
      <Form layout="vertical" initialValues={user} onFinish={onFinish} requiredMark={false} className="flex flex-col gap-6">
        <Section title="Về bạn">
          <Form.Item name="display_name" label="Tên hiển thị" rules={[{ required: true, message: 'Nhập tên hiển thị' }]}>
            <Input size="large" maxLength={80} />
          </Form.Item>
          <Form.Item name="bio" label="Giới thiệu" extra="Hiện trên trang cá nhân của bạn trong Cộng đồng.">
            <Input.TextArea maxLength={200} showCount autoSize={{ minRows: 2, maxRows: 4 }} placeholder="VD: Đang luyện HSK 3, thích chụp đồ ăn để học từ" />
          </Form.Item>
          <Form.Item name="learner_type" label="Đối tượng" extra="Chế độ trẻ em ẩn bảng tin, kết bạn và nhóm học trong Cộng đồng." className="!mb-0">
            <Radio.Group options={[{ value: 'adult', label: 'Người lớn' }, { value: 'kid', label: 'Trẻ em' }]} />
          </Form.Item>
        </Section>
        <Section title="Ngôn ngữ">
          <Form.Item name="learning_languages" label="Ngôn ngữ muốn học">
            <Checkbox.Group options={LANGS} />
          </Form.Item>
          <Form.Item name="active_language" label="Đang học">
            <Radio.Group options={LANGS} />
          </Form.Item>
          <Form.Item name="zh_script" label="Dạng chữ Hán">
            <Radio.Group className="!flex !flex-col gap-2"
              options={[
                { value: 'hans', label: <span>Giản thể – chuẩn Trung Quốc đại lục (<span lang="zh-Hans">汉字</span>)</span> },
                { value: 'hant', label: <span>Phồn thể – chuẩn Đài Loan (<span lang="zh-Hant">漢字</span>)</span> },
              ]}
            />
          </Form.Item>
          <Form.Item name="show_zhuyin" label="Hiện Zhuyin (注音) cho phồn thể" valuePropName="checked" className="!mb-0">
            <Switch />
          </Form.Item>
        </Section>
        <div>
          <Button type="primary" size="large" htmlType="submit" loading={saving}>Lưu thay đổi</Button>
        </div>
      </Form>
      <GoalSection />
      <NotificationSection />
      {user?.has_password !== false && <PasswordSection />}
      <DeleteAccountSection />
      <p className="text-center text-sm text-slate-500 m-0">
        <Link to="/releases">Có gì mới</Link> · <Link to="/privacy">Quyền riêng tư</Link> · <Link to="/terms">Điều khoản</Link>
      </p>
    </div>
  )
}
