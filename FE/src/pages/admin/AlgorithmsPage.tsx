import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, App, Button, Card, Col, Descriptions, Empty, Image, Row, Select, Space, Table, Tabs, Tag, Tooltip } from 'antd'
import { ExperimentOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useState } from 'react'
import { api, errorMessage } from '../../api/client'
import SearchBox from '../../components/SearchBox'

/* eslint-disable @typescript-eslint/no-explicit-any */
type Exp = { created_at: string; duration_s: number; results: any }
interface AlgoData {
  config: Record<string, any>
  choices: Record<string, { value: string; label: string }[]>
  experiments: Partial<Record<'benchmark' | 'yolo' | 'vision' | 'word2vec' | 'srs' | 'ga' | 'vip' | 'distractor' | 'proximity', Exp>>
}

const algoApi = {
  get: () => api.get<AlgoData>('/admin/algorithms/').then((r) => r.data),
  patch: (data: Record<string, unknown>) => api.patch('/admin/algorithms/', data).then((r) => r.data),
  run: (kind: string) => api.post(`/admin/algorithms/run/${kind}/`, {}, { timeout: 600000 }).then((r) => r.data),
  vip: () => api.get<{ results: any[] }>('/admin/algorithms/vip-preview/').then((r) => r.data.results),
  distractor: (q: string, lang: string) => api.get('/admin/algorithms/distractor-preview/', { params: { q, lang } }).then((r) => r.data),
}

/** Minimal SVG line chart (no chart library in the project). */
function LineChart({ series, height = 180, xLabel = 'thế hệ' }: { series: { name: string; color: string; values: number[] }[]; height?: number; xLabel?: string }) {
  const all = series.flatMap((s) => s.values)
  if (!all.length) return null
  const min = Math.min(...all), max = Math.max(...all)
  const n = Math.max(...series.map((s) => s.values.length))
  const W = 600, H = height, pad = 32
  const x = (i: number) => pad + (i / Math.max(n - 1, 1)) * (W - pad - 8)
  const y = (v: number) => H - pad + 8 - ((v - min) / (max - min || 1)) * (H - pad - 8)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: height }}>
      <line x1={pad} y1={H - pad + 8} x2={W} y2={H - pad + 8} stroke="#cdd6e1" />
      <text x={2} y={y(max) + 4} fontSize="11" fill="#556273">{max.toFixed(3)}</text>
      <text x={2} y={y(min)} fontSize="11" fill="#556273">{min.toFixed(3)}</text>
      <text x={W / 2} y={H - 4} fontSize="11" fill="#556273" textAnchor="middle">{xLabel}</text>
      {series.map((s) => (
        <g key={s.name}>
          <polyline fill="none" stroke={s.color} strokeWidth={2} points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')} />
          <text x={W - 4} y={y(s.values[s.values.length - 1]) - 6} fontSize="11" fill={s.color} textAnchor="end">{s.name}</text>
        </g>
      ))}
    </svg>
  )
}

function Bars({ rows }: { rows: { label: string; value: number | null; color?: string }[] }) {
  return (
    <div className="flex flex-col gap-1">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-2 text-xs">
          <span className="w-44 shrink-0 text-slate-600">{r.label}</span>
          <div className="flex-1 bg-slate-100 rounded h-4">
            <div className="h-4 rounded" style={{ width: `${Math.round((r.value ?? 0) * 100)}%`, background: r.color ?? '#1899f0' }} />
          </div>
          <span className="w-12 text-right">{r.value == null ? '–' : `${Math.round(r.value * 100)}%`}</span>
        </div>
      ))}
    </div>
  )
}

function RunButton({ kind, onDone, label = 'Chạy lại', primary }: { kind: string; onDone: () => void; label?: string; primary?: boolean }) {
  const { message } = App.useApp()
  const [busy, setBusy] = useState(false)
  return (
    <Button size="small" type={primary ? 'primary' : 'default'} icon={<ReloadOutlined />} loading={busy} onClick={async () => {
      setBusy(true)
      try { await algoApi.run(kind); message.success('Đã chạy xong'); onDone() } catch (e) { message.error(errorMessage(e)) } finally { setBusy(false) }
    }}>{label}</Button>
  )
}

/** Scatter of every simulated combination: overall recall (x) vs recall of visually confusable words (y). */
function Scatter({ rows, chosen, label }: { rows: any[]; chosen: any; label: (r: any) => string }) {
  const W = 640, H = 300, pad = 40
  const xs = rows.map((r) => r.recall_all), ys = rows.map((r) => r.recall_confusable ?? 0)
  const x0 = Math.min(...xs) - 0.01, x1 = Math.max(...xs) + 0.01, y0 = 0, y1 = Math.min(1, Math.max(...ys) + 0.05)
  const x = (v: number) => pad + ((v - x0) / (x1 - x0)) * (W - pad - 10)
  const y = (v: number) => H - pad - ((v - y0) / (y1 - y0)) * (H - pad - 10)
  const color = (r: any) => (r.priority === 'due' ? '#1899f0' : r.priority.startsWith('vip_due') ? '#10c79a' : '#ffb020')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: H }}>
      <line x1={pad} y1={H - pad} x2={W} y2={H - pad} stroke="#cdd6e1" /><line x1={pad} y1={0} x2={pad} y2={H - pad} stroke="#cdd6e1" />
      <text x={W / 2} y={H - 8} fontSize="11" fill="#556273" textAnchor="middle">tỉ lệ nhớ – mọi từ →</text>
      <text x={12} y={H / 2} fontSize="11" fill="#556273" textAnchor="middle" transform={`rotate(-90 12 ${H / 2})`}>từ dễ nhầm qua ảnh →</text>
      {[x0, x1].map((v) => <text key={v} x={x(v)} y={H - pad + 14} fontSize="10" fill="#8292a8" textAnchor="middle">{Math.round(v * 100)}%</text>)}
      {[y0, y1].map((v) => <text key={v} x={pad - 4} y={y(v) + 4} fontSize="10" fill="#8292a8" textAnchor="end">{Math.round(v * 100)}%</text>)}
      {rows.map((r, i) => (
        <circle key={i} cx={x(r.recall_all)} cy={y(r.recall_confusable ?? 0)} r={r === chosen ? 7 : r.pareto ? 5 : 3.5}
          fill={color(r)} fillOpacity={r.eligible ? 0.95 : 0.35} stroke={r === chosen ? '#15233b' : 'none'} strokeWidth={2}>
          <title>{`${label(r)}: ${(r.recall_all * 100).toFixed(1)}% / ${((r.recall_confusable ?? 0) * 100).toFixed(1)}%`}</title>
        </circle>
      ))}
    </svg>
  )
}

const PRIORITY_LABEL: Record<string, string> = { due: 'theo hạn', vip: 'VIP', vip_history: 'VIP thiên lịch sử', vip_vision: 'VIP thiên thị giác',
  risk_only: 'nguy cơ quên', vip_due1: 'VIP lai 1 ngày', vip_due3: 'VIP lai 3 ngày', vip_due7: 'VIP lai 7 ngày' }
const SCHED_LABEL: Record<string, string> = { leitner: 'Leitner', sm2: 'SM-2', fsrs: 'FSRS', fsrs_ga: 'FSRS+GA' }
const VIP_PRIO: Record<string, string> = { due: 'theo hạn', vip: 'VIP thuần', vip_hybrid: 'VIP lai' }
const VIP_COLOR: Record<string, string> = { due: '#1899f0', vip: '#ffb020', vip_hybrid: '#10c79a' }
const comboLabel = (r: any) => SCHED_LABEL[r.scheduler] + (r.retention && r.scheduler.startsWith('fsrs') ? ` r=${r.retention}` : '')
  + (r.priority === 'due' ? '' : ` + ${PRIORITY_LABEL[r.priority]}`)

const meta = (e?: Exp) => e && <span className="text-xs text-slate-400">{dayjs(e.created_at).format('DD/MM HH:mm')} · {e.duration_s}s</span>

export default function AlgorithmsPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const q = useQuery({ queryKey: ['admin-algorithms'], queryFn: algoApi.get })
  const vip = useQuery({ queryKey: ['admin-vip-preview'], queryFn: algoApi.vip })
  const [dq, setDq] = useState('cat')
  const [dlang, setDlang] = useState('en')
  const dist = useQuery({ queryKey: ['admin-distractor', dq, dlang], queryFn: () => algoApi.distractor(dq, dlang), enabled: !!dq, retry: false })
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['admin-algorithms'] })
  const d = q.data
  const ex = d?.experiments ?? {}

  const setConfig = async (field: string, value: string) => {
    try { await algoApi.patch({ [field]: value }); message.success('Đã lưu cấu hình'); refresh() } catch (e) { message.error(errorMessage(e)) }
  }

  const srs = ex.srs?.results
  const ga = ex.ga?.results
  const vipRes = ex.vip?.results
  const prox = ex.proximity?.results
  const dis = ex.distractor?.results
  const w2v = ex.word2vec?.results
  const vis = ex.vision?.results
  const yolo = ex.yolo?.results
  const bench = ex.benchmark?.results
  const pct = (v: number | null | undefined) => (v == null ? '–' : `${(v * 100).toFixed(1)}%`)
  const MODEL_LABEL: Record<string, string> = { leitner: 'Leitner (cũ)', sm2: 'SM-2', fsrs: 'FSRS mặc định', fsrs_ga: 'FSRS + GA', fsrs_default: 'FSRS mặc định' }

  return (
    <Card title={<span><ExperimentOutlined /> Thuật toán AI & thực nghiệm</span>} loading={q.isLoading}>
      <Alert className="mb-4" type="info" showIcon
        message="Các thuật toán trong đề cương (ngoài YOLOv10) đều tự cài đặt bằng Python/NumPy trong BE/apps/algorithms. Ở đây chọn thuật toán đang dùng cho toàn hệ thống và xem kết quả so sánh với phương pháp cơ sở."
        description="Lưu ý: lịch sử ôn tập hiện là của người học mẫu (trí nhớ giả lập theo mô hình quên), thí nghiệm VIP chạy trên người học mô phỏng. Khi có người dùng thật, bấm 'Chạy lại' để có số liệu cho báo cáo." />
      {d && (
        <Card size="small" title="Cấu hình đang dùng" className="mb-4">
          <Row gutter={[16, 12]}>
            {([['scheduler', 'Lập lịch ôn tập'], ['review_priority', 'Thứ tự ôn tập'], ['distractor', 'Đáp án gây nhiễu'], ['proximity', 'Tìm POI lân cận']] as const).map(([f, label]) => (
              <Col xs={24} md={12} lg={6} key={f}>
                <div className="text-xs text-slate-500 mb-1">{label}</div>
                <Select className="w-full" value={d.config[f]} options={d.choices[f]} onChange={(v) => setConfig(f, v)} />
              </Col>
            ))}
          </Row>
          <div className="mt-2 text-xs text-slate-500">
            {d.config.scheduler === 'fsrs' && <>FSRS: retention mong muốn {d.config.desired_retention}{d.config.fsrs_weights?.length === 17 ? ', bộ tham số do GA tối ưu' : ', tham số mặc định'}. </>}
            {d.config.review_priority === 'vip' && <>VIP: {d.config.vip_weights?.due_days ? `lai – theo hạn ôn, ưu tiên sớm tối đa ${d.config.vip_weights.due_days} ngày` : 'xếp hoàn toàn theo điểm VIP'}.</>}
          </div>
        </Card>
      )}
      <Tabs items={[
        {
          key: 'benchmark', label: 'Tổng hợp & chọn tốt nhất',
          children: bench ? (
            <Space direction="vertical" className="w-full" size="large">
              <div className="flex justify-between flex-wrap gap-2">{meta(ex.benchmark)}
                <Space wrap><RunButton kind="benchmark" onDone={refresh} label="Chạy lại (chỉ so sánh)" />
                  <RunButton kind="benchmark_apply" onDone={refresh} label="Chạy & áp dụng tốt nhất" primary /></Space></div>
              <Alert type="success" showIcon message={bench.rule} description={bench.note} />
              <Table size="small" pagination={false} rowKey="decision" dataSource={bench.decisions} scroll={{ x: true }}
                columns={[{ title: 'Quyết định', dataIndex: 'decision' }, { title: 'Các phương án đã thử', dataIndex: 'options', render: (v) => <span className="text-xs">{v}</span> },
                  { title: 'Chọn', dataIndex: 'chosen', render: (v) => <Tag color="green">{v}</Tag> },
                  { title: 'Bằng chứng', dataIndex: 'evidence', render: (v, r: any) => <span className="text-xs">{v}{r.note ? ` – ${r.note}` : ''}</span> }]} />
              {Object.keys(bench.applied ?? {}).length > 0 && <Tag color="blue">Kết quả này đã được áp dụng vào hệ thống</Tag>}
              <Card size="small" title={`Lịch ôn × thứ tự ôn: ${bench.schedule.rows.length} tổ hợp, mô phỏng 3 nhóm × ${bench.schedule.setup.learners} người học × ${bench.schedule.setup.days} ngày`}>
                <Scatter rows={bench.schedule.rows} chosen={bench.schedule.rows.find((r: any) => comboLabel(r) === comboLabel(bench.schedule.chosen))} label={comboLabel} />
                <div className="text-xs text-slate-500 mb-2">Xanh ngọc: theo hạn · vàng: VIP thuần · tím: VIP lai · viền đen: tổ hợp được chọn · mờ: ngoài ngưỡng nhớ chung. Rê chuột lên điểm để xem tên.</div>
                <Table size="small" rowKey={(r: any) => comboLabel(r)} pagination={{ pageSize: 8 }} dataSource={bench.schedule.rows}
                  columns={[{ title: 'Tổ hợp', render: (_, r: any) => <span>{comboLabel(r)} {r.pareto && <Tag>Pareto</Tag>}</span> },
                    { title: 'Nhớ – mọi từ', dataIndex: 'recall_all', sorter: (a: any, b: any) => a.recall_all - b.recall_all, defaultSortOrder: 'descend' as const, render: pct },
                    { title: 'Nhớ – từ dễ nhầm', dataIndex: 'recall_confusable', sorter: (a: any, b: any) => a.recall_confusable - b.recall_confusable, render: pct },
                    { title: 'Lượt ôn / người', dataIndex: 'reviews' }]} />
              </Card>
              <Card size="small" title="Kiểm tra lại trên nhóm người học mới (không dùng để chọn)">
                <Table size="small" pagination={false} rowKey="label" dataSource={bench.schedule.validation}
                  columns={[{ title: 'Tổ hợp', dataIndex: 'label' }, { title: 'Nhớ – mọi từ', dataIndex: 'recall_all', render: pct }, { title: 'Nhớ – từ dễ nhầm', dataIndex: 'recall_confusable', render: pct }]} />
              </Card>
              <Card size="small" title={`Dự đoán nhớ / quên trên ${bench.prediction.test_cards} thẻ kiểm tra`}>
                <Table size="small" pagination={false} rowKey="model" dataSource={Object.entries(bench.prediction.models).map(([model, m]: any) => ({ model, ...m }))}
                  columns={[{ title: 'Mô hình', dataIndex: 'model', render: (v) => MODEL_LABEL[v] ?? v }, { title: 'Log-loss ↓', dataIndex: 'log_loss' },
                    { title: 'AUC ↑', dataIndex: 'auc' }, { title: 'Accuracy ↑', dataIndex: 'accuracy', render: pct }, { title: 'Tỉ lệ nhớ thật', dataIndex: 'recall_rate', render: pct }]} />
              </Card>
            </Space>
          ) : <div className="flex justify-end"><RunButton kind="benchmark" onDone={refresh} /></div>,
        },
        {
          key: 'yolo', label: 'Model YOLO',
          children: yolo ? (
            <Space direction="vertical" className="w-full" size="large">
              <div className="flex flex-wrap justify-between gap-2">{meta(ex.yolo)}<RunButton kind="yolo" onDone={refresh} /></div>
              {yolo.runs.map((r: any) => (
                <Card key={r.name} size="small" title={<span>{r.name} <Tag>{r.base_model}</Tag>{r.tflite ? <Tag color="green">có TFLite</Tag> : <Tag color="orange">chưa có TFLite</Tag>}</span>}>
                  <Descriptions size="small" bordered column={{ xs: 1, md: 4 }} items={[
                    { label: 'Số lớp', children: r.classes }, { label: 'Epochs', children: r.train_args.epochs },
                    { label: 'Ảnh / batch', children: `${r.train_args.imgsz} px / ${r.train_args.batch}` }, { label: 'Optimizer', children: r.train_args.optimizer ?? '–' },
                    { label: 'Precision', children: r.metrics.precision?.toFixed(3) }, { label: 'Recall', children: r.metrics.recall?.toFixed(3) },
                    { label: 'mAP50', children: <b>{r.metrics.map50?.toFixed(3)}</b> }, { label: 'mAP50-95', children: <b>{r.metrics.map50_95?.toFixed(3)}</b> }]} />
                  {r.curves?.map50 && <>
                    <div className="font-medium mt-3">Quá trình huấn luyện (tập validation)</div>
                    <LineChart xLabel="epoch" height={220} series={[{ name: 'mAP50', color: '#1899f0', values: r.curves.map50 },
                      { name: 'mAP50-95', color: '#10c79a', values: r.curves.map50_95 }, { name: 'precision', color: '#ffb020', values: r.curves.precision },
                      { name: 'recall', color: '#ef4444', values: r.curves.recall }]} />
                  </>}
                  <div className="font-medium mt-3">Biểu đồ do Ultralytics xuất (bấm để phóng to)</div>
                  <Image.PreviewGroup>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {r.plots.map((u: string) => <div key={u}><Image src={u} className="rounded border" /><div className="text-xs text-slate-500 truncate">{u.split('/').pop()}</div></div>)}
                    </div>
                  </Image.PreviewGroup>
                  <div className="font-medium mt-3">AP theo từng lớp (tập test)</div>
                  <Table size="small" rowKey="label" pagination={{ pageSize: 10 }} dataSource={r.per_class}
                    columns={[{ title: 'Lớp', dataIndex: 'label' },
                      ...['precision', 'recall', 'map50', 'map50_95'].filter((k) => r.per_class[0]?.[k] !== undefined).map((k) => ({
                        title: k, dataIndex: k, sorter: (a: any, b: any) => a[k] - b[k], defaultSortOrder: k === 'map50' ? ('ascend' as const) : undefined,
                        render: (v: number) => v?.toFixed(3) }))]} />
                </Card>
              ))}
              <Card size="small" title="So sánh trên ảnh từ vựng (ảnh thật, không có trong dữ liệu train)">
                <Table size="small" pagination={false} rowKey={(x: any) => x.model + x.kind}
                  dataSource={yolo.comparison.models.flatMap((m: any) => Object.entries(m.results).map(([kind, v]: any) => ({ model: m.model, kind, ...v })))}
                  columns={[{ title: 'Model', dataIndex: 'model' },
                    { title: 'Cách chạy', dataIndex: 'kind', render: (v) => ({ trained: 'Model tự train', coco: 'COCO gốc (chỉ lớp COCO)', combined: 'Kết hợp (đang dùng)' } as any)[v] ?? v },
                    { title: 'Số ảnh', dataIndex: 'photos' }, { title: 'Top-1 đúng', dataIndex: 'top1', render: (v) => (v == null ? '–' : `${Math.round(v * 100)}%`) },
                    { title: 'Có trong kết quả', dataIndex: 'found', render: (v) => (v == null ? '–' : `${Math.round(v * 100)}%`) },
                    { title: 'Top-1 lớp ngoài COCO', dataIndex: 'top1_new_classes', render: (v) => (v == null ? '–' : `${Math.round(v * 100)}%`) },
                    { title: 'ms/ảnh (CPU)', dataIndex: 'ms_per_image' }]} />
                <div className="text-xs text-slate-500 mt-2">{yolo.comparison.note}</div>
              </Card>
            </Space>
          ) : <div className="flex justify-end"><RunButton kind="yolo" onDone={refresh} /></div>,
        },
        {
          key: 'srs', label: 'SM-2 vs FSRS',
          children: srs ? (
            <Space direction="vertical" className="w-full">
              <div className="flex flex-wrap justify-between gap-2">{meta(ex.srs)}<RunButton kind="srs" onDone={refresh} /></div>
              <div className="text-sm text-slate-600">Dự đoán xác suất nhớ trước mỗi lần ôn trên {srs.reviews} lượt ôn của {srs.cards} thẻ (replay lịch sử). Log-loss và RMSE càng thấp càng tốt, AUC càng cao càng tốt.</div>
              <Table size="small" pagination={false} rowKey="model"
                dataSource={Object.entries(srs.models).map(([model, m]: any) => ({ model, ...m }))}
                columns={[{ title: 'Mô hình', dataIndex: 'model', render: (v) => MODEL_LABEL[v] ?? v },
                  { title: 'Log-loss', dataIndex: 'log_loss' }, { title: 'RMSE', dataIndex: 'rmse' }, { title: 'AUC', dataIndex: 'auc' },
                  { title: 'Accuracy', dataIndex: 'accuracy', render: (v) => (v == null ? '–' : `${(v * 100).toFixed(1)}%`) }, { title: 'Số dự đoán', dataIndex: 'n' }]} />
              <div className="text-xs text-slate-400">{srs.note}</div>
            </Space>
          ) : <Empty description="Chưa chạy" />,
        },
        {
          key: 'ga', label: 'Genetic Algorithm',
          children: ga ? (
            <Space direction="vertical" className="w-full">
              <div className="flex flex-wrap justify-between gap-2">{meta(ex.ga)}<RunButton kind="ga" onDone={refresh} /></div>
              <div className="text-sm text-slate-600">Tối ưu 17 tham số FSRS: quần thể {ga.population}, {ga.generations} thế hệ, chọn lọc tournament, lai ghép BLX-α, đột biến Gauss, giữ 2 cá thể tốt nhất. Huấn luyện trên {ga.train_cards} thẻ, đánh giá trên {ga.test_cards} thẻ chưa dùng.</div>
              <LineChart series={[{ name: 'tốt nhất', color: '#1899f0', values: ga.history.map((h: any) => h.best) },
                { name: 'trung bình', color: '#8292a8', values: ga.history.map((h: any) => h.mean) }]} />
              <Table size="small" pagination={false} rowKey="model"
                dataSource={Object.entries(ga.test).map(([model, m]: any) => ({ model, ...m }))}
                columns={[{ title: 'Trên tập kiểm tra', dataIndex: 'model', render: (v) => MODEL_LABEL[v] ?? v },
                  { title: 'Log-loss', dataIndex: 'log_loss' }, { title: 'RMSE', dataIndex: 'rmse' }, { title: 'AUC', dataIndex: 'auc' },
                  { title: 'Accuracy', dataIndex: 'accuracy', render: (v) => (v == null ? '–' : `${(v * 100).toFixed(1)}%`) }]} />
              <Tag color={ga.applied ? 'green' : 'default'}>{ga.applied ? 'Đã áp dụng làm cấu hình tham chiếu (tốt hơn trên tập kiểm tra)' : 'Không áp dụng (không tốt hơn mặc định)'}</Tag>
              <div className="text-xs text-slate-500 break-all">w = [{ga.weights.join(', ')}]</div>
            </Space>
          ) : <Empty description="Chưa chạy" />,
        },
        {
          key: 'vip', label: 'VIP',
          children: (
            <Space direction="vertical" className="w-full">
              {vipRes && <>
                <div className="flex flex-wrap justify-between gap-2">{meta(ex.vip)}<RunButton kind="vip" onDone={refresh} /></div>
                <div className="text-sm text-slate-600">
                  {vipRes.setup.learners} người học mô phỏng × {vipRes.setup.days} ngày, {vipRes.setup.new_per_day} từ mới/ngày, tối đa {vipRes.setup.review_budget} lượt ôn/ngày; {vipRes.confusable_words} từ có lớp YOLO dễ nhầm (score ≥ 0,3). Chỉ số: xác suất nhớ thật ở cuối kỳ.
                </div>
                <Row gutter={16}>
                  <Col xs={24} md={12}><div className="font-medium mb-1">Toàn bộ từ</div>
                    <Bars rows={vipRes.rows.map((r: any) => ({ label: `${MODEL_LABEL[r.scheduler]} · ${VIP_PRIO[r.priority] ?? r.priority}`, value: r.recall_all, color: VIP_COLOR[r.priority] ?? '#1899f0' }))} /></Col>
                  <Col xs={24} md={12}><div className="font-medium mb-1">Từ dễ nhầm thị giác</div>
                    <Bars rows={vipRes.rows.map((r: any) => ({ label: `${MODEL_LABEL[r.scheduler]} · ${VIP_PRIO[r.priority] ?? r.priority}`, value: r.recall_confusable, color: VIP_COLOR[r.priority] ?? '#1899f0' }))} /></Col>
                </Row>
                <div className="text-xs text-slate-400">{vipRes.note}</div>
              </>}
              <div className="font-medium mt-2">Thứ tự ôn VIP hiện tại (các từ đến hạn của mọi học viên)</div>
              <Table size="small" rowKey={(r: any) => `${r.user}-${r.word}-${r.vip_rank}`} loading={vip.isLoading} dataSource={vip.data} pagination={{ pageSize: 10 }}
                columns={[{ title: 'VIP', dataIndex: 'vip_rank', width: 50 }, { title: 'Theo hạn', dataIndex: 'due_rank', width: 70 },
                  { title: 'Từ', dataIndex: 'word' }, { title: 'Lớp YOLO', dataIndex: 'yolo_label', render: (v) => v || '–' },
                  { title: 'Học viên', dataIndex: 'user' }, { title: 'Điểm', dataIndex: 'score' },
                  { title: 'Quên · Khó · (1−conf) · Nhầm', dataIndex: 'components', render: (c: any) => `${c.forget} · ${c.difficulty} · ${c.confidence} · ${c.confusion}` }]} />
            </Space>
          ),
        },
        {
          key: 'vision', label: 'Nhầm lẫn thị giác',
          children: vis ? (
            <Space direction="vertical" className="w-full">
              <div className="flex flex-wrap justify-between gap-2">{meta(ex.vision)}<RunButton kind="vision" onDone={refresh} /></div>
              <div className="text-sm text-slate-600">Nguồn: {vis.source === 'photos' ? 'model YOLO đang hoạt động chạy trên ảnh của từng từ (sẽ thay bằng confusion matrix khi có model tự train)' : 'confusion matrix của model đã train'} + phản hồi sai của người dùng.</div>
              <Table size="small" rowKey="label" pagination={{ pageSize: 10 }}
                dataSource={Object.entries(vis.classes).map(([label, v]: any) => ({ label, ...v })).sort((a: any, b: any) => b.score - a.score)}
                columns={[{ title: 'Lớp', dataIndex: 'label' }, { title: 'Điểm nhầm', dataIndex: 'score' },
                  { title: 'Confidence', dataIndex: 'mean_conf', render: (v) => v ?? '–' },
                  { title: 'Bị nhầm thành', dataIndex: 'confusion', render: (c: Record<string, number>) => Object.entries(c).map(([k, v]) => <Tag key={k}>{k} {v}</Tag>) }]} />
            </Space>
          ) : <Empty description="Chưa chạy" />,
        },
        {
          key: 'distractor', label: 'Smart Distractor',
          children: (
            <Space direction="vertical" className="w-full">
              {w2v && <Descriptions size="small" bordered column={{ xs: 1, md: 3 }} title="Word2Vec (skip-gram + negative sampling, tự cài bằng NumPy)"
                items={[{ label: 'Câu huấn luyện', children: w2v.sentences.toLocaleString() }, { label: 'Từ điển', children: w2v.vocab.toLocaleString() },
                  { label: 'Khái niệm có vector', children: `${w2v.concepts_with_vector}/${w2v.concepts_total}` },
                  { label: 'Láng giềng gần nhất', span: 3, children: Object.entries(w2v.neighbours).map(([k, v]: any) => <div key={k}><b>{k}</b>: {v.join(', ')}</div>) }]} />}
              {dis?.stats && <>
                <div className="flex flex-wrap justify-between gap-2">{meta(ex.distractor)}<RunButton kind="distractor" onDone={refresh} /></div>
                <Table size="small" pagination={false} rowKey="name" dataSource={Object.entries(dis.stats).map(([name, s]: any) => ({ name, ...s }))}
                  columns={[{ title: `Trên ${dis.words} từ`, dataIndex: 'name', render: (v) => (v === 'smart' ? 'Smart Distractor' : 'Ngẫu nhiên (baseline)') },
                    { title: <Tooltip title="Cosine trung bình giữa đáp án và đáp án nhiễu – càng cao càng 'đánh lừa' tốt">Tương đồng ngữ nghĩa</Tooltip>, dataIndex: 'mean_similarity' },
                    { title: 'Cùng từ loại', dataIndex: 'same_pos_rate', render: (v) => `${Math.round(v * 100)}%` },
                    { title: <Tooltip title="Đáp án nhiễu trùng nghĩa với đáp án đúng (câu hỏi có 2 đáp án đúng)">Không hợp lệ</Tooltip>, dataIndex: 'invalid_rate', render: (v) => `${Math.round(v * 100)}%` }]} />
              </>}
              {!dis?.stats && <div className="flex justify-end"><RunButton kind="distractor" onDone={refresh} /></div>}
              <Space wrap>
                <SearchBox defaultValue={dq} placeholder="Từ (VD cat, bánh mì, 猫)" onSearch={setDq} style={{ width: 240 }} />
                <Select value={dlang} onChange={setDlang} options={[{ value: 'en', label: 'Tiếng Anh' }, { value: 'zh', label: 'Tiếng Trung' }, { value: 'vi', label: 'Tiếng Việt' }]} />
              </Space>
              {dist.data && (
                <Row gutter={16}>
                  <Col xs={24} md={12}><div className="font-medium">Ngẫu nhiên</div>{dist.data.random.map((w: any) => <div key={w.text}>{w.text} <span className="text-slate-400">({w.vi})</span></div>)}</Col>
                  <Col xs={24} md={12}><div className="font-medium">Smart Distractor cho "{dist.data.word.text}"</div>{dist.data.smart.map((w: any) => <div key={w.text}>{w.text} <span className="text-slate-400">({w.vi}) · {w.score}</span></div>)}</Col>
                </Row>
              )}
              {dist.isError && <Alert type="warning" message="Không tìm thấy từ" />}
            </Space>
          ),
        },
        {
          key: 'proximity', label: 'Proximity Search',
          children: prox ? (
            <Space direction="vertical" className="w-full">
              <div className="flex flex-wrap justify-between gap-2">{meta(ex.proximity)}<RunButton kind="proximity" onDone={refresh} /></div>
              <Descriptions size="small" bordered column={{ xs: 1, md: 3 }} items={[
                { label: 'POI', children: prox.pois }, { label: 'Truy vấn thử', children: prox.queries },
                { label: 'Grid khớp brute force', children: prox.grid_equals_brute },
                { label: 'Grid index (ms/truy vấn)', children: prox.grid_ms }, { label: 'Brute force (ms)', children: prox.brute_ms },
                { label: 'PostgreSQL earthdistance (ms)', children: prox.postgres_ms ?? '–' },
                { label: 'Khớp PostgreSQL', children: prox.grid_vs_postgres_ids }, { label: 'Lệch khoảng cách tối đa', children: `${prox.max_distance_diff_m} m`, span: 2 }]} />
              <div className="text-xs text-slate-500">{prox.note}</div>
              <Table size="small" pagination={false} rowKey="pois" dataSource={prox.scaling}
                columns={[{ title: 'Số POI (giả lập quanh Hà Nội)', dataIndex: 'pois', render: (v) => v.toLocaleString() },
                  { title: 'Grid (ms)', dataIndex: 'grid_ms' }, { title: 'Brute force (ms)', dataIndex: 'brute_ms' }, { title: 'Nhanh hơn', dataIndex: 'speedup', render: (v) => `${v}×` }]} />
            </Space>
          ) : <Empty description="Chưa chạy" />,
        },
      ]} />
    </Card>
  )
}
