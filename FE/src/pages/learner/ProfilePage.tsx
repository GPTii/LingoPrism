import { App, Button, Checkbox, Form, Input, Radio, Switch } from 'antd'
import { useState } from 'react'
import { authApi } from '../../api/auth'
import { errorMessage } from '../../api/client'
import type { User } from '../../api/types'
import { useAuth } from '../../auth/store'
import { LangGlyph } from '../../components/brand/Brand'
import { PageHeader, Section, UserAvatar } from '../../components/ui'

const LANGS = [
  { value: 'en', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="en" size={18} />Tiếng Anh</span> },
  { value: 'zh', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="zh" size={18} />Tiếng Trung</span> },
  { value: 'vi', label: <span className="inline-flex items-center gap-2"><LangGlyph lang="vi" size={18} />Tiếng Việt</span> },
]

export default function ProfilePage() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const [saving, setSaving] = useState(false)

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
            <UserAvatar name={user.display_name} src={user.avatar} size={56} />
            <span className="min-w-0">
              {user.display_name}
              <span className="block text-base font-medium text-slate-500 mt-0.5">{user.email}</span>
            </span>
          </span>
        } />
      <Form layout="vertical" initialValues={user} onFinish={onFinish} requiredMark={false} className="flex flex-col gap-6">
        <Section title="Về bạn">
          <Form.Item name="display_name" label="Tên hiển thị" rules={[{ required: true, message: 'Nhập tên hiển thị' }]}>
            <Input size="large" />
          </Form.Item>
          <Form.Item name="learner_type" label="Đối tượng" extra="Chế độ trẻ em ẩn bảng tin và nhóm học trong Cộng đồng." className="!mb-0">
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
    </div>
  )
}
