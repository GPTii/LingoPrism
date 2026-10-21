import { App, Button, Card, Form, Input, Modal, Popconfirm, Select, Space, Table, Tag } from 'antd'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
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
const ROLE_COLOR: Record<Role, string> = { admin: 'red', staff: 'blue', learner: 'default' }
const LANG_OPTIONS = [
  { value: 'en', label: 'Tiếng Anh' },
  { value: 'zh', label: 'Tiếng Trung' },
  { value: 'vi', label: 'Tiếng Việt' },
]
const LANG_LABEL: Record<string, string> = { en: 'Anh', zh: 'Trung', vi: 'Việt' }

type UserForm = Pick<User, 'email' | 'display_name' | 'role' | 'status' | 'learner_type' | 'active_language' | 'zh_script'> & {
  learning_languages: User['learning_languages']
  password?: string
}

export default function UsersPage() {
  const { message } = App.useApp()
  const me = useAuth((s) => s.user)
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | undefined>()
  const [editing, setEditing] = useState<User | 'new' | null>(null)
  const [form] = Form.useForm<UserForm>()
  const activeLanguage = Form.useWatch('active_language', form)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', page, search, role],
    queryFn: () =>
      api.get<Paginated<User>>('/admin/users/', { params: { page, search: search || undefined, role } }).then((r) => r.data),
  })

  const done = (text: string) => {
    message.success(text)
    queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  }

  const save = useMutation({
    mutationFn: (values: UserForm) => {
      const body = { ...values, password: values.password || undefined }
      return editing === 'new' ? api.post('/admin/users/', body) : api.patch(`/admin/users/${(editing as User).id}/`, body)
    },
    onSuccess: () => {
      done(editing === 'new' ? 'Đã tạo tài khoản' : 'Đã cập nhật')
      setEditing(null)
    },
    onError: (e) => message.error(errorMessage(e)),
  })

  const remove = useMutation({
    mutationFn: (id: number) => api.delete(`/admin/users/${id}/`),
    onSuccess: () => done('Đã xóa tài khoản'),
    onError: (e) => message.error(errorMessage(e)),
  })

  const openForm = (user: User | 'new') => {
    setEditing(user)
    form.resetFields()
    form.setFieldsValue(
      user === 'new'
        ? { role: 'learner', status: 'active', learner_type: 'adult', active_language: 'en', learning_languages: ['en'], zh_script: 'hans' }
        : { ...user, password: '' },
    )
  }

  const isAdmin = me?.role === 'admin'
  const isSelf = editing !== null && editing !== 'new' && editing.id === me?.id

  return (
    <Card
      title="Người dùng"
      extra={
        <div className="flex flex-wrap gap-2">
          <Select allowClear placeholder="Vai trò" options={ROLE_OPTIONS} value={role} onChange={(v) => { setRole(v); setPage(1) }} style={{ width: 170 }} />
          <Input.Search placeholder="Tìm email, tên" allowClear onSearch={(v) => { setSearch(v); setPage(1) }} style={{ width: 240 }} />
          {isAdmin && <Button type="primary" icon={<PlusOutlined />} onClick={() => openForm('new')}>Thêm người dùng</Button>}
        </div>
      }
    >
      <Table<User>
        rowKey="id"
        loading={isLoading}
        dataSource={data?.results}
        scroll={{ x: 900 }}
        pagination={{ current: page, total: data?.count, pageSize: 20, onChange: setPage, showSizeChanger: false }}
        columns={[
          { title: 'Email', dataIndex: 'email' },
          { title: 'Tên', dataIndex: 'display_name' },
          { title: 'Vai trò', dataIndex: 'role', render: (v: Role) => <Tag color={ROLE_COLOR[v]}>{ROLE_OPTIONS.find((o) => o.value === v)?.label}</Tag> },
          { title: 'Đối tượng', dataIndex: 'learner_type', render: (v) => (v === 'kid' ? <Tag color="orange">Trẻ em</Tag> : <Tag>Người lớn</Tag>) },
          {
            title: 'Đang học',
            dataIndex: 'active_language',
            render: (v: string, row) => (v === 'zh' ? `Trung (${row.zh_script === 'hant' ? 'phồn' : 'giản'})` : LANG_LABEL[v] ?? v),
          },
          { title: 'Trạng thái', dataIndex: 'status', render: (v) => (v === 'locked' ? <Tag color="red">Bị khóa</Tag> : <Tag color="green">Hoạt động</Tag>) },
          { title: 'Ngày tạo', dataIndex: 'created_at', render: (v) => dayjs(v).format('DD/MM/YYYY') },
          {
            title: '',
            key: 'actions',
            width: 100,
            render: (_, row) =>
              isAdmin && (
                <Space>
                  <Button size="small" icon={<EditOutlined />} onClick={() => openForm(row)} />
                  <Popconfirm
                    title="Xóa tài khoản này?"
                    description="Toàn bộ dữ liệu học của người dùng sẽ bị xóa. Có thể khóa tài khoản thay vì xóa."
                    okText="Xóa"
                    okButtonProps={{ danger: true }}
                    cancelText="Hủy"
                    disabled={row.id === me?.id}
                    onConfirm={() => remove.mutate(row.id)}
                  >
                    <Button size="small" danger icon={<DeleteOutlined />} disabled={row.id === me?.id} />
                  </Popconfirm>
                </Space>
              ),
          },
        ]}
      />

      <Modal
        open={editing !== null}
        title={editing === 'new' ? 'Thêm người dùng' : 'Sửa người dùng'}
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={save.isPending}
        onCancel={() => setEditing(null)}
        onOk={() => form.validateFields().then((v) => save.mutate(v))}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email', message: 'Email không hợp lệ' }]}>
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label={editing === 'new' ? 'Mật khẩu' : 'Mật khẩu mới (để trống nếu không đổi)'}
            rules={[{ required: editing === 'new', message: 'Nhập mật khẩu' }, { min: 8, message: 'Ít nhất 8 ký tự' }]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item name="display_name" label="Tên hiển thị"><Input /></Form.Item>
          <div className="grid grid-cols-2 gap-x-4">
            <Form.Item name="role" label="Vai trò"><Select options={ROLE_OPTIONS} disabled={isSelf} /></Form.Item>
            <Form.Item name="status" label="Trạng thái">
              <Select disabled={isSelf} options={[{ value: 'active', label: 'Hoạt động' }, { value: 'locked', label: 'Bị khóa' }]} />
            </Form.Item>
            <Form.Item name="learner_type" label="Đối tượng">
              <Select options={[{ value: 'adult', label: 'Người lớn' }, { value: 'kid', label: 'Trẻ em' }]} />
            </Form.Item>
            <Form.Item name="active_language" label="Ngôn ngữ đang học"><Select options={LANG_OPTIONS} /></Form.Item>
          </div>
          <Form.Item name="learning_languages" label="Các ngôn ngữ đăng ký học"><Select mode="multiple" options={LANG_OPTIONS} /></Form.Item>
          {activeLanguage === 'zh' && (
            <Form.Item name="zh_script" label="Chữ Hán">
              <Select options={[{ value: 'hans', label: 'Giản thể (Trung Quốc đại lục)' }, { value: 'hant', label: 'Phồn thể (Đài Loan)' }]} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </Card>
  )
}
