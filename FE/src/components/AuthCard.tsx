import type { ReactNode } from 'react'

export default function AuthCard({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 via-white to-sky-50 p-4">
      <div className="w-full max-w-md rounded-3xl bg-white shadow-xl shadow-brand-100/60 p-8">
        <div className="flex items-center gap-3 mb-6">
          <img src="/logo.png" alt="LingoPrism" className="h-12 w-12 rounded-2xl" />
          <div>
            <div className="text-xl font-bold text-slate-800">LingoPrism</div>
            <div className="text-xs text-slate-500">One snap. Three languages.</div>
          </div>
        </div>
        <h1 className="text-2xl font-semibold text-slate-800">{title}</h1>
        {subtitle ? <p className="text-slate-500 mt-1 mb-6">{subtitle}</p> : <div className="mb-4" />}
        {children}
      </div>
    </div>
  )
}
