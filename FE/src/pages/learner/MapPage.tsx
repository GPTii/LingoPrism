import { useEffect, useState, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { useNavigate } from 'react-router-dom'
import { App, Select } from 'antd'
import {
  BankOutlined, BookOutlined, CarOutlined, CoffeeOutlined, EnvironmentFilled, HomeOutlined, MedicineBoxOutlined,
  ReadOutlined, RocketOutlined, ShopOutlined, ShoppingCartOutlined, SmileOutlined, TrophyOutlined, VideoCameraOutlined,
} from '@ant-design/icons'
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import { learnApi, type Poi } from '../../api/app'
import { errorMessage } from '../../api/client'
import { PageHeader } from '../../components/ui'

const HCMC: [number, number] = [10.7769, 106.7009]
const ICONS: Record<string, ReactNode> = {
  market: <ShopOutlined />, supermarket: <ShoppingCartOutlined />, hospital: <MedicineBoxOutlined />, school: <ReadOutlined />,
  park: <SmileOutlined />, zoo: <SmileOutlined />, museum: <BankOutlined />, airport: <RocketOutlined />, station: <CarOutlined />,
  religious: <HomeOutlined />, restaurant: <CoffeeOutlined />, stadium: <TrophyOutlined />, landmark: <EnvironmentFilled />,
  library: <BookOutlined />, theater: <VideoCameraOutlined />,
}
const iconOf = (category: string) => ICONS[category] ?? <EnvironmentFilled />

/** Map pin: the category's icon on a blue drop. */
const pinIcon = (category: string) => L.divIcon({
  className: '',
  iconSize: [34, 40],
  iconAnchor: [17, 38],
  html: `<div style="width:34px;height:34px;border-radius:17px 17px 17px 4px;transform:rotate(-45deg);background:#1899f0;border:2px solid #fff;display:grid;place-items:center;box-shadow:0 4px 10px -4px rgb(21 35 59 / .5)">
    <span style="transform:rotate(45deg);color:#fff;font-size:16px;line-height:0">${renderToStaticMarkup(<>{iconOf(category)}</>)}</span></div>`,
})
const meIcon = L.divIcon({ html: '<div style="width:18px;height:18px;border-radius:50%;background:#10c79a;border:3px solid white;box-shadow:0 0 0 4px rgb(16 199 154 / .25)"></div>', className: '', iconSize: [18, 18] })

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
  const [selected, setSelected] = useState<number | null>(null)

  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      (p) => { const c: [number, number] = [p.coords.latitude, p.coords.longitude]; setMe(c); setCenter(c) },
      () => message.info('Không lấy được vị trí của bạn – đang hiển thị trung tâm TP.HCM'),
      { enableHighAccuracy: true, timeout: 8000 },
    )
  }, [message])

  useEffect(() => {
    learnApi.nearby(center[0], center[1], radius)
      .then((r) => { setPois(r.results); setQueryMs(r.query_ms) })
      .catch((e) => message.error(errorMessage(e)))
  }, [center, radius, message])

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <PageHeader title="Học theo vị trí" description="Địa điểm quanh bạn và chủ đề từ vựng hợp với nơi đó: ở chợ học tên đồ ăn, ở bệnh viện học từ sức khoẻ."
        actions={
          <label className="flex items-center gap-2 text-sm text-slate-500">
            Bán kính
            <Select value={radius} onChange={setRadius} style={{ width: 100 }} aria-label="Bán kính tìm"
              options={[1000, 3000, 5000, 10000].map((r) => ({ value: r, label: `${r / 1000} km` }))} />
          </label>
        } />
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-[55vh] min-h-[320px] lg:h-[560px] rounded-2xl overflow-hidden border border-slate-200">
          <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <Recenter center={center} />
            {me && <Marker position={me} icon={meIcon}><Popup>Bạn đang ở đây</Popup></Marker>}
            {pois.map((p) => (
              <Marker key={p.id} position={[p.lat, p.lng]} icon={pinIcon(p.category)} eventHandlers={{ click: () => setSelected(p.id) }}>
                <Popup>
                  <div className="font-semibold">{p.name}</div>
                  <div className="text-xs">{p.category_label}</div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {p.topics_detail.map((t) => (
                      <a key={t.id} onClick={() => navigate(`/vocab/topics/${t.id}`)}>{t.icon} {t.name_vi}</a>
                    ))}
                  </div>
                </Popup>
              </Marker>
            ))}
            {pois.map((p) => <Circle key={`c${p.id}`} center={[p.lat, p.lng]} radius={p.radius_m} pathOptions={{ color: '#1899f0', weight: 1, fillOpacity: 0.06 }} />)}
          </MapContainer>
        </div>
        <div className="flex flex-col gap-2 lg:max-h-[560px] overflow-y-auto">
          {queryMs != null && <div className="num text-sm text-slate-500 px-1">{pois.length} địa điểm trong {radius / 1000} km</div>}
          {pois.map((p) => (
            <div key={p.id} role="button" tabIndex={0}
              onClick={() => { setCenter([p.lat, p.lng]); setSelected(p.id) }}
              onKeyDown={(e) => { if (e.key === 'Enter') { setCenter([p.lat, p.lng]); setSelected(p.id) } }}
              className={`btn-3d p-3 cursor-pointer text-left ${selected === p.id ? '!border-brand-500' : ''}`}>
              <div className="flex items-center gap-2 font-semibold text-slate-800">
                <span className="text-brand-600">{iconOf(p.category)}</span>{p.name}
              </div>
              <div className="num text-xs text-slate-500 mt-0.5">{p.category_label}{p.distance_m != null && ` · ${(p.distance_m / 1000).toFixed(1)} km`}</div>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {p.topics_detail.map((t) => (
                  <button key={t.id} type="button" onClick={(e) => { e.stopPropagation(); navigate(`/vocab/topics/${t.id}`) }}
                    className="rounded-md bg-brand-50 text-brand-700 px-2 py-0.5 text-xs font-semibold cursor-pointer hover:bg-brand-100">
                    {t.icon} {t.name_vi}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {!pois.length && queryMs != null && (
            <p className="text-slate-500 text-sm px-1">Không có địa điểm nào trong {radius / 1000} km. Thử tăng bán kính.</p>
          )}
        </div>
      </div>
    </div>
  )
}
