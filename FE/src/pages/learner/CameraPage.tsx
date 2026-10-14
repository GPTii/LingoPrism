import { App, Button, Checkbox, Empty, Spin, Tag, Tooltip, Upload } from 'antd'
import { CameraOutlined, DislikeOutlined, LikeOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { learnApi, type DetectionResult } from '../../api/app'
import { errorMessage } from '../../api/client'
import TargetWord, { langTag } from '../../components/TargetWord'

export default function CameraPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const detect = async (file: File) => {
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setLoading(true)
    try {
      const r = await learnApi.detect(file)
      const seen = new Set<string>()
      r.items = r.items.filter((i) => !seen.has(i.label) && seen.add(i.label))
      r.items.forEach((i) => (i.selected = !!i.card && !i.card.personal && i.confidence >= 0.4))
      setResult(r)
      if (!r.items.length) message.info('Không phát hiện được đồ vật nào. Hãy thử ảnh rõ hơn.')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setLoading(false)
    }
    return false
  }

  const update = (id: number, patch: Partial<DetectionResult['items'][number]>) =>
    setResult((r) => (r ? { ...r, items: r.items.map((i) => (i.id === id ? { ...i, ...patch } : i)) } : r))

  const save = async () => {
    if (!result) return
    setSaving(true)
    try {
      const r = await learnApi.confirm(result.id, result.items.map((i) => ({ id: i.id, selected: i.selected, feedback: i.feedback })))
      message.success(`Đã lưu ${r.saved} từ vào thư viện`)
      queryClient.invalidateQueries({ queryKey: ['summary'] })
      queryClient.invalidateQueries({ queryKey: ['game-summary'] })
      setResult({ ...result, confirmed: true })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 m-0">Gửi ảnh, học ngay từ mới!</h1>
        <p className="text-slate-500">YOLOv10 nhận diện đồ vật trong ảnh và hiển thị từ vựng theo ngôn ngữ bạn đang học.</p>
      </div>
      <Upload.Dragger accept="image/*" showUploadList={false} beforeUpload={detect} disabled={loading}>
        <p className="text-4xl text-brand-600"><CameraOutlined /></p>
        <p className="font-medium">Kéo thả hoặc bấm để chọn ảnh</p>
        <p className="text-slate-400 text-sm">JPG/PNG, tối đa 10 MB</p>
      </Upload.Dragger>

      {(preview || loading) && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="relative rounded-2xl overflow-hidden bg-slate-100">
            {preview && <img src={preview} alt="" className="w-full block" />}
            {result?.items.map((i) =>
              i.bbox.length === 4 ? (
                <div key={i.id} className={`absolute border-2 rounded ${i.feedback === 'wrong' ? 'border-red-500' : 'border-emerald-400'}`}
                  style={{ left: `${i.bbox[0] * 100}%`, top: `${i.bbox[1] * 100}%`, width: `${(i.bbox[2] - i.bbox[0]) * 100}%`, height: `${(i.bbox[3] - i.bbox[1]) * 100}%` }}>
                  <span lang={i.card?.target ? langTag(i.card.target.language) : undefined} className="absolute -top-6 left-0 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded">
                    {i.card?.target?.text ?? i.label} {Math.round(i.confidence * 100)}%
                  </span>
                </div>
              ) : null,
            )}
            {loading && <div className="absolute inset-0 flex items-center justify-center bg-white/60"><Spin size="large" tip="Đang nhận diện…" /></div>}
          </div>

          <div className="flex flex-col gap-3">
            {result && (
              <div className="text-xs text-slate-500">
                {result.device === 'server' ? 'Máy chủ' : 'Thiết bị'} · {result.model}{result.inference_ms != null && ` · ${result.inference_ms} ms`}
              </div>
            )}
            {result?.items.length === 0 && <Empty description="Không có đối tượng" />}
            {result?.items.map((i) => (
              <div key={i.id} className="rounded-2xl bg-white border border-slate-200 p-4 flex gap-3 items-start">
                <Checkbox checked={i.selected} disabled={!i.card || i.feedback === 'wrong' || result.confirmed}
                  onChange={(e) => update(i.id, { selected: e.target.checked })} />
                <div className="flex-1">
                  {i.card?.target ? <TargetWord target={i.card.target} size="md" /> : <div className="font-medium">{i.label}</div>}
                  <div className="text-center text-slate-600">{i.card?.meaning_vi ?? 'Chưa có trong bộ từ vựng đã kiểm tra'}</div>
                  <div className="flex justify-center gap-2 mt-1">
                    <Tag>{Math.round(i.confidence * 100)}%</Tag>
                    {i.card?.personal && <Tag color="green">Đã có trong thư viện</Tag>}
                  </div>
                </div>
                <div className="flex flex-col">
                  <Tooltip title="Nhận diện đúng">
                    <Button type="text" icon={<LikeOutlined className={i.feedback === 'correct' ? 'text-emerald-600' : ''} />}
                      onClick={() => update(i.id, { feedback: i.feedback === 'correct' ? 'unknown' : 'correct' })} />
                  </Tooltip>
                  <Tooltip title="Nhận diện sai">
                    <Button type="text" icon={<DislikeOutlined className={i.feedback === 'wrong' ? 'text-red-500' : ''} />}
                      onClick={() => update(i.id, { feedback: i.feedback === 'wrong' ? 'unknown' : 'wrong', selected: false })} />
                  </Tooltip>
                </div>
              </div>
            ))}
            {result && result.items.length > 0 && (
              <Button type="primary" size="large" loading={saving} disabled={result.confirmed} onClick={save}>
                {result.confirmed ? 'Đã lưu' : 'Lưu từ đã chọn'}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
