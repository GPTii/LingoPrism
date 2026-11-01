# Kết quả geofence và realtime

Nguồn geofence: máy phát triển, 30 POI, 120 lượt đi qua mỗi ô, nhiễu GPS 8.0 m. Máy chủ kiểm tra một lần: TB 3.507 ms, p95 5.38 ms.

## Bảng 1. Geofence: tỷ lệ phát hiện và độ trễ kích hoạt

| Chính sách | Di chuyển | Phát hiện | Trễ TB (s) | Trễ p50 (s) | Trễ p95 (s) | Báo nhầm | Lần gọi/giờ |
|---|---|---|---|---|---|---|---|
| cũ: 100 m / 2 phút | đi bộ | 95.6% | 65.9 | 71.5 | 130 | 0.0% | 23.8 |
| cũ: 100 m / 2 phút | xe đạp | 56.7% | 48.1 | 42 | 97 | 0.0% | 26.8 |
| cũ: 100 m / 2 phút | xe máy | 38.9% | 25.7 | 20 | 70 | 0.0% | 29.0 |
| 25 m / 30 giây | đi bộ | 100.0% | 15.3 | 13.0 | 36 | 3.3% | 95.2 |
| 25 m / 30 giây | xe đạp | 96.7% | 15.5 | 15 | 31 | 0.0% | 106.1 |
| 25 m / 30 giây | xe máy | 88.9% | 14.4 | 13.5 | 31 | 0.0% | 110.1 |
| đang dùng: 25 m / 15 giây | đi bộ | 100.0% | 8.7 | 7.0 | 28 | 0.0% | 161.6 |
| đang dùng: 25 m / 15 giây | xe đạp | 100.0% | 8.1 | 7.0 | 17 | 3.3% | 191.2 |
| đang dùng: 25 m / 15 giây | xe máy | 100.0% | 8.7 | 8.0 | 16 | 0.0% | 204.4 |
| 10 m / 10 giây | đi bộ | 100.0% | 6.4 | 4.0 | 17 | 3.3% | 312.1 |
| 10 m / 10 giây | xe đạp | 100.0% | 5.2 | 5.0 | 11 | 0.0% | 314.6 |
| 10 m / 10 giây | xe máy | 100.0% | 5.3 | 6.0 | 10 | 0.0% | 317.5 |

## Bảng 2. Realtime – máy này (InMemoryChannelLayer)

| Đường đi | Mẫu | TB (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Lớn nhất (ms) |
|---|---|---|---|---|---|---|
| Ping → pong | 50 | 0.4 | 0.4 | 0.6 | 0.67 | 0.67 |
| Nhóm → thành viên khác | 240 | 5.69 | 5.29 | 7.79 | 10.4 | 10.5 |
| Nhóm → người gửi | 48 | 6.09 | 5.65 | 8.27 | 10.62 | 10.62 |
| Tin riêng: gửi + lưu | 30 | 9.05 | 8.77 | 11.52 | 19.48 | 19.48 |
| Tin riêng → người nhận | 30 | 9.28 | 8.94 | 11.7 | 19.63 | 19.63 |
| Tin riêng → máy khác người gửi | 30 | 9.18 | 8.85 | 11.63 | 19.58 | 19.58 |

## Bảng 3. Realtime – tính nhất quán

| nguồn | lượt giao tin nhóm | mất | trùng | cùng thứ tự | gửi lại tạo tin mới | dồn tin nhận/từ chối |
|---|---|---|---|---|---|---|
| máy này (InMemoryChannelLayer) | 288/288 | 0 | 0 | có | không | 8/16 |

Hình: `AI/notebooks/figures/09_geofence_minh_hoa.png`, `09_geofence_phat_hien.png`, `09_geofence_do_tre.png`, `09_geofence_danh_doi.png`, `09_realtime_do_tre.png`, `09_realtime_don_tin.png`.
