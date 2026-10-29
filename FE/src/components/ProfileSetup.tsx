import { App, Button, DatePicker, Form, Input, Modal, Radio, Upload } from 'antd'
import { CameraOutlined } from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import { useState } from 'react'
import { authApi } from '../api/auth'
import { gameApi } from '../api/app'
import { errorMessage } from '../api/client'
import type { User } from '../api/types'
import { isStaffRole, useAuth } from '../auth/store'
import { UserAvatar } from './ui'

/** A photo, an app preset, or Prismo chosen to stand in for the photo. */
export const hasAvatar = (user: User) => !!user.avatar || !!user.mascot?.as_avatar

/** What the sign-in prompt asks for: a picture, a birthday and a gender (the bio is a bonus, never asked for). */
export const profileMissing = (user: User) => !hasAvatar(user) || !user.birth_date || !user.gender

export const GENDERS = [{ value: 'male', label: 'Nam' }, { value: 'female', label: 'Nữ' }, { value: 'other', label: 'Khác' }]

/** "YYYY-MM-DD" from the API ⇄ the date picker */
export const birthDateProps = {
  getValueProps: (v: string | null | undefined) => ({ value: v ? dayjs(v) : null }),
  normalize: (d: Dayjs | null) => (d ? d.format('YYYY-MM-DD') : null),
}
export const birthDateLimit = (d: Dayjs) => d.isAfter(dayjs()) || d.isBefore(dayjs('1900-01-01'))

/** Avatar: click to pick a photo; the server keeps it and every screen shows it. */
export function AvatarPicker({ user, size = 72 }: { user: User; size?: number }) {
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
        <UserAvatar name={user.display_name} src={user.avatar} mascot={user.mascot} size={size} />
        <span className={`absolute -bottom-1 -right-1 h-8 w-8 rounded-full grid place-items-center bg-brand-600 text-white ring-4 ring-[var(--surface)] ${busy ? 'animate-pulse' : ''}`}>
          <CameraOutlined />
        </span>
      </button>
    </Upload>
  )
}

/** The picture block of the sign-in prompt and the welcome survey: upload a photo, or let Prismo be the avatar. */
export function AvatarChoice({ user }: { user: User }) {
  const { message } = App.useApp()
  const setUser = useAuth((s) => s.setUser)
  const usePrismo = async () => {
    try {
      await gameApi.dress({ as_avatar: true })
      setUser(await authApi.me())
      message.success('Prismo đã là ảnh đại diện của bạn')
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <div className="flex items-center gap-4">
      <AvatarPicker user={user} />
      <div className="flex-1 min-w-0 text-sm text-slate-500">
        {hasAvatar(user) ? 'Đẹp lắm! Chạm vào ảnh để đổi.' : 'Chạm vào ảnh để tải ảnh của bạn lên (tối đa 5 MB).'}
        {!user.mascot?.as_avatar && (
          <div><Button type="link" className="!px-0" onClick={usePrismo}>Hoặc dùng Prismo làm ảnh đại diện</Button></div>
        )}
      </div>
    </div>
  )
}

interface Answers { display_name: string; bio?: string; birth_date?: string | null; gender?: string }

/**
 * Right after signing in: if the profile still lacks a picture, a birthday or a gender, ask once for them
 * ("Để sau" is always there). New accounts fill the same things in the welcome survey instead.
 */
export function ProfilePrompt() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const ask = useAuth((s) => s.askProfile)
  const setUser = useAuth((s) => s.setUser)
  const done = useAuth((s) => s.doneAskingProfile)
  const [saving, setSaving] = useState(false)
  const open = !!user && ask && user.onboarding_completed && !isStaffRole(user) && profileMissing(user)
  if (!open || !user) return null
  const kid = user.learner_type === 'kid'

  const save = async (v: Answers) => {
    setSaving(true)
    try {
      setUser(await authApi.updateMe({
        display_name: v.display_name.trim(), ...(kid ? {} : { bio: (v.bio ?? '').trim() }),
        ...(v.birth_date ? { birth_date: v.birth_date } : {}), ...(v.gender ? { gender: v.gender } : {}),
      }))
      message.success('Đã cập nhật hồ sơ')
      done()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open centered footer={null} onCancel={done} mask={{ closable: false }} title="Hoàn thiện hồ sơ của bạn" width={520}>
      <p className="text-slate-500 -mt-1 mb-4">
        {kid ? 'Chọn ảnh đại diện và cho LingoPrism biết thêm về con nhé.' : 'Thêm ảnh đại diện và vài thông tin để bạn bè dễ nhận ra bạn.'}
      </p>
      <Form<Answers> layout="vertical" requiredMark={false} onFinish={save}
        initialValues={{ display_name: user.display_name, bio: user.bio, birth_date: user.birth_date, gender: user.gender || undefined }}>
        <div className="mb-5"><AvatarChoice user={user} /></div>
        <Form.Item name="display_name" label="Tên hiển thị" rules={[{ required: true, whitespace: true, message: 'Nhập tên hiển thị' }]}>
          <Input size="large" maxLength={80} />
        </Form.Item>
        {!kid && (
          <Form.Item name="bio" label="Giới thiệu (không bắt buộc)">
            <Input.TextArea maxLength={200} showCount autoSize={{ minRows: 2, maxRows: 4 }} placeholder="VD: Đang luyện HSK 3, thích chụp đồ ăn để học từ" />
          </Form.Item>
        )}
        <div className="grid sm:grid-cols-2 gap-x-4">
          <Form.Item name="birth_date" label="Ngày sinh" {...birthDateProps}>
            <DatePicker size="large" className="w-full" format="DD/MM/YYYY" placeholder="Chọn ngày" disabledDate={birthDateLimit} />
          </Form.Item>
          <Form.Item name="gender" label="Giới tính">
            <Radio.Group optionType="button" options={GENDERS} />
          </Form.Item>
        </div>
        <div className="flex justify-end gap-2">
          <Button size="large" onClick={done}>Để sau</Button>
          <Button type="primary" htmlType="submit" size="large" loading={saving}>Lưu</Button>
        </div>
      </Form>
    </Modal>
  )
}
