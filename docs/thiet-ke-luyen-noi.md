# Thiết kế: Luyện nói – chấm phát âm chi tiết

Ngày: 06/11/2026. Trạng thái: **bản thiết kế, chưa làm**.

## 1. Hiện trạng

App đã có "Luyện phát âm" (web `SpeakPage.tsx` + `lib/pronounce.ts`, điện thoại `modules/speak` + `widgets/speak_check.dart`):

1. Người học bấm mic, đọc từ.
2. Nhận dạng giọng nói **của điện thoại / trình duyệt** (Google / Apple) trả về chữ nghe được.
3. So chữ nghe được với chữ đúng bằng khoảng cách Levenshtein (tiếng Trung so từng chữ Hán, tiếng khác so từng chữ cái) → điểm 0–100, tô đỏ chữ sai.

Hạn chế:

| Vấn đề | Ví dụ |
|---|---|
| Bộ nhận dạng **tự sửa** về từ có thật gần nhất: phát âm sai vẫn ra đúng chữ | nói "tink" vẫn nhận thành *think* → 100 điểm |
| So **chữ cái**, không phải **âm** | *knife* – chữ k câm; chữ đúng nhưng âm sai không biết |
| Không chấm **thanh điệu** riêng | 妈 mā đọc thành mà: chỉ biết sai khi máy ra chữ khác |
| Không nói **sai ở đâu, sửa thế nào** | chỉ có "Chưa đúng 40/100" |
| Không lưu kết quả | không có tiến bộ theo thời gian, không biết âm nào hay sai |
| Chỉ có từ đơn | chưa luyện câu, cặp âm dễ nhầm, nói theo (shadowing) |

## 2. Mục tiêu

* Chấm tới **từng âm** (âm vị) và **thanh điệu** (tiếng Trung, tiếng Việt), không bị bộ nhận dạng "sửa hộ".
* Phản hồi dễ hiểu bằng tiếng Việt: âm nào sai, nghe giống âm gì, mẹo khẩu hình, nghe lại giọng mẫu chậm.
* Lưu lịch sử → biểu đồ tiến bộ, danh sách "âm hay sai của bạn", ôn lại đúng âm đó.
* Chạy trên server hiện tại (CPU, không GPU), **không cần API trả phí**.
* Đo được độ tin cậy cho báo cáo (so với điểm của giám khảo người).

## 3. Các cách chấm phát âm (tìm hiểu)

| Cách | Ý tưởng | Ưu | Nhược |
|---|---|---|---|
| A. STT + so chữ (đang có) | nhận dạng ra chữ rồi so | đơn giản, chạy offline | tự sửa lỗi, không biết âm |
| B. GOP + căn chỉnh cưỡng bức (Witt & Young, 2000) | mô hình âm học tính xác suất từng âm mong đợi trên đoạn âm thanh đã căn | chuẩn mực trong nghiên cứu, chấm từng âm | cần Kaldi / mô hình âm học từng ngôn ngữ, khó dựng |
| C. **Nhận dạng âm vị (wav2vec2 + CTC) + so khớp chuỗi âm** | mô hình nghe ra chuỗi âm IPA *thật sự đã nói* rồi căn với chuỗi âm mong đợi | không tự sửa thành từ; một mô hình đa ngôn ngữ (en, vi, zh); có xác suất từng âm (giống GOP); chạy được ONNX trên CPU | mô hình ~300M tham số (INT8 ~320 MB), 1–3 s mỗi câu trên CPU (cần đo); không có dấu thanh |
| D. Phân tích cao độ F0 (pYIN) | đo đường cao độ của mỗi âm tiết, so mẫu thanh | chấm được thanh điệu | cần biết ranh giới âm tiết (lấy từ C) |
| E. API đám mây (Azure Pronunciation Assessment, Speechace…) | gửi âm thanh, nhận điểm | chất lượng cao, ít code | tốn phí / cần tài khoản, gửi giọng người học ra ngoài, trẻ em → vấn đề riêng tư |

**Chọn: C + D**, giữ A làm chế độ nhanh / offline. Lý do: không phí, không gửi giọng ra bên thứ ba, một mô hình cho cả ba ngôn ngữ, và có tính mới để viết trong đồ án (nhận dạng âm vị + căn chuỗi + cao độ).

Mô hình ứng viên (Hugging Face, train sẵn để nhận dạng âm vị đa ngôn ngữ, đầu ra IPA kiểu espeak; Xu và cộng sự 2021,
*Simple and Effective Zero-shot Cross-lingual Phoneme Recognition*):
`facebook/wav2vec2-xlsr-53-espeak-cv-ft` (hoặc `wav2vec2-lv-60-espeak-cv-ft`). Chọn bản nào sau khi đo trên dữ liệu chấm.

## 4. Luồng chấm (server)

```
Người học bấm mic ──► ghi âm 16 kHz mono (≤ 8 s) ──► POST /api/v1/speech/assess/ {item, audio}
                                                         │
             ┌───────────────────────────────────────────┤
             ▼                                           ▼
  1. Chuỗi âm MONG ĐỢI                        2. Chuỗi âm NGHE ĐƯỢC
     en: IPA của từ (Word.ipa, đã duyệt)          wav2vec2 (ONNX INT8) → xác suất CTC từng khung 20 ms
     zh: pinyin (đã duyệt) → bảng pinyin→IPA      → chuỗi IPA + vị trí thời gian mỗi âm
         + số thanh 1–5
     vi: chữ quốc ngữ → bảng âm vị tiếng Việt
         (âm đầu / vần / thanh, viết tay theo
          quy tắc chính tả)
             │                                           │
             └──────────────► 3. CĂN CHUỖI ◄─────────────┘
                 Needleman–Wunsch, chi phí thay thế = khoảng cách đặc trưng cấu âm
                 (thư viện panphon: /θ/ gần /s/, /t/ hơn /m/) → mỗi âm: đúng / thay / thiếu / thừa
                                    │
                 4. ĐIỂM TỪNG ÂM: xác suất CTC trung bình của âm mong đợi trên đoạn đã căn (kiểu GOP)
                                    │
                 5. THANH ĐIỆU (zh, vi): cắt âm tiết theo thời gian ở bước 2 → F0 bằng pYIN → chuẩn hoá theo
                    giọng người nói (semitone so với trung vị) → so đường cong mẫu (zh: 1 ngang cao, 2 lên,
                    3 xuống-lên, 4 xuống; vi: ngang, huyền, sắc, hỏi, ngã, nặng) bằng DTW → thanh nghe được
                                    │
                 6. TỔNG HỢP: điểm âm (60%) + thanh (25%) + đầy đủ, không thiếu âm (15%) → 0–100
                    + danh sách lỗi có mã (vd en.TH_AS_S, zh.TONE3_AS_2, vi.FINAL_DROPPED)
```

Bảng mẹo sửa lỗi (soạn tay, nguồn giáo trình ngữ âm, có duyệt như dữ liệu từ vựng): mã lỗi → câu giải thích tiếng Việt +
mẹo khẩu hình + cặp từ luyện. Ví dụ hay gặp ở người Việt:

| Ngôn ngữ | Mã | Mẹo |
|---|---|---|
| en | TH_AS_S / TH_AS_T | /θ/ trong *think*: đặt đầu lưỡi giữa hai hàm răng rồi thổi, không chạm răng như /t/ |
| en | FINAL_DROPPED | âm cuối /s/, /t/, /d/, /k/ bị nuốt: *cats* → nói rõ /s/ cuối |
| en | SHIP_SHEEP | /ɪ/ ngắn và /iː/ dài |
| en | R_AS_Z | /r/ không rung, lưỡi cong, không chạm |
| zh | ZH_AS_Z, X_AS_S, Q_AS_CH | âm uốn lưỡi / mặt lưỡi |
| zh | TONE3_AS_2 | thanh 3 phải xuống thấp rồi mới lên; đứng trước thanh 3 khác thì đọc thành thanh 2 (biến điệu) |
| vi | HOI_NGA | người miền Nam dễ gộp hỏi/ngã – chấm "gần đúng", không tính sai nặng |

## 5. Dữ liệu (BE)

* `PronunciationItem` – thứ để đọc: `word` hoặc `sentence` (ExampleSentence), `language`, `expected_phones` (JSON:
  âm tiết → âm vị, thanh), sinh từ dữ liệu đã duyệt, cache lại.
* `PronunciationAttempt` – `user`, `item`, `score`, `phone_score`, `tone_score`, `completeness`, `phones` (JSON kết quả
  từng âm), `errors` (danh sách mã lỗi), `heard_ipa`, `mode` (`quick` STT / `detailed`), `ms`, `created_at`.
  File ghi âm **không lưu mặc định** (tôn trọng riêng tư, nhất là trẻ em); chỉ lưu khi người học bật "cho phép dùng để
  cải thiện" – tài khoản trẻ em không có lựa chọn này.
* `PhoneSkill` – tổng hợp theo người học × âm (số lần, tỉ lệ đúng, lần cuối) → "âm hay sai của bạn", và đưa vào lịch ôn
  (SRS) như từ vựng.

API:

| Phương thức | Đường dẫn | Việc |
|---|---|---|
| POST | `/speech/assess/` | gửi âm thanh + item → kết quả chấm (đồng bộ, ≤ 3 s; quá thì trả `job_id`, Celery làm) |
| GET | `/speech/items/?mode=word|sentence|pairs|weak` | danh sách bài luyện |
| GET | `/speech/progress/` | điểm theo ngày, âm yếu nhất |
| GET | `/speech/tips/<code>/` | mẹo của một mã lỗi |

## 6. Màn hình (web + điện thoại)

**Màn luyện một từ / câu**
1. Thẻ từ: chữ, IPA / pinyin, hình, nút loa (giọng mẫu, chậm 0.7×).
2. Nút mic lớn, sóng âm khi đang nói, tự dừng khi im 1.5 s.
3. Kết quả:
   * điểm tổng (vòng tròn) + 3 thanh nhỏ: âm · thanh điệu · đầy đủ;
   * chữ tô màu **theo âm tiết** (xanh đúng / vàng gần đúng / đỏ sai), dưới mỗi âm tiết là IPA mong đợi và IPA nghe được;
   * chạm vào âm tiết đỏ → thẻ lỗi: "Bạn đọc /s/ thay vì /θ/" + mẹo khẩu hình + nút nghe mẫu âm đó + nút "Luyện âm này";
   * tiếng Trung: vẽ đường cao độ của bạn chồng lên đường mẫu của thanh.
4. Nút "Nói lại" / "Tiếp".

**Các chế độ**
* Từ trong thư viện (như hiện tại, nâng cấp chấm).
* Câu (ExampleSentence đã duyệt) – chấm từng từ trong câu.
* Cặp âm dễ nhầm (ship/sheep, zh/z, hỏi/ngã) – nghe rồi chọn, sau đó nói cả hai.
* Âm yếu của tôi – sinh từ `PhoneSkill`.
* Nói theo (shadowing) – nghe câu rồi nói ngay, chấm độ khớp.

**Trang tiến bộ**: biểu đồ điểm trung bình theo tuần, top 5 âm hay sai, số lần luyện. Giáo viên thấy tổng hợp của lớp
(gắn với bài tập nhóm 1.9.0: loại bài "đọc to").

## 7. Đánh giá (cho báo cáo)

* **speechocean762** (Zhang và cộng sự, Interspeech 2021; 5000 câu tiếng Anh của người học, giám khảo chấm điểm từng âm,
  từ, câu; giấy phép CC BY 4.0): tính tương quan Pearson giữa điểm của hệ thống và điểm giám khảo ở mức âm và câu; so
  với cách A (STT + so chữ) để chứng minh cải thiện.
* Tiếng Trung / tiếng Việt: tự thu ~100 câu (bạn bè đọc đúng và cố tình đọc sai thanh), đo tỉ lệ phát hiện lỗi thanh.
* Thời gian chấm trên server (ms / câu), dung lượng RAM.

## 8. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Mô hình ~320 MB INT8, RAM của VM | đo trước; nếu thiếu thì nạp theo yêu cầu trong worker Celery riêng, hoặc dùng bản base nhỏ hơn |
| Âm vị tiếng Việt / pinyin → IPA tự viết có thể sai | viết bảng theo tài liệu ngữ âm, có test vàng (golden tests) như quy tắc dữ liệu ngôn ngữ của dự án |
| Giọng trẻ em, tạp âm | ngưỡng "không nghe rõ" (độ dài, năng lượng, xác suất trung bình thấp) → yêu cầu nói lại thay vì chấm sai |
| Giọng vùng miền tiếng Việt | chấp nhận biến thể (hỏi/ngã, r/d/gi, n/ng cuối miền Nam) là "gần đúng" |

## 9. Kế hoạch làm

1. BE: dịch vụ chấm (ONNX wav2vec2, G2P en/zh/vi, căn chuỗi, F0), model + API, test vàng. Đo trên speechocean762.
2. Điện thoại: ghi âm (`record`), màn kết quả theo âm tiết, thẻ lỗi, chế độ câu + âm yếu.
3. Web: như điện thoại (MediaRecorder).
4. Trang tiến bộ + loại bài "đọc to" trong bài tập nhóm.
5. Notebook đánh giá `11_pronunciation.ipynb` cho báo cáo.
