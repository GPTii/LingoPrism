import { useInfiniteQuery } from '@tanstack/react-query'
import { Button, Skeleton } from 'antd'
import { CameraOutlined, CheckOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { Link } from 'react-router-dom'
import { learnApi, type DetectedItem, type DetectionResult } from '../../api/app'
import { langTag } from '../../components/TargetWord'
import { Prismo } from '../../components/brand/Brand'
import PhotoDialogue from '../../components/PhotoDialogue'
import { EmptyState, PageHeader } from '../../components/ui'

/** The word an object stands for: the learner's correction first, then the model's answer. */
const wordOf = (i: DetectedItem) => i.corrected_card ?? i.card

function Shot({ d }: { d: DetectionResult }) {
  const items = d.items.filter((i) => !(i.feedback === 'wrong' && !i.corrected_label))
  // one chip per word: three slices of watermelon are one word, ×3
  const words = Object.values(items.reduce<Record<string, { key: string; item: DetectedItem; n: number; saved: boolean }>>((acc, i) => {
    const key = i.corrected_label || i.label
    acc[key] ??= { key, item: i, n: 0, saved: false }
    acc[key].n += 1
    acc[key].saved ||= i.selected
    return acc
  }, {}))
  return (
    <article className="lp-card overflow-hidden flex flex-col break-inside-avoid mb-4">
      {/* the whole photo, never cropped, so the boxes (fractions of the photo) land on their objects */}
      <div className="bg-slate-100">
        {d.image ? (
          <div className="relative">
            <img src={d.image} alt="" loading="lazy" className="block w-full h-auto" />
            {items.map((i) => i.bbox.length === 4 && (
              <span key={i.id} className="absolute border-2 border-[#10c79a] rounded"
                style={{ left: `${i.bbox[0] * 100}%`, top: `${i.bbox[1] * 100}%`, width: `${(i.bbox[2] - i.bbox[0]) * 100}%`, height: `${(i.bbox[3] - i.bbox[1]) * 100}%` }} />
            ))}
          </div>
        ) : (
          <div className="text-slate-500 text-sm px-4 py-10 text-center">Ảnh không được lưu (nhận diện trên điện thoại)</div>
        )}
      </div>
      <div className="p-4 flex flex-col gap-3 flex-1">
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span className="num">{dayjs(d.created_at).format('HH:mm · DD/MM/YYYY')}</span>
          {d.confirmed && <span className="font-semibold text-emerald-600"><CheckOutlined /> Đã lưu từ</span>}
        </div>
        {words.length ? (
          <ul className="m-0 p-0 list-none flex flex-wrap gap-2">
            {words.map(({ key, item: i, n, saved }) => {
              const c = wordOf(i)
              return (
                <li key={key} className={`rounded-lg px-2.5 py-1 text-sm ${saved ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-700'}`}>
                  {c?.target ? <b lang={langTag(c.target.language)} className="font-semibold">{c.target.text}</b> : <b className="font-semibold">{i.corrected_label || i.label}</b>}
                  {c?.meaning_vi && <span> · {c.meaning_vi}</span>}
                  {n > 1 && <span className="num opacity-70"> ×{n}</span>}
                </li>
              )
            })}
          </ul>
        ) : <p className="m-0 text-sm text-slate-500">Không có đồ vật nào trong ảnh này.</p>}
        {d.confirmed && words.some((w) => w.saved) && (
          <PhotoDialogue detectionId={d.id} locale={words.map((w) => wordOf(w.item)?.target?.tts_locale).find(Boolean) ?? ''} />
        )}
      </div>
    </article>
  )
}

/** Lịch sử ảnh đã nhận diện: every photo with the words found in it (web and phone alike). */
export default function DetectionHistoryPage() {
  const q = useInfiniteQuery({
    queryKey: ['detections'],
    queryFn: ({ pageParam }) => learnApi.detections(pageParam),
    initialPageParam: 1,
    getNextPageParam: (last, pages) => (last.next ? pages.length + 1 : undefined),
  })
  const shots = q.data?.pages.flatMap((p) => p.results) ?? []
  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <PageHeader back={{ to: '/camera', label: 'Chụp ảnh' }} title="Lịch sử ảnh"
        description="Những ảnh bạn đã chụp và từ vựng tìm thấy trong đó, gồm cả ảnh chụp trên điện thoại."
        actions={<Link to="/camera"><Button type="primary" size="large" icon={<CameraOutlined />}>Chụp ảnh mới</Button></Link>} />
      {q.isLoading ? <Skeleton active /> : shots.length ? (
        <>
          {/* masonry: every photo at its own shape */}
          <div className="columns-1 sm:columns-2 lg:columns-3 gap-4">
            {shots.map((d) => <Shot key={d.id} d={d} />)}
          </div>
          {q.hasNextPage && (
            <div className="flex justify-center">
              <Button size="large" loading={q.isFetchingNextPage} onClick={() => q.fetchNextPage()}>Xem ảnh cũ hơn</Button>
            </div>
          )}
        </>
      ) : (
        <div className="lp-card">
          <EmptyState art={<Prismo mood="wow" size={88} />} title="Bạn chưa chụp ảnh nào"
            description="Chụp một đồ vật quanh bạn để học tên của nó bằng ba thứ tiếng."
            action={<Link to="/camera"><Button type="primary">Chụp ảnh đầu tiên</Button></Link>} />
        </div>
      )}
    </div>
  )
}
