import { App, Button, Checkbox, Input, Spin, Tooltip, Upload } from 'antd'
import { CameraOutlined, CloseOutlined, DislikeOutlined, LikeOutlined, PlusOutlined, ShareAltOutlined } from '@ant-design/icons'
import { useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { communityApi, learnApi, type DetectedItem, type DetectionResult, type NameLookup } from '../../api/app'
import { useAuth } from '../../auth/store'
import type { WordCard } from '../../api/vocab'
import { errorMessage } from '../../api/client'
import TargetWord, { langTag } from '../../components/TargetWord'
import { Prismo } from '../../components/brand/Brand'
import PhotoDialogue from '../../components/PhotoDialogue'
import { EmptyState, PageHeader } from '../../components/ui'

/** a small status word under the result, coloured by what it means */
const Note = ({ tone, children }: { tone: 'brand' | 'amber' | 'red' | 'green' | 'slate'; children: ReactNode }) => {
  const cls = { brand: 'bg-brand-50 text-brand-700', amber: 'bg-amber-50 text-amber-700', red: 'bg-red-50 text-red-700', green: 'bg-green-50 text-green-700', slate: 'bg-slate-100 text-slate-600' }[tone]
  return <span className={`num rounded-md px-2 py-0.5 text-xs font-semibold ${cls}`}>{children}</span>
}

/** picked: the object the learner says it is (error report); notObject: "there is no object here";
 * typed: the Vietnamese name they typed, pickedWord the dictionary word they chose for it */
type Item = DetectedItem & { picked?: string; pickedCard?: WordCard; pickedWord?: number; typed?: string; notObject?: boolean }
/** an object the detector missed, named by the learner */
type Added = { typed: string; found: NameLookup | null }

/** "Gõ tên tiếng Việt": the learner names the object, the checked dictionary gives its word in the language learned
 * (no machine translation). A name the dictionary lacks is still sent: the vocabulary team adds it later. */
function NameIt({ onPick, placeholder = 'Gõ tên tiếng Việt, VD: cái ly' }: {
  onPick: (found: NameLookup | null, typed: string) => void
  placeholder?: string
}) {
  const [query, setQuery] = useState('')
  const found = useQuery({ queryKey: ['name-lookup', query], queryFn: () => learnApi.lookupName(query), enabled: !!query, staleTime: 600_000 })
  return (
    <div className="flex flex-col items-center gap-2 w-full">
      <Input.Search placeholder={placeholder} enterButton="Dịch" maxLength={80} allowClear className="max-w-xs"
        aria-label="Tên đồ vật bằng tiếng Việt" loading={found.isFetching} onSearch={(v) => setQuery(v.trim())} />
      {query && found.data && (found.data.length ? (
        <div className="flex flex-wrap justify-center gap-1.5">
          {found.data.map((r) => (
            <Button key={r.word_id} size="small" data-word={r.word_id} onClick={() => onPick(r, query)}>
              <span lang={r.card.target ? langTag(r.card.target.language) : undefined} className="font-semibold">{r.card.target?.text}</span>
              {r.card.meaning_vi && <span className="opacity-70 ml-1">({r.card.meaning_vi})</span>}
            </Button>
          ))}
          <Button size="small" type="link" onClick={() => onPick(null, query)}>Không phải từ nào ở đây – gửi “{query}”</Button>
        </div>
      ) : (
        <div className="text-sm text-slate-500 text-center">
          Từ điển đã kiểm tra chưa có “{query}”.{' '}
          <Button size="small" type="link" className="!px-0" onClick={() => onPick(null, query)}>Vẫn gửi tên này</Button>
          {' '}để đội ngũ bổ sung.
        </div>
      ))}
    </div>
  )
}

/** The word shown for an object: the one the learner picked, else the model's answer. */
const shownCard = (i: Item) =>
  i.picked ? i.pickedCard ?? i.alternatives.find((a) => a.label === i.picked)?.card ?? null : i.card

/** After saving: post the photo with its words to the community feed (others can save the words from it). */
function SharePhoto({ file, detectionId, cards }: { file: File; detectionId: number; cards: WordCard[] }) {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [caption, setCaption] = useState(() => cards.map((c) => c.target?.text ?? '').filter(Boolean).join(' · '))
  const share = useMutation({
    mutationFn: () => communityApi.create(file, caption.trim(), cards.map((c) => c.id), detectionId),
    onSuccess: () => {
      message.success('Đã chia sẻ lên cộng đồng')
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    },
    onError: (e) => message.error(errorMessage(e)),
  })
  if (share.isSuccess)
    return (
      <div className="lp-card p-4 flex items-center justify-between gap-3">
        <span className="font-semibold text-slate-700">Ảnh đã lên bảng tin cộng đồng</span>
        <Link to="/community"><Button>Xem bảng tin</Button></Link>
      </div>
    )
  return (
    <div className="lp-card p-4 flex flex-col gap-2">
      <div className="font-semibold text-slate-800">Chia sẻ ảnh này lên cộng đồng</div>
      <div className="text-sm text-slate-500">Mọi người thấy ảnh cùng {cards.length} từ bạn vừa lưu và có thể lưu các từ đó.</div>
      <Input.TextArea value={caption} onChange={(e) => setCaption(e.target.value)} maxLength={500} autoSize={{ minRows: 2, maxRows: 4 }}
        placeholder="Viết vài dòng về ảnh…" aria-label="Chú thích" />
      <Button icon={<ShareAltOutlined />} loading={share.isPending} onClick={() => share.mutate()}>Chia sẻ</Button>
    </div>
  )
}

export default function CameraPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const isKid = useAuth((s) => s.user?.learner_type === 'kid') // kids have no community feed
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [added, setAdded] = useState<Added[]>([])

  const detect = async (file: File) => {
    setFile(file)
    setPreview(URL.createObjectURL(file))
    setResult(null)
    setAdded([])
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
  const notObject = (i: Item) => update(i.id, { picked: undefined, pickedCard: undefined, pickedWord: undefined, typed: undefined, notObject: true, feedback: 'wrong', selected: false })
  // the learner typed the object's Vietnamese name: the word found (or only the name, for the vocabulary team)
  const named = (i: Item, found: NameLookup | null, typed: string) => found
    ? update(i.id, { picked: found.label, pickedCard: found.card, pickedWord: found.word_id, typed, notObject: false, feedback: 'wrong', selected: !found.card.personal })
    : update(i.id, { picked: undefined, pickedCard: undefined, pickedWord: undefined, typed, notObject: false, feedback: 'wrong', selected: false })

  const save = async () => {
    if (!result) return
    setSaving(true)
    try {
      const r = await learnApi.confirm(result.id, (result.items as Item[]).map((i) => ({
        id: i.id, selected: i.selected, feedback: i.feedback, corrected_label: i.picked ?? '', not_object: !!i.notObject,
        corrected_word: i.pickedWord ?? null, typed: i.typed ?? '',
      })), added.map((a) => ({ word: a.found?.word_id ?? null, typed: a.typed })))
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
      <PageHeader title="Chụp một đồ vật" actions={<Link to="/camera/history"><Button size="large">Lịch sử ảnh</Button></Link>} description="Máy nhận ra đồ vật trong ảnh và cho bạn từ vựng theo ngôn ngữ đang học. Nhận sai thì bấm sửa – lần sau hệ thống sẽ nhận đúng." />
      <Upload.Dragger accept="image/*" showUploadList={false} beforeUpload={detect} disabled={loading} className="[&_.ant-upload-drag]:!rounded-2xl">
        <div className="flex flex-col items-center gap-2 py-4">
          <span className="h-16 w-16 rounded-2xl prism-bg grid place-items-center text-3xl text-white"><CameraOutlined /></span>
          <span className="font-semibold text-slate-800 text-lg">Chọn hoặc kéo thả một ảnh</span>
          <span className="text-slate-500 text-sm">Trên điện thoại, bấm để chụp trực tiếp · JPG hoặc PNG, tối đa 10 MB</span>
        </div>
      </Upload.Dragger>

      {(preview || loading) && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="relative rounded-2xl overflow-hidden bg-slate-100">
            {preview && <img src={preview} alt="" className="w-full block" />}
            {(result?.items as Item[] | undefined)?.map((i) =>
              i.bbox.length === 4 ? (
                <div key={i.id} className={`absolute border-2 rounded ${i.notObject ? 'border-red-500 opacity-40' : i.feedback === 'wrong' && !i.picked ? 'border-red-500' : i.uncertain && !i.picked && i.feedback === 'unknown' ? 'border-amber-400 border-dashed' : 'border-emerald-400'}`}
                  style={{ left: `${i.bbox[0] * 100}%`, top: `${i.bbox[1] * 100}%`, width: `${(i.bbox[2] - i.bbox[0]) * 100}%`, height: `${(i.bbox[3] - i.bbox[1]) * 100}%` }}>
                  <span lang={shownCard(i)?.target ? langTag(shownCard(i)!.target!.language) : undefined} className="num absolute -top-6 left-0 bg-[#15233b]/85 text-white text-xs font-semibold px-1.5 py-0.5 rounded-md whitespace-nowrap">
                    {shownCard(i)?.target?.text ?? i.picked ?? i.label}{!i.picked && ` ${Math.round(i.confidence * 100)}%`}{i.uncertain && !i.picked && i.feedback === 'unknown' && ' ?'}
                  </span>
                </div>
              ) : null,
            )}
            {loading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-white/70 text-slate-700 font-semibold">
                <Spin size="large" />Đang tìm đồ vật trong ảnh…
              </div>
            )}
          </div>

          <div className="flex flex-col gap-3">
            {result && (
              <div className="num text-xs text-slate-500">
                {result.items.length} đồ vật · nhận diện trên {result.device === 'server' ? 'máy chủ' : 'thiết bị'}{result.inference_ms != null && ` trong ${result.inference_ms} ms`}
              </div>
            )}
            {result?.items.length === 0 && (
              <div className="lp-card">
                <EmptyState art={<Prismo mood="think" size={88} />} title="Chưa thấy đồ vật nào"
                  description="Thử chụp gần hơn, đủ sáng, để đồ vật chiếm phần lớn khung hình." />
              </div>
            )}
            {(result?.items as Item[] | undefined)?.map((i) => {
              const c = shownCard(i)
              const asking = (i.uncertain || i.feedback === 'wrong') && !result!.confirmed
              return (
              <div key={i.id} className="lp-card p-4 flex gap-3 items-start">
                <Checkbox checked={i.selected} disabled={!c || (i.feedback === 'wrong' && !i.picked) || result!.confirmed}
                  onChange={(e) => update(i.id, { selected: e.target.checked })} />
                <div className="flex-1">
                  {c?.target ? <TargetWord target={c.target} size="md" /> : <div className="font-semibold text-slate-800">{i.picked ?? i.label}</div>}
                  <div className="text-center text-slate-600">{c?.meaning_vi ?? 'Chưa có trong bộ từ vựng đã kiểm tra'}</div>
                  <div className="flex flex-wrap justify-center gap-1.5 mt-2">
                    {i.picked ? <Note tone="brand">Bạn đã chọn</Note> : i.notObject ? <Note tone="red">Không phải đồ vật</Note>
                      : <Note tone={i.uncertain ? 'amber' : 'slate'}>Chắc {Math.round(i.confidence * 100)}%</Note>}
                    {i.learned && !i.picked && (
                      <Tooltip title="Mô hình từng nhận sai vật trông giống thế này; hệ thống đã tự sửa theo báo lỗi của người dùng">
                        <span><Note tone="brand">Đã sửa nhờ báo lỗi</Note></span>
                      </Tooltip>
                    )}
                    {c?.personal && <Note tone="green">Đã có trong thư viện</Note>}
                  </div>
                  {asking && (
                    <div className="mt-3 text-center">
                      <div className="text-sm font-semibold text-slate-600 mb-1.5">{i.feedback === 'wrong' && !i.picked ? 'Vậy đây là gì?' : 'Chưa chắc lắm – có phải là:'}</div>
                      <div className="flex flex-wrap justify-center gap-1.5">
                        {[{ label: i.label, card: i.card }, ...i.alternatives].map((a) => a.card && (
                          <Button key={a.label} size="small" type={(i.picked ?? (i.feedback === 'correct' ? i.label : '')) === a.label ? 'primary' : 'default'}
                            onClick={() => pick(i, a.label)}>
                            <span lang={a.card.target ? langTag(a.card.target.language) : undefined}>{a.card.target?.text ?? a.label}</span>
                            {a.card.meaning_vi && <span className="opacity-70 ml-1">({a.card.meaning_vi})</span>}
                          </Button>
                        ))}
                      </div>
                      <div className="mt-3 text-sm font-semibold text-slate-600 mb-1.5">Không có trong đó? Gõ tên tiếng Việt:</div>
                      <NameIt onPick={(found, typed) => named(i, found, typed)} />
                      {i.typed && !i.pickedWord && <div className="mt-1"><Note tone="amber">Đã ghi nhận “{i.typed}” – đội ngũ sẽ bổ sung từ này</Note></div>}
                      <div className="flex flex-wrap justify-center items-center gap-1.5 mt-2">
                        <Button size="small" danger type={i.notObject ? 'primary' : 'default'} onClick={() => notObject(i)}>
                          Không phải đồ vật
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex flex-col">
                  <Tooltip title="Nhận diện đúng">
                    <Button type="text" aria-label="Nhận diện đúng" aria-pressed={i.feedback === 'correct'} icon={<LikeOutlined className={i.feedback === 'correct' ? 'text-emerald-600' : ''} />}
                      onClick={() => (i.feedback === 'correct' ? update(i.id, { feedback: 'unknown' }) : pick(i, i.label))} />
                  </Tooltip>
                  <Tooltip title="Nhận diện sai">
                    <Button type="text" aria-label="Nhận diện sai" aria-pressed={i.feedback === 'wrong'} icon={<DislikeOutlined className={i.feedback === 'wrong' ? 'text-red-500' : ''} />}
                      onClick={() => update(i.id, { feedback: i.feedback === 'wrong' ? 'unknown' : 'wrong', selected: false, picked: undefined, pickedCard: undefined, notObject: false })} />
                  </Tooltip>
                </div>
              </div>
              )
            })}
            {result && !result.confirmed && (
              <div className="lp-card p-4 flex flex-col items-center gap-2">
                <div className="font-semibold text-slate-700 flex items-center gap-1.5"><PlusOutlined /> Máy bỏ sót đồ vật? Gõ tên để thêm</div>
                {added.map((a, k) => (
                  <div key={k} className="w-full flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2">
                    <div className="flex-1">
                      {a.found?.card.target ? <TargetWord target={a.found.card.target} size="md" /> : <span className="font-semibold">{a.typed}</span>}
                      <div className="text-sm text-slate-500">{a.found ? a.found.card.meaning_vi : 'Chưa có trong từ điển – đã ghi nhận để bổ sung'}</div>
                    </div>
                    <Button type="text" size="small" aria-label="Bỏ" icon={<CloseOutlined />} onClick={() => setAdded(added.filter((_, j) => j !== k))} />
                  </div>
                ))}
                {added.length < 5 && <NameIt key={added.length} placeholder="VD: cái ly, quả bơ…" onPick={(found, typed) => setAdded([...added, { found, typed }])} />}
              </div>
            )}
            {result && (result.items.length > 0 || added.length > 0) && (
              <Button type="primary" size="large" loading={saving} disabled={result.confirmed} onClick={save}>
                {result.confirmed ? 'Đã lưu vào thư viện'
                  : `Lưu ${result.items.filter((x) => x.selected).length + added.filter((a) => a.found && !a.found.card.personal).length} từ đã chọn`}
              </Button>
            )}
            {result?.confirmed && file && !isKid && (result.items as Item[]).some((x) => x.selected && shownCard(x)) && (
              <SharePhoto file={file} detectionId={result.id}
                cards={(result.items as Item[]).filter((x) => x.selected).map(shownCard).filter((c): c is WordCard => !!c)} />
            )}
            {result?.confirmed && result.items.some((x) => x.selected) && (
              <PhotoDialogue detectionId={result.id}
                locale={result.items.map(shownCard).find((c) => c?.target)?.target?.tts_locale ?? ''} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
