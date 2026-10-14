import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_guide_controller.dart';

class ProfileGuideView extends GetView<ProfileGuideController> {
  const ProfileGuideView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE6F9FF),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE6F9FF),
        elevation: 0,
        leading: IconButton(
          onPressed: Get.back,
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: const Color(0xFF0B1D28),
        ),
        title: Text(
          'Hướng dẫn sử dụng',
          style: TextStyle(
            color: const Color(0xFF0B1D28),
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      body: Stack(
        children: [
          Positioned.fill(
            child: IgnorePointer(
              ignoring: true,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      const Color(0xFFB6F3FF).withOpacity(0.45),
                      const Color(0xFFE6F9FF),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SingleChildScrollView(
            padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _heroCard(),
                SizedBox(height: 18.h),
                _section(
                  title: '1. Bắt đầu với SnapLingua',
                  accentIcon: Icons.rocket_launch_rounded,
                  bullets: const [
                    'Đăng nhập hoặc tạo tài khoản để đồng bộ tiến trình học.',
                    'Chọn mục tiêu học và trình độ để nhận lộ trình phù hợp.',
                    'Bật nhắc học hằng ngày để không bỏ lỡ lịch ôn tập.',
                  ],
                ),
                SizedBox(height: 14.h),
                _section(
                  title: '2. Học và ôn tập',
                  accentIcon: Icons.menu_book_rounded,
                  bullets: const [
                    'Hoàn thành các vòng học để mở khóa vòng kiểm tra.',
                    'Dùng Flashcard để củng cố từ vựng trước khi kiểm tra.',
                    'Ôn tập lại các từ sai trong vòng cuối để giữ streak.',
                  ],
                ),
                SizedBox(height: 14.h),
                _section(
                  title: '3. Cộng đồng & nhóm học',
                  accentIcon: Icons.groups_rounded,
                  bullets: const [
                    'Tham gia nhóm để tích lũy XP cùng bạn bè.',
                    'Gửi lời giới thiệu ngắn gọn khi xin vào nhóm có phê duyệt.',
                    'Tương tác trên dòng thời gian để nhận thêm động lực học.',
                  ],
                ),
                SizedBox(height: 14.h),
                _section(
                  title: '4. Quản lý tài khoản',
                  accentIcon: Icons.settings_suggest_rounded,
                  bullets: const [
                    'Cập nhật tên và ảnh đại diện để đồng bộ khắp cộng đồng.',
                    'Kiểm tra bảng xếp hạng để xem thứ hạng hàng tuần.',
                    'Bật/thay đổi giờ nhắc học trong phần Thông báo.',
                  ],
                ),
                SizedBox(height: 14.h),
                _section(
                  title: '5. Mẹo nhanh',
                  accentIcon: Icons.lightbulb_rounded,
                  bullets: const [
                    'Học ngắn nhưng đều đặn mỗi ngày để giữ streak.',
                    'Dùng loa phát âm để nghe và lặp lại nhiều lần.',
                    'Gửi thử thông báo để chắc chắn quyền thông báo đã bật.',
                  ],
                ),
                SizedBox(height: 22.h),
                _tipsCard(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _heroCard() {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0A69C7), Color(0xFF1CB0F6)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18.r),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0A69C7).withOpacity(0.18),
            blurRadius: 18.r,
            offset: Offset(0, 10.h),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52.w,
            height: 52.w,
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.school_rounded,
                color: const Color(0xFF0A69C7), size: 28.sp),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Tận dụng SnapLingua hiệu quả',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 6.h),
                Text(
                  'Làm theo từng bước ngắn gọn bên dưới để học đều, giữ streak và tiến bộ nhanh.',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 13.sp,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _section({
    required String title,
    required List<String> bullets,
    IconData? accentIcon,
  }) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10.r,
            offset: Offset(0, 6.h),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (accentIcon != null)
                Container(
                  padding: EdgeInsets.all(8.w),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE6F2FF),
                    borderRadius: BorderRadius.circular(12.r),
                  ),
                  child: Icon(
                    accentIcon,
                    color: const Color(0xFF0A69C7),
                    size: 18.sp,
                  ),
                ),
              if (accentIcon != null) SizedBox(width: 10.w),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: const Color(0xFF0B1D28),
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 10.h),
          ...bullets.map(
            (item) => Padding(
              padding: EdgeInsets.only(bottom: 6.h),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('• ', style: TextStyle(fontSize: 14.sp, height: 1.4)),
                  Expanded(
                    child: Text(
                      item,
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: const Color(0xFF405166),
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tipsCard() {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0A69C7), Color(0xFF1CB0F6)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16.r),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0A69C7).withOpacity(0.2),
            blurRadius: 16.r,
            offset: Offset(0, 10.h),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.lightbulb_outline, color: Colors.white),
          SizedBox(width: 10.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Mẹo cho bạn',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 4.h),
                Text(
                  'Học đều mỗi ngày 10-15 phút, bật nhắc học và ôn lại từ sai ở vòng cuối để tiến bộ nhanh.',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 13.sp,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
