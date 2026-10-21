import { useQuery } from '@tanstack/react-query'
import { Button, Segmented, Skeleton } from 'antd'
import { Column } from '@ant-design/plots'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import dayjs from 'dayjs'
import { vocabApi } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import { useIsDark } from '../../theme/store'
import TargetWord from '../../components/TargetWord'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, Facts, PageHeader, Section } from '../../components/ui'

const pct = (v: number | null) => (v == null ? '–' : `${Math.round(v * 100)}%`)

/** A thin horizontal meter with its value at the end (accuracy, mastered share). */
function Meter({ value, color = '#6d4aff' }: { value: number | null; color?: string }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_3rem] items-center gap-3">
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${Math.round((value ?? 0) * 100)}%`, background: color }} />
      </div>
      <span className="num text-right text-sm font-semibold text-slate-700">{pct(value)}</span>
    </div>
  )
}

/** Thống kê học tập (FEATURES 12.1–12.3): my answers by day, by question type, by topic, and my hardest words. */
export default function StatsPage() {
  const [days, setDays] = useState(30)
  const user = useAuth((s) => s.user)
  const dark = useIsDark()
  const q = useQuery({ queryKey: ['learning-stats', days, user?.active_language, user?.zh_script], queryFn: () => vocabApi.stats(days) })
  const s = q.data
  const ink = dark ? '#a8a3c4' : '#5d5878'
  // two series → two named colours and a legend; wrong answers in the coral beam, right ones in mint
  const chart = s?.daily.flatMap((d) => [
    { date: dayjs(d.date).format('DD/MM'), kind: 'Đúng', value: d.correct },
    { date: dayjs(d.date).format('DD/MM'), kind: 'Sai', value: d.answers - d.correct },
  ]) ?? []

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <PageHeader title="Thống kê học tập" description="Bạn đã trả lời bao nhiêu, đúng bao nhiêu, mạnh ở chủ đề nào và từ nào còn hay sai."
        actions={<Segmented size="large" value={days} onChange={(v) => setDays(v as number)}
          options={[{ value: 7, label: '7 ngày' }, { value: 30, label: '30 ngày' }, { value: 90, label: '90 ngày' }]} />} />

      {q.isLoading || !s ? <Skeleton active /> : s.answers === 0 && s.words.total === 0 ? (
        <div className="lp-card">
          <EmptyState art={<Prismo mood="wow" size={90} />} title="Chưa có số liệu"
            description="Học vài từ mới, số liệu của bạn sẽ hiện ở đây."
            action={<Link to="/learn?kind=learn"><Button type="primary">Học từ mới</Button></Link>} />
        </div>
      ) : (
        <>
          <Section>
            <Facts items={[
              { label: 'từ trong thư viện', value: s.words.total },
              { label: 'từ đã thuộc', value: s.words.mastered },
              { label: `câu trả lời · ${days} ngày`, value: s.answers.toLocaleString('vi-VN') },
              { label: 'trả lời đúng', value: pct(s.accuracy) },
              { label: 'đúng ngay lần đầu', value: pct(s.first_try_accuracy) },
              { label: 'ngày có học', value: s.active_days, hint: `/ ${days}` },
            ]} />
          </Section>

          <Section title="Câu trả lời mỗi ngày">
            <Column data={chart} xField="date" yField="value" colorField="kind" stack height={260}
              theme={dark ? 'classicDark' : 'classic'}
              scale={{ color: { domain: ['Đúng', 'Sai'], range: ['#10c79a', '#ff6b81'] } }}
              style={{ radiusTopLeft: 3, radiusTopRight: 3, maxWidth: 18 }}
              axis={{
                x: { labelFill: ink, line: false, tick: false, labelAutoHide: true },
                y: { labelFill: ink, grid: true, gridStroke: dark ? '#29243f' : '#e7e4f0', gridLineDash: [0, 0], gridStrokeOpacity: 1 },
              }}
              legend={{ color: { position: 'top', itemLabelFill: ink } }} />
          </Section>

          <div className="grid lg:grid-cols-2 gap-6">
            <Section title="Độ chính xác theo dạng câu hỏi">
              {s.by_question_type.length ? (
                <ul className="m-0 p-0 list-none flex flex-col gap-3">
                  {s.by_question_type.map((r) => (
                    <li key={r.type}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-slate-700">{r.label}</span>
                        <span className="num text-slate-500">{r.answers} câu</span>
                      </div>
                      <Meter value={r.accuracy} />
                    </li>
                  ))}
                </ul>
              ) : <p className="m-0 text-slate-500">Chưa có câu trả lời trong {days} ngày qua.</p>}
            </Section>

            <Section title="Theo chủ đề">
              {s.by_topic.length ? (
                <ul className="m-0 p-0 list-none flex flex-col gap-3">
                  {s.by_topic.map((t) => (
                    <li key={t.id}>
                      <Link to={`/vocab/topics/${t.id}`} className="flex justify-between text-sm mb-1 !text-slate-700">
                        <span className="font-medium">{t.icon} {t.name}</span>
                        <span className="num text-slate-500">thuộc {t.mastered}/{t.words} · đúng {pct(t.accuracy)}</span>
                      </Link>
                      <Meter value={t.words ? t.mastered / t.words : 0} color="#10c79a" />
                    </li>
                  ))}
                </ul>
              ) : <p className="m-0 text-slate-500">Lưu từ theo chủ đề để xem tiến độ từng chủ đề.</p>}
            </Section>
          </div>

          <Section title="Từ hay sai" extra={s.hardest.length > 0 && <Link to="/learn?kind=review"><Button type="primary">Ôn các từ này</Button></Link>}>
            {s.hardest.length ? (
              <ul className="m-0 p-0 list-none grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {s.hardest.map((h) => h.card.target && (
                  <li key={h.card.id} className="rounded-xl bg-slate-50 p-4 flex flex-col items-center text-center gap-1">
                    <TargetWord target={h.card.target} size="md" showReading={false} />
                    <div className="text-slate-600">{h.card.meaning_vi}</div>
                    <div className="num text-sm font-semibold text-[#e0445e]">sai {h.wrong}/{h.answers} lần</div>
                  </li>
                ))}
              </ul>
            ) : <p className="m-0 text-slate-500">Chưa có từ nào bạn hay sai. Giỏi lắm!</p>}
          </Section>
        </>
      )}
    </div>
  )
}
