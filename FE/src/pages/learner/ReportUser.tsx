import { FlagOutlined } from '@ant-design/icons'
import { App, Button, Checkbox, Input, Modal, Radio } from 'antd'
import { useState } from 'react'
import { communityApi } from '../../api/app'
import { errorMessage } from '../../api/client'

const REASONS = [
  { value: 'harassment', label: 'Quấy rối, đe doạ, xúc phạm' },
  { value: 'spam', label: 'Spam, lừa đảo, xin tiền' },
  { value: 'inappropriate', label: 'Nội dung không phù hợp' },
  { value: 'impersonation', label: 'Giả mạo người khác' },
  { value: 'other', label: 'Khác' },
]

/** "Báo cáo" a learner to the moderators. From a conversation (`threadId`) the server keeps its last messages as
 * evidence; "chặn luôn" also blocks them at once, which is what someone being harassed usually wants. */
export function ReportUserButton({ userId, name, threadId, blocked, onDone, compact }: {
  userId: number; name: string; threadId?: number; blocked?: boolean; onDone?: () => void; compact?: boolean
}) {
  const { message } = App.useApp()
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState('harassment')
  const [details, setDetails] = useState('')
  const [block, setBlock] = useState(!blocked)
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    setBusy(true)
    try {
      await communityApi.reportUser(userId, { reason, details, block: block && !blocked, thread: threadId })
      message.success(block && !blocked ? `Đã gửi báo cáo và chặn ${name}.` : 'Đã gửi báo cáo. Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.')
      setOpen(false)
      setDetails('')
      onDone?.()
    } catch (e) {
      message.error(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      {compact ? (
        <Button type="text" icon={<FlagOutlined />} onClick={() => setOpen(true)} aria-label={`Báo cáo ${name}`} title="Báo cáo" />
      ) : (
        <Button size="large" type="text" icon={<FlagOutlined />} onClick={() => setOpen(true)}>Báo cáo</Button>
      )}
      <Modal open={open} title={`Báo cáo ${name}`} onCancel={() => setOpen(false)} onOk={submit} confirmLoading={busy}
        okText="Gửi báo cáo" cancelText="Huỷ" okButtonProps={{ danger: true }} destroyOnHidden>
        <div className="flex flex-col gap-3">
          <p className="text-slate-500 m-0">
            {threadId
              ? 'Đội ngũ kiểm duyệt sẽ xem các tin nhắn gần đây trong cuộc trò chuyện này. Người kia không biết ai đã báo cáo.'
              : 'Người kia không biết ai đã báo cáo.'}
          </p>
          <Radio.Group value={reason} onChange={(e) => setReason(e.target.value)} className="flex! flex-col gap-2"
            options={REASONS} />
          <Input.TextArea value={details} onChange={(e) => setDetails(e.target.value)} maxLength={500} rows={3}
            placeholder={reason === 'other' ? 'Mô tả chuyện gì đã xảy ra (bắt buộc)' : 'Thêm chi tiết (không bắt buộc)'} />
          {!blocked && (
            <Checkbox checked={block} onChange={(e) => setBlock(e.target.checked)}>
              Chặn {name} luôn: hai bạn không nhắn tin và không thấy bài của nhau nữa
            </Checkbox>
          )}
        </div>
      </Modal>
    </>
  )
}
