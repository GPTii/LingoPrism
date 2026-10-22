# Nhận diện ảnh – số liệu cho báo cáo

Ngày đo: 19/10/2026. Ảnh từ vựng: mỗi từ một ảnh thật đã duyệt (Wikimedia Commons), không nằm trong dữ liệu train. Ảnh tự chụp: AI/eval_photos/ (tên file = vật trong ảnh). 'combined' = cả hai model cùng chạy, mỗi vật giữ nhãn tự tin nhất (cách server đang chạy). precision = box có nhãn đúng / mọi box.

## Ảnh thật (ảnh từ vựng / ảnh tự chụp)

| Bộ ảnh | Cách chạy | Số ảnh | Top-1 | Tìm thấy | Precision | Box sai | ms/ảnh |
|---|---|---|---|---|---|---|---|
| ảnh từ vựng | lingoprism-yolov10n riêng lẻ | 78 | 50% | 54% | 55% | 63 | 39.8 |
| ảnh từ vựng | COCO gốc | 54 | 87% | 94% | 65% | 53 | 126.2 |
| ảnh từ vựng | lingoprism-yolov10n kết hợp với COCO | 78 | 81% | 91% | 66% | 72 | 230.5 |
| ảnh từ vựng | yolov8s-oiv7-lingoprism riêng lẻ | 231 | 62% | 67% | 62% | 150 | 160.9 |
| ảnh từ vựng | yolov8s-oiv7-lingoprism kết hợp với COCO | 231 | 77% | 85% | 63% | 209 | 338.5 |
| ảnh từ vựng | yolov8m-oiv7-lingoprism riêng lẻ | 231 | 66% | 69% | 61% | 163 | 148.2 |
| ảnh từ vựng | yolov8m-oiv7-lingoprism kết hợp với COCO **(đang dùng)** | 231 | 77% | 85% | 61% | 227 | 324.1 |

## Tập test có gắn box (2542 ảnh: 796 COCO-2017 val, 1746 Open Images V7 val, 10016 vật)

| Cách chạy | Precision | Recall | F1 | mAP50 | mAP50-95 | Accuracy (nhãn) | Accuracy (phát hiện) | ms/ảnh |
|---|---|---|---|---|---|---|---|---|
| v1 tự train | 0.685 | 0.353 | 0.466 | 0.453 | 0.322 | 0.909 | 0.304 | 35.7 |
| COCO yolov10n | 0.774 | 0.507 | 0.613 | 0.609 | 0.468 | 0.955 | 0.442 | 44.8 |
| v1 + COCO | 0.679 | 0.473 | 0.558 | 0.517 | 0.392 | 0.941 | 0.387 | 80.5 |
| OIV7 s 78 lớp + COCO n (cũ) | 0.778 | 0.500 | 0.609 | 0.633 | 0.493 | 0.957 | 0.438 | 212.5 |
| OIV7 yolov8s | 0.864 | 0.339 | 0.487 | 0.595 | 0.468 | 0.951 | 0.322 | 206.9 |
| OIV7 s + COCO n (cũ) | 0.779 | 0.494 | 0.604 | 0.624 | 0.486 | 0.957 | 0.433 | 251.7 |
| COCO yolov10m | 0.781 | 0.646 | 0.707 | 0.723 | 0.582 | 0.966 | 0.547 | 342.2 |
| OIV7 yolov8m | 0.862 | 0.386 | 0.533 | 0.639 | 0.521 | 0.963 | 0.364 | 430.5 |
| OIV7 m + COCO m | 0.769 | 0.611 | 0.681 | 0.705 | 0.574 | 0.967 | 0.516 | 772.7 |
| OIV7 m + COCO m + CLIP | 0.748 | 0.610 | 0.672 | 0.705 | 0.575 | 0.963 | 0.506 | 831.4 |
| OIV7 m + COCO m, INT8 | 0.771 | 0.603 | 0.677 | 0.698 | 0.565 | 0.967 | 0.512 | 265.4 |
| OIV7 m + COCO m, INT8 + CLIP (đang dùng) | 0.751 | 0.602 | 0.668 | 0.696 | 0.564 | 0.961 | 0.502 | 322.1 |

Số liệu từng lớp và ma trận nhầm lẫn: `testset/metrics.json`, `testset/confusion_matrix_*.json`. Biểu đồ: `07_test_chi_so.png`, `07_test_pr_f1.png`, `07_test_ma_tran_nham_lan.png`, `07_test_ma_tran_nham_lan_top.png`, `07_test_ma_tran_nham_lan_v1.png`, `07_test_ap_tung_lop.png`.

## Ảnh từ vựng: các ảnh model đang dùng trả lời sai (top-1)

| Đáp án | Model trả lời | Độ tin | Có trong kết quả |
|---|---|---|---|
| ambulance | person | 0.808 | ✗ |
| arm | person | 0.9212 | ✗ |
| beer | wine glass | 0.9533 | ✗ |
| belt | (không thấy gì) |  | ✗ |
| bookshelf | person | 0.4094 | ✓ |
| bread | donut | 0.9756 | ✓ |
| candy | (không thấy gì) |  | ✗ |
| cheese | orange | 0.6755 | ✓ |
| chopsticks | pen | 0.5465 | ✓ |
| coat | face | 0.7499 | ✓ |
| cucumber | flower | 0.6837 | ✗ |
| dining table | vase | 0.9107 | ✓ |
| doll | face | 0.5 | ✓ |
| drum | suitcase | 0.6362 | ✗ |
| ear | face | 0.6364 | ✗ |
| face | person | 0.9481 | ✓ |
| flashlight | bottle | 0.6099 | ✗ |
| flute | pen | 0.3636 | ✗ |
| football | sports ball | 0.583 | ✗ |
| french fries | (không thấy gì) |  | ✗ |
| hair | person | 0.9423 | ✗ |
| hair drier | person | 0.9289 | ✓ |
| handbag | (không thấy gì) |  | ✗ |
| helicopter | airplane | 0.827 | ✓ |
| helmet | sports ball | 0.2501 | ✗ |
| ice cream | fire hydrant | 0.8424 | ✗ |
| jacket | person | 0.7177 | ✗ |
| keyboard | person | 0.9289 | ✓ |
| knife | scissors | 0.9874 | ✗ |
| lemon | orange | 0.9363 | ✗ |
| mango | orange | 0.9033 | ✗ |
| milk | cup | 0.9581 | ✗ |
| mirror | vase | 0.9107 | ✗ |
| pants | person | 0.9033 | ✓ |
| peach | apple | 0.8699 | ✗ |
| pig | cow | 0.7926 | ✓ |
| pillow | bed | 0.8424 | ✓ |
| plate | knife | 0.9002 | ✓ |
| potato | (không thấy gì) |  | ✗ |
| potted plant | chair | 0.9289 | ✓ |
| printer | (không thấy gì) |  | ✗ |
| rocket | person | 0.808 | ✓ |
| sandals | shoes | 0.6784 | ✗ |
| seat belt | person | 0.6862 | ✗ |
| shorts | (không thấy gì) |  | ✗ |
| shrimp | (không thấy gì) |  | ✗ |
| skateboard | person | 0.9002 | ✓ |
| spoon | scissors | 0.8567 | ✗ |
| suit | person | 0.8165 | ✗ |
| tablet | flower | 0.7888 | ✗ |
| tea | bowl | 0.9662 | ✗ |
| towel | socks | 0.7539 | ✓ |
| volleyball | frisbee | 0.7737 | ✗ |

Ảnh có vẽ box: `detections/word_photos/dung`, `detections/word_photos/sai` (xanh = đúng nhãn, đỏ = sai).
Biểu đồ: `AI/notebooks/figures/07_so_sanh_model_anh_that.png`, `07_dung_sai_tung_lop.png`, `07_toc_do.png`.

## Ghi chú các lần thay đổi model

Notebook 07 chép nguyên file `AI/report/yolo/ghi_chu.md` vào cuối báo cáo này, nên phần này được viết tay và không mất khi chạy lại.

**v4: fine-tune trên Colab, ngày 18/10/2026, không dùng**

- Cách làm: fine-tune yolov8s-oiv7, 150 ảnh/lớp, nhãn bù tự gán (pseudo-label), đóng băng 10 lớp backbone.
- Quá trình train: dừng sớm ở epoch 10, vì mAP tốt nhất đã đạt ở epoch 2.
- Kết quả trên tập test: mAP50 0.544 khi chạy riêng, 0.578 khi kết hợp COCO. Cả hai đều thấp hơn model gốc chưa fine-tune (0.595–0.602) và cách server đang chạy (0.633).
- Nguyên nhân: nhãn tự gán làm model lệch. Precision giảm từ 0.864 xuống 0.694.

**Mở rộng từ 78 lên 232 lớp, ngày 18/10/2026 (sau đó chuyển sang model lớn hơn, xem mục dưới)**

- Lý do: model 78 lớp gặp vật ngoài danh sách thì ép vào lớp gần nhất. Ví dụ bó hoa ra "broccoli" hoặc "orange", tức là ra món ăn.
- Cách làm: Open Images V7 đã biết sẵn 601 loại vật. Script gộp thêm 154 lớp mà từ điển đã có từ, gồm hoa, cây, bình hoa, quần áo, động vật, đồ ăn, đồ dùng và bộ phận cơ thể (`extra` trong `AI/classes.yaml`). Không cần train lại.
- Kết quả:

| Đo trên | 78 lớp (cũ) | 232 lớp (mới) |
|---|---|---|
| Tập test 2 542 ảnh, 78 lớp – mAP50 | 0.633 | 0.624 |
| Tập test – độ đúng nhãn | 0.957 | 0.957 |
| Ảnh từ vựng của 78 từ cũ – top-1 / tìm thấy | 83% / 87% | 83% / 87% |
| Ảnh từ vựng của 78 từ cũ – precision | 78% | 67% |
| Ảnh từ vựng của 153 từ mới – top-1 / tìm thấy | không nhận ra được | 56% / 64% |
| 12 ảnh bó hoa (Wikimedia Commons) | potted plant / broccoli / orange / không thấy | flower, vase |

- Precision trên ảnh 78 từ cũ giảm vì có thêm 28 box của lớp mới, đa số là vật có thật trong ảnh: 12 flower trong ảnh chậu cây, vase, tree, face. Precision ở đây chỉ tính box đúng đáp án của ảnh, nên con số này là cận dưới.
- Ở bộ ảnh 153 từ mới, top-1 hay sai khi vật chính nằm trên người: arm, face, jacket, pants ra "person", và mouth, nose ra "face". Kết quả vẫn có người hoặc mặt, chỉ là không phải box tự tin nhất. Ngoài ra còn nhầm giữa các vật gần nhau, như lemon/mango/peach ra orange, hoặc sandals ra shoes.

**Model lớn hơn: OIV7 m + COCO m, ngày 18/10/2026 (sau đó thêm INT8 + CLIP, xem mục dưới)**

- Cách làm: vẫn là model pretrained của Ultralytics, không train lại. Đổi yolov8s-oiv7 thành **yolov8m-oiv7** (cũng gộp về 232 lớp), và đổi model COCO yolov10n thành **yolov10m**. Điện thoại vẫn dùng bản s (TFLite) để chạy offline nhanh.
- Kết quả trên tập test 2 542 ảnh (78 lớp):

| Cách chạy | P | R | F1 | mAP50 | mAP50-95 | ms/ảnh (máy dev) |
|---|---|---|---|---|---|---|
| OIV7 s + COCO n (cũ) | 0.779 | 0.494 | 0.604 | 0.624 | 0.486 | 252 |
| OIV7 s + COCO s | 0.750 | 0.576 | 0.651 | 0.661 | 0.525 | 361 |
| OIV7 m + COCO n | 0.774 | 0.518 | 0.621 | 0.647 | 0.515 | 475 |
| OIV7 m + COCO s | 0.747 | 0.590 | 0.659 | 0.681 | 0.549 | 584 |
| OIV7 s + COCO m | 0.771 | 0.598 | 0.673 | 0.687 | 0.553 | 549 |
| **OIV7 m + COCO m** | **0.769** | **0.611** | **0.681** | **0.705** | **0.574** | 773 |

- Phần lớn mức tăng đến từ model COCO lớn hơn: recall tăng từ 0.494 lên 0.611, nghĩa là bỏ sót ít vật hơn. Model OIV7 bản m giúp thêm ở các lớp COCO không có (mũ, gối, cửa…).
- Đổi lại, mỗi ảnh chậm hơn khoảng 3 lần nhưng vẫn dưới 1 giây trên máy dev.
- Dòng "COCO yolov10m" chạy riêng (mAP50 0.723) chỉ tính trên các lớp mà COCO biết, nên không so trực tiếp được với các dòng ghép.
- **Đã thử và bỏ:** ngưỡng tin cậy riêng cho từng lớp (`AI/scripts/tune_thresholds.py`). Ngưỡng được chọn trên một nửa tập test và kiểm tra trên nửa còn lại. F1 không tăng (0.690 → 0.686), tức là ngưỡng chọn ra chỉ khớp với nửa dùng để chọn, nên giữ ngưỡng chung 0.25.

**INT8 + CLIP kiểm tra lại nhãn, ngày 19/10/2026, đang dùng**

- Vẫn không train lại. Thử 4 cách vá điểm yếu của OIV7 m + COCO m, mỗi cách đo trên tập test 2 542 ảnh và 231 ảnh từ vựng:

| Cách thử | mAP50 tập test | Top-1 ảnh từ vựng | Thời gian | Kết luận |
|---|---|---|---|---|
| Không đổi (OIV7 m + COCO m) | 0.705 | 68% | 773 ms/ảnh | mốc so sánh |
| Xếp box to và chắc lên đầu thay vì chỉ theo độ tin | 0.705 | 68% → 67% | như cũ | bỏ |
| Ảnh vào 800 px thay vì 640 px | 0.697–0.700 | – | chậm hơn ~1,6 lần | bỏ: model được train ở 640 px |
| CLIP đổi nhãn mọi box | 0.653 | 90% | +~170 ms/box | bỏ: CLIP kém ở vật nhỏ, bị che |
| **CLIP chỉ đổi nhãn box YOLO không chắc** | **0.705** | **77%** | +~60 ms/ảnh | **dùng** |
| **INT8 cả hai model** | **0.698** | – | **265 ms/ảnh** | **dùng** |

- CLIP: MobileCLIP2-S2 (OpenCLIP, train trên 2 tỉ cặp ảnh – chữ, không fine-tune) so vùng ảnh của box với câu "a photo of a …" của 232 nhãn (`AI/scripts/export_clip.py`, `inference.LabelVerifier`). Chỉ được đổi nhãn khi YOLO không chắc (độ tin < 0,6), box chiếm ≥ 10% ảnh, CLIP chắc nhãn khác (≥ 0,6) và gần như loại nhãn của YOLO (< 0,1). Nhãn của YOLO được giữ làm phương án thay thế cho người học chọn.
- Sửa được đúng kiểu lỗi nhầm vật giống nhau: chanh/xoài/đào → cam/táo, dép → giày, violin → guitar, dao/thìa → kéo, mũi/tai/miệng → mặt, taxi → car. Trên 231 ảnh từ vựng không có ảnh nào đang đúng bị đổi thành sai.
- INT8: lượng tử hoá tĩnh 8-bit (`AI/scripts/quantize_onnx.py`), phần giải mã box giữ số thực. Đo 2 luồng CPU như server: OIV7 m 387 → 153 ms, COCO m 314 → 128 ms. File nhỏ hơn 4 lần (27 MB + 17 MB thay vì 105 MB + 62 MB); CLIP thêm 144 MB.
- Cấu hình server cuối (INT8 + CLIP) trên tập test: P 0.751, R 0.602, F1 0.668, mAP50 0.696, mAP50-95 0.564, 322 ms/ảnh trên máy dev. Ảnh từ vựng: top-1 77%, tìm thấy 85% (trước 68% / 74%).
- Lưu ý khi đọc số: ảnh từ vựng lấy từ Wikimedia Commons nên CLIP có thể đã thấy lúc train, vì vậy ngưỡng được chọn sao cho tập test COCO/OI không tụt. INT8 được hiệu chỉnh thang giá trị trên 96 ảnh của tập test (không dùng nhãn). Các dòng OIV7 s trong bảng ảnh thật ở trên giờ cũng chạy kèm COCO m INT8 + CLIP, nên không còn là cách chạy cũ.
