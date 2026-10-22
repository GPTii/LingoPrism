import { Button, Modal } from 'antd'
import { LeftOutlined, RightOutlined, SoundOutlined, SwapOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import type { WordCard } from '../api/vocab'
import { speak } from '../lib/speech'
import { langTag } from './TargetWord'

/**
 * Flashcards for a set of words, as in the app: the word (with its picture) on the front, the meaning and an
 * example on the back. Tap / Space flips, ← → move, the speaker reads it aloud.
 */
export default function Flashcards({ open, onClose, cards, title }: { open: boolean; onClose: () => void; cards: WordCard[]; title: string }) {
  const [deck, setDeck] = useState<WordCard[]>([])
  const [i, setI] = useState(0)
  const [back, setBack] = useState(false)

  useEffect(() => {
    if (open) {
      setDeck(cards.filter((c) => c.target))
      setI(0)
      setBack(false)
    }
  }, [open, cards])

  const card = deck[i]
  const go = (d: number) => {
    setBack(false)
    setI((n) => Math.min(deck.length - 1, Math.max(0, n + d)))
  }
  const say = () => card?.target && speak(card.target.text, card.target.tts_locale)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') go(1)
      else if (e.key === 'ArrowLeft') go(-1)
      else if (e.key === ' ') { e.preventDefault(); setBack((b) => !b) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const shuffle = () => {
    setDeck((d) => [...d].sort(() => Math.random() - 0.5))
    setI(0)
    setBack(false)
  }
  const reading = card?.target ? card.target.ipa ? `/${card.target.ipa}/` : card.target.pinyin ?? '' : ''
  const example = card?.examples[0]

  return (
    <Modal open={open} onCancel={onClose} footer={null} title={`Flashcard · ${title}`} width={520} destroyOnHidden>
      {!card ? <p className="text-slate-500">Chủ đề chưa có từ nào để ôn.</p> : (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span className="num">{i + 1} / {deck.length}</span>
            <Button size="small" type="text" icon={<SwapOutlined />} onClick={shuffle}>Trộn thẻ</Button>
          </div>
          <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${((i + 1) / deck.length) * 100}%` }} />
          </div>
          <button type="button" onClick={() => setBack((b) => !b)} aria-label={back ? 'Xem mặt trước' : 'Lật thẻ'}
            className="btn-3d cursor-pointer min-h-72 p-6 flex flex-col items-center justify-center gap-3 text-center">
            {!back ? (
              <>
                {card.image ? <img src={card.image} alt="" className="h-36 w-full max-w-72 object-cover rounded-xl" />
                  : card.emoji && <span className="text-7xl">{card.emoji}</span>}
                <span lang={langTag(card.target!.language)} className="text-4xl font-extrabold text-slate-900">{card.target!.text}</span>
                {reading && <span className="text-slate-500">{reading}</span>}
                <span className="text-xs text-slate-400 mt-1">Bấm để lật thẻ</span>
              </>
            ) : (
              <>
                <span className="text-3xl font-extrabold text-brand-700">{card.meaning_vi}</span>
                {card.english && card.target!.language !== 'en' && <span className="text-slate-500">{card.english}</span>}
                {example && (
                  <span className="mt-2 text-slate-700">
                    <span lang={langTag(card.target!.language)} className="block font-semibold">{example.text}</span>
                    {example.translation_vi && <span className="block text-sm text-slate-500 mt-1">{example.translation_vi}</span>}
                  </span>
                )}
              </>
            )}
          </button>
          <div className="flex items-center gap-2">
            <Button size="large" icon={<LeftOutlined />} disabled={i === 0} onClick={() => go(-1)} aria-label="Thẻ trước" />
            <Button size="large" icon={<SoundOutlined />} onClick={say} className="flex-1">Nghe</Button>
            {i < deck.length - 1
              ? <Button size="large" type="primary" icon={<RightOutlined />} iconPosition="end" onClick={() => go(1)} className="flex-1">Thẻ tiếp</Button>
              : <Button size="large" type="primary" onClick={onClose} className="flex-1">Xong</Button>}
          </div>
        </div>
      )}
    </Modal>
  )
}
