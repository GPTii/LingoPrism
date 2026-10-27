import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { LangGlyph, Logo, Prismo } from './brand/Brand'

const LANGS = [
  { glyph: <LangGlyph lang="en" size={28} />, word: 'apple', name: 'Tiếng Anh' },
  { glyph: <LangGlyph lang="zh" size={28} />, word: <span lang="zh-Hans">苹果</span>, name: 'Tiếng Trung' },
  { glyph: <LangGlyph lang="vi" size={28} />, word: 'quả táo', name: 'Tiếng Việt' },
]

/** Login / register / password pages: the brand and Prismo on one side, the form on the other. */
export default function AuthCard({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="learner min-h-screen grid lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="hidden lg:flex ink-bg text-white flex-col justify-between p-12 xl:p-16">
        <Logo inverse />
        <div className="flex flex-col gap-8 max-w-md">
          <Prismo mood="happy" size={150} />
          <div>
            <h2 className="text-[2.75rem] font-extrabold leading-[1.08] m-0 text-white">Một lần chụp.<br />Ba thứ tiếng.</h2>
            <p className="text-lg text-white/75 mt-4 mb-0">
              Chụp đồ vật quanh bạn và học ngay tên của nó bằng ba thứ tiếng. Mỗi ngày vài phút, lịch ôn tự nhắc đúng lúc sắp quên.
            </p>
          </div>
          {/* one snap of an apple, as the three beams see it */}
          <ul className="m-0 p-0 list-none flex flex-col gap-3">
            {LANGS.map((l) => (
              <li key={l.name} className="flex items-center gap-3">
                {l.glyph}
                <span className="text-xl font-semibold">{l.word}</span>
                <span className="text-sm text-white/55">{l.name}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-white/50 m-0">Việt · Anh · Trung giản thể · Trung phồn thể</p>
      </aside>
      <main className="flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-[420px] animate-rise">
          <div className="lg:hidden mb-8"><Logo /></div>
          <h1 className="text-3xl font-extrabold text-slate-800 m-0">{title}</h1>
          {subtitle ? <p className="text-slate-500 mt-2 mb-7">{subtitle}</p> : <div className="mb-6" />}
          {children}
          <nav className="mt-8 flex justify-center gap-4 text-sm text-slate-500" aria-label="Chính sách">
            <Link to="/privacy" className="text-slate-500">Quyền riêng tư</Link>
            <Link to="/terms" className="text-slate-500">Điều khoản</Link>
            <Link to="/releases" className="text-slate-500">Có gì mới</Link>
          </nav>
        </div>
      </main>
    </div>
  )
}

/** Under the Google button: signing up with Google also accepts the Terms (recorded by the server). */
export function GoogleTermsNote() {
  return (
    <p className="text-xs text-slate-500 text-center mt-2 mb-0">
      Tiếp tục với Google nghĩa là bạn đồng ý <Link to="/terms" target="_blank">Điều khoản</Link> và{' '}
      <Link to="/privacy" target="_blank">Chính sách quyền riêng tư</Link>.
    </p>
  )
}
