import { Button, Form, Input, App } from 'antd'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthCard from '../../components/AuthCard'
import { authApi } from '../../api/auth'
import { errorMessage } from '../../api/client'
import { useAuth } from '../../auth/store'

export default function RegisterPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const setSession = useAuth((s) => s.setSession)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { email: string; password: string; display_name: string }) => {
    setLoading(true)
    try {
      const { user, tokens } = await authApi.register(values.email, values.password, values.display_name)
      setSession(user, tokens)
      message.success('Đăng ký thành công!')
      navigate('/', { replace: true })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Tạo tài khoản" subtitle="Bắt đầu học Việt · Anh · Trung qua hình ảnh">
      <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
        <Form.Item name="display_name" label="Tên của bạn" rules={[{ required: true, message: 'Nhập tên' }]}>
          <Input size="large" />
        </Form.Item>
        <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email', message: 'Email không hợp lệ' }]}>
          <Input size="large" autoComplete="email" />
        </Form.Item>
        <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, min: 8, message: 'Tối thiểu 8 ký tự' }]}>
          <Input.Password size="large" autoComplete="new-password" />
        </Form.Item>
        <Form.Item
          name="confirm"
          label="Nhập lại mật khẩu"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Nhập lại mật khẩu' },
            ({ getFieldValue }) => ({
              validator: (_, v) =>
                !v || v === getFieldValue('password') ? Promise.resolve() : Promise.reject(new Error('Mật khẩu không khớp')),
            }),
          ]}
        >
          <Input.Password size="large" autoComplete="new-password" />
        </Form.Item>
        <Button type="primary" htmlType="submit" size="large" block loading={loading}>Tạo tài khoản</Button>
      </Form>
      <p className="text-center text-slate-500 mt-6">
        Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
      </p>
    </AuthCard>
  )
}
