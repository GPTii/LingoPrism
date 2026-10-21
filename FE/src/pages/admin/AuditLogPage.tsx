import { useQuery } from '@tanstack/react-query'
import { Card, Input, Select, Table, Tag } from 'antd'
import dayjs from 'dayjs'
import { useState } from 'react'
import { api } from '../../api/client'
import type { Paginated } from '../../api/types'

interface AuditLog {
  id: number
  actor_email: string
  actor_role: 'admin' | 'staff'
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string
  resource: string
  object_id: string
  status_code: number
  fields: string[]
  ip: string | null
  created_at: string
}

const METHOD = {
  POST: { label: 'Tạo / thực hiện', color: 'green' },
  PUT: { label: 'Sửa', color: 'blue' },
  PATCH: { label: 'Sửa', color: 'blue' },
  DELETE: { label: 'Xoá', color: 'red' },
} as const

/** Nhật ký thao tác (FEATURES 13.12): every change an admin or staff member made, newest first. */
export default function AuditLogPage() {
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [method, setMethod] = useState<string | undefined>()
  const logs = useQuery({
    queryKey: ['audit-logs', page, q, method],
    queryFn: () => api.get<Paginated<AuditLog>>('/admin/audit-logs/', { params: { page, q: q || undefined, method } }).then((r) => r.data),
  })

  return (
    <Card title="Nhật ký thao tác"
      extra={
        <div className="flex flex-wrap gap-2">
          <Input.Search allowClear placeholder="Email hoặc đường dẫn" style={{ width: 240 }} onSearch={(v) => { setQ(v); setPage(1) }} />
          <Select allowClear placeholder="Loại thao tác" style={{ width: 150 }} value={method} onChange={(v) => { setMethod(v); setPage(1) }}
            options={[{ value: 'POST', label: 'Tạo / thực hiện' }, { value: 'PATCH', label: 'Sửa' }, { value: 'DELETE', label: 'Xoá' }]} />
        </div>
      }>
      <p className="text-slate-500 mt-0">
        Mọi thay đổi admin và staff thực hiện qua hệ thống đều được ghi lại. Chỉ lưu <b>tên</b> các trường đã gửi, không lưu nội dung, nên mật khẩu hay tin nhắn không bao giờ nằm trong nhật ký.
      </p>
      <Table<AuditLog> rowKey="id" size="middle" loading={logs.isLoading} dataSource={logs.data?.results}
        pagination={{ current: page, total: logs.data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        columns={[
          { title: 'Thời gian', dataIndex: 'created_at', width: 150, render: (v: string) => <span className="num">{dayjs(v).format('HH:mm:ss DD/MM/YYYY')}</span> },
          { title: 'Người thực hiện', dataIndex: 'actor_email', render: (v: string, r) => <span>{v} <Tag className="ml-1">{r.actor_role === 'admin' ? 'Admin' : 'Staff'}</Tag></span> },
          { title: 'Thao tác', dataIndex: 'method', width: 130, render: (m: AuditLog['method']) => <Tag color={METHOD[m]?.color}>{METHOD[m]?.label ?? m}</Tag> },
          { title: 'Đối tượng', dataIndex: 'resource', render: (v: string, r) => <span className="font-medium">{v}{r.object_id && <span className="text-slate-500"> #{r.object_id}</span>}</span> },
          { title: 'Trường đã gửi', dataIndex: 'fields', render: (f: string[]) => <span className="text-slate-500 text-xs">{f.join(', ') || '—'}</span> },
          { title: 'IP', dataIndex: 'ip', width: 130, render: (v: string | null) => <span className="num text-slate-500">{v ?? '—'}</span> },
        ]} />
    </Card>
  )
}
