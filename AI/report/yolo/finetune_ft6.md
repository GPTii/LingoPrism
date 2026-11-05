# Fine-tune ft6: trước / sau trên tập test 2542 ảnh

Dữ liệu: 21590 ảnh (17040 Open Images V7 *train* + 4550 COCO train2017/LVIS; nhãn người vẽ), 29 lớp yếu + 203 lớp ôn lại.

| Chỉ số | Đang dùng | Sau fine-tune | Chênh |
|---|---|---|---|
| Precision | 0.751 | 0.684 | -0.067 |
| Recall | 0.602 | 0.630 | +0.028 |
| F1 | 0.668 | 0.656 | -0.012 |
| mAP50 | 0.696 | 0.683 | -0.013 |
| mAP50-95 | 0.564 | 0.546 | -0.018 |
| mAP50 trung bình 21 lớp yếu | 0.483 | 0.471 | -0.012 |
| Thời gian (ms / ảnh) | 322.1 | 295.9 | |

## Từng lớp yếu (AP50)

| Lớp | Đang dùng | Sau | Chênh | Recall trước → sau |
|---|---|---|---|---|
| chopsticks | 0.352 | 0.727 | +0.375 | 0.062 → 0.562 |
| pillow | 0.531 | 0.596 | +0.065 | 0.293 → 0.585 |
| window | 0.334 | 0.380 | +0.046 | 0.102 → 0.144 |
| egg | 0.434 | 0.467 | +0.033 | 0.302 → 0.365 |
| potted plant | 0.502 | 0.534 | +0.032 | 0.368 → 0.460 |
| dining table | 0.492 | 0.504 | +0.012 | 0.416 → 0.442 |
| car | 0.730 | 0.731 | +0.001 | 0.698 → 0.712 |
| spoon | 0.559 | 0.556 | -0.003 | 0.529 → 0.510 |
| carrot | 0.454 | 0.429 | -0.024 | 0.421 → 0.466 |
| backpack | 0.501 | 0.475 | -0.026 | 0.405 → 0.456 |
| toothbrush | 0.528 | 0.501 | -0.027 | 0.515 → 0.544 |
| orange | 0.491 | 0.451 | -0.040 | 0.415 → 0.393 |
| broccoli | 0.467 | 0.425 | -0.042 | 0.467 → 0.545 |
| apple | 0.546 | 0.501 | -0.045 | 0.534 → 0.500 |
| knife | 0.467 | 0.419 | -0.048 | 0.389 → 0.400 |
| handbag | 0.423 | 0.371 | -0.053 | 0.321 → 0.348 |
| banana | 0.366 | 0.305 | -0.061 | 0.292 → 0.434 |
| book | 0.379 | 0.313 | -0.066 | 0.310 → 0.403 |
| scissors | 0.584 | 0.500 | -0.084 | 0.486 → 0.486 |
| bench | 0.494 | 0.408 | -0.085 | 0.421 → 0.439 |
| door | 0.508 | 0.306 | -0.202 | 0.216 → 0.162 |

**Kết luận (quy tắc: mAP50 chung không giảm quá 0.005, trung bình lớp yếu phải tăng): KHÔNG dùng: mAP chung giảm quá ngưỡng.**

## Phân tích thêm (trên dự đoán đã lưu, không CLIP)

| Cách ghép với COCO m INT8 | mAP50 | mAP50-95 | P | R | Lớp COCO | Lớp khác |
|---|---|---|---|---|---|---|
| Model gốc (đang dùng) | 0.698 | 0.565 | 0.771 | 0.603 | 0.703 | 0.689 |
| ft6, luật ghép hiện tại | 0.679 | 0.542 | 0.695 | 0.628 | 0.673 | 0.694 |
| ft6, bỏ box ft6 của lớp COCO (để model COCO lo) | 0.694 | 0.557 | 0.796 | 0.585 | 0.689 | **0.705** |

* Chạy riêng, ft6 giữ mAP50 (0.639 → 0.638) và tăng recall 0.386 → 0.525: model không hỏng, phần thua nằm ở chỗ nó
  thêm box cho lớp COCO trùng với model COCO (precision 0.77 → 0.70).
* Đổi ngưỡng "lớp lạ phủ box COCO" (0.25 → 0.9) không giúp gì.
* Box nhãn ngoài COCO đặt lên vật khác tăng 242 → 421 (orange → lemon, sheep → pig, fork → chopsticks, elephant →
  rhinoceros; một phần là tập test thiếu nhãn: plate trên bàn ăn, jacket trên người).
* Nguyên nhân gốc: ảnh COCO mới chỉ vẽ đủ 80 lớp COCO, nhãn LVIS thưa, door/window không có → vật không box bị dạy là
  nền (door −0.20). Hướng v7: model gốc gán nhãn giả phần chưa vẽ (`AI/scripts/pseudo_label_finetune.py`), 10 epoch.
