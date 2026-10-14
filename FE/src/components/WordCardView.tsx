import { App, Button, Form, Input, Modal, Select, Tag } from 'antd'
import { FlagOutlined, PlusOutlined, CheckOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { vocabApi, type WordCard } from '../api/vocab'
import { errorMessage } from '../api/client'
import TargetWord, { langTag } from './TargetWord'

const STATUS: Record<string, { label: string; color: string }> = {
  new: { label: 'Chưa học', color: 'default' },
  learning: { label: 'Đang học', color: 'blue' },
  mastered: { label: 'Đã thuộc', color: 'green' },
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
      <Button size="small" type="text" icon={<FlagOutlined />} onClick={(e) => { e.stopPropagation(); setOpen(true) }}>Báo lỗi</Button>
      <Modal title="Báo lỗi từ vựng" open={open} onOk={submit} onCancel={() => setOpen(false)} okText="Gửi" cancelText="Huỷ">
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
    <div className="rounded-2xl bg-white border border-slate-200 p-4 flex flex-col gap-3 hover:shadow-md transition">
      <div className="h-28 rounded-xl bg-brand-50 flex items-center justify-center overflow-hidden">
        {card.image ? <img src={card.image} alt={card.meaning_vi} className="h-full object-contain" /> : <span className="text-4xl">🔺</span>}
      </div>
      <TargetWord target={card.target} size="md" />
      <div className="text-center">
        <div className="font-medium text-slate-700">{card.meaning_vi}</div>
        {card.english && <div className="text-xs text-slate-400">{card.english}</div>}
      </div>
      {card.examples[0] && (
        <div className="text-sm text-slate-600 bg-slate-50 rounded-lg p-2">
          <div lang={langTag(card.target.language)}>{card.examples[0].text}</div>
          <div className="text-slate-400">{card.examples[0].translation_vi}</div>
        </div>
      )}
      <div className="flex items-center justify-between mt-auto">
        {card.personal ? (
          <Tag color={STATUS[card.personal.status].color} icon={<CheckOutlined />}>{STATUS[card.personal.status].label}</Tag>
        ) : (
          <Button size="small" type="primary" ghost icon={<PlusOutlined />} loading={saving} onClick={add}>Lưu</Button>
        )}
        <ReportButton card={card} />
      </div>
    </div>
  )
}
