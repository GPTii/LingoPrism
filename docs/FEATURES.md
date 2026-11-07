# LingoPrism — Danh sách chức năng đầy đủ

**Nguồn:** `[SL]` có sẵn trong SnapLingua (chuyển sang) · `[ĐC]` yêu cầu trong đề cương · `[Mới]` bổ sung để hệ thống hoàn chỉnh
**Nền tảng:** 📱 App mobile (Flutter) · 🌐 Web học viên (React) · 🛠 Web Admin/Staff (React)
**Ngôn ngữ học:** Tiếng Việt (trẻ em) · Tiếng Anh · Tiếng Trung giản thể (chuẩn đại lục) / phồn thể (chuẩn Đài Loan) — người học tự chọn

---

## 1. Tài khoản & bảo mật
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 1.1 | Đăng ký bằng email + mật khẩu | SL, ĐC | 📱🌐 |
| 1.2 | Đăng nhập email; đăng nhập Google | SL, ĐC | 📱🌐🛠 |
| 1.3 | Đăng nhập Facebook (tùy chọn) | SL | 📱🌐 |
| 1.4 | Quên mật khẩu: gửi mã qua email → xác minh mã → đặt mật khẩu mới | SL | 📱🌐 |
| 1.5 | Đổi mật khẩu | SL | 📱🌐🛠 |
| 1.6 | Đăng xuất, tự làm mới phiên (JWT refresh) | SL, Mới | 📱🌐🛠 |
| 1.7 | Phân quyền theo vai trò: Admin / Staff (giáo viên – người hỗ trợ) / Học viên; phân loại học viên Trẻ em / Người lớn | ĐC | 🛠 |
| 1.8 | Khóa/mở khóa tài khoản vi phạm | Mới | 🛠 |

## 2. Onboarding, khảo sát, hồ sơ, mục tiêu
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 2.1 | Màn giới thiệu: "Chụp ảnh học từ vựng", "Học mọi lúc mọi nơi", "Học cùng nhau" | SL | 📱🌐 |
| 2.2 | Khảo sát đầu vào: tên gọi, ngày sinh, giới tính, mục đích học (giao tiếp, công việc, học tập, kết bạn…), thời gian học mỗi ngày | SL | 📱🌐 |
| 2.3 | Chọn **ngôn ngữ học** (Việt / Anh / Trung), **đối tượng** (trẻ em / người lớn), **dạng chữ Hán** (giản thể đại lục / phồn thể Đài Loan), bật/tắt Zhuyin | ĐC, Mới | 📱🌐 |
| 2.4 | Hồ sơ cá nhân: avatar, tên, rank, XP, streak, bài đăng gần đây, nhóm, người theo dõi / đang theo dõi | SL | 📱🌐 |
| 2.5 | Chỉnh sửa hồ sơ | SL | 📱🌐 |
| 2.6 | Mục tiêu học: số từ mới / ngày, số từ ôn / ngày | SL | 📱🌐 |
| 2.7 | Cài đặt: thông báo, mục tiêu, ngôn ngữ & dạng chữ, đổi mật khẩu, hướng dẫn sử dụng, đăng xuất | SL | 📱🌐 |
| 2.8 | Xem hồ sơ công khai của người học khác, theo dõi / bỏ theo dõi | SL | 📱🌐 |

## 3. Từ vựng & chủ đề (3 ngôn ngữ)
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 3.1 | Thư viện chủ đề hệ thống: Động vật, Thực phẩm, Đồ vật, Nội thất & gia dụng, Công nghệ, Giao thông, Giáo dục, Du lịch, Thể thao, Thiên nhiên, Con người & phụ kiện… (lọc theo trẻ em / người lớn) | SL, ĐC | 📱🌐 |
| 3.2 | Thẻ từ đầy đủ: ảnh minh họa, từ ở ngôn ngữ đang học, nghĩa tiếng Việt, IPA (Anh), pinyin / zhuyin + lượng từ (Trung), cấp độ HSK / TOCFL / CEFR, câu ví dụ + bản dịch | SL, ĐC, Mới | 📱🌐 |
| 3.3 | Phát âm (TTS đúng giọng vi-VN / en-US / zh-CN / zh-TW) | SL | 📱🌐 |
| 3.4 | Lưu từ / lưu cả chủ đề vào thư viện cá nhân; trạng thái chưa học / đang học / đã học | SL | 📱🌐 |
| 3.5 | Tạo chủ đề cá nhân, thêm từ thủ công, xóa chủ đề | SL | 📱🌐 |
| 3.6 | Tìm kiếm nhanh từ vựng | SL | 📱🌐 |
| 3.7 | Nút **Báo lỗi** trên mọi thẻ từ (sai chữ, sai phiên âm, sai nghĩa) | Mới | 📱🌐 |
| 3.8 | Trang "Nguồn dữ liệu & giấy phép" (CC-CEDICT, từ điển Bộ GD Đài Loan, HSK, TOCFL, Tatoeba, CMUdict…) | Mới | 📱🌐 |

## 4. Nhận diện vật thể bằng YOLOv10
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 4.1 | Chụp ảnh bằng camera (zoom, flash) hoặc chọn ảnh từ thư viện | SL, ĐC | 📱 |
| 4.2 | Upload ảnh để nhận diện | ĐC, Mới | 🌐 |
| 4.3 | Nhận diện bằng **YOLOv10 tự huấn luyện**: chạy trên máy (TFLite, offline) hoặc trên server (khi có mạng) | ĐC | 📱🌐 |
| 4.4 | Kết quả: khung bao quanh từng vật, nhãn, **confidence score**, từ vựng ở ngôn ngữ đang học + nghĩa + phát âm | SL, ĐC | 📱🌐 |
| 4.5 | Chọn từ muốn lưu, gán chủ đề cho từng từ hoặc cho tất cả | SL | 📱🌐 |
| 4.6 | Lịch sử ảnh đã nhận diện | Mới | 📱🌐 |
| 4.7 | Ghi log nhận diện (nhãn, confidence, top-k, người dùng xác nhận đúng / sai) làm dữ liệu cho VIP | ĐC | (hệ thống) |
| 4.8 | Chia sẻ ảnh + từ vựng lên cộng đồng | SL | 📱🌐 |

## 5. Học & ôn tập
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 5.1 | **Học từ mới** theo mục tiêu ngày ("Học thêm 10 từ mới") | SL | 📱🌐 |
| 5.2 | **Ôn tập** từ đến hạn theo lịch lặp lại ngắt quãng (SRS) | SL, ĐC | 📱🌐 |
| 5.3 | Flashcard: lật thẻ, "Đã nhớ / Chưa nhớ", vuốt thẻ | SL | 📱🌐 |
| 5.4 | Dạng câu hỏi: gõ lại từ; nghe phát âm và gõ lại; trắc nghiệm nghĩa; chọn ảnh đúng; nối từ – nghĩa; điền từ vào câu | SL, Mới | 📱🌐 |
| 5.5 | Dạng câu hỏi riêng cho tiếng Trung: chọn pinyin / thanh điệu đúng, chọn mặt chữ đúng (phân biệt chữ dễ nhầm), chọn lượng từ | Mới | 📱🌐 |
| 5.6 | Vòng "Kiểm tra lần cuối", tổng kết buổi học, danh sách "từ cần ôn thêm" | SL | 📱🌐 |
| 5.7 | Thư viện từ cá nhân và tiến độ từng từ | SL | 📱🌐 |
| 5.8 | **Chế độ trẻ em**: học tiếng Việt qua hình ảnh, giao diện to, mascot chim cánh cụt, sticker và phần thưởng | ĐC | 📱🌐 |
| 5.9 | Học **offline**, tự đồng bộ kết quả khi có mạng | SL, ĐC | 📱 |

## 6. Kiểm tra – đề thi – chấm bài
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 6.1 | Danh sách đề thi theo chủ đề / ngôn ngữ / cấp độ | ĐC | 📱🌐 |
| 6.2 | Làm đề **trắc nghiệm** (tự chấm ngay), có giới hạn thời gian | ĐC | 📱🌐 |
| 6.3 | Làm đề **tự luận** (viết câu, đoạn), nộp bài | ĐC | 📱🌐 |
| 6.4 | Xem điểm, đáp án, nhận xét của giáo viên, lịch sử làm bài | ĐC | 📱🌐 |
| 6.5 | Staff **chấm bài tự luận**, cho điểm và nhận xét | ĐC | 🛠 |
| 6.6 | Ngân hàng câu hỏi, tạo đề, xuất bản / ẩn đề | ĐC | 🛠 |

## 7. Học theo vị trí (GIS)
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 7.1 | Bản đồ các địa điểm (POI) quanh vị trí hiện tại (chợ, siêu thị, bệnh viện, trường học, sân bay, công viên…) | ĐC | 📱🌐 |
| 7.2 | Tìm POI trong bán kính cấu hình (Proximity Search) | ĐC | 📱🌐 |
| 7.3 | **Geofencing**: khi người dùng đi vào vùng của một POI → thông báo gợi ý chủ đề từ vựng phù hợp (VD vào siêu thị → chủ đề Thực phẩm) | ĐC | 📱 |
| 7.4 | Học nhanh chủ đề gợi ý theo vị trí | ĐC | 📱🌐 |
| 7.5 | Quản lý POI trên bản đồ (WebGIS): thêm / sửa / kéo thả, gán chủ đề, bán kính geofence | ĐC | 🛠 |

## 8. Game hóa
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 8.1 | **XP**: điểm kinh nghiệm cho mỗi hoạt động, lịch sử XP, XP tuần / tổng | SL | 📱🌐 |
| 8.2 | **Streak**: chuỗi ngày học liên tiếp, lịch streak theo tháng, thông điệp động viên | SL | 📱🌐 |
| 8.3 | Tiền tệ trong app: **Vảy** và **Ngọc** | SL | 📱🌐 |
| 8.4 | **Cửa hàng**: Đá băng (giữ streak khi nghỉ 1 ngày), Bình cực quang (x2 XP trong 15 phút), Vảy tăng tốc (+25% XP trong 24 giờ), sticker (dùng trong chat và bình luận); kho "Vật phẩm của tôi" | SL | 📱🌐 |
| 8.5 | **Nhiệm vụ hằng ngày**: lưu từ, đạt mục tiêu học, đạt mục tiêu ôn, đăng ảnh cộng đồng, tương tác cộng đồng; nhận thưởng | SL | 📱🌐 |
| 8.6 | **Nhiệm vụ tháng**: hoàn thành đủ số nhiệm vụ ngày để nhận thưởng tháng | SL | 📱🌐 |
| 8.7 | **Huy hiệu / thành tựu** và sticker thưởng (theo mốc XP, streak, số từ…) | SL, ĐC | 📱🌐 |
| 8.8 | **Giải đấu tuần (League)**: hạng Tân binh Igloo → Igloo Đồng → Bạc → Vàng → Kim cương; vùng thăng hạng / an toàn / xuống hạng | SL | 📱🌐 |
| 8.9 | Bảng xếp hạng (giải đấu, bạn bè) | SL, ĐC | 📱🌐 |
| 8.10 | Nhân vật ảo (mascot) và phần thưởng dành cho trẻ em | ĐC | 📱🌐 |

## 9. Cộng đồng
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 9.1 | Bảng tin: đăng ảnh kèm từ vựng, chú thích, chọn chủ đề | SL, ĐC | 📱🌐 |
| 9.2 | Thích, bình luận (bằng chữ hoặc sticker), bình luận nổi bật | SL | 📱🌐 |
| 9.3 | Lưu từ vựng từ bài đăng của người khác | SL | 📱🌐 |
| 9.4 | Xóa bài của mình; báo cáo vi phạm (chọn lý do, mô tả) | SL | 📱🌐 |
| 9.5 | Theo dõi người học khác | SL | 📱🌐 |
| 9.6 | Kiểm duyệt bài đăng / bình luận bị báo cáo | SL, ĐC | 🛠 |

## 10. Nhóm học & chat realtime
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 10.1 | Tạo nhóm học (tên, mô tả, icon), chế độ tham gia tự do hoặc cần trưởng nhóm duyệt | SL | 📱🌐 |
| 10.2 | Tìm / tham gia / rời nhóm; trưởng nhóm duyệt thành viên, xóa nhóm | SL | 📱🌐 |
| 10.3 | **Chat nhóm realtime** (chữ, sticker, chia sẻ huy hiệu) | SL, ĐC | 📱🌐 |
| 10.4 | **Chat với người hỗ trợ** (học viên ↔ Staff), trạng thái đã gửi / đã nhận / đã xem | ĐC | 📱🌐🛠 |
| 10.5 | Đồng bộ realtime tiến độ, kết quả bài làm và thông báo giữa web, app và server | ĐC | 📱🌐🛠 |

## 11. Thông báo
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 11.1 | Danh sách thông báo trong app, đánh dấu đã đọc / đọc tất cả, bấm để mở đúng màn hình | SL | 📱🌐 |
| 11.2 | Push notification (nhắc học, thành tựu mới, thăng hạng, có người theo dõi, bình luận, tin nhắn) | SL | 📱 |
| 11.3 | Nhắc học theo giờ sáng / tối, nhắc thông minh, nhắc theo ngữ cảnh vị trí | SL, ĐC | 📱 |
| 11.4 | Thông báo realtime trên web | ĐC | 🌐🛠 |
| 11.5 | Admin gửi thông báo hàng loạt / theo nhóm người dùng | ĐC | 🛠 |

## 12. Thống kê tiến độ học viên
| # | Chức năng | Nguồn | Nền tảng |
|---|---|---|---|
| 12.1 | Tiến độ hôm nay: từ mới đã học / mục tiêu, từ đã ôn / đến hạn, XP | SL | 📱🌐 |
| 12.2 | Heatmap ngày học, lịch streak | SL | 📱🌐 |
| 12.3 | Thống kê theo ngôn ngữ / chủ đề, tỷ lệ trả lời đúng, từ hay sai | Mới | 📱🌐 |

## 13. Quản trị (Web Admin / Staff)
| # | Chức năng | Nguồn |
|---|---|---|
| 13.1 | Dashboard: người dùng mới, người học hoạt động mỗi ngày, lượt học, lượt nhận diện, độ chính xác theo lớp vật thể, biểu đồ | ĐC |
| 13.2 | Quản lý người dùng & phân quyền, khóa tài khoản, xem tiến độ từng học viên | ĐC |
| 13.3 | Quản lý ngôn ngữ, chủ đề, từ vựng 3 ngôn ngữ (import / export CSV, ảnh minh họa) | ĐC |
| 13.4 | **Hàng chờ kiểm tra dữ liệu ngôn ngữ**: từ bị lệch nguồn (`flagged`) và báo lỗi từ học viên → xem đối chiếu các nguồn → duyệt / sửa / loại | Mới |
| 13.5 | Ngân hàng câu hỏi, đề thi, chấm tự luận | ĐC |
| 13.6 | Quản lý POI trên bản đồ (WebGIS) | ĐC |
| 13.7 | Kiểm duyệt cộng đồng (bài đăng, bình luận, báo cáo), quản lý nhóm | SL, ĐC |
| 13.8 | Hộp thư chat hỗ trợ | ĐC |
| 13.9 | Gửi thông báo hàng loạt | ĐC |
| 13.10 | Quản lý game hóa: huy hiệu, nhiệm vụ, vật phẩm cửa hàng, mùa giải | SL |
| 13.11 | Nhật ký nhận diện (ảnh, nhãn, confidence), quản lý phiên bản model YOLOv10 | ĐC |
| 13.12 | Nhật ký thao tác của Admin (audit log) | SL |

## 14. AI & thuật toán nghiên cứu — **Phase 5 (làm sau)**
| # | Chức năng | Nguồn |
|---|---|---|
| 14.1 | Huấn luyện / đánh giá YOLOv10: Precision, Recall, mAP, confidence, confusion matrix *(huấn luyện làm ngay từ Phase 0–4; phần phân tích đưa vào báo cáo)* | ĐC |
| 14.2 | **SM-2** tự cài đặt làm baseline lập lịch ôn | ĐC |
| 14.3 | **FSRS** (Difficulty – Stability – Retrievability) để so sánh với SM-2 | ĐC |
| 14.4 | **VIP** – ưu tiên ôn tập dựa trên mức nhầm lẫn thị giác + confidence + lịch sử học | ĐC |
| 14.5 | **Smart Distractor Generation** – đáp án nhiễu theo độ tương đồng ngữ nghĩa (Word2Vec / PhoBERT), tự cài phần lọc và xếp hạng | ĐC |
| 14.6 | **Proximity Search** tự cài đặt (Haversine + chỉ mục không gian tự xây), so sánh với PostGIS | ĐC |
| 14.7 | **Genetic Algorithm** tối ưu bộ tham số cơ chế ôn tập trên dữ liệu lịch sử học tổng hợp | ĐC |
| 14.8 | Trang thực nghiệm và so sánh: SM-2 vs SM-2+VIP, SM-2 vs FSRS, distractor ngẫu nhiên vs thông minh, trước / sau GA, độ trễ realtime, độ trễ geofence | ĐC |

## 15. Hệ thống & triển khai
| # | Chức năng | Nguồn |
|---|---|---|
| 15.1 | REST API dùng chung cho web và app + tài liệu Swagger | Mới |
| 15.2 | WebSocket cho chat, thông báo, đồng bộ | ĐC |
| 15.3 | Kiểm tra dữ liệu ngôn ngữ tự động + golden test giản / phồn / đa âm trong CI | Mới |
| 15.4 | Đóng gói Docker Compose (Django, PostgreSQL/PostGIS, Redis, nginx), deploy VPS có HTTPS | Mới |
| 15.5 | Dữ liệu mẫu đầy đủ cho demo (lệnh `seed_all`) | Mới |
