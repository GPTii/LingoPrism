import { useQuery } from '@tanstack/react-query'
import { Button, Progress, Skeleton } from 'antd'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { vocabApi } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import SpeakCheck from '../../components/SpeakCheck'
import TargetWord from '../../components/TargetWord'
import WordPicture from '../../components/WordPicture'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader } from '../../components/ui'
import { canRecognise } from '../../lib/pronounce'

const ROUND = 10

/** Luyện phát âm: ten words from my library, one at a time – listen, say it, see the score. */
export default function SpeakPage() {
  const user = useAuth((s) => s.user)
  const words = useQuery({ queryKey: ['my-words', user?.active_language, user?.zh_script, 'speak'], queryFn: () => vocabApi.myWords({ page_size: 50 }) })
  const [round, setRound] = useState(0)
  const [index, setIndex] = useState(0)
  const [scores, setScores] = useState<Record<number, number>>({})
  // a shuffled round of words that have a spoken form in the language being learned
  const deck = useMemo(() => {
    const list = (words.data?.results ?? []).filter((c) => c.target?.tts_locale)
    return [...list].sort(() => Math.random() - 0.5).slice(0, ROUND)
  }, [words.data, round]) // eslint-disable-line react-hooks/exhaustive-deps
  const card = deck[index]
  const done = deck.length > 0 && index >= deck.length
  const avg = Object.values(scores).length ? Math.round(Object.values(scores).reduce((a, b) => a + b, 0) / Object.values(scores).length) : 0

  const header = <PageHeader title="Luyện phát âm" description="Nghe giọng mẫu, đọc theo vào micro, máy chấm điểm và chỉ ra phần đọc chưa đúng." />
  if (!canRecognise()) {
    return (
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {header}
        <div className="lp-card"><EmptyState art={<Prismo mood="think" size={90} />} title="Trình duyệt này chưa nghe được giọng nói"
          description="Hãy mở LingoPrism bằng Google Chrome hoặc Microsoft Edge (máy tính hoặc điện thoại Android) để luyện phát âm." /></div>
      </div>
    )
  }
  if (words.isLoading) return <div className="max-w-3xl mx-auto">{header}<Skeleton active className="mt-6" /></div>
  if (!deck.length) {
    return (
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {header}
        <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={90} />} title="Thư viện của bạn chưa có từ nào"
          description="Lưu vài từ từ một chủ đề hoặc chụp ảnh một đồ vật, rồi quay lại luyện phát âm."
          action={<Link to="/vocab"><Button type="primary">Chọn chủ đề</Button></Link>} /></div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      {header}
      <div className="flex items-center gap-3">
        <Progress percent={Math.round((Math.min(index, deck.length) / deck.length) * 100)} showInfo={false} className="flex-1 m-0" />
        <span className="num text-sm font-bold text-slate-500">{Math.min(index + 1, deck.length)}/{deck.length}</span>
      </div>
      {done ? (
        <div className="lp-card p-8 flex flex-col items-center text-center gap-3 animate-rise">
          <Prismo mood={avg >= 80 ? 'celebrate' : avg >= 50 ? 'happy' : 'think'} size={130} />
          <h2 className="text-2xl font-extrabold text-slate-900 m-0">Điểm phát âm trung bình: <span className="num">{avg}</span>/100</h2>
          <p className="text-slate-500 m-0">{avg >= 80 ? 'Rất tốt! Giọng bạn đã rõ ràng.' : 'Nghe lại giọng mẫu thật chậm rồi thử lại, nhất là những từ có phần gạch đỏ.'}</p>
          <div className="flex gap-3 mt-2">
            <Link to="/"><Button size="large">Về trang chủ</Button></Link>
            <Button size="large" type="primary" onClick={() => { setRound(round + 1); setIndex(0); setScores({}) }}>Luyện thêm 10 từ</Button>
          </div>
        </div>
      ) : card?.target && (
        <div key={card.id} className="lp-card p-6 sm:p-8 flex flex-col items-center gap-5 animate-rise">
          <WordPicture image={card.image} emoji={card.emoji} credit={card.image_credit} source={card.image_source} alt={card.meaning_vi} height="h-36" />
          <TargetWord target={card.target} size="xl" />
          <div className="text-slate-600">{card.meaning_vi}</div>
          <SpeakCheck text={card.target.text} language={card.target.language} locale={card.target.tts_locale}
            onScore={(s) => setScores((m) => ({ ...m, [card.id]: Math.max(m[card.id] ?? 0, s.score) }))} />
          <Button size="large" type={scores[card.id] != null ? 'primary' : 'default'} onClick={() => setIndex(index + 1)}>
            {scores[card.id] != null ? 'Từ tiếp theo' : 'Bỏ qua từ này'}
          </Button>
        </div>
      )}
    </div>
  )
}
