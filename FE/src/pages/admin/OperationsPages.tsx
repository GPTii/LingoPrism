import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Badge, Button, Card, Form, Image, Input, List, Select, Space, Table, Tabs, Tag } from 'antd'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { adminApi, type DetectionLog, type DetectionReport, type PostReport, type UserReport } from '../../api/admin'
import { errorMessage } from '../../api/client'
import { SupportChatBox } from '../learner/SupportPage'
import { BulkDeleteBar, DateRangeFilter, dateParams, pagination, useBulkDelete, useSelection, type DateRange } from '../../components/DataTools'
import SearchBox from '../../components/SearchBox'

const REASONS: Record<string, string> = {
  spam: 'Spam', inappropriate: 'Không phù hợp', wrong_vocab: 'Từ vựng sai', harassment: 'Quấy rối',
  impersonation: 'Giả mạo', other: 'Khác',
}

export function ModerationPage() {
  const [params, setParams] = useSearchParams()
  const pendingUsers = useQuery({ queryKey: ['user-reports', 'pending'], queryFn: () => adminApi.userReports('pending') })
  const pendingPosts = useQuery({ queryKey: ['post-reports', 'pending'], queryFn: () => adminApi.postReports('pending') })
  return (
    <Card title="Kiểm duyệt cộng đồng">
      <Tabs activeKey={params.get('tab') ?? 'posts'} onChange={(tab) => setParams({ tab }, { replace: true })} items={[
        { key: 'posts', label: <Badge count={pendingPosts.data?.count} offset={[10, 0]} size="small">Bài đăng</Badge>, children: <PostReports /> },
        { key: 'users', label: <Badge count={pendingUsers.data?.count} offset={[10, 0]} size="small">Người dùng</Badge>, children: <UserReports /> },
      ]} />
    </Card>
  )
}

/** Reports about a learner, mostly from private messages. The messages shown are the copy taken when the report was
 * sent; locking the account signs that learner out everywhere and closes all pending reports about them. */
function UserReports() {
  const { message, modal } = App.useApp()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState('pending')
  const [created, setCreated] = useState<DateRange>(null)
  const list = useQuery({ queryKey: ['user-reports', status, dateParams(created)], queryFn: () => adminApi.userReports(status, dateParams(created)) })
  const resolve = (r: UserReport, lock: boolean) => {
    const run = async () => {
      try {
        await adminApi.resolveUserReport(r.id, lock)
        message.success(lock ? `Đã khoá tài khoản ${r.reported_email}` : 'Đã bỏ qua báo cáo')
        queryClient.invalidateQueries({ queryKey: ['user-reports'] })
      } catch (e) {
        message.error(errorMessage(e))
      }
    }
    if (!lock) return run()
    modal.confirm({
      title: `Khoá tài khoản ${r.reported_name}?`,
      content: 'Người này bị đăng xuất ngay trên mọi thiết bị và không đăng nhập lại được. Có thể mở khoá ở trang Người dùng.',
      okText: 'Khoá tài khoản', okButtonProps: { danger: true }, cancelText: 'Huỷ', onOk: run,
    })
  }
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2 justify-end">
        <DateRangeFilter value={created} onChange={setCreated} placeholder={['Báo từ ngày', 'đến ngày']} />
        <Select value={status} onChange={setStatus} style={{ width: 180 }}
          options={[{ value: 'pending', label: 'Chờ xử lý' }, { value: 'resolved', label: 'Đã khoá tài khoản' }, { value: 'dismissed', label: 'Bỏ qua' }]} />
      </div>
      <Table<UserReport> rowKey="id" loading={list.isLoading} dataSource={list.data?.results}
        expandable={{
          rowExpandable: (r) => r.evidence.length > 0,
          expandedRowRender: (r) => (
            <div className="flex flex-col gap-1.5 max-w-2xl">
              <div className="text-xs text-slate-500 mb-1">{r.evidence.length} tin nhắn gần nhất lúc báo cáo</div>
              {r.evidence.map((m, i) => (
                <div key={i} className={`flex gap-2 ${m.sender_id === r.reported ? '' : 'opacity-70'}`}>
                  <span className="shrink-0 w-24 text-xs text-slate-500 pt-0.5">{dayjs(m.created_at).format('HH:mm DD/MM')}</span>
                  <span className={`font-semibold shrink-0 ${m.sender_id === r.reported ? 'text-red-600' : 'text-slate-600'}`}>{m.sender}:</span>
                  <span className="whitespace-pre-wrap break-words">{m.content}</span>
                </div>
              ))}
            </div>
          ),
        }}
        columns={[
          { title: 'Bị báo cáo', render: (_, r) => (
            <div>
              <div className="font-semibold">{r.reported_name}</div>
              <div className="text-xs text-slate-500">{r.reported_email}</div>
              {r.reported_status === 'locked' && <Tag color="red" className="mt-1">Đã khoá</Tag>}
            </div>
          ) },
          { title: 'Lý do', render: (_, r) => <div><Tag color="red">{REASONS[r.reason]}</Tag><div className="text-xs">{r.details}</div></div> },
          { title: 'Số người báo', dataIndex: 'reports_against', render: (n: number) => (n > 1 ? <Tag color="volcano">{n} người</Tag> : '1') },
          { title: 'Tin nhắn', render: (_, r) => (r.evidence.length ? `${r.evidence.length} tin` : '—') },
          { title: 'Người báo', render: (_, r) => <div><div>{r.reporter_name}</div><div className="text-xs text-slate-500">{r.reporter_email}</div></div> },
          { title: 'Lúc', dataIndex: 'created_at', render: (v) => dayjs(v).format('HH:mm DD/MM') },
          { title: '', render: (_, r) => r.status === 'pending' && (
            <Space><Button danger onClick={() => resolve(r, true)}>Khoá tài khoản</Button><Button onClick={() => resolve(r, false)}>Bỏ qua</Button></Space>
          ) },
        ]} />
    </div>
  )
}

function PostReports() {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState('pending')
  const [created, setCreated] = useState<DateRange>(null)
  const list = useQuery({ queryKey: ['post-reports', status, dateParams(created)], queryFn: () => adminApi.postReports(status, dateParams(created)) })
  const resolve = async (id: number, hide: boolean) => {
    await adminApi.resolveReport(id, hide)
    queryClient.invalidateQueries({ queryKey: ['post-reports'] })
  }
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2 justify-end">
        <DateRangeFilter value={created} onChange={setCreated} placeholder={['Báo từ ngày', 'đến ngày']} />
        <Select value={status} onChange={setStatus} style={{ width: 180 }}
          options={[{ value: 'pending', label: 'Chờ xử lý' }, { value: 'resolved', label: 'Đã ẩn bài' }, { value: 'dismissed', label: 'Bỏ qua' }]} />
      </div>
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
    </div>
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
  const [created, setCreated] = useState<DateRange>(null)
  const reports = useQuery({
    queryKey: ['detection-reports', status, page, dateParams(created)],
    queryFn: () => adminApi.detectionReports(status, page, dateParams(created)),
  })
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
      <div className="flex flex-wrap gap-2 mb-3">
        <Select className="w-56" value={status ?? 'all'} onChange={(v) => { setStatus(v === 'all' ? undefined : v); setPage(1) }}
          options={[{ value: 'pending', label: 'Chờ duyệt' }, { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Đã từ chối' }, { value: 'all', label: 'Tất cả' }]} />
        <DateRangeFilter value={created} onChange={(v) => { setCreated(v); setPage(1) }} placeholder={['Báo từ ngày', 'đến ngày']} />
      </div>
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
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [device, setDevice] = useState<string | undefined>()
  const [confirmed, setConfirmed] = useState<string | undefined>()
  const [created, setCreated] = useState<DateRange>(null)
  const filters = { search: search || undefined, device, confirmed, ...dateParams(created) }
  const logs = useQuery({ queryKey: ['admin-detections', page, pageSize, filters], queryFn: () => adminApi.detections({ page, page_size: pageSize, ...filters }) })
  const selection = useSelection<DetectionLog>([filters])
  const bulk = useBulkDelete('/admin/detections/bulk-delete/', () => {
    selection.clear()
    queryClient.invalidateQueries({ queryKey: ['admin-detections'] })
    queryClient.invalidateQueries({ queryKey: ['detection-stats'] })
  })
  const filter = <V,>(set: (v: V) => void) => (v: V) => { set(v); setPage(1) }
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
        <Card title="Tên người dùng gõ mà từ điển chưa có (từ cần bổ sung)">
          <Table size="small" rowKey="text" dataSource={stats.data?.missing_words}
            columns={[{ title: 'Tên tiếng Việt', dataIndex: 'text' }, { title: 'Số lần', dataIndex: 'count' }]} />
        </Card>
        <Card title="Đồ vật model chưa có lớp (lớp mới cho lần train sau)">
          <Table size="small" rowKey="label" dataSource={stats.data?.new_classes}
            columns={[{ title: 'Từ (slug)', dataIndex: 'label' }, { title: 'Số lần người dùng gõ', dataIndex: 'count' }]} />
        </Card>
      </div>
      <DetectionReportsCard />
      <Card title="Nhật ký nhận diện">
        <div className="flex flex-wrap gap-2 mb-3">
          <SearchBox placeholder="Email, tên hoặc nhãn vật" allowClear onSearch={filter(setSearch)} style={{ width: 230 }} />
          <Select allowClear placeholder="Thiết bị" value={device} onChange={filter(setDevice)} style={{ width: 130 }}
            options={[{ value: 'server', label: 'Máy chủ' }, { value: 'on_device', label: 'Điện thoại' }]} />
          <Select allowClear placeholder="Lưu từ" value={confirmed} onChange={filter(setConfirmed)} style={{ width: 140 }}
            options={[{ value: 'true', label: 'Đã lưu từ' }, { value: 'false', label: 'Chưa lưu từ' }]} />
          <DateRangeFilter value={created} onChange={filter(setCreated)} placeholder={['Chụp từ ngày', 'đến ngày']} />
        </div>
        <BulkDeleteBar count={selection.keys.length} noun="ảnh" busy={bulk.busy} onClear={selection.clear}
          warning="Ảnh, các vật nhận ra và báo lỗi kèm theo bị xoá khỏi máy chủ. Từ học viên đã lưu vẫn còn trong thư viện của họ."
          onDelete={() => bulk.run(selection.keys, (n) => `${n} ảnh`)} />
        <Table<DetectionLog> rowKey="id" loading={logs.isLoading} dataSource={logs.data?.results}
          rowSelection={selection.rowSelection}
          pagination={pagination(page, logs.data?.count, pageSize, (p, size) => { setPage(size === pageSize ? p : 1); setPageSize(size) })}
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
