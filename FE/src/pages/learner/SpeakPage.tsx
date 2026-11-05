import { useQuery } from '@tanstack/react-query'
import { Button, Modal, Progress, Segmented, Skeleton } from 'antd'
import { LineChartOutlined, SoundOutlined } from '@ant-design/icons'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { speechApi } from '../../api/speech'
import { vocabApi, type WordCard } from '../../api/vocab'
import { useAuth } from '../../auth/store'
import PronunciationCheck from '../../components/PronunciationCheck'
import SpeakCheck from '../../components/SpeakCheck'
import TargetWord, { langTag } from '../../components/TargetWord'
import WordPicture from '../../components/WordPicture'
import { Prismo } from '../../components/brand/Brand'
import { EmptyState, PageHeader } from '../../components/ui'
import { canRecognise } from '../../lib/pronounce'
import { canRecord } from '../../lib/recordWav'
import { speak } from '../../lib/speech'

const ROUND = 10
const sentenceOf = (c: WordCard) => c.examples.find((e) => e.id && e.text.length <= 120)

/**
 * Luyện phát âm: ten words – or their example sentences – from my library, one at a time: listen, say it, see the
 * score. When the server scores recordings (BE apps.speech) each sound and tone is checked; otherwise the browser's
 * speech recogniser compares the words.
 */
export default function SpeakPage() {
  const user = useAuth((s) => s.user)
  const words = useQuery({ queryKey: ['my-words', user?.active_language, user?.zh_script, 'speak'], queryFn: () => vocabApi.myWords({ page_size: 50 }) })
  const status = useQuery({ queryKey: ['speech-status'], queryFn: speechApi.status, staleTime: 10 * 60_000, retry: false })
  const detailed = !!status.data?.enabled && canRecord()
  const [sentences, setSentences] = useState(false)
  const [round, setRound] = useState(0)
  const [index, setIndex] = useState(0)
  const [scores, setScores] = useState<Record<number, number>>({})
  const [showProgress, setShowProgress] = useState(false)
  // a shuffled round of words that have a spoken form in the language being learned
  const deck = useMemo(() => {
    const list = (words.data?.results ?? []).filter((c) => c.target?.tts_locale && (!sentences || sentenceOf(c)))
    return [...list].sort(() => Math.random() - 0.5).slice(0, ROUND)
  }, [words.data, round, sentences]) // eslint-disable-line react-hooks/exhaustive-deps
  const card = deck[index]
  const sentence = card && sentences ? sentenceOf(card) : undefined
  const done = deck.length > 0 && index >= deck.length
  const avg = Object.values(scores).length ? Math.round(Object.values(scores).reduce((a, b) => a + b, 0) / Object.values(scores).length) : 0
  const restart = () => { setRound(round + 1); setIndex(0); setScores({}) }
  const keep = (id: number) => (s: number) => setScores((m) => ({ ...m, [id]: Math.max(m[id] ?? 0, s) }))

  const header = (
    <PageHeader title="Luyện phát âm"
      description={detailed ? 'Đọc to vào micro, máy chấm từng âm và thanh điệu, chỉ ra âm nào sai và cách sửa.' : 'Nghe giọng mẫu, đọc theo vào micro, máy chấm điểm và chỉ ra phần đọc chưa đúng.'}
      actions={detailed ? <Button icon={<LineChartOutlined />} onClick={() => setShowProgress(true)}>Tiến bộ</Button> : undefined} />
  )
  if (status.isLoading) return <div className="max-w-3xl mx-auto"><Skeleton active className="mt-6" /></div>
  if (!detailed && !canRecognise()) {
    return (
      <div className="max-w-3xl mx-auto flex flex-col gap-6">
        {header}
        <div className="lp-card"><EmptyState art={<Prismo mood="think" size={90} />} title="Trình duyệt này chưa nghe được giọng nói"
          description="Hãy mở LingoPrism bằng Google Chrome hoặc Microsoft Edge (máy tính hoặc điện thoại Android) để luyện phát âm." /></div>
      </div>
    )
  }
  if (words.isLoading) return <div className="max-w-3xl mx-auto">{header}<Skeleton active className="mt-6" /></div>

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      {header}
      {detailed && (
        <Segmented block value={sentences ? 'sentence' : 'word'} onChange={(v) => { setSentences(v === 'sentence'); restart() }}
          options={[{ label: 'Luyện từ', value: 'word' }, { label: 'Luyện câu', value: 'sentence' }]} />
      )}
      {!deck.length ? (
        <div className="lp-card"><EmptyState art={<Prismo mood="wow" size={90} />}
          title={sentences ? 'Các từ trong thư viện chưa có câu ví dụ' : 'Thư viện của bạn chưa có từ nào'}
          description="Lưu thêm từ từ một chủ đề hoặc chụp ảnh một đồ vật, rồi quay lại luyện phát âm."
          action={<Link to="/vocab"><Button type="primary">Chọn chủ đề</Button></Link>} /></div>
      ) : (
        <>
          <div className="flex items-center gap-3">
            <Progress percent={Math.round((Math.min(index, deck.length) / deck.length) * 100)} showInfo={false} className="flex-1 m-0" />
            <span className="num text-sm font-bold text-slate-500">{Math.min(index + 1, deck.length)}/{deck.length}</span>
          </div>
          {done ? (
            <div className="lp-card p-8 flex flex-col items-center text-center gap-3 animate-rise">
              <Prismo mood={avg >= 80 ? 'celebrate' : avg >= 50 ? 'happy' : 'think'} size={130} />
              <h2 className="text-2xl font-extrabold text-slate-900 m-0">Điểm phát âm trung bình: <span className="num">{avg}</span>/100</h2>
              <p className="text-slate-500 m-0">{avg >= 80 ? 'Rất tốt! Giọng bạn đã rõ ràng.' : 'Nghe lại giọng mẫu thật chậm rồi thử lại, nhất là những âm được tô đỏ.'}</p>
              <div className="flex gap-3 mt-2">
                <Link to="/"><Button size="large">Về trang chủ</Button></Link>
                <Button size="large" type="primary" onClick={restart}>Luyện thêm {sentences ? '10 câu' : '10 từ'}</Button>
              </div>
            </div>
          ) : card?.target && (
            <div key={`${card.id}-${sentences}`} className="lp-card p-6 sm:p-8 flex flex-col items-center gap-5 animate-rise">
              <WordPicture image={card.image} emoji={card.emoji} credit={card.image_credit} source={card.image_source} alt={card.meaning_vi} height="h-36" />
              <TargetWord target={card.target} size={sentence ? 'lg' : 'xl'} />
              <div className="text-slate-600">{card.meaning_vi}</div>
              {sentence && (
                <div className="text-center flex flex-col items-center gap-1">
                  <div lang={langTag(card.target.language)} className="text-2xl font-bold text-slate-900">{sentence.text}</div>
                  {sentence.transliteration && <div className="text-slate-500">{sentence.transliteration}</div>}
                  {sentence.translation_vi && <div className="text-slate-400 text-sm">{sentence.translation_vi}</div>}
                  <Button type="link" icon={<SoundOutlined />} onClick={() => speak(sentence.text, card.target!.tts_locale)}>Nghe câu mẫu</Button>
                </div>
              )}
              {detailed ? (
                <PronunciationCheck language={card.target.language} onScore={keep(card.id)}
                  translationId={sentence ? undefined : card.target.id} sentenceId={sentence?.id} />
              ) : (
                <SpeakCheck text={card.target.text} language={card.target.language} locale={card.target.tts_locale}
                  onScore={(s) => keep(card.id)(s.score)} />
              )}
              <Button size="large" type={scores[card.id] != null ? 'primary' : 'default'} onClick={() => setIndex(index + 1)}>
                {scores[card.id] != null ? (sentences ? 'Câu tiếp theo' : 'Từ tiếp theo') : (sentences ? 'Bỏ qua câu này' : 'Bỏ qua từ này')}
              </Button>
            </div>
          )}
        </>
      )}
      <Modal open={showProgress} onCancel={() => setShowProgress(false)} footer={null} title="Tiến bộ phát âm" destroyOnHidden>
        <SpeechProgressPanel />
      </Modal>
    </div>
  )
}

function SpeechProgressPanel() {
  const q = useQuery({ queryKey: ['speech-progress'], queryFn: speechApi.progress })
  if (q.isLoading) return <Skeleton active />
  const p = q.data
  if (!p || !p.attempts) return <EmptyState art={<Prismo mood="think" size={80} />} title="Chưa có lượt luyện nói nào" description="Luyện vài từ, điểm và các âm hay sai sẽ hiện ở đây." />
  const days = p.by_day.slice(-14)
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="text-2xl font-extrabold">Trung bình 7 ngày: <span className="num">{p.average_7d ?? '–'}</span>/100</div>
        <div className="text-slate-500">{p.attempts} lượt trong 60 ngày</div>
      </div>
      <div className="flex items-end gap-1 h-28">
        {days.map((d) => (
          <div key={d.date} title={`${d.date}: ${d.average}/100 (${d.count} lượt)`} className="flex-1 max-w-10 rounded-t bg-blue-400"
            style={{ height: `${Math.max(4, d.average)}%` }} />
        ))}
      </div>
      <div className="font-bold">Âm bạn hay sai</div>
      {p.weak_sounds.map((w) => (
        <div key={w.code + w.expected} className="rounded-xl bg-slate-50 p-3 text-sm">
          <div className="font-bold">{w.heard ? `/${w.expected}/ → /${w.heard}/` : `Thiếu /${w.expected}/`} <span className="text-slate-400 font-normal">· {w.count} lần</span></div>
          <div className="text-slate-600">{w.tip}</div>
        </div>
      ))}
    </div>
  )
}
