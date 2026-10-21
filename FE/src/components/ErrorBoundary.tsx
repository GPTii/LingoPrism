import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from 'antd'
import { Prismo } from './brand/Brand'

/** One broken page shows a message with a way out instead of blanking the whole app. Reset by changing `key`. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="max-w-md mx-auto flex flex-col items-center text-center gap-3 py-16">
        <Prismo mood="sad" size={110} />
        <h1 className="text-2xl font-extrabold text-slate-900 m-0">Trang này gặp lỗi</h1>
        <p className="text-slate-500 m-0">Phần còn lại của ứng dụng vẫn dùng được. Thử tải lại trang, nếu vẫn lỗi hãy báo cho giáo viên.</p>
        <div className="flex gap-3 mt-2">
          <Button onClick={() => window.location.reload()}>Tải lại trang</Button>
          <Button type="primary" href="/">Về trang chủ</Button>
        </div>
      </div>
    )
  }
}
