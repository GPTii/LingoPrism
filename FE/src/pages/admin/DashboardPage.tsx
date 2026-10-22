import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Skeleton, Table } from 'antd'
import { ArrowRightOutlined, CheckCircleFilled } from '@ant-design/icons'
import { Column } from '@ant-design/plots'
import { Link } from 'react-router-dom'
import { adminApi } from '../../api/admin'
import { useIsDark } from '../../theme/store'
import { Facts } from '../../components/ui'

const LANG: Record<string, string> = { en: 'Tiếng Anh', vi: 'Tiếng Việt', zh: 'Tiếng Trung' }

/** One series per chart, so one colour: the brand violet (lighter step in dark mode). */
function DailyColumns({ data, label, dark }: { data: { date: string; value: number }[]; label: string; dark: boolean }) {
  const ink = dark ? '#a8a3c4' : '#5d5878'
  return (
    <Column data={data} xField="date" yField="value" height={240} theme={dark ? 'classicDark' : 'classic'}
      style={{ fill: dark ? '#a995ff' : '#6d4aff', radiusTopLeft: 4, radiusTopRight: 4, maxWidth: 22 }}
      axis={{
        x: { labelFill: ink, line: false, tick: false },
        y: { labelFill: ink, grid: true, gridStroke: dark ? '#2a2640' : '#e7e4f0', gridLineDash: [0, 0], gridStrokeOpacity: 1 },
      }}
      tooltip={{ title: (d: { date: string }) => d.date, items: [{ channel: 'y', name: label }] }} />
  )
}

export default function DashboardPage() {
  const dark = useIsDark()
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: adminApi.dashboard, refetchInterval: 60_000 })
  if (isLoading || !data) return <Skeleton active />
  const sessions = data.learning.sessions_per_day.map((d) => ({ date: d.date.slice(5), value: d.count }))
  const detections = data.detection.per_day.map((d) => ({ date: d.date.slice(5), value: d.count }))
  const byLang = data.users.by_language.map((r) => ({
    key: `${r.active_language}-${r.zh_script}`,
    language: r.active_language === 'zh' ? `${LANG.zh} ${r.zh_script === 'hant' ? '(phồn thể)' : '(giản thể)'}` : LANG[r.active_language] ?? r.active_language,
    n: r.n,
  }))
  const todo = [
    { label: 'bài tự luận chờ chấm', value: data.exams.waiting_for_grading, to: '/admin/exams' },
    { label: 'báo lỗi từ vựng', value: data.content.open_error_reports, to: '/admin/language-review' },
    { label: 'bài đăng bị báo cáo', value: data.content.pending_post_reports, to: '/admin/moderation' },
    { label: 'người dùng bị báo cáo', value: data.content.pending_user_reports, to: '/admin/moderation?tab=users' },
    { label: 'hội thoại hỗ trợ đang mở', value: data.support.open_conversations, to: '/admin/support' },
  ]
  const open = todo.filter((t) => t.value > 0)

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-extrabold text-slate-800 m-0">Tổng quan</h1>

      {/* what needs a person now comes first */}
      <Card title="Việc cần xử lý" extra={!open.length && <span className="text-emerald-600 font-semibold"><CheckCircleFilled /> Không còn việc tồn</span>}>
        <ul className="m-0 p-0 list-none grid sm:grid-cols-2 xl:grid-cols-4 gap-2">
          {todo.map((t) => (
            <li key={t.label}>
              <Link to={t.to} className={`group flex items-center gap-3 rounded-xl px-4 py-3 transition-colors ${t.value ? 'bg-amber-50 hover:bg-amber-100' : 'bg-slate-50 hover:bg-slate-100'}`}>
                <span className={`num text-2xl font-bold ${t.value ? 'text-amber-700' : 'text-slate-400'}`}>{t.value}</span>
                <span className="flex-1 text-sm font-medium text-slate-700">{t.label}</span>
                <ArrowRightOutlined className="text-slate-400 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <Facts items={[
          { label: 'người dùng', value: data.users.total.toLocaleString('vi-VN') },
          { label: 'học viên', value: data.users.learners.toLocaleString('vi-VN') },
          { label: 'trẻ em', value: data.users.kids.toLocaleString('vi-VN') },
          { label: 'mới trong 7 ngày', value: data.users.new_7d.toLocaleString('vi-VN') },
          { label: 'học hôm nay', value: data.users.active_today.toLocaleString('vi-VN') },
          { label: 'câu trả lời hôm nay', value: data.learning.answers_today.toLocaleString('vi-VN') },
        ]} />
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}><Card title="Phiên học mỗi ngày · 14 ngày qua"><DailyColumns data={sessions} label="Phiên học" dark={dark} /></Card></Col>
        <Col xs={24} lg={12}><Card title="Lượt nhận diện ảnh mỗi ngày · 14 ngày qua"><DailyColumns data={detections} label="Lượt nhận diện" dark={dark} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Học viên theo ngôn ngữ đang học">
            <Table size="small" pagination={false} rowKey="key" dataSource={byLang}
              columns={[{ title: 'Ngôn ngữ', dataIndex: 'language' }, { title: 'Số học viên', dataIndex: 'n', align: 'right' }]} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Đồ vật được nhận diện nhiều nhất">
            <Table size="small" pagination={false} rowKey="label" dataSource={data.detection.top_labels}
              columns={[{ title: 'Nhãn', dataIndex: 'label' }, { title: 'Số lần', dataIndex: 'n', align: 'right' }]} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
