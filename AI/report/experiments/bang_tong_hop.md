# Kết quả các thuật toán

Chưa có số liệu đầy đủ từ production (chạy run-experiments.bat không kèm quick): SM-2/FSRS/GA dưới đây là của học viên mẫu trên máy phát triển.

## Bảng 1. SM-2 vs FSRS – dự đoán nhớ/quên (11883 lượt ôn, nguồn: máy phát triển)

| mô hình | log_loss | rmse | auc | accuracy |
|---|---|---|---|---|
| Leitner (cũ) | 0.6779 | 0.4790 | 0.6757 | 0.6853 |
| SM-2 | 0.6337 | 0.4649 | 0.6354 | 0.6838 |
| FSRS mặc định | 0.6986 | 0.4831 | 0.6955 | 0.6829 |
| FSRS + GA | 0.5249 | 0.4169 | 0.7628 | 0.7520 |

## Bảng 2. Genetic Algorithm – trên 691 thẻ kiểm tra (nguồn: máy phát triển)

| mô hình | log_loss | rmse | auc | accuracy |
|---|---|---|---|---|
| SM-2 | 0.6319 | 0.4652 | 0.6357 | 0.6881 |
| FSRS mặc định | 0.7086 | 0.4873 | 0.6909 | 0.6758 |
| FSRS + GA | 0.5210 | 0.4147 | 0.7713 | 0.7688 |

GA giảm log-loss 26.5% so với tham số FSRS mặc định.

## Bảng 3. VIP – mô phỏng 12 người học × 60 ngày (nguồn: máy phát triển)

| lịch ôn | thứ tự | nhớ chung | nhớ từ dễ nhầm | lượt ôn / người |
|---|---|---|---|---|
| SM-2 | theo hạn (baseline) | 44.5% | 25.7% | 1377.8000 |
| SM-2 | VIP | 31.9% | 62.1% | 1377.2000 |
| SM-2 | VIP hybrid | 44.0% | 30.5% | 1376.3000 |
| FSRS | theo hạn (baseline) | 45.4% | 30.8% | 1376.5000 |
| FSRS | VIP | 37.8% | 74.0% | 1376.4000 |
| FSRS | VIP hybrid | 47.4% | 31.3% | 1375.5000 |
| Leitner | theo hạn (baseline) | 36.8% | 19.5% | 1345.6000 |

## Bảng 4. Smart Distractor – 250 từ (nguồn: máy phát triển)

| phương pháp | số đáp án nhiễu | tương đồng ngữ nghĩa | cùng từ loại | không hợp lệ |
|---|---|---|---|---|
| ngẫu nhiên cùng chủ đề | 750 | 0.4114 | 100% | 0.0% |
| Smart Distractor | 750 | 0.6128 | 100% | 0.0% |

## Bảng 5. Proximity Search – 30 POI (nguồn: máy phát triển)

| phương pháp | ms / truy vấn | khớp kết quả |
|---|---|---|
| lưới + Haversine (tự cài) | 0.0153 | 500/500 với brute force |
| brute force | 0.0172 | – |
| PostgreSQL earthdistance | 1.4852 | 499/500 với lưới |

| pois | grid_ms | speedup | brute_ms |
|---|---|---|---|
| 1000 | 0.0030 | 257.7000 | 0.8300 |
| 10000 | 0.0270 | 391.7000 | 10.7580 |
| 50000 | 0.0740 | 414.6000 | 30.7720 |

## Bảng 6. Quyết định chọn cấu hình (nguồn: máy phát triển)

| quyết định | chọn | bằng chứng |
|---|---|---|
| Lịch ôn | FSRS+GA r=0.9 | nhớ chung 47.5%, từ dễ nhầm 36.1% (mô phỏng) |
| Thứ tự ôn | VIP lai 1 ngày | trong ngưỡng −2% nhớ chung, giữ từ dễ nhầm tốt nhất |
| Đáp án nhiễu | smart | độ gần nghĩa 0.4114 → 0.6128, đáp án nhiễu cũng đúng 0% |
| Tìm điểm gần | grid | đúng 500/500 so với brute force, 0.0153 ms vs 1.4852 ms |
| Nhận diện ảnh (lingoprism-yolov10n) | combined | coco top-1 87%, trained top-1 50%, combined top-1 81% |
| Nhận diện ảnh (yolov8s-oiv7-lingoprism) | combined | coco top-1 87%, trained top-1 62%, combined top-1 77% |
| Nhận diện ảnh (yolov8m-oiv7-lingoprism) | combined | coco top-1 87%, trained top-1 66%, combined top-1 77% |

Hình: `AI/notebooks/figures/10_srs_so_sanh.png`, `10_ga.png`, `10_vip.png`, `10_distractor.png`, `10_proximity.png`. Geofence và realtime: `bang_ket_qua.md` (notebook 09).
