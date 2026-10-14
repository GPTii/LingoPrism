import { useAuth } from '../../auth/store'

export default function HomePage() {
  const user = useAuth((s) => s.user)
  return (
    <div className="max-w-5xl mx-auto">
      <div className="rounded-3xl bg-gradient-to-r from-brand-500 to-sky-500 p-8 text-white">
        <h1 className="text-3xl font-bold">Xin chào, {user?.display_name}! 👋</h1>
        <p className="mt-2 opacity-90">Hôm nay mình học gì nào? Chụp một bức ảnh – học ngay ba thứ tiếng.</p>
      </div>
    </div>
  )
}
