# Notebook thuật toán

Mỗi thuật toán của đề cương một notebook. Notebook gọi đúng mã nguồn của server (`BE/apps/algorithms`), chạy trên
database thật và lưu kết quả vào bảng `ExperimentRun`, nên trang **Admin → Thuật toán AI** luôn hiện lần chạy mới nhất.
Mọi biểu đồ được lưu thêm thành ảnh PNG trong `figures/` để đưa vào báo cáo.

| Notebook | Thuật toán | Thời gian (CPU) |
|---|---|---|
| `01_sm2_fsrs.ipynb` | SM-2, FSRS-4.5: đường cong quên, khoảng cách ôn, so sánh dự đoán (log-loss, RMSE, AUC), hiệu chuẩn | ~1 phút |
| `02_ga_fsrs.ipynb` | Thuật toán di truyền tối ưu 17 tham số FSRS (train / test) | vài phút |
| `03_vip.ipynb` | VIP: hồ sơ nhầm lẫn thị giác từ confusion matrix YOLO + mô phỏng người học | ~1 phút |
| `04_word2vec.ipynb` | Word2Vec skip-gram negative sampling tự cài bằng NumPy | 300k câu: vài phút; 2 triệu câu: ~20 phút |
| `05_smart_distractor.ipynb` | Smart Distractor vs ngẫu nhiên cùng chủ đề | ~1 phút |
| `06_proximity.ipynb` | Chỉ mục lưới + Haversine vs brute force vs PostgreSQL | ~10 giây |
| `07_yolo_report.ipynb` | Báo cáo model nhận diện: model tự train (đường cong, AP từng lớp) + so sánh mọi cách chạy trên ảnh thật, ghi precision/recall của model đang dùng, lưu `AI/report/yolo/` | ~2 phút |
| `08_benchmark.ipynb` | **So sánh tổng hợp**: thử mọi phương án (64 tổ hợp lịch ôn × thứ tự ôn, dự đoán nhớ/quên, đáp án nhiễu, tìm điểm gần, nhận diện ảnh), tự chọn tốt nhất và áp dụng | ~2 phút |
| `train_yolov10_colab.ipynb` | Train YOLOv10 (cần GPU → chạy trên Google Colab) | 5–6 giờ |

## Cách chạy

1. Cài một lần (đã cài sẵn trên máy này):
   ```
   BE\.venv\Scripts\python -m pip install ipykernel matplotlib nbconvert
   BE\.venv\Scripts\python -m ipykernel install --user --name lingoprism --display-name "LingoPrism (BE venv)"
   ```
2. PostgreSQL phải đang chạy (không cần bật server Django).
3. Mở notebook bằng VS Code, chọn kernel **LingoPrism (BE venv)** → *Run All*.
   Hoặc chạy không cần mở: `BE\.venv\Scripts\python -m nbconvert --to notebook --execute --inplace 01_sm2_fsrs.ipynb`.

Tham số chỉnh được nằm ở ô đầu mỗi notebook (số thế hệ GA, số người học mô phỏng, số câu Word2Vec…).

**Lưu ý:**
- `02_ga_fsrs` với `APPLY = True` sẽ ghi bộ tham số FSRS mới vào hệ thống nếu tốt hơn trên tập test.
- `04_word2vec` chỉ ghi đè vector đang dùng khi đặt `SAVE_VECTORS = True`.
- Sau khi có model YOLO mới, chạy `07` rồi `03` để VIP dùng confusion matrix mới, cuối cùng `08` để chọn lại tổ hợp tốt nhất.
- `08_benchmark` với `APPLY = True` ghi cấu hình tốt nhất vào hệ thống. Cùng chức năng: `python manage.py benchmark_algorithms --apply`
  hoặc nút "Chạy & áp dụng tốt nhất" ở Admin → Thuật toán AI → Tổng hợp.
