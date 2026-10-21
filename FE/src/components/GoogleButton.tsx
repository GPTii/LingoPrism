import { useEffect, useRef, useState } from 'react'
import { App } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useLocation, useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'
import { errorMessage } from '../api/client'
import { isStaffRole, useAuth } from '../auth/store'
import { useIsDark } from '../theme/store'

interface GoogleId {
  initialize: (o: { client_id: string; callback: (r: { credential: string }) => void; ux_mode?: string; context?: string }) => void
  renderButton: (el: HTMLElement, o: Record<string, unknown>) => void
}
declare global {
  interface Window { google?: { accounts: { id: GoogleId } } }
}

let script: Promise<void> | null = null
/** Google Identity Services, loaded once and only on the pages that show the button. */
function loadGis(): Promise<void> {
  script ??= new Promise((resolve, reject) => {
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => { script = null; reject(new Error('gis')) }
    document.head.appendChild(s)
  })
  return script
}

/**
 * Google's own "Sign in with Google" button. Google hands back an ID token, the server checks it
 * (audience = our client IDs, verified e-mail) and answers with our usual session.
 * Renders nothing when the server has no Google client configured.
 */
export default function GoogleButton({ text = 'continue_with' }: { text?: 'signin_with' | 'signup_with' | 'continue_with' }) {
  const ref = useRef<HTMLDivElement>(null)
  const dark = useIsDark()
  const { message } = App.useApp()
  const navigate = useNavigate()
  const location = useLocation()
  const setSession = useAuth((s) => s.setSession)
  const [failed, setFailed] = useState(false)
  const config = useQuery({ queryKey: ['google-config'], queryFn: authApi.googleConfig, staleTime: Infinity, retry: 0 })
  const clientId = config.data?.client_id

  useEffect(() => {
    if (!clientId || !ref.current) return
    let cancelled = false
    loadGis().then(() => {
      if (cancelled || !ref.current || !window.google) return
      window.google.accounts.id.initialize({
        client_id: clientId,
        context: text === 'signup_with' ? 'signup' : 'signin',
        callback: async ({ credential }) => {
          try {
            const { user, tokens } = await authApi.google(credential)
            setSession(user, tokens)
            const from = (location.state as { from?: string } | null)?.from
            navigate(from ?? (isStaffRole(user) ? '/admin' : '/'), { replace: true })
          } catch (e) {
            message.error(errorMessage(e))
          }
        },
      })
      window.google.accounts.id.renderButton(ref.current, {
        type: 'standard', theme: dark ? 'filled_black' : 'outline', size: 'large', shape: 'pill',
        text, logo_alignment: 'center', width: Math.min(ref.current.offsetWidth || 400, 400), locale: 'vi',
      })
    }).catch(() => setFailed(true))
    return () => { cancelled = true }
  }, [clientId, dark, text]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!clientId || failed) return null
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3 text-sm text-slate-500">
        <span className="h-px flex-1 bg-slate-200" />hoặc<span className="h-px flex-1 bg-slate-200" />
      </div>
      <div ref={ref} className="flex justify-center min-h-10" />
    </div>
  )
}
