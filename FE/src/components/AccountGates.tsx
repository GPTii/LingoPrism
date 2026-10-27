import { useQuery } from '@tanstack/react-query'
import { App, Button, Checkbox, Input, Modal, Tag } from 'antd'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../api/auth'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/store'
import { useLogout } from '../auth/useLogout'
import { ReleaseLists } from '../pages/legal/LegalPages'
import { Logo, Prismo } from './brand/Brand'

/** Above every learner page until the e-mail is verified: type the mailed code, or get a new one. */
export function VerifyEmailBanner() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState<'verify' | 'resend' | null>(null)
  if (!user || user.email_verified !== false) return null
  const verify = async () => {
    setBusy('verify')
    try {
      useAuth.getState().setUser(await authApi.verifyEmail(code.trim()))
      message.success('Đã xác minh email. Giờ bạn dùng được đầy đủ Cộng đồng.')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }
  const resend = async () => {
    setBusy('resend')
    try {
      message.success((await authApi.resendEmailCode()).detail)
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(null)
    }
  }
  return (
    <div role="status" className="lp-card mb-4 p-4 flex flex-col md:flex-row md:items-center gap-3 border-amber-300 bg-amber-50/60">
      <div className="flex-1 min-w-0">
        <div className="font-bold text-slate-800">Xác minh email của bạn</div>
        <div className="text-sm text-slate-600">Nhập mã 6 số đã gửi tới <b>{user.email}</b>. Đăng bài, kết bạn và nhắn tin cần bước này.</div>
      </div>
      <div className="flex gap-2">
        <Input value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} onPressEnter={verify}
          inputMode="numeric" placeholder="Mã 6 số" aria-label="Mã xác minh email" style={{ width: 130 }} />
        <Button type="primary" disabled={code.length !== 6} loading={busy === 'verify'} onClick={verify}>Xác minh</Button>
        <Button type="text" loading={busy === 'resend'} onClick={resend}>Gửi lại mã</Button>
      </div>
    </div>
  )
}

/** In place of the app for a child's account (kid mode or under 16) until a parent or guardian agreed: their
 * e-mail gets a code with the Privacy policy; typing the code is the consent (Decree 13/2023). */
export function ParentConsentGate() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const logout = useLogout()
  const [parentEmail, setParentEmail] = useState('')
  const [agree, setAgree] = useState(false)
  const [sentTo, setSentTo] = useState<string | null>(user?.parent_consent === 'pending' ? '' : null)
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const ask = async () => {
    setBusy(true)
    try {
      const r = await authApi.askParent(parentEmail.trim())
      setSentTo(r.parent_email ?? parentEmail)
      message.success('Đã gửi email cho phụ huynh')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  const confirm = async () => {
    setBusy(true)
    try {
      useAuth.getState().setUser(await authApi.confirmParent(code.trim()))
      message.success('Cảm ơn phụ huynh! Chúc bé học vui.')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="learner min-h-screen grid place-items-center p-4">
      <div className="lp-card w-full max-w-lg p-6 sm:p-8 flex flex-col gap-4">
        <div className="flex items-center justify-between"><Logo /><Prismo mood="happy" size={64} /></div>
        <h1 className="text-2xl font-extrabold text-slate-800 m-0">Xin phép bố mẹ một chút nhé</h1>
        <p className="m-0 text-slate-600">
          Tài khoản của trẻ em cần <b>bố, mẹ hoặc người giám hộ</b> đồng ý trước khi dùng. Hãy nhờ phụ huynh nhập email của họ:
          LingoPrism sẽ gửi một mã cùng <Link to="/privacy" target="_blank">Chính sách quyền riêng tư</Link> để phụ huynh đọc.
        </p>
        {sentTo === null ? (
          <>
            <Input size="large" type="email" value={parentEmail} onChange={(e) => setParentEmail(e.target.value)}
              placeholder="Email của phụ huynh" aria-label="Email của phụ huynh" />
            <Checkbox checked={agree} onChange={(e) => setAgree(e.target.checked)}>
              Tôi là phụ huynh / người giám hộ và đã đọc Chính sách quyền riêng tư
            </Checkbox>
            <Button type="primary" size="large" disabled={!agree || !/\S+@\S+\.\S+/.test(parentEmail)} loading={busy} onClick={ask}>
              Gửi mã cho phụ huynh
            </Button>
          </>
        ) : (
          <>
            <p className="m-0">{sentTo ? <>Đã gửi mã tới <b>{sentTo}</b>.</> : 'Đã gửi mã cho phụ huynh.'} Nhập mã 6 số trong email (hiệu lực 24 giờ):</p>
            <Input size="large" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} onPressEnter={confirm}
              inputMode="numeric" placeholder="Mã 6 số" aria-label="Mã của phụ huynh" />
            <Button type="primary" size="large" disabled={code.length !== 6} loading={busy} onClick={confirm}>Xác nhận</Button>
            <Button type="text" onClick={() => { setSentTo(null); setCode('') }}>Gửi lại hoặc dùng email khác</Button>
          </>
        )}
        <div className="flex justify-between text-sm pt-2 border-t border-slate-100">
          <button type="button" className="cursor-pointer text-slate-500" onClick={() => logout()}>Đăng xuất</button>
          <Link to="/delete-account" className="text-slate-500">Không đồng ý? Xoá tài khoản</Link>
        </div>
      </div>
    </div>
  )
}

const SEEN_KEY = 'lingoprism-seen-release'

/** "Có gì mới": once after each update. Someone opening LingoPrism for the first time is not shown the history. */
export function WhatsNew() {
  const signedIn = useAuth((s) => !!s.user)
  const q = useQuery({ queryKey: ['releases'], queryFn: authApi.releases, enabled: signedIn, staleTime: 60 * 60_000 })
  const [open, setOpen] = useState(false)
  const latest = q.data?.results[0]
  useEffect(() => {
    if (!latest) return
    let seen: string | null = null
    try {
      seen = localStorage.getItem(SEEN_KEY)
      if (!seen) localStorage.setItem(SEEN_KEY, latest.version)
    } catch { /* private mode: never shown */ }
    if (seen && seen !== latest.version) setOpen(true)
  }, [latest])
  const close = () => {
    setOpen(false)
    try { localStorage.setItem(SEEN_KEY, latest!.version) } catch { /* ignore */ }
  }
  if (!latest) return null
  return (
    <Modal open={open} onCancel={close} onOk={close} okText="Tuyệt!" cancelButtonProps={{ style: { display: 'none' } }}
      title={<span className="flex items-center gap-2">Có gì mới <Tag color="blue">{latest.version}</Tag></span>}>
      <p className="font-bold text-slate-800 mt-0">{latest.title}</p>
      <ReleaseLists r={latest} />
      <Link to="/releases" onClick={close}>Xem mọi phiên bản</Link>
    </Modal>
  )
}

/** Profile, at the bottom: delete the account for good (password, or the word XOA for a Google-only account). */
export function DeleteAccountSection() {
  const { message } = App.useApp()
  const user = useAuth((s) => s.user)
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState('')
  const [busy, setBusy] = useState(false)
  const hasPassword = user?.has_password !== false
  const remove = async () => {
    setBusy(true)
    try {
      await authApi.deleteAccount(hasPassword ? { password: value } : { confirm: value })
      message.success('Đã xoá tài khoản. Tạm biệt và cảm ơn bạn đã học cùng LingoPrism!')
      useAuth.getState().logout()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="lp-card p-5 sm:p-6 border-rose-200">
      <h2 className="m-0 text-lg font-bold text-rose-700">Xoá tài khoản</h2>
      <p className="text-slate-600 mt-2">
        Xoá vĩnh viễn tài khoản cùng tiến độ học, từ đã lưu, ảnh, bài đăng, tin nhắn và bạn bè. Không thể khôi phục.
      </p>
      <Button danger onClick={() => { setValue(''); setOpen(true) }}>Xoá tài khoản của tôi</Button>
      <Modal open={open} title="Xoá vĩnh viễn tài khoản?" okText="Xoá vĩnh viễn" okButtonProps={{ danger: true, disabled: !value, loading: busy }}
        cancelText="Huỷ" onOk={remove} onCancel={() => setOpen(false)} destroyOnHidden>
        <p>Mọi dữ liệu của <b>{user?.email}</b> sẽ bị xoá ngay và mọi thiết bị bị đăng xuất.</p>
        {hasPassword
          ? <Input.Password autoFocus value={value} onChange={(e) => setValue(e.target.value)} placeholder="Nhập mật khẩu để xác nhận" autoComplete="current-password" />
          : <Input autoFocus value={value} onChange={(e) => setValue(e.target.value)} placeholder="Gõ XOA để xác nhận" />}
      </Modal>
    </section>
  )
}
