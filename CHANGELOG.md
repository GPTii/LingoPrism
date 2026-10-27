# Nhật ký phiên bản LingoPrism

<!-- Sinh từ BE/apps/core/releases.json bằng `python manage.py changelog` – sửa ở file đó, không sửa ở đây. -->

## 1.4.0 – 28/10/2026: Quyền riêng tư và an toàn cho trẻ em

### Mới

- Trang Chính sách quyền riêng tư và Điều khoản sử dụng; khi đăng ký cần đồng ý với hai văn bản này.
- Xác minh email bằng mã 6 số sau khi đăng ký. Đăng bài, bình luận, kết bạn và nhắn tin cần email đã xác minh.
- Tài khoản trẻ em (hoặc dưới 16 tuổi) cần phụ huynh đồng ý qua mã gửi tới email của phụ huynh.
- Tự xoá tài khoản trong Hồ sơ, trên web và trong app: xoá hẳn tiến độ học, ảnh, bài đăng và tin nhắn.
- Mục "Có gì mới" sau mỗi lần cập nhật.

### Cải thiện

- Ảnh, ảnh bài đăng và ảnh đại diện bị xoá khỏi máy chủ cùng lúc với dữ liệu, không còn nằm lại trên ổ đĩa.

## 1.3.0 – 28/10/2026: Nhanh hơn, chịu tải tốt hơn, quản trị tiện hơn

### Mới

- Quản trị: tick chọn nhiều dòng và xoá một lần (người dùng, từ vựng, câu hỏi, đề thi, ảnh nhận diện, điểm POI).
- Bộ lọc theo ngày tạo trên mọi danh sách dài, cùng bộ lọc riêng của từng loại (người không hoạt động, ảnh minh hoạ, đã xuất bản…).
- Người học: "Chọn nhiều" để xoá từ đã lưu, ảnh đã chụp và thông báo; lọc theo ngày.
- Ô tìm kiếm tìm ngay khi đang gõ, không cần bấm Enter.

### Cải thiện

- Trang web mở nhanh hơn nhiều (lần đầu tải 412 KB thay vì 1,4 MB).
- App nhận diện ảnh rõ ngay trên điện thoại; chỉ ảnh khó mới gửi lên máy chủ.
- App chỉ kết nối máy chủ qua HTTPS và cất thông tin đăng nhập trong kho bảo mật của điện thoại.
- Máy chủ chịu được 200 người dùng cùng lúc và vẫn chạy khi bộ nhớ đệm gặp sự cố.

### Sửa lỗi

- Lỗi khi nhiều người cùng dùng (khoảng 20 người trở lên).
- Bấm đăng ký hoặc kết bạn hai lần liên tiếp không còn báo lỗi.

## 1.2.0 – 24/10/2026: Bạn bè, phần thưởng và tủ đồ của Prismo

### Mới

- Kết bạn bằng ID 8 số, lưu bài đăng, trả lời lời mời ngay trong thông báo.
- Chủ đề tự tạo, thêm được từ, ôn bằng flashcard.
- Gói sticker, 54 huy hiệu tặng ngọc và nhiều cách kiếm ngọc hơn.
- Tủ đồ: mỗi người tự mặc đồ cho Prismo của mình.
- Nhiệm vụ có mũi tên dẫn tới đúng chỗ cần làm.

### Cải thiện

- Giao diện màu xanh mới, biểu tượng nhiều màu, Prismo làm biểu tượng app.
- Danh sách dài hiện vài mục đầu với nút Xem tất cả / Thu gọn.

## 1.1.0 – 22/10/2026: Giao diện mới, học offline và cộng đồng

### Mới

- Đăng nhập bằng Google, đặt lại mật khẩu qua email.
- Luyện phát âm có chấm điểm, hội thoại AI từ ảnh đã chụp.
- Học không cần mạng trong app, camera trực tiếp (thử nghiệm), nhận diện ảnh ngay trên điện thoại.
- Tin nhắn riêng, bảng xếp hạng bạn bè, gợi ý theo dõi, chặn và báo cáo người dùng.
- Thống kê học tập, cài web như một app (PWA).

### Cải thiện

- Thiết kế lại toàn bộ web và app với hai chế độ sáng và tối.
- Bài học chuyển động mượt như Duolingo.

## 1.0.0 – 17/10/2026: Ra mắt LingoPrism

### Mới

- Học từ vựng Việt · Anh · Trung (giản thể và phồn thể), mọi từ đều đã được kiểm tra.
- Chụp ảnh đồ vật để học tên bằng ba thứ tiếng (YOLO).
- Ôn tập ngắt quãng, bài kiểm tra, học theo vị trí trên bản đồ.
- XP, chuỗi ngày học, cửa hàng, giải đấu tuần.
- Cộng đồng, nhóm học và chat realtime; web quản trị cho giáo viên.
