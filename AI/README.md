# AI – YOLOv10

Huấn luyện, đánh giá và export mô hình nhận diện vật thể YOLOv10 cho LingoPrism.

```
AI/
├── classes.yaml        # danh sách lớp vật thể ↔ khái niệm từ vựng
├── data.yaml           # cấu hình dataset (ultralytics)
├── scripts/            # tải/gộp dataset, chia tập, train, export, đánh giá
├── notebooks/          # train YOLO (Colab) + 01–08: một notebook cho mỗi thuật toán + so sánh tổng hợp (xem notebooks/README.md)
├── datasets/           # (gitignored) ảnh + nhãn
├── runs/               # (gitignored) kết quả train
└── weights/            # (gitignored) best.pt, .onnx, .tflite
```

Kết quả cần lưu cho báo cáo: Precision, Recall, mAP50, mAP50-95, confusion matrix, phân bố confidence.
Model export: ONNX (server, `BE/models/`) và TFLite float16 (app, `MOBILE/assets/ml_models/`).

## Model pretrained Open Images V7 (không cần train)

Model Open Images V7 của Ultralytics (601 lớp) phủ đủ 78/78 lớp train, cộng thêm 154 lớp `extra` đã có từ vựng (hoa, cây, quần áo, động vật...), tổng 232 lớp. Script gộp các lớp Open Images thành nhãn LingoPrism ngay trong ONNX, và server ghép thêm một model COCO (`YOLO_BASE_MODEL_PATH`).

- **Server** chạy **yolov8m-oiv7 + COCO yolov10m**, cả hai ở dạng **INT8** (nhanh ~2,5 lần, mAP50 0.705 → 0.698), rồi **CLIP** (MobileCLIP2-S2) kiểm tra lại nhãn của box mà YOLO không chắc. Kết quả đo ở `AI/report/yolo/ghi_chu.md`.
- **Điện thoại** chạy **yolov8s-oiv7** dạng TFLite vì nhẹ hơn.

```bash
pip install ultralytics onnx onnxslim tensorflow-cpu onnx2tf onnx_graphsurgeon sng4onnx tf_keras
# server: model m + COCO m
python AI/scripts/export_pretrained_oiv7.py --weights yolov8m-oiv7.pt --out AI/runs/oiv7-pretrained
python -c "from ultralytics import YOLO; YOLO('yolov10m.pt').export(format='onnx', simplify=True)"
cp AI/runs/oiv7-pretrained/yolov8m-oiv7-lingoprism.onnx yolov10m.onnx BE/models/
python AI/scripts/quantize_onnx.py AI/runs/oiv7-pretrained/yolov8m-oiv7-lingoprism.onnx   # -> ...-int8.onnx
python AI/scripts/quantize_onnx.py AI/runs/coco/yolov10m.onnx                               # -> yolov10m-int8.onnx
pip install open_clip_torch && python AI/scripts/export_clip.py                             # -> BE/models/clip-mobileclip2-s2.onnx
cp AI/runs/oiv7-pretrained/yolov8m-oiv7-lingoprism-int8.onnx AI/runs/coco/yolov10m-int8.onnx BE/models/
cd BE && python manage.py register_model --onnx models/yolov8m-oiv7-lingoprism-int8.onnx --card ../AI/runs/oiv7-pretrained/model_card.json
# điện thoại: model s dạng TFLite
python AI/scripts/export_pretrained_oiv7.py --weights yolov8s-oiv7.pt --out AI/runs/oiv7s --tflite
cp AI/runs/oiv7s/yolov8s-oiv7-lingoprism_float16.tflite MOBILE/assets/ml_models/lingoprism.tflite
cp AI/runs/oiv7s/labels.txt MOBILE/assets/ml_models/
```

CLIP chỉ được đổi nhãn khi YOLO không chắc (độ tin < 0,6), box chiếm ≥ 10% ảnh, CLIP chắc nhãn khác (≥ 0,6) và gần như loại
nhãn của YOLO (< 0,1); nhãn cũ được giữ làm phương án thay thế. Cho CLIP đổi mọi box thì ảnh từ vựng lên 90% nhưng tập test tụt
(CLIP kém ở vật nhỏ/bị che). Bỏ file `clip-mobileclip2-s2.onnx` (hoặc đặt `DETECTION_CLIP_PATH=`) là tắt bước này.

Điện thoại (khi không gọi được server) chạy bản TFLite float16 (~23 MB) một mình, không có COCO ghép kèm (74% top-1 trên bộ ảnh dưới).
Khi model không chắc (độ tin cậy < 0,6), web và app hỏi người học "Có phải: A / B / C?" (các lớp ứng viên kèm từ vựng);
từ được chọn mới được lưu, và lựa chọn đó được ghi lại là phản hồi sai/đúng cho lần train sau.

## Train lại (v3)

`build_dataset.py` bỏ ảnh có box "crowd" (COCO) / "group of" (Open Images), bỏ box vẽ trên tranh/poster, và với
`--pseudo-label` dùng `yolov8x-oiv7` + `yolo11x` gán nhãn bù cho các vật mà nguồn dữ liệu không gắn nhãn
(gối trong ảnh COCO, người trong ảnh Open Images…) – chỉ trên tập train, val/test giữ nhãn người gắn.
Notebook Colab đã bật sẵn (`PSEUDO = True`). Train xong so với model pretrained bằng `eval_photos.py` rồi chọn model tốt hơn.

## So sánh model trên ảnh thật

`AI/scripts/eval_photos.py` chạy đúng code inference của server; đáp án lấy từ tên file/thư mục (`cup.jpg`, `cup+spoon.jpg`, `pillow/IMG_01.jpg`).

```bash
python AI/scripts/eval_photos.py BE/media/photos --model coco=BE/models/yolov10n.onnx \
  --model oiv7+coco=BE/models/yolov8s-oiv7-lingoprism.onnx+BE/models/yolov10n.onnx
```

Kết quả trên 78 ảnh từ vựng thật (mỗi lớp một ảnh đã duyệt, không nằm trong dữ liệu train; notebook 07, 18/10/2026):

| Cách chạy | top-1 | tìm thấy (recall) | precision | box sai | ms/ảnh (CPU) |
|---|---|---|---|---|---|
| v1 tự train | 50% | 54% | 55% | 63 | ~32 |
| COCO yolov10n (chỉ 54 ảnh lớp COCO) | 80% | 81% | 71% | 39 | ~32 |
| v1 tự train + COCO | 65% | 67% | 58% | 76 | ~62 |
| OIV7 yolov8s | 74% | 79% | 87% | 16 | ~93 |
| **OIV7 + COCO** (đang dùng) | **83%** | **87%** | 78% | 38 | ~128 |

Số liệu đầy đủ, danh sách ảnh sai và ảnh có vẽ box: `AI/report/yolo/` (README.md, metrics.json, detections/).
Ảnh tự chụp để đánh giá sát thực tế bỏ vào `AI/eval_photos/` (tên file = vật trong ảnh) rồi chạy lại notebook 07.

## Báo lỗi nhận diện → hệ thống tự học (không cần train lại)

1. Người học bấm 👎 / "Vật khác…" / "Không phải đồ vật" trên kết quả nhận diện (web + app).
2. Server lưu vùng ảnh của vật đó thành vector (`BE/models/embedder.onnx`, tạo bằng `python AI/scripts/export_embedder.py`).
3. Lần sau mô hình đoán lại **đúng nhãn sai đó** trên vật **trông giống** (cosine ≥ 0,75) → server trả nhãn đúng, gắn "Đã học từ báo lỗi".
   Có hiệu lực ngay cho người báo; cho mọi người khi 3 người khác nhau báo cùng lỗi hoặc admin duyệt; bị 2 người phản đối thì tự huỷ.
4. Admin → Nhận diện YOLO → Báo lỗi → "Xuất dữ liệu train" → tải zip lên Drive thành `MyDrive/lingoprism_feedback.zip`
   → notebook Colab tự gộp vào tập train (`merge_feedback.py`, mỗi ảnh chép 3 lần vì là ca khó) ở lần train sau.
