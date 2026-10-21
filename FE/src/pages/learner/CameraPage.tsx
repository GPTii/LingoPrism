import { App, Button, Checkbox, Empty, Select, Spin, Tag, Tooltip, Upload } from 'antd'
import { CameraOutlined, DislikeOutlined, LikeOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { learnApi, type DetectedItem, type DetectionResult } from '../../api/app'
import type { WordCard } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import TargetWord, { langTag } from '../../components/TargetWord'

/** picked: the object the learner says it is (error report); notObject: "there is no object here" */
type Item = DetectedItem & { picked?: string; pickedCard?: WordCard; notObject?: boolean }

/** The word shown for an object: the one the learner picked, else the model's answer. */
const shownCard = (i: Item) =>
  i.picked ? i.pickedCard ?? i.alternatives.find((a) => a.label === i.picked)?.card ?? null : i.card

export default function CameraPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const allLabels = useQuery({ queryKey: ['detect-labels'], queryFn: learnApi.detectLabels, enabled: !!result, staleTime: 3600_000 })

  const detect = async (file: File) => {
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setLoading(true)
    try {
      const r = await learnApi.detect(file)
      const seen = new Set<string>()
      r.items = r.items.filter((i) => !seen.has(i.label) && seen.add(i.label))
      // an unsure object is only selected once the learner says which one it is
      r.items.forEach((i) => (i.selected = !!i.card && !i.card.personal && i.confidence >= 0.4 && !i.uncertain))
      setResult(r)
      if (!r.items.length) message.info('Không phát hiện được đồ vật nào. Hãy thử ảnh rõ hơn.')
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setLoading(false)
    }
    return false
  }

  const update = (id: number, patch: Partial<Item>) =>
    setResult((r) => (r ? { ...r, items: r.items.map((i) => (i.id === id ? { ...i, ...patch } : i)) } : r))

  // "Có phải…?": the model's answer → correct; another object → model wrong, learn that word instead
  const pick = (i: Item, label: string, card?: WordCard) => {
    if (label === i.label)
      return update(i.id, { picked: undefined, pickedCard: undefined, notObject: false, feedback: 'correct', selected: !!i.card && !i.card.personal })
    const c = card ?? i.alternatives.find((a) => a.label === label)?.card
    update(i.id, { picked: label, pickedCard: c, notObject: false, feedback: 'wrong', selected: !!c && !c.personal })
  }
  // error report: nothing of the kind in the photo – the server remembers it and stops showing this box
  const notObject = (i: Item) => update(i.id, { picked: undefined, pickedCard: undefined, notObject: true, feedback: 'wrong', selected: false })

  const save = async () => {
    if (!result) return
    setSaving(true)
    try {
      const r = await learnApi.confirm(result.id, (result.items as Item[]).map((i) => ({
        id: i.id, selected: i.selected, feedback: i.feedback, corrected_label: i.picked ?? '', not_object: !!i.notObject,
      })))
      message.success(`Đã lưu ${r.saved} từ vào thư viện`)
      if (r.reported) message.info(`Cảm ơn bạn đã báo lỗi! Lần sau gặp vật tương tự, hệ thống sẽ nhận đúng.`, 5)
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
            {(result?.items as Item[] | undefined)?.map((i) =>
              i.bbox.length === 4 ? (
                <div key={i.id} className={`absolute border-2 rounded ${i.notObject ? 'border-red-500 opacity-40' : i.feedback === 'wrong' && !i.picked ? 'border-red-500' : i.uncertain && !i.picked && i.feedback === 'unknown' ? 'border-amber-400 border-dashed' : 'border-emerald-400'}`}
                  style={{ left: `${i.bbox[0] * 100}%`, top: `${i.bbox[1] * 100}%`, width: `${(i.bbox[2] - i.bbox[0]) * 100}%`, height: `${(i.bbox[3] - i.bbox[1]) * 100}%` }}>
                  <span lang={shownCard(i)?.target ? langTag(shownCard(i)!.target!.language) : undefined} className="absolute -top-6 left-0 bg-black/60 text-white text-xs px-1.5 py-0.5 rounded">
                    {shownCard(i)?.target?.text ?? i.picked ?? i.label}{!i.picked && ` ${Math.round(i.confidence * 100)}%`}{i.uncertain && !i.picked && i.feedback === 'unknown' && ' ?'}
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
            {(result?.items as Item[] | undefined)?.map((i) => {
              const c = shownCard(i)
              const asking = (i.uncertain || i.feedback === 'wrong') && !result!.confirmed
              const listed = new Set([i.label, ...i.alternatives.map((a) => a.label)])
              return (
              <div key={i.id} className="rounded-2xl bg-white border border-slate-200 p-4 flex gap-3 items-start">
                <Checkbox checked={i.selected} disabled={!c || (i.feedback === 'wrong' && !i.picked) || result!.confirmed}
                  onChange={(e) => update(i.id, { selected: e.target.checked })} />
                <div className="flex-1">
                  {c?.target ? <TargetWord target={c.target} size="md" /> : <div className="font-medium">{i.picked ?? i.label}</div>}
                  <div className="text-center text-slate-600">{c?.meaning_vi ?? 'Chưa có trong bộ từ vựng đã kiểm tra'}</div>
                  <div className="flex justify-center gap-2 mt-1">
                    {i.picked ? <Tag color="blue">Bạn đã chọn</Tag> : i.notObject ? <Tag color="red">Không phải đồ vật</Tag> : <Tag color={i.uncertain ? 'orange' : undefined}>{Math.round(i.confidence * 100)}%</Tag>}
                    {i.learned && !i.picked && (
                      <Tooltip title="Mô hình từng nhận sai vật trông giống thế này; hệ thống đã tự sửa theo báo lỗi của người dùng">
                        <Tag color="purple">Đã học từ báo lỗi</Tag>
                      </Tooltip>
                    )}
                    {c?.personal && <Tag color="green">Đã có trong thư viện</Tag>}
                  </div>
                  {asking && (
                    <div className="mt-3 text-center">
                      <div className="text-xs text-slate-500 mb-1">{i.feedback === 'wrong' && !i.picked ? 'Vậy đây là gì?' : 'Chưa chắc lắm – có phải là:'}</div>
                      <div className="flex flex-wrap justify-center gap-1.5">
                        {[{ label: i.label, card: i.card }, ...i.alternatives].map((a) => a.card && (
                          <Button key={a.label} size="small" type={(i.picked ?? (i.feedback === 'correct' ? i.label : '')) === a.label ? 'primary' : 'default'}
                            onClick={() => pick(i, a.label)}>
                            <span lang={a.card.target ? langTag(a.card.target.language) : undefined}>{a.card.target?.text ?? a.label}</span>
                            {a.card.meaning_vi && <span className="text-slate-400 ml-1">({a.card.meaning_vi})</span>}
                          </Button>
                        ))}
                      </div>
                      <div className="flex flex-wrap justify-center items-center gap-1.5 mt-2">
                        <Select size="small" showSearch placeholder="Vật khác…" className="min-w-[180px]"
                          loading={allLabels.isLoading} value={i.picked && !listed.has(i.picked) ? i.picked : undefined}
                          optionFilterProp="search"
                          options={(allLabels.data ?? []).filter((o) => !listed.has(o.label)).map((o) => ({
                            value: o.label,
                            label: `${o.card.target?.text ?? o.label}${o.card.meaning_vi ? ` (${o.card.meaning_vi})` : ''}`,
                            search: `${o.label} ${o.card.target?.text ?? ''} ${o.card.meaning_vi ?? ''}`,
                          }))}
                          onChange={(label: string) => pick(i, label, allLabels.data?.find((o) => o.label === label)?.card)} />
                        <Button size="small" danger type={i.notObject ? 'primary' : 'default'} onClick={() => notObject(i)}>
                          Không phải đồ vật
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex flex-col">
                  <Tooltip title="Nhận diện đúng">
                    <Button type="text" icon={<LikeOutlined className={i.feedback === 'correct' ? 'text-emerald-600' : ''} />}
                      onClick={() => (i.feedback === 'correct' ? update(i.id, { feedback: 'unknown' }) : pick(i, i.label))} />
                  </Tooltip>
                  <Tooltip title="Nhận diện sai">
                    <Button type="text" icon={<DislikeOutlined className={i.feedback === 'wrong' ? 'text-red-500' : ''} />}
                      onClick={() => update(i.id, { feedback: i.feedback === 'wrong' ? 'unknown' : 'wrong', selected: false, picked: undefined, pickedCard: undefined, notObject: false })} />
                  </Tooltip>
                </div>
              </div>
              )
            })}
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
