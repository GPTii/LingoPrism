import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Progress, Skeleton, Tooltip } from 'antd'
import { CheckOutlined, LockFilled, RocketOutlined, StarFilled, ThunderboltOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { LEVEL_COLORS, levelsApi } from '../api/levels'
import { errorMessage } from '../api/client'
import { useAuth } from '../auth/store'

const ZH_HINT = ['≈ HSK 1', '≈ HSK 2', '≈ HSK 3', 'HSK 4 trở lên']

/** The 4-level path of the language being learned: a road of stops – progress, locks, choosing the level, skip test. */
export default function LevelPath() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuth((s) => s.user)
  const lang = user?.active_language ?? 'en'
  const q = useQuery({ queryKey: ['levels', lang, user?.zh_script], queryFn: levelsApi.progress })

  if (q.isLoading || !q.data) return <div className="lp-card p-6"><Skeleton active /></div>
  const p = q.data

  const choose = async (level: number) => {
    try {
      queryClient.setQueryData(['levels', lang, user?.zh_script], await levelsApi.choose(level))
      message.success(`Đã chuyển sang cấp ${level}`)
    } catch (e) {
      message.error(errorMessage(e))
    }
  }

  return (
    <section className="lp-card p-5 sm:p-6 flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-bold text-slate-800 text-xl m-0">Con đường 4 cấp độ</h2>
          <div className="text-slate-500 text-sm mt-0.5">
            Học {p.unlock_percent}% số từ của một cấp để mở cấp tiếp theo – hoặc kiểm tra vượt cấp nếu bạn đã biết.
          </div>
        </div>
        <Button size="large" icon={<RocketOutlined />} onClick={() => navigate('/learn?kind=learn')}>
          Học tiếp cấp {p.current}
        </Button>
      </div>

      <div className="relative grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* the road joining the stops (laptop and larger) */}
        <div className="hidden lg:block absolute left-[12%] right-[12%] top-8 h-2 rounded-full bg-slate-100" />
        {p.levels.map((r) => {
          const color = LEVEL_COLORS[r.level - 1]
          const next = p.levels[r.level]
          const done = r.percent >= 100
          return (
            <div key={r.level} className="relative flex flex-col items-center text-center gap-2">
              <div className="relative h-16 w-16 rounded-full grid place-items-center text-2xl font-bold text-white"
                style={{
                  background: r.unlocked ? color : 'var(--color-slate-200)',
                  boxShadow: r.current ? `0 0 0 6px ${color}33` : undefined,
                  color: r.unlocked ? '#fff' : 'var(--color-slate-400)',
                }}>
                {!r.unlocked ? <LockFilled /> : done ? <CheckOutlined /> : r.current ? <StarFilled /> : r.level}
              </div>
              <div className="w-full rounded-xl bg-slate-50 p-3 flex flex-col gap-1.5 flex-1"
                style={r.current ? { boxShadow: `inset 0 0 0 1.5px ${color}` } : undefined}>
                <div className="font-bold" style={{ color: r.unlocked ? color : 'var(--color-slate-400)' }}>
                  Cấp {r.level} · {r.name}
                </div>
                {lang === 'zh' && <div className="text-xs font-bold text-slate-400">{ZH_HINT[r.level - 1]}</div>}
                <div className="text-xs text-slate-500 font-semibold min-h-8">{r.description}</div>
                <Progress percent={r.percent} size="small" strokeColor={color} showInfo={false} />
                <div className="num text-xs font-semibold text-slate-500">{r.started}/{r.total} từ · {r.mastered} đã thuộc</div>
                {r.unlocked && !r.current && <Button size="small" onClick={() => choose(r.level)}>Học cấp này</Button>}
                {r.unlocked && next && !next.unlocked && (
                  <Tooltip title={`Còn ${r.needed} từ nữa là mở cấp ${r.level + 1}. Đã biết rồi? Làm bài ${p.test.size} câu, đúng từ ${p.test.pass} câu là qua.`}>
                    <Button size="small" type="dashed" icon={<ThunderboltOutlined />} onClick={() => navigate(`/levels/${r.level}/test`)}>
                      Kiểm tra vượt cấp
                    </Button>
                  </Tooltip>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
