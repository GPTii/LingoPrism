import { Button, Form, Input, App } from 'antd'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthCard from '../../components/AuthCard'
import GoogleButton from '../../components/GoogleButton'
import { authApi } from '../../api/auth'
import { errorMessage } from '../../api/client'
import { isStaffRole, useAuth } from '../../auth/store'

export default function LoginPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const location = useLocation()
  const setSession = useAuth((s) => s.setSession)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const { user, tokens } = await authApi.login(values.email, values.password)
      setSession(user, tokens)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from ?? (isStaffRole(user) ? '/admin' : '/'), { replace: true })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Đăng nhập" subtitle="Chào mừng bạn quay lại!">
      <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
        <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email', message: 'Email không hợp lệ' }]}>
          <Input size="large" autoComplete="email" />
        </Form.Item>
        <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, message: 'Nhập mật khẩu' }]}>
          <Input.Password size="large" autoComplete="current-password" />
        </Form.Item>
        <div className="flex justify-end -mt-2 mb-4">
          <Link to="/forgot-password" className="text-sm">Quên mật khẩu?</Link>
        </div>
        <Button type="primary" htmlType="submit" size="large" block loading={loading}>Đăng nhập</Button>
      </Form>
      <div className="mt-5"><GoogleButton text="signin_with" /></div>
      <p className="text-center text-slate-500 mt-6">
        Chưa có tài khoản? <Link to="/register">Đăng ký</Link>
      </p>
    </AuthCard>
  )
}
