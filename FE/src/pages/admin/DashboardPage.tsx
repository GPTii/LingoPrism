import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Skeleton, Statistic, Table } from 'antd'
import { Column } from '@ant-design/plots'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '../../api/admin'

const LANG: Record<string, string> = { en: 'Tiếng Anh', vi: 'Tiếng Việt', zh: 'Tiếng Trung' }

export default function DashboardPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: adminApi.dashboard, refetchInterval: 60_000 })
  if (isLoading || !data) return <Skeleton active />
  const sessions = data.learning.sessions_per_day.map((d) => ({ date: d.date.slice(5), value: d.count, type: 'Phiên học' }))
  const detections = data.detection.per_day.map((d) => ({ date: d.date.slice(5), value: d.count, type: 'Nhận diện ảnh' }))
  const byLang = data.users.by_language.map((r) => ({
    key: `${r.active_language}-${r.zh_script}`,
    language: r.active_language === 'zh' ? `${LANG.zh} ${r.zh_script === 'hant' ? '(phồn thể)' : '(giản thể)'}` : LANG[r.active_language] ?? r.active_language,
    n: r.n,
  }))
  const todo = [
    { label: 'Bài tự luận chờ chấm', value: data.exams.waiting_for_grading, to: '/admin/exams' },
    { label: 'Báo lỗi từ vựng', value: data.content.open_error_reports, to: '/admin/language-review' },
    { label: 'Bài đăng bị báo cáo', value: data.content.pending_post_reports, to: '/admin/moderation' },
    { label: 'Hội thoại hỗ trợ đang mở', value: data.support.open_conversations, to: '/admin/support' },
  ]
  return (
    <div className="flex flex-col gap-4">
      <Row gutter={[16, 16]}>
        <Col xs={12} lg={4}><Card><Statistic title="Người dùng" value={data.users.total} /></Card></Col>
        <Col xs={12} lg={4}><Card><Statistic title="Học viên" value={data.users.learners} /></Card></Col>
        <Col xs={12} lg={4}><Card><Statistic title="Trẻ em" value={data.users.kids} /></Card></Col>
        <Col xs={12} lg={4}><Card><Statistic title="Mới 7 ngày" value={data.users.new_7d} /></Card></Col>
        <Col xs={12} lg={4}><Card><Statistic title="Học hôm nay" value={data.users.active_today} /></Card></Col>
        <Col xs={12} lg={4}><Card><Statistic title="Câu trả lời hôm nay" value={data.learning.answers_today} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]}>
        {todo.map((t) => (
          <Col xs={12} lg={6} key={t.label}>
            <Card hoverable onClick={() => navigate(t.to)}><Statistic title={t.label} value={t.value} valueStyle={{ color: t.value ? '#d97706' : undefined }} /></Card>
          </Col>
        ))}
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}><Card title="Phiên học 14 ngày qua"><Column data={sessions} xField="date" yField="value" height={260} /></Card></Col>
        <Col xs={24} lg={12}><Card title="Lượt nhận diện ảnh 14 ngày qua"><Column data={detections} xField="date" yField="value" height={260} style={{ fill: '#0d9488' }} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Học viên theo ngôn ngữ đang học">
            <Table size="small" pagination={false} rowKey="key" dataSource={byLang} columns={[{ title: 'Ngôn ngữ', dataIndex: 'language' }, { title: 'Số học viên', dataIndex: 'n' }]} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Đồ vật được nhận diện nhiều nhất">
            <Table size="small" pagination={false} rowKey="label" dataSource={data.detection.top_labels} columns={[{ title: 'Nhãn YOLO', dataIndex: 'label' }, { title: 'Số lần', dataIndex: 'n' }]} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
