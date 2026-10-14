import { Button, Form, Input, App, Steps } from 'antd'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import AuthCard from '../../components/AuthCard'
import { authApi } from '../../api/auth'
import { errorMessage } from '../../api/client'

export default function ForgotPasswordPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [email, setEmail] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [loading, setLoading] = useState(false)

  const run = async (fn: () => Promise<void>) => {
    setLoading(true)
    try {
      await fn()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Quên mật khẩu">
      <Steps
        size="small"
        current={step}
        className="mb-6"
        items={[{ title: 'Email' }, { title: 'Mã xác minh' }, { title: 'Mật khẩu mới' }]}
      />
      {step === 0 && (
        <Form
          layout="vertical"
          onFinish={(v: { email: string }) =>
            run(async () => {
              await authApi.forgot(v.email)
              setEmail(v.email)
              setStep(1)
              message.success('Đã gửi mã xác minh tới email')
            })
          }
        >
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email', message: 'Email không hợp lệ' }]}>
            <Input size="large" />
          </Form.Item>
          <Button type="primary" htmlType="submit" size="large" block loading={loading}>Gửi mã</Button>
        </Form>
      )}
      {step === 1 && (
        <Form
          layout="vertical"
          onFinish={(v: { code: string }) =>
            run(async () => {
              const r = await authApi.verify(email, v.code)
              setResetToken(r.reset_token)
              setStep(2)
            })
          }
        >
          <Form.Item name="code" label={`Mã 6 số đã gửi tới ${email}`} rules={[{ required: true, len: 6, message: 'Nhập đủ 6 số' }]}>
            <Input.OTP length={6} size="large" />
          </Form.Item>
          <Button type="primary" htmlType="submit" size="large" block loading={loading}>Xác minh</Button>
        </Form>
      )}
      {step === 2 && (
        <Form
          layout="vertical"
          onFinish={(v: { password: string }) =>
            run(async () => {
              await authApi.reset(resetToken, v.password)
              message.success('Đặt lại mật khẩu thành công')
              navigate('/login')
            })
          }
        >
          <Form.Item name="password" label="Mật khẩu mới" rules={[{ required: true, min: 8, message: 'Tối thiểu 8 ký tự' }]}>
            <Input.Password size="large" />
          </Form.Item>
          <Button type="primary" htmlType="submit" size="large" block loading={loading}>Đặt lại mật khẩu</Button>
        </Form>
      )}
      <p className="text-center mt-6"><Link to="/login">Quay lại đăng nhập</Link></p>
    </AuthCard>
  )
}
