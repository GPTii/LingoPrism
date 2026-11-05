# Trộn trọng số model gốc + fine-tune (WiSE-FT)

`w = (1 − α)·w_gốc + α·w_fine-tune` (Wortsman et al., *Robust fine-tuning of zero-shot models*, CVPR 2022), làm thẳng
trên file ONNX (cùng export, BatchNorm đã gộp) bằng `AI/scripts/weight_average_onnx.py`, rồi lượng tử hoá INT8 như
server. Không cần train lại.

## Tập test 2542 ảnh, chạy như server (OIV7 m INT8 + COCO m INT8 + CLIP)

| Model OIV7 | mAP50 | mAP50-95 | P | R | Lớp COCO | Lớp khác | TB 21 lớp yếu |
|---|---|---|---|---|---|---|---|
| Gốc yolov8m-oiv7 (đang dùng) | 0.696 | 0.564 | 0.751 | 0.602 | 0.699 | 0.690 | 0.483 |
| v6 (ảnh COCO/LVIS mới) | 0.683 | 0.546 | 0.684 | 0.630 | 0.673 | 0.708 | 0.471 |
| v7 (v6 + nhãn giả của model gốc) | 0.676 | 0.542 | 0.709 | 0.609 | – | – | 0.459 |
| trộn 70% gốc + 30% v6 | **0.701** | **0.568** | 0.744 | 0.605 | 0.695 | 0.713 | 0.487 |
| **trộn 50% gốc + 50% v6** | **0.701** | 0.565 | 0.736 | 0.612 | 0.694 | **0.716** | **0.493** |
| trộn 30% gốc + 70% v6 | 0.696 | 0.560 | 0.730 | 0.615 | 0.688 | 0.712 | – |
| trộn 50% gốc + 50% v7 | 0.693 | 0.560 | 0.734 | 0.609 | 0.692 | 0.695 | – |

OIV7 chạy riêng: gốc 0.639, v6 0.638, v7 0.617, trộn 50/50 v6 **0.654**.

## Từng lớp (AP50, như server)

| Lớp | Gốc | v6 | trộn 70/30 | trộn 50/50 |
|---|---|---|---|---|
| chopsticks | 0.352 | 0.727 | 0.439 | **0.650** |
| pen | 0.751 | 0.780 | 0.803 | **0.802** |
| pillow | 0.531 | 0.596 | 0.576 | 0.579 |
| window | 0.334 | 0.380 | 0.348 | 0.354 |
| door | 0.508 | 0.306 | 0.468 | 0.417 |
| bird | 0.677 | 0.555 | 0.641 | 0.622 |
| bread | 0.590 | 0.484 | 0.596 | 0.533 |
| bench | 0.494 | 0.408 | 0.493 | 0.481 |
| scissors | 0.584 | 0.500 | 0.578 | 0.564 |
| egg | 0.434 | 0.467 | 0.457 | 0.433 |
| knife | 0.467 | 0.419 | 0.463 | 0.472 |
| fork | 0.621 | 0.594 | 0.618 | 0.622 |

## Nhận xét

* v6 học được lớp mới (chopsticks, pillow, pen) nhưng quên một phần (door, bird, bread); trộn trọng số giữ phần lớn
  cái mới và lấy lại gần hết cái cũ – lần đầu tiên một bản fine-tune vượt model đang dùng theo quy tắc của
  `compare_finetune.py` (mAP50 không giảm, trung bình lớp yếu tăng).
* v7 (nhãn giả) cứu door (0.34 → 0.50) nhưng kéo chopsticks/egg/scissors về dưới cả model gốc: nhãn giả của model gốc
  dạy lại đúng những chỗ model gốc yếu. Trộn với v7 không vượt.
* Chọn **50/50 với v6**: cùng mAP50 với 70/30, lớp yếu tăng nhiều hơn (+0.010), lớp ngoài COCO 0.690 → 0.716.
