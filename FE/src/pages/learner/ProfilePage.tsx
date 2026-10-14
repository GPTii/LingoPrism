import { App, Button, Card, Checkbox, Form, Input, Radio, Switch } from 'antd'
import { useState } from 'react'
import { authApi } from '../../api/auth'
import { errorMessage } from '../../api/client'
import type { User } from '../../api/types'
import { useAuth } from '../../auth/store'

export default function ProfilePage() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const [saving, setSaving] = useState(false)

  const onFinish = async (values: Partial<User>) => {
    setSaving(true)
    try {
      setUser(await authApi.updateMe(values))
      message.success('Đã cập nhật hồ sơ')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  if (!user) return null
  return (
    <div className="max-w-2xl mx-auto">
      <Card title="Hồ sơ & cài đặt học tập">
        <Form layout="vertical" initialValues={user} onFinish={onFinish}>
          <Form.Item name="display_name" label="Tên hiển thị" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="learner_type" label="Đối tượng">
            <Radio.Group options={[{ value: 'adult', label: 'Người lớn' }, { value: 'kid', label: 'Trẻ em' }]} />
          </Form.Item>
          <Form.Item name="learning_languages" label="Ngôn ngữ muốn học">
            <Checkbox.Group options={[{ value: 'en', label: 'Tiếng Anh' }, { value: 'zh', label: 'Tiếng Trung' }, { value: 'vi', label: 'Tiếng Việt' }]} />
          </Form.Item>
          <Form.Item name="active_language" label="Đang học">
            <Radio.Group optionType="button" options={[{ value: 'en', label: 'Tiếng Anh' }, { value: 'zh', label: 'Tiếng Trung' }, { value: 'vi', label: 'Tiếng Việt' }]} />
          </Form.Item>
          <Form.Item name="zh_script" label="Dạng chữ Hán">
            <Radio.Group
              options={[
                { value: 'hans', label: <span>Giản thể – chuẩn Trung Quốc đại lục (<span lang="zh-Hans">汉字</span>)</span> },
                { value: 'hant', label: <span>Phồn thể – chuẩn Đài Loan (<span lang="zh-Hant">漢字</span>)</span> },
              ]}
            />
          </Form.Item>
          <Form.Item name="show_zhuyin" label="Hiện Zhuyin (注音) cho phồn thể" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>Lưu</Button>
        </Form>
      </Card>
    </div>
  )
}
