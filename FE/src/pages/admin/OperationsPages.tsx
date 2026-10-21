import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Badge, Button, Card, Form, Image, Input, List, Select, Space, Table, Tag } from 'antd'
import { useState } from 'react'
import dayjs from 'dayjs'
import { adminApi, type DetectionLog, type DetectionReport, type PostReport } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { SupportChatBox } from '../learner/SupportPage'

const REASONS: Record<string, string> = { spam: 'Spam', inappropriate: 'Không phù hợp', wrong_vocab: 'Từ vựng sai', harassment: 'Quấy rối', other: 'Khác' }

export function ModerationPage() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState('pending')
  const list = useQuery({ queryKey: ['post-reports', status], queryFn: () => adminApi.postReports(status) })
  const resolve = async (id: number, hide: boolean) => {
    await adminApi.resolveReport(id, hide)
    queryClient.invalidateQueries({ queryKey: ['post-reports'] })
  }
  return (
    <Card title="Kiểm duyệt cộng đồng" extra={<Select value={status} onChange={setStatus} style={{ width: 160 }}
      options={[{ value: 'pending', label: 'Chờ xử lý' }, { value: 'resolved', label: 'Đã ẩn bài' }, { value: 'dismissed', label: 'Bỏ qua' }]} />}>
      <Table<PostReport> rowKey="id" loading={list.isLoading} dataSource={list.data?.results} columns={[
        { title: 'Ảnh', dataIndex: 'post_image', render: (v) => <Image src={v} width={80} /> },
        { title: 'Bài đăng', render: (_, r) => <div><div>{r.post_caption}</div><div className="text-xs text-slate-400">{r.post_author}</div></div> },
        { title: 'Lý do', render: (_, r) => <div><Tag color="red">{REASONS[r.reason]}</Tag><div className="text-xs">{r.details}</div></div> },
        { title: 'Người báo', dataIndex: 'reporter_email' },
        { title: 'Lúc', dataIndex: 'created_at', render: (v) => dayjs(v).format('HH:mm DD/MM') },
        { title: '', render: (_, r) => r.status === 'pending' && (
          <Space><Button danger onClick={() => resolve(r.id, true)}>Ẩn bài</Button><Button onClick={() => resolve(r.id, false)}>Bỏ qua</Button></Space>
        ) },
      ]} />
    </Card>
  )
}

export function BroadcastPage() {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const send = async () => {
    const v = await form.validateFields()
    try {
      const r = await adminApi.broadcast(v)
      message.success(`Đã gửi tới ${r.sent} người dùng (realtime trên web & app)`)
      form.resetFields()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <Card title="Gửi thông báo hàng loạt" className="max-w-2xl">
      <Form form={form} layout="vertical" initialValues={{ role: 'learner', learner_type: 'all' }}>
        <Form.Item name="title" label="Tiêu đề" rules={[{ required: true }]}><Input maxLength={120} /></Form.Item>
        <Form.Item name="body" label="Nội dung"><Input.TextArea maxLength={300} rows={4} /></Form.Item>
        <Space wrap>
          <Form.Item name="role" label="Vai trò"><Select style={{ width: 160 }} options={[{ value: 'all', label: 'Tất cả' }, { value: 'learner', label: 'Học viên' }, { value: 'staff', label: 'Giáo viên' }]} /></Form.Item>
          <Form.Item name="learner_type" label="Đối tượng"><Select style={{ width: 160 }} options={[{ value: 'all', label: 'Tất cả' }, { value: 'adult', label: 'Người lớn' }, { value: 'kid', label: 'Trẻ em' }]} /></Form.Item>
        </Space>
        <Button type="primary" onClick={send}>Gửi</Button>
      </Form>
    </Card>
  )
}

export function SupportAdminPage() {
  const [status, setStatus] = useState('open')
  const [current, setCurrent] = useState<number | null>(null)
  const list = useQuery({ queryKey: ['support-inbox', status], queryFn: () => adminApi.conversations(status), refetchInterval: 15_000 })
  const conv = list.data?.find((c) => c.id === current)
  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card title="Hộp thư hỗ trợ" extra={<Select value={status} onChange={setStatus} style={{ width: 120 }} options={[{ value: 'open', label: 'Đang mở' }, { value: 'closed', label: 'Đã đóng' }]} />}>
        <List loading={list.isLoading} dataSource={list.data} renderItem={(c) => (
          <List.Item className={`cursor-pointer ${c.id === current ? 'bg-brand-50' : ''}`} onClick={() => setCurrent(c.id)}>
            <List.Item.Meta
              title={<Badge count={c.unread} size="small" offset={[10, 0]}>{c.learner.display_name}</Badge>}
              description={<div className="truncate">{c.last_message?.content}</div>}
            />
          </List.Item>
        )} />
      </Card>
      <div className="lg:col-span-2">
        {current ? <SupportChatBox key={current} conversationId={current} title={`${conv?.learner.display_name ?? ''} · ${conv?.learner.email ?? ''}`} /> : <Card>Chọn một cuộc trò chuyện</Card>}
      </div>
    </div>
  )
}

const REPORT_STATUS: Record<DetectionReport['status'], [string, string]> = {
  pending: ['orange', 'Chờ duyệt'], approved: ['green', 'Áp dụng cho mọi người'], rejected: ['default', 'Đã từ chối'],
}

/** Learners' error reports: reviewed here, applied by the server at once, exported for the next training run. */
function DetectionReportsCard() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<string | undefined>('pending')
  const [page, setPage] = useState(1)
  const [exporting, setExporting] = useState(false)
  const reports = useQuery({ queryKey: ['detection-reports', status, page], queryFn: () => adminApi.detectionReports(status, page) })
  const summary = useQuery({ queryKey: ['detection-report-summary'], queryFn: adminApi.detectionReportSummary })
  const review = async (r: DetectionReport, approve: boolean) => {
    try {
      await adminApi.reviewDetectionReport(r.id, approve)
      queryClient.invalidateQueries({ queryKey: ['detection-reports'] })
      queryClient.invalidateQueries({ queryKey: ['detection-report-summary'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const exportZip = async () => {
    setExporting(true)
    try {
      const blob = await adminApi.exportDetectionReports()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `lingoprism_feedback_${dayjs().format('YYYYMMDD')}.zip`
      a.click()
      URL.revokeObjectURL(a.href)
      message.success('Đã xuất. Tải file lên Google Drive thành MyDrive/lingoprism_feedback.zip rồi chạy notebook train.', 6)
      queryClient.invalidateQueries({ queryKey: ['detection-report-summary'] })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setExporting(false)
    }
  }
  const s = summary.data
  return (
    <Card title="Báo lỗi nhận diện của người dùng"
      extra={
        <Button type="primary" loading={exporting} disabled={!s?.approved} onClick={exportZip}>
          Xuất dữ liệu train{s?.approved_not_exported ? ` (${s.approved_not_exported} mới)` : ''}
        </Button>
      }>
      {s && (
        <div className="text-sm text-slate-600 mb-3 flex flex-col gap-1">
          <div>
            Chờ duyệt <b>{s.pending}</b> · Đang áp dụng cho mọi người <b>{s.approved}</b> · Từ chối <b>{s.rejected}</b> ·
            Server đã tự sửa <b>{s.applied}</b> lượt nhận diện
          </div>
          <div className="text-slate-500">
            Báo lỗi có hiệu lực ngay cho người báo; tự áp dụng cho mọi người khi {s.consensus_users} người khác nhau báo cùng một lỗi
            hoặc khi bạn duyệt. Chỉ sửa khi mô hình đoán lại đúng nhãn sai đó trên vật trông giống ảnh báo lỗi.
          </div>
          {!s.memory_enabled && (
            <Tag color="red">Chưa có BE/models/embedder.onnx – server chỉ ghi nhận, chưa tự sửa (python AI/scripts/export_embedder.py)</Tag>
          )}
        </div>
      )}
      <Select className="mb-3 w-56" value={status ?? 'all'} onChange={(v) => { setStatus(v === 'all' ? undefined : v); setPage(1) }}
        options={[{ value: 'pending', label: 'Chờ duyệt' }, { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Đã từ chối' }, { value: 'all', label: 'Tất cả' }]} />
      <Table<DetectionReport> size="small" rowKey="id" loading={reports.isLoading} dataSource={reports.data?.results}
        pagination={{ current: page, total: reports.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        columns={[
          { title: 'Vật', render: (_, r) => (r.crop ? <Image src={r.crop} width={72} preview={{ src: r.photo ?? r.crop }} /> : '—') },
          { title: 'Mô hình đoán → Người dùng sửa', render: (_, r) => (
            <span><Tag color="red">{r.wrong_label}</Tag>→ <Tag color="green">{r.correct_label || 'không phải đồ vật'}</Tag></span>
          ) },
          { title: 'Số người báo', dataIndex: 'same_reports' },
          { title: 'Đã tự sửa', dataIndex: 'applied' },
          { title: 'Bị phản đối', dataIndex: 'disputes', render: (v: number) => (v ? <Tag color="volcano">{v}</Tag> : 0) },
          { title: 'Người báo', dataIndex: 'user' },
          { title: 'Trạng thái', render: (_, r) => <Tag color={REPORT_STATUS[r.status][0]}>{REPORT_STATUS[r.status][1]}</Tag> },
          { title: '', render: (_, r) => (
            <Space>
              {r.status !== 'approved' && <Button size="small" type="primary" onClick={() => review(r, true)}>Duyệt</Button>}
              {r.status !== 'rejected' && <Button size="small" danger onClick={() => review(r, false)}>Từ chối</Button>}
            </Space>
          ) },
          { title: 'Lúc', dataIndex: 'created_at', render: (v) => dayjs(v).format('HH:mm DD/MM') },
        ]} />
    </Card>
  )
}

export function DetectionsAdminPage() {
  const [page, setPage] = useState(1)
  const logs = useQuery({ queryKey: ['admin-detections', page], queryFn: () => adminApi.detections(page) })
  const stats = useQuery({ queryKey: ['detection-stats'], queryFn: adminApi.detectionStats })
  const models = useQuery({ queryKey: ['model-versions'], queryFn: adminApi.modelVersions })
  return (
    <div className="flex flex-col gap-4">
      <Card title="Phiên bản mô hình YOLOv10">
        <Table size="small" rowKey="id" pagination={false} dataSource={models.data} locale={{ emptyText: 'Chưa đăng ký mô hình tự train – server đang dùng yolov10n COCO mặc định (python manage.py register_model)' }}
          columns={[
            { title: 'Tên', dataIndex: 'name' }, { title: 'Số lớp', render: (_, m) => m.classes.length },
            { title: 'Precision', dataIndex: 'precision' }, { title: 'Recall', dataIndex: 'recall' }, { title: 'mAP50', dataIndex: 'map50' },
            { title: 'Đang dùng', dataIndex: 'is_active', render: (v) => (v ? <Tag color="green">Đang dùng</Tag> : null) },
          ]} />
      </Card>
      <div className="grid lg:grid-cols-2 gap-4">
        <Card title="Thống kê theo lớp (dữ liệu cho VIP)">
          <Table size="small" rowKey="label" dataSource={stats.data?.per_label} columns={[
            { title: 'Nhãn', dataIndex: 'label' }, { title: 'Lượt', dataIndex: 'count' },
            { title: 'Conf. TB', dataIndex: 'avg_confidence', render: (v: number) => v?.toFixed(2) },
            { title: 'Đúng', dataIndex: 'correct' }, { title: 'Sai', dataIndex: 'wrong' },
          ]} />
        </Card>
        <Card title="Cặp nhầm lẫn (nhãn dự đoán → nhãn người dùng sửa)">
          <Table size="small" rowKey={(r) => `${r.label}-${r.corrected_label}`} dataSource={stats.data?.confusion}
            columns={[{ title: 'Dự đoán', dataIndex: 'label' }, { title: 'Thực tế', dataIndex: 'corrected_label' }, { title: 'Số lần', dataIndex: 'count' }]} />
          <div className="mt-3 text-sm text-slate-500">
            {stats.data?.by_device.map((d) => <div key={d.device}>{d.device === 'server' ? 'Máy chủ' : 'Điện thoại'}: {d.count} lượt · TB {Math.round(d.avg_ms ?? 0)} ms</div>)}
          </div>
        </Card>
      </div>
      <DetectionReportsCard />
      <Card title="Nhật ký nhận diện">
        <Table<DetectionLog> rowKey="id" loading={logs.isLoading} dataSource={logs.data?.results}
          pagination={{ current: page, total: logs.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
          columns={[
            { title: 'Ảnh', dataIndex: 'image', render: (v) => (v ? <Image src={v} width={64} /> : '—') },
            { title: 'Người dùng', dataIndex: 'user' },
            { title: 'Thiết bị', render: (_, d) => `${d.device === 'server' ? 'Máy chủ' : 'Điện thoại'} · ${d.inference_ms ?? '–'} ms` },
            { title: 'Kết quả', render: (_, d) => d.items.map((i, k) => (
              <Tag key={k} color={i.feedback === 'wrong' ? 'red' : i.feedback === 'correct' ? 'green' : undefined}>
                {i.label} {Math.round(i.confidence * 100)}%{i.corrected_label && ` → ${i.corrected_label}`}
              </Tag>
            )) },
            { title: 'Lúc', dataIndex: 'created_at', render: (v) => dayjs(v).format('HH:mm DD/MM') },
          ]} />
      </Card>
    </div>
  )
}

export function GamificationAdminPage() {
  const { message } = App.useApp()
  const items = useQuery({ queryKey: ['admin-items'], queryFn: adminApi.items })
  const badges = useQuery({ queryKey: ['admin-badges'], queryFn: adminApi.badges })
  const tiers = useQuery({ queryKey: ['admin-tiers'], queryFn: adminApi.tiers })
  return (
    <div className="flex flex-col gap-4">
      <Card title="Giải đấu tuần" extra={<Button onClick={async () => { const r = await adminApi.closeWeek(); message.success(`Đã chốt ${r.closed} nhóm giải đấu`) }}>Chốt tuần đã kết thúc</Button>}>
        <Table size="small" rowKey="id" pagination={false} dataSource={tiers.data}
          columns={[{ title: 'Thứ tự', dataIndex: 'order' }, { title: 'Hạng', dataIndex: 'name' }, { title: 'Thăng hạng top', dataIndex: 'promote_top' }, { title: 'Xuống hạng cuối', dataIndex: 'demote_bottom' }]} />
      </Card>
      <Card title="Vật phẩm cửa hàng">
        <Table size="small" rowKey="id" pagination={false} dataSource={items.data}
          columns={[{ title: 'Mã', dataIndex: 'code' }, { title: 'Tên', dataIndex: 'name' }, { title: 'Hiệu ứng', dataIndex: 'effect' },
            { title: 'Giá Vảy', dataIndex: 'cost_scales' }, { title: 'Giá Ngọc', dataIndex: 'cost_gems' }]} />
      </Card>
      <Card title="Huy hiệu">
        <Table size="small" rowKey="id" pagination={false} dataSource={badges.data}
          columns={[{ title: 'Tên', dataIndex: 'name' }, { title: 'Mô tả', dataIndex: 'description' }, { title: 'Điều kiện', dataIndex: 'condition' }, { title: 'Ngưỡng', dataIndex: 'threshold' }]} />
      </Card>
    </div>
  )
}
