import { App, Card, Input, Select, Table, Tag } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import dayjs from 'dayjs'
import { api, errorMessage } from '../../api/client'
import type { Paginated, Role, User } from '../../api/types'
import { useAuth } from '../../auth/store'

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Quản trị viên' },
  { value: 'staff', label: 'Giáo viên / Hỗ trợ' },
  { value: 'learner', label: 'Học viên' },
]

export default function UsersPage() {
  const { message } = App.useApp()
  const me = useAuth((s) => s.user)
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | undefined>()

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', page, search, role],
    queryFn: () =>
      api.get<Paginated<User>>('/admin/users/', { params: { page, search: search || undefined, role } }).then((r) => r.data),
  })

  const update = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<User> }) => api.patch(`/admin/users/${id}/`, patch),
    onSuccess: () => {
      message.success('Đã cập nhật')
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (e) => message.error(errorMessage(e)),
  })

  const isAdmin = me?.role === 'admin'

  return (
    <Card
      title="Người dùng"
      extra={
        <div className="flex gap-2">
          <Select allowClear placeholder="Vai trò" options={ROLE_OPTIONS} value={role} onChange={(v) => { setRole(v); setPage(1) }} style={{ width: 170 }} />
          <Input.Search placeholder="Tìm email, tên" allowClear onSearch={(v) => { setSearch(v); setPage(1) }} style={{ width: 240 }} />
        </div>
      }
    >
      <Table<User>
        rowKey="id"
        loading={isLoading}
        dataSource={data?.results}
        pagination={{ current: page, total: data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        columns={[
          { title: 'Email', dataIndex: 'email' },
          { title: 'Tên', dataIndex: 'display_name' },
          { title: 'Đối tượng', dataIndex: 'learner_type', render: (v) => (v === 'kid' ? <Tag color="orange">Trẻ em</Tag> : <Tag>Người lớn</Tag>) },
          {
            title: 'Vai trò',
            dataIndex: 'role',
            render: (v: Role, row) => (
              <Select
                size="small"
                value={v}
                options={ROLE_OPTIONS}
                disabled={!isAdmin || row.id === me?.id}
                onChange={(roleValue) => update.mutate({ id: row.id, patch: { role: roleValue } })}
                style={{ width: 160 }}
              />
            ),
          },
          {
            title: 'Trạng thái',
            dataIndex: 'status',
            render: (v: User['status'], row) => (
              <Select
                size="small"
                value={v}
                disabled={!isAdmin || row.id === me?.id}
                options={[{ value: 'active', label: 'Hoạt động' }, { value: 'locked', label: 'Bị khóa' }]}
                onChange={(status) => update.mutate({ id: row.id, patch: { status } })}
                style={{ width: 120 }}
              />
            ),
          },
          { title: 'Ngày tạo', dataIndex: 'created_at', render: (v) => dayjs(v).format('DD/MM/YYYY') },
        ]}
      />
    </Card>
  )
}
