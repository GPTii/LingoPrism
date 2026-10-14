# AI – YOLOv10

Huấn luyện, đánh giá và export mô hình nhận diện vật thể YOLOv10 cho LingoPrism.

```
AI/
├── classes.yaml        # danh sách lớp vật thể ↔ khái niệm từ vựng
├── data.yaml           # cấu hình dataset (ultralytics)
├── scripts/            # tải/gộp dataset, chia tập, train, export, đánh giá
├── notebooks/          # notebook Colab/Kaggle
├── datasets/           # (gitignored) ảnh + nhãn
├── runs/               # (gitignored) kết quả train
└── weights/            # (gitignored) best.pt, .onnx, .tflite
```

Kết quả cần lưu cho báo cáo: Precision, Recall, mAP50, mAP50-95, confusion matrix, phân bố confidence.
Model export: ONNX (server, `BE/models/`) và TFLite float16 (app, `MOBILE/assets/ml_models/`).
