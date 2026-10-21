import { useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Card, Form, Input, InputNumber, Popconfirm, Select, Switch, Table } from 'antd'
import { useState } from 'react'
import { Circle, MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { adminApi } from '../../api/admin'
import type { Poi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { vocabApi } from '../../api/vocab'

const CATEGORIES = [
  ['market', 'Chợ'], ['supermarket', 'Siêu thị / TTTM'], ['hospital', 'Bệnh viện'], ['school', 'Trường học'], ['park', 'Công viên'],
  ['zoo', 'Sở thú'], ['museum', 'Bảo tàng'], ['airport', 'Sân bay'], ['station', 'Nhà ga / bến xe'], ['religious', 'Chùa / nhà thờ'],
  ['restaurant', 'Nhà hàng / ẩm thực'], ['stadium', 'Sân vận động'], ['landmark', 'Địa danh'], ['library', 'Thư viện'], ['theater', 'Nhà hát / rạp'], ['other', 'Khác'],
].map(([value, label]) => ({ value, label }))

const pin = L.divIcon({ html: '<div style="font-size:26px">📍</div>', className: '', iconSize: [26, 26], iconAnchor: [13, 26] })
const pinActive = L.divIcon({ html: '<div style="font-size:32px">📌</div>', className: '', iconSize: [32, 32], iconAnchor: [16, 32] })

function ClickToPlace({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e) => onPick(e.latlng.lat, e.latlng.lng) })
  return null
}

/** WebGIS: manage points of interest on the map (click to place, drag to move) and link them to topics. */
export default function PoisAdminPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [form] = Form.useForm()
  const [editing, setEditing] = useState<Partial<Poi> | null>(null)
  const pois = useQuery({ queryKey: ['admin-pois'], queryFn: adminApi.pois })
  const topics = useQuery({ queryKey: ['topics-all'], queryFn: () => vocabApi.topics() })
  const stats = useQuery({ queryKey: ['poi-stats'], queryFn: adminApi.poiStats })

  const edit = (p: Partial<Poi>) => {
    setEditing(p)
    form.setFieldsValue({ radius_m: 150, is_active: true, ...p })
  }
  const save = async () => {
    const v = await form.validateFields()
    try {
      await adminApi.savePoi({ ...editing, ...v })
      message.success('Đã lưu điểm quan tâm')
      setEditing(null)
      queryClient.invalidateQueries({ queryKey: ['admin-pois'] })
    } catch (e) {
      message.error(errorMessage(e))
    }
  }
  const lat = Form.useWatch('lat', form)
  const lng = Form.useWatch('lng', form)
  const radius = Form.useWatch('radius_m', form)

  return (
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="lg:col-span-2" title="Bản đồ POI – bấm lên bản đồ để thêm điểm mới, kéo ghim để di chuyển" styles={{ body: { padding: 0, height: 560 } }}>
        <MapContainer center={[10.7769, 106.7009]} zoom={12} style={{ height: '100%' }}>
          <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <ClickToPlace onPick={(la, ln) => (editing ? form.setFieldsValue({ lat: la, lng: ln }) : edit({ lat: la, lng: ln }))} />
          {pois.data?.filter((p) => p.id !== editing?.id).map((p) => (
            <Marker key={p.id} position={[p.lat, p.lng]} icon={pin} eventHandlers={{ click: () => edit(p) }} />
          ))}
          {editing && lat != null && lng != null && (
            <>
              <Marker position={[lat, lng]} icon={pinActive} draggable
                eventHandlers={{ dragend: (e) => { const ll = (e.target as L.Marker).getLatLng(); form.setFieldsValue({ lat: ll.lat, lng: ll.lng }) } }} />
              <Circle center={[lat, lng]} radius={radius ?? 150} pathOptions={{ color: '#6d4aff' }} />
            </>
          )}
        </MapContainer>
      </Card>
      <Card title={editing ? (editing.id ? 'Sửa điểm quan tâm' : 'Thêm điểm quan tâm') : 'Chọn một điểm trên bản đồ'}>
        {editing ? (
          <Form form={form} layout="vertical">
            <Form.Item name="name" label="Tên" rules={[{ required: true }]}><Input /></Form.Item>
            <Form.Item name="category" label="Loại" rules={[{ required: true }]}><Select options={CATEGORIES} /></Form.Item>
            <div className="flex gap-2">
              <Form.Item name="lat" label="Vĩ độ" rules={[{ required: true }]}><InputNumber step={0.0001} /></Form.Item>
              <Form.Item name="lng" label="Kinh độ" rules={[{ required: true }]}><InputNumber step={0.0001} /></Form.Item>
            </div>
            <Form.Item name="radius_m" label="Bán kính geofence (m)"><InputNumber min={20} max={5000} /></Form.Item>
            <Form.Item name="address" label="Địa chỉ"><Input /></Form.Item>
            <Form.Item name="topics" label="Chủ đề từ vựng gợi ý">
              <Select mode="multiple" options={topics.data?.results.map((t) => ({ value: t.id, label: `${t.icon} ${t.name_vi}` }))} />
            </Form.Item>
            <Form.Item name="is_active" label="Hiển thị" valuePropName="checked"><Switch /></Form.Item>
            <div className="flex gap-2">
              <Button type="primary" onClick={save}>Lưu</Button>
              <Button onClick={() => setEditing(null)}>Huỷ</Button>
              {editing.id && (
                <Popconfirm title="Xoá điểm này?" onConfirm={async () => { await adminApi.deletePoi(editing.id!); setEditing(null); pois.refetch() }}>
                  <Button danger>Xoá</Button>
                </Popconfirm>
              )}
            </div>
          </Form>
        ) : (
          <Table size="small" rowKey="id" pagination={false} dataSource={stats.data}
            columns={[{ title: 'Điểm được ghé nhiều nhất', dataIndex: 'name' }, { title: 'Lượt', dataIndex: 'visits' }]} />
        )}
      </Card>
    </div>
  )
}
