# Luyện nói – đánh giá bộ chấm phát âm (06/11/2026)

Bộ chấm: `BE/apps/speech` (thiết kế: `docs/thiet-ke-luyen-noi.md`). Model nhận dạng âm vị wav2vec2 XLSR-53 espeak
(`facebook/wav2vec2-xlsr-53-espeak-cv-ft`, Xu và cộng sự 2021), ONNX INT8 318 MB, CPU; âm mong đợi từ espeak-ng;
căn chuỗi theo đặc trưng cấu âm; điểm kiểu GOP; thanh điệu theo cao độ (YIN).

## 1. So với giám khảo: speechocean762 (tập test, 2 500 câu tiếng Anh của người học, 5 giám khảo)

`AI/scripts/eval_speechocean.py` → `speechocean762.json`, `speechocean762.md`.

| Nhóm | Số câu | PCC câu (accuracy) | PCC câu (total) | PCC từ | Phát hiện từ đọc sai P / R / F1 |
|---|---|---|---|---|---|
| Tất cả | 2 499 | **0.632** | **0.660** | 0.321 | 0.227 / 0.638 / 0.335 |
| Trẻ em ≤ 12 tuổi | 1 039 | 0.519 | 0.560 | 0.305 | 0.174 / 0.670 / 0.276 |
| Trên 12 tuổi | 1 460 | **0.712** | **0.729** | 0.331 | 0.257 / 0.627 / 0.364 |

734 ms / câu trên CPU máy phát triển (một từ: 130–300 ms). PCC = hệ số tương quan Pearson.

* Ở mức câu, điểm của máy đi cùng chiều với giám khảo khá rõ (0.63; người lớn 0.71); giọng trẻ em khó hơn (0.52).
* Ở mức từ máy **khắt khe hơn** giám khảo: giám khảo chỉ đánh dấu 7% số từ có âm đọc sai (1 127 / 15 937), máy bắt
  được 64% trong số đó nhưng cũng báo thêm nhiều từ giám khảo bỏ qua (precision 0.23). Đã nới bằng: nguyên âm gần
  nhau là "gần đúng", âm có xác suất ≥ 0.3 ở chỗ đã căn coi như đã nói (GOP) – trên 200 câu đầu F1 0.14 → 0.23.

## 2. Giọng người bản ngữ (Lingua Libre, Wikimedia Commons, CC BY-SA)

| Ngôn ngữ | Kết quả |
|---|---|
| Tiếng Anh | think 99/100; cùng bản ghi chấm với "sink" → 84, báo /s/ đọc thành /θ/ |
| Tiếng Việt (19 từ) | điểm âm của người bản ngữ chỉ 27–92: model gần như không được train tiếng Việt → **tắt chấm chi tiết cho tiếng Việt** |
| Thanh tiếng Việt theo F0 (32 âm tiết bản ngữ) | 16 đúng, 7 gần đúng, 9 sai (hay nhầm nặng → ngang: giọng miền Nam) |

## 3. Kiểm tra trên trình duyệt (luồng thật: ghi âm → WAV 16 kHz → server → kết quả)

"go to school" (giọng TTS) → 98/100, ba từ xanh; "go to cool" → 84, chữ *school*: /s/ → thiếu.

## Hạn chế, hướng tiếp

* Thanh điệu dựa trên luật hình dạng đường cao độ: đánh dấu "thử nghiệm" trong app.
* Tiếng Việt cần model âm vị được train tiếng Việt (VIVOS, Common Voice vi) – fine-tune wav2vec2 khi có GPU.
* Chưa có: cặp âm dễ nhầm, nói theo, bài "đọc to" trong bài tập nhóm.
