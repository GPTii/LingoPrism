import { App, Button, Form, Input, Modal, Select } from 'antd'
import { FlagOutlined, PlusOutlined, CheckOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { vocabApi, type WordCard } from '../api/vocab'
import { errorMessage } from '../api/client'
import TargetWord, { langTag } from './TargetWord'
import { TokenLine } from './SentenceView'
import WordPicture from './WordPicture'
import { LEVEL_COLORS } from '../api/levels'

const STATUS: Record<string, { label: string; className: string }> = {
  new: { label: 'Chưa học', className: 'text-slate-500' },
  learning: { label: 'Đang học', className: 'text-brand-600' },
  mastered: { label: 'Đã thuộc', className: 'text-emerald-600' },
}

const REASONS = [
  { value: 'wrong_character', label: 'Sai mặt chữ' },
  { value: 'wrong_pronunciation', label: 'Sai phiên âm / phát âm' },
  { value: 'wrong_meaning', label: 'Sai nghĩa' },
  { value: 'wrong_example', label: 'Câu ví dụ sai' },
  { value: 'wrong_image', label: 'Ảnh không đúng' },
  { value: 'other', label: 'Khác' },
]

export function ReportButton({ card }: { card: WordCard }) {
  const { message } = App.useApp()
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm()
  const submit = async () => {
    const v = await form.validateFields()
    try {
      await vocabApi.report(card.id, card.target?.id, v.reason, v.details ?? '')
      message.success('Cảm ơn bạn! Đội ngũ sẽ kiểm tra sớm nhất.')
      setOpen(false)
      form.resetFields()
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  return (
    <>
      <Button size="small" type="text" icon={<FlagOutlined />} className="!text-slate-500" onClick={(e) => { e.stopPropagation(); setOpen(true) }}>Báo lỗi</Button>
      <Modal title="Báo lỗi từ vựng" open={open} onOk={submit} onCancel={() => setOpen(false)} okText="Gửi báo lỗi" cancelText="Huỷ">
        <Form form={form} layout="vertical">
          <Form.Item name="reason" label="Lỗi gì?" rules={[{ required: true, message: 'Chọn loại lỗi' }]}>
            <Select options={REASONS} />
          </Form.Item>
          <Form.Item name="details" label="Mô tả (không bắt buộc)">
            <Input.TextArea rows={3} maxLength={500} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default function WordCardView({ card, topicId }: { card: WordCard; topicId?: number }) {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [saving, setSaving] = useState(false)
  if (!card.target) return null

  const add = async () => {
    setSaving(true)
    try {
      await vocabApi.addWord(card.id, 'topic', topicId)
      message.success('Đã lưu vào thư viện')
      queryClient.invalidateQueries({ queryKey: ['topic-words'] })
      queryClient.invalidateQueries({ queryKey: ['summary'] })
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="relative lp-card p-4 flex flex-col gap-3 transition-colors hover:border-[var(--line-strong)]">
      {card.level && (
        <span className="absolute top-3 left-3 z-10 rounded-md px-1.5 py-0.5 text-[11px] font-bold text-white" style={{ background: LEVEL_COLORS[card.level - 1] }}>
          Cấp {card.level}
        </span>
      )}
      <div className="h-28 rounded-xl bg-slate-50 flex items-center justify-center overflow-hidden">
        <WordPicture image={card.image} emoji={card.emoji || '🖼️'} credit={card.image_credit} source={card.image_source} alt={card.meaning_vi} height="h-28" />
      </div>
      <TargetWord target={card.target} size="md" />
      <div className="text-center">
        <div className="font-semibold text-slate-700">{card.meaning_vi}</div>
        {card.english && <div className="text-xs text-slate-500">{card.english}</div>}
      </div>
      {card.examples[0] && (
        <div className="text-sm text-slate-600 bg-slate-50 rounded-lg p-2">
          {card.examples[0].tokens?.length ? (
            <TokenLine tokens={card.examples[0].tokens} language={card.target.language} highlight={card.examples[0].target_tokens} size="text-base" />
          ) : (
            <div lang={langTag(card.target.language)}>{card.examples[0].text}</div>
          )}
          <div className="text-slate-500">{card.examples[0].translation_vi || card.examples[0].translation_en}</div>
        </div>
      )}
      {card.personal?.recall != null && (() => {
        const r = card.personal.recall
        const color = r >= 0.85 ? '#10c79a' : r >= 0.6 ? '#ffb020' : '#ff6b81'
        return (
          <div title="Ước tính theo FSRS: khả năng bạn còn nhớ từ này hôm nay">
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>Nhớ khoảng</span>
              <span className="num font-semibold text-slate-700">{Math.round(r * 100)}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${Math.round(r * 100)}%`, background: color }} />
            </div>
          </div>
        )
      })()}
      <div className="flex items-center justify-between mt-auto">
        {card.personal ? (
          <span className={`inline-flex items-center gap-1 text-sm font-semibold ${STATUS[card.personal.status].className}`}>
            <CheckOutlined /> {STATUS[card.personal.status].label}
          </span>
        ) : (
          <Button size="small" type="primary" icon={<PlusOutlined />} loading={saving} onClick={add}>Lưu từ</Button>
        )}
        <ReportButton card={card} />
      </div>
    </div>
  )
}
