# Tăng độ chính xác không cần train: model OIV7 lớn hơn, trộn trọng số, WBF

Tập test 2542 ảnh (COCO val2017 + Open Images val), INT8 như server, ghép với COCO yolov10m INT8. Đo ngày 06/11/2026.

## Như server (có CLIP)

| OIV7 | mAP50 | mAP50-95 | P | R | Lớp COCO | Lớp khác | TB 21 lớp yếu | OIV7 ms/ảnh* |
|---|---|---|---|---|---|---|---|---|
| yolov8m (đang dùng) | 0.696 | 0.564 | 0.751 | 0.602 | 0.699 | 0.690 | 0.483 | 157 |
| trộn 50% yolov8m + 50% fine-tune v6 | 0.701 | 0.565 | 0.736 | 0.612 | 0.694 | 0.716 | 0.493 | 157 |
| **yolov8l** (Ultralytics, không train) | **0.708** | **0.576** | 0.754 | 0.609 | **0.701** | **0.724** | **0.496** | 257 |

\* đo trên máy phát triển (10 luồng, onnxruntime CPU), 40 ảnh; model COCO m thêm 134 ms.
OIV7 chạy riêng: m 0.639 / 0.521, l 0.655 / 0.539 (mAP50 / mAP50-95).

## Cách gộp box của hai model (không CLIP, `AI/scripts/eval_wbf.py`)

| OIV7 | Cách gộp | mAP50 | mAP50-95 | P | R |
|---|---|---|---|---|---|
| m | server: box tự tin nhất thắng | 0.698 | 0.565 | 0.771 | 0.603 |
| m | WBF trung bình, COCO trọng số 2 | 0.701 | 0.565 | 0.856 | 0.553 |
| trộn 50/50 | server | 0.701 | 0.565 | 0.754 | 0.613 |
| trộn 50/50 | WBF trung bình, COCO trọng số 2 | 0.706 | 0.567 | 0.839 | 0.568 |
| l | server | 0.708 | 0.576 | 0.774 | 0.611 |
| **l** | **WBF trung bình, COCO trọng số 2** | **0.710** | **0.576** | **0.860** | 0.562 |

WBF (Solovyev et al., *Weighted boxes fusion*, 2021): box cùng nhãn của hai model (IoU ≥ 0.55) gộp thành một, toạ độ
trung bình theo độ tin cậy, độ tin cậy = trung bình hai model (model không thấy vật tính 0). Lớp chỉ một model biết
thì model đó tự quyết.

## Nhận xét

* Đổi yolov8m → **yolov8l** là bước tăng lớn nhất (+0.012 mAP50, +0.012 mAP50-95) và không cần train; giá là ~100 ms
  mỗi ảnh trên CPU.
* WBF tăng mAP ít (+0.002–0.005) nhưng ở ngưỡng hiển thị 0.25 precision 0.77 → 0.86: ít box sai hơn hẳn cho người học,
  đổi lại recall giảm ~5 điểm.
* Fine-tune trên Colab miễn phí (v5–v7) không vượt được model gốc; chỉ khi trộn trọng số với model gốc (WiSE-FT) mới
  hơn một chút (`finetune_soup.md`). Fine-tune yolov8l rồi trộn là bước tiếp theo nếu có GPU.

## Cấu hình đưa lên server (06/11/2026)

yolov8l-oiv7 INT8 + COCO yolov10m INT8, gộp **WBF** (IoU 0.55, COCO trọng số 2, mỗi model giải mã từ 0.05, hiện box
từ 0.25) + CLIP đổi nhãn khi YOLO < 0.6 (như cũ). yolov8m vẫn đăng ký, không kích hoạt, làm bản dự phòng.

### Tập test 2542 ảnh

| Cấu hình | P | R | mAP50 | mAP50-95 |
|---|---|---|---|---|
| Cũ: yolov8m, gộp "tự tin nhất thắng", CLIP < 0.6 | 0.751 | 0.602 | 0.696 | 0.564 |
| yolov8l, WBF, CLIP < 0.4 | 0.845 | 0.562 | 0.716 | 0.585 |
| **Mới: yolov8l, WBF, CLIP < 0.6** | **0.831** | 0.559 | **0.712** | **0.583** |

### Ảnh thật (`AI/scripts/eval_word_photos.py`, `word_photos.json`)

Ảnh từ vựng: ảnh Wikimedia đã duyệt của mỗi từ có nhãn YOLO (một vật). Ảnh nhiều vật: 21 ảnh Wikimedia Commons trong
`AI/eval_photos/` (nguồn, giấy phép: `AI/eval_photos/SOURCES.md`), gắn nhãn bằng tay.

| Bộ ảnh | Cấu hình | Số ảnh | Top-1 | Top-1 lớp ngoài COCO | Tìm thấy | Precision | Box sai |
|---|---|---|---|---|---|---|---|
| ảnh từ vựng | cũ | 231 | 77% | 71% | 85% | 61% | 227 |
| ảnh từ vựng | **mới** | 231 | **81%** | **77%** | **87%** | **69%** | **160** |
| ảnh nhiều vật | cũ | 21 | 76% | 77% | 81% | 73% | 47 |
| ảnh nhiều vật | **mới** | 21 | **86%** | 77% | 74% | 72% | **39** |

Tách từng phần trên ảnh từ vựng (top-1 / box sai): m + gộp cũ + CLIP 0.6 77% / 227; m + gộp cũ + CLIP 0.4 70% / 259;
l + gộp cũ + CLIP 0.6 76% / 233; l + gộp cũ + CLIP 0.4 69% / 266; m + WBF + CLIP 0.6 81% / 155; l + WBF + CLIP 0.6
81% / 160; l + WBF + CLIP 0.4 72% / 200. → WBF mang lại phần lớn cái lợi trên ảnh thật; CLIP phải giữ ngưỡng 0.6 (hạ
xuống 0.4 cho tập test +0.004 mAP nhưng mất 9 điểm top-1 trên ảnh thật); yolov8l hơn m trên tập test (+0.010 mAP50),
ngang m trên ảnh từ vựng.
