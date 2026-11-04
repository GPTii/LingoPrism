# Kết quả geofence và realtime

Nguồn geofence: production (lingoprism.id.vn), 30 POI, 120 lượt đi qua mỗi ô, nhiễu GPS 8.0 m. Máy chủ kiểm tra một lần: TB 3.704 ms, p95 4.429 ms.

## Bảng 1. Geofence: tỷ lệ phát hiện và độ trễ kích hoạt

| Chính sách | Di chuyển | Phát hiện | Trễ TB (s) | Trễ p50 (s) | Trễ p95 (s) | Báo nhầm | Lần gọi/giờ |
|---|---|---|---|---|---|---|---|
| cũ: 100 m / 2 phút | đi bộ | 93.3% | 54.1 | 61.0 | 125 | 3.3% | 23.6 |
| cũ: 100 m / 2 phút | xe đạp | 48.9% | 34.5 | 31.0 | 69 | 0.0% | 25.6 |
| cũ: 100 m / 2 phút | xe máy | 40.0% | 23.2 | 18.0 | 51 | 0.0% | 28.0 |
| 25 m / 30 giây | đi bộ | 100.0% | 13.5 | 11.5 | 38 | 0.0% | 95.0 |
| 25 m / 30 giây | xe đạp | 97.8% | 14.8 | 14.0 | 29 | 0.0% | 106.6 |
| 25 m / 30 giây | xe máy | 85.6% | 13.1 | 13 | 28 | 0.0% | 110.5 |
| đang dùng: 25 m / 15 giây | đi bộ | 100.0% | 5.9 | 4.0 | 18 | 0.0% | 160.8 |
| đang dùng: 25 m / 15 giây | xe đạp | 100.0% | 8.1 | 8.0 | 16 | 0.0% | 192.6 |
| đang dùng: 25 m / 15 giây | xe máy | 97.8% | 7.3 | 7.0 | 15 | 0.0% | 204.8 |
| 10 m / 10 giây | đi bộ | 100.0% | 6.3 | 5.5 | 17 | 3.3% | 311.9 |
| 10 m / 10 giây | xe đạp | 100.0% | 5.1 | 5.0 | 11 | 3.3% | 314.6 |
| 10 m / 10 giây | xe máy | 100.0% | 5.0 | 5.0 | 10 | 0.0% | 317.1 |

## Bảng 2. Realtime – máy này (InMemoryChannelLayer)

| Đường đi | Mẫu | TB (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Lớn nhất (ms) |
|---|---|---|---|---|---|---|
| Ping → pong | 50 | 0.5 | 0.49 | 0.77 | 0.83 | 0.83 |
| Nhóm → thành viên khác | 240 | 8.01 | 7.31 | 11.52 | 24.52 | 29.8 |
| Nhóm → người gửi | 48 | 8.65 | 7.69 | 12.56 | 24.77 | 24.77 |
| Tin riêng: gửi + lưu | 30 | 13.07 | 12.27 | 16.15 | 43.57 | 43.57 |
| Tin riêng → người nhận | 30 | 13.43 | 12.71 | 16.87 | 43.75 | 43.75 |
| Tin riêng → máy khác người gửi | 30 | 13.27 | 12.58 | 16.51 | 43.69 | 43.69 |

## Bảng 3. Realtime – production (RedisChannelLayer)

| Đường đi | Mẫu | TB (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Lớn nhất (ms) |
|---|---|---|---|---|---|---|
| Ping → pong | 50 | 0.3 | 0.29 | 0.34 | 0.35 | 0.35 |
| Nhóm → thành viên khác | 240 | 28.08 | 7.94 | 145.89 | 167.95 | 169.0 |
| Nhóm → người gửi | 48 | 27.77 | 7.78 | 140.77 | 166.25 | 166.25 |
| Tin riêng: gửi + lưu | 30 | 15.37 | 12.8 | 46.01 | 53.97 | 53.97 |
| Tin riêng → người nhận | 30 | 15.83 | 13.14 | 46.27 | 54.21 | 54.21 |
| Tin riêng → máy khác người gửi | 30 | 15.51 | 12.89 | 46.1 | 54.13 | 54.13 |

## Bảng 4. Realtime – tính nhất quán

| nguồn | lượt giao tin nhóm | mất | trùng | cùng thứ tự | gửi lại tạo tin mới | dồn tin nhận/từ chối |
|---|---|---|---|---|---|---|
| máy này (InMemoryChannelLayer) | 288/288 | 0 | 0 | có | không | 8/16 |
| production (RedisChannelLayer) | 288/288 | 0 | 0 | có | không | 8/16 |

Hình: `AI/notebooks/figures/09_geofence_minh_hoa.png`, `09_geofence_phat_hien.png`, `09_geofence_do_tre.png`, `09_geofence_danh_doi.png`, `09_realtime_do_tre.png`, `09_realtime_don_tin.png`.
