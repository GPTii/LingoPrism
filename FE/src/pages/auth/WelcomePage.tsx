import { App, Button, DatePicker, Form, Input, Radio } from 'antd'
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import type { Dayjs } from 'dayjs'
import AuthCard from '../../components/AuthCard'
import { authApi } from '../../api/auth'
import { errorMessage } from '../../api/client'
import type { User } from '../../api/types'
import { isStaffRole, useAuth } from '../../auth/store'
import { LangGlyph } from '../../components/brand/Brand'

interface Answers {
  display_name: string
  language: 'en' | 'zh:hans' | 'zh:hant' | 'vi'
  learner_type: 'adult' | 'kid'
  purpose: string
  daily_minutes: number
  birth_date?: Dayjs
  gender?: 'male' | 'female' | 'other'
}

const LANGS = [
  { value: 'en', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="en" size={18} />Tiếng Anh</span> },
  { value: 'zh:hans', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="zh" script="hans" size={18} />Tiếng Trung giản thể</span> },
  { value: 'zh:hant', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="zh" script="hant" size={18} />Tiếng Trung phồn thể</span> },
  { value: 'vi', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="vi" size={18} />Tiếng Việt</span> },
]

/**
 * First visit on the web: the same questions the app's survey asks (language, who is learning,
 * why, how long a day). Saved on the profile with onboarding_completed, so it is asked only once.
 */
export default function WelcomePage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const [saving, setSaving] = useState(false)

  if (!user) return <Navigate to="/login" replace />
  if (user.onboarding_completed || isStaffRole(user)) return <Navigate to="/" replace />

  const onFinish = async (v: Answers) => {
    const [lang, script] = v.language.split(':') as [User['active_language'], User['zh_script'] | undefined]
    setSaving(true)
    try {
      const updated = await authApi.updateMe({
        display_name: v.display_name.trim(),
        active_language: lang,
        learning_languages: [lang],
        ...(script ? { zh_script: script, show_zhuyin: script === 'hant' } : {}),
        learner_type: v.learner_type,
        purpose: v.purpose,
        daily_minutes: v.daily_minutes,
        ...(v.birth_date ? { birth_date: v.birth_date.format('YYYY-MM-DD') } : {}),
        ...(v.gender ? { gender: v.gender } : {}),
        onboarding_completed: true,
      })
      setUser(updated)
      queryClient.invalidateQueries()
      navigate('/', { replace: true })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <AuthCard title="Chào mừng bạn!" subtitle="Trả lời vài câu để LingoPrism chọn bài học hợp với bạn. Bạn đổi lại được trong Hồ sơ.">
      <Form<Answers> layout="vertical" requiredMark={false} onFinish={onFinish}
        initialValues={{ display_name: user.display_name, language: 'en', learner_type: 'adult', purpose: 'communication', daily_minutes: 10 }}>
        <Form.Item name="display_name" label="Bạn muốn được gọi là gì?" rules={[{ required: true, whitespace: true, message: 'Nhập tên gọi' }]}>
          <Input size="large" maxLength={80} />
        </Form.Item>
        <Form.Item name="language" label="Bạn muốn học ngôn ngữ nào?">
          <Radio.Group className="!grid grid-cols-1 sm:grid-cols-2 gap-2" options={LANGS} />
        </Form.Item>
        <Form.Item name="learner_type" label="Ai sẽ học?" extra="Chế độ trẻ em ẩn bảng tin và nhóm học trong Cộng đồng.">
          <Radio.Group optionType="button" buttonStyle="solid" options={[{ value: 'adult', label: 'Người lớn' }, { value: 'kid', label: 'Trẻ em' }]} />
        </Form.Item>
        <Form.Item name="purpose" label="Bạn học để làm gì?">
          <Radio.Group className="!flex flex-wrap gap-2" optionType="button" options={[
            { value: 'communication', label: 'Giao tiếp hằng ngày' }, { value: 'study', label: 'Học tập' },
            { value: 'work', label: 'Công việc' }, { value: 'friends', label: 'Kết bạn' }, { value: 'none', label: 'Chưa có' },
          ]} />
        </Form.Item>
        <Form.Item name="daily_minutes" label="Mỗi ngày bạn dành bao lâu?">
          <Radio.Group optionType="button" options={[5, 10, 15, 20].map((m) => ({ value: m, label: `${m} phút` }))} />
        </Form.Item>
        <div className="grid sm:grid-cols-2 gap-x-4">
          <Form.Item name="birth_date" label="Ngày sinh (không bắt buộc)">
            <DatePicker size="large" className="w-full" format="DD/MM/YYYY" placeholder="Chọn ngày" />
          </Form.Item>
          <Form.Item name="gender" label="Giới tính (không bắt buộc)">
            <Radio.Group optionType="button" options={[{ value: 'male', label: 'Nam' }, { value: 'female', label: 'Nữ' }, { value: 'other', label: 'Khác' }]} />
          </Form.Item>
        </div>
        <Button type="primary" htmlType="submit" size="large" block loading={saving}>Bắt đầu học</Button>
      </Form>
    </AuthCard>
  )
}
