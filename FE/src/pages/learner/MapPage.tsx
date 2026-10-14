import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Card, Select, Tag } from 'antd'
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import { learnApi, type Poi } from '../../api/app'
import { errorMessage } from '../../api/client'

const HCMC: [number, number] = [10.7769, 106.7009]
const ICONS: Record<string, string> = {
  market: '🛒', supermarket: '🏬', hospital: '🏥', school: '🏫', park: '🌳', zoo: '🦁', museum: '🏛️', airport: '✈️',
  station: '🚉', religious: '⛪', restaurant: '🍜', stadium: '🏟️', landmark: '📍', library: '📚', theater: '🎭',
}

const emojiIcon = (emoji: string) => L.divIcon({ html: `<div style="font-size:26px">${emoji}</div>`, className: '', iconSize: [30, 30], iconAnchor: [15, 15] })
const meIcon = L.divIcon({ html: '<div style="width:18px;height:18px;border-radius:50%;background:#2563eb;border:3px solid white;box-shadow:0 0 4px #0005"></div>', className: '', iconSize: [18, 18] })

function Recenter({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => { map.setView(center) }, [center, map])
  return null
}

/** Học theo vị trí: POI quanh người học (tìm lân cận bằng PostgreSQL earthdistance) và chủ đề từ vựng phù hợp. */
export default function MapPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [center, setCenter] = useState<[number, number]>(HCMC)
  const [me, setMe] = useState<[number, number] | null>(null)
  const [radius, setRadius] = useState(3000)
  const [pois, setPois] = useState<Poi[]>([])
  const [queryMs, setQueryMs] = useState<number | null>(null)

  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      (p) => { const c: [number, number] = [p.coords.latitude, p.coords.longitude]; setMe(c); setCenter(c) },
      () => message.info('Không lấy được vị trí – đang hiển thị trung tâm TP.HCM'),
      { enableHighAccuracy: true, timeout: 8000 },
    )
  }, [message])

  useEffect(() => {
    learnApi.nearby(center[0], center[1], radius)
      .then((r) => { setPois(r.results); setQueryMs(r.query_ms) })
      .catch((e) => message.error(errorMessage(e)))
  }, [center, radius, message])

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold m-0">Học theo vị trí</h1>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          Bán kính
          <Select value={radius} onChange={setRadius} style={{ width: 110 }}
            options={[1000, 3000, 5000, 10000].map((r) => ({ value: r, label: `${r / 1000} km` }))} />
          {queryMs != null && <span>· {pois.length} địa điểm · truy vấn {queryMs} ms</span>}
        </div>
      </div>
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-[560px] rounded-2xl overflow-hidden border border-slate-200">
          <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <Recenter center={center} />
            {me && <Marker position={me} icon={meIcon}><Popup>Bạn đang ở đây</Popup></Marker>}
            {pois.map((p) => (
              <Marker key={p.id} position={[p.lat, p.lng]} icon={emojiIcon(ICONS[p.category] ?? '📍')}>
                <Popup>
                  <div className="font-semibold">{p.name}</div>
                  <div className="text-xs">{p.category_label}</div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {p.topics_detail.map((t) => (
                      <a key={t.id} onClick={() => navigate(`/vocab/topics/${t.id}`)}>{t.icon} {t.name_vi}</a>
                    ))}
                  </div>
                </Popup>
              </Marker>
            ))}
            {pois.map((p) => <Circle key={`c${p.id}`} center={[p.lat, p.lng]} radius={p.radius_m} pathOptions={{ color: '#0d9488', weight: 1, fillOpacity: 0.08 }} />)}
          </MapContainer>
        </div>
        <div className="flex flex-col gap-3 max-h-[560px] overflow-y-auto">
          {pois.map((p) => (
            <Card key={p.id} size="small" className="!rounded-xl" hoverable onClick={() => setCenter([p.lat, p.lng])}>
              <div className="font-semibold">{ICONS[p.category] ?? '📍'} {p.name}</div>
              <div className="text-xs text-slate-500">{p.category_label}{p.distance_m != null && ` · ${(p.distance_m / 1000).toFixed(1)} km`}</div>
              <div className="flex flex-wrap gap-1 mt-2">
                {p.topics_detail.map((t) => (
                  <Tag key={t.id} color="cyan" className="cursor-pointer" onClick={(e) => { e.stopPropagation(); navigate(`/vocab/topics/${t.id}`) }}>{t.icon} {t.name_vi}</Tag>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
