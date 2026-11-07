# Tài liệu LingoPrism

Mọi tài liệu của dự án và **toàn bộ nguồn số liệu, hình, sơ đồ dùng cho báo cáo đồ án** – gom về một chỗ để tra.
Bản thảo báo cáo, đề cương, phiếu chấm (file Word / PDF riêng tư) nằm trong `private/bao-cao/` – không lên git.

## 1. Dự án

| Tài liệu | Nội dung |
|---|---|
| [PLAN.md](PLAN.md) | Kế hoạch, kiến trúc, mô hình dữ liệu, quy tắc dữ liệu ngôn ngữ (§3b), các giai đoạn |
| [FEATURES.md](FEATURES.md) | Danh sách tính năng theo vai trò |
| [../CHANGELOG.md](../CHANGELOG.md) | Lịch sử phiên bản (web, app, server) |
| [../SECURITY.md](../SECURITY.md) | Chính sách bảo mật, báo lỗi |
| [../README.md](../README.md) | Chạy local, cấu trúc thư mục, deploy |

## 2. Thiết kế

| Tài liệu | Nội dung |
|---|---|
| [thiet-ke/luyen-noi.md](thiet-ke/luyen-noi.md) | Luyện nói – chấm phát âm từng âm (wav2vec2 + espeak + thanh điệu) |
| [database/](database/README.md) | Sơ đồ CSDL (ERD theo nhóm bảng, `.mmd` + `.png`), script sinh lại |
| [diagrams/](diagrams/README.md) | 72 sơ đồ Mermaid: use case, hoạt động, tuần tự, kiến trúc (`.mmd` + `.png`), [tất cả mã](diagrams/TAT_CA_MA_MERMAID.md) |

## 3. Số liệu & hình cho báo cáo (chương thực nghiệm)

| Chủ đề | Bảng / số liệu | Notebook vẽ hình |
|---|---|---|
| Lặp lại ngắt quãng SM-2 / FSRS, GA, VIP | [AI/report/experiments/](../AI/report/experiments/bang_tong_hop.md) | [01](../AI/notebooks/01_sm2_fsrs.ipynb) · [02](../AI/notebooks/02_ga_fsrs.ipynb) · [03](../AI/notebooks/03_vip.ipynb) |
| Word2Vec, Smart Distractor, Proximity | [bang_ket_qua.md](../AI/report/experiments/bang_ket_qua.md) | [04](../AI/notebooks/04_word2vec.ipynb) · [05](../AI/notebooks/05_smart_distractor.ipynb) · [06](../AI/notebooks/06_proximity.ipynb) |
| Nhận diện ảnh (YOLO, ensemble, WBF, fine-tune) | [AI/report/yolo/](../AI/report/yolo/README.md) – [nâng cấp](../AI/report/yolo/ensemble_upgrade.md), [fine-tune](../AI/report/yolo/finetune_soup.md) | [07](../AI/notebooks/07_yolo_report.ipynb) |
| Benchmark thuật toán | [AI/report/experiments/](../AI/report/experiments/) | [08](../AI/notebooks/08_benchmark.ipynb) |
| Geofence & realtime trên server thật | [production.json](../AI/report/experiments/production.json) | [09](../AI/notebooks/09_geofence_realtime.ipynb) · [10](../AI/notebooks/10_production_report.ipynb) |
| Chấm phát âm (speechocean762, giọng bản ngữ) | [AI/report/speech/](../AI/report/speech/README.md) | – |
| Hình đã xuất từ notebook | [AI/notebooks/figures/](../AI/notebooks/figures/) (40 hình) | |

Chạy lại thực nghiệm trên server: `scripts/run-experiments.bat`. Dữ liệu huấn luyện, model: [AI/README.md](../AI/README.md).
