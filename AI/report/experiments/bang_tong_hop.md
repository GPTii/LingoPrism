# Kết quả các thuật toán

Lịch sử ôn trên production: 12991 lượt, trong đó 1% của 2 người dùng thật, phần còn lại của học viên mẫu.

## Bảng 1. SM-2 vs FSRS – dự đoán nhớ/quên (11758 lượt ôn, nguồn: production)

| mô hình | log_loss | rmse | auc | accuracy |
|---|---|---|---|---|
| Leitner (cũ) | 0.6512 | 0.4679 | 0.6734 | 0.6996 |
| SM-2 | 0.5988 | 0.4498 | 0.6587 | 0.7073 |
| FSRS mặc định | 0.6720 | 0.4732 | 0.6985 | 0.6969 |
| FSRS + GA | 0.5137 | 0.4115 | 0.7658 | 0.7617 |

## Bảng 2. Genetic Algorithm – trên 688 thẻ kiểm tra (nguồn: production)

| mô hình | log_loss | rmse | auc | accuracy |
|---|---|---|---|---|
| SM-2 | 0.6163 | 0.4570 | 0.6340 | 0.6945 |
| FSRS mặc định | 0.6775 | 0.4751 | 0.6971 | 0.6958 |
| FSRS + GA | 0.5185 | 0.4136 | 0.7617 | 0.7578 |

GA giảm log-loss 23.5% so với tham số FSRS mặc định.

## Bảng 3. VIP – mô phỏng 12 người học × 60 ngày (nguồn: production)

| lịch ôn | thứ tự | nhớ chung | nhớ từ dễ nhầm | lượt ôn / người |
|---|---|---|---|---|
| SM-2 | theo hạn (baseline) | 45.8% | 28.5% | 1378.6000 |
| SM-2 | VIP | 36.5% | 67.0% | 1373.2000 |
| SM-2 | VIP hybrid | 47.8% | 34.0% | 1373.2000 |
| FSRS | theo hạn (baseline) | 41.4% | 23.7% | 1418.0000 |
| FSRS | VIP | 38.3% | 80.5% | 1416.4000 |
| FSRS | VIP hybrid | 46.2% | 30.9% | 1416.4000 |
| Leitner | theo hạn (baseline) | 33.8% | 16.1% | 1346.3000 |

## Bảng 4. Smart Distractor – 250 từ (nguồn: production)

| phương pháp | số đáp án nhiễu | tương đồng ngữ nghĩa | cùng từ loại | không hợp lệ |
|---|---|---|---|---|
| ngẫu nhiên cùng chủ đề | 750 | 0.4169 | 100% | 0.0% |
| Smart Distractor | 750 | 0.6087 | 100% | 0.0% |

## Bảng 5. Proximity Search – 30 POI (nguồn: production)

| phương pháp | ms / truy vấn | khớp kết quả |
|---|---|---|
| lưới + Haversine (tự cài) | 0.0255 | 500/500 với brute force |
| brute force | 0.0315 | – |
| PostgreSQL earthdistance | 0.9419 | 499/500 với lưới |

| pois | grid_ms | speedup | brute_ms |
|---|---|---|---|
| 1000 | 0.0110 | 97.1000 | 1.0720 |
| 10000 | 0.0250 | 385.1000 | 9.8070 |
| 50000 | 0.1200 | 403.8000 | 48.5550 |

## Bảng 6. Quyết định chọn cấu hình (nguồn: production)

| quyết định | chọn | bằng chứng |
|---|---|---|
| Lịch ôn | FSRS+GA r=0.85 | nhớ chung 46.6%, từ dễ nhầm 37.2% (mô phỏng) |
| Thứ tự ôn | VIP lai 7 ngày | trong ngưỡng −2% nhớ chung, giữ từ dễ nhầm tốt nhất |
| Đáp án nhiễu | smart | độ gần nghĩa 0.4169 → 0.6087, đáp án nhiễu cũng đúng 0% |
| Tìm điểm gần | grid | đúng 500/500 so với brute force, 0.0255 ms vs 0.9419 ms |

Hình: `AI/notebooks/figures/10_srs_so_sanh.png`, `10_ga.png`, `10_vip.png`, `10_distractor.png`, `10_proximity.png`. Geofence và realtime: `bang_ket_qua.md` (notebook 09).
