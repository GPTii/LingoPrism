import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_notification_controller.dart';

class ProfileNotificationView extends GetView<ProfileNotificationController> {
  const ProfileNotificationView({super.key});

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
          'Thông báo học tập',
          style: TextStyle(
            color: const Color(0xFF0B1D28),
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: false,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 24.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildToggleCard(),
            SizedBox(height: 20.h),
            Obx(() => controller.notificationsEnabled.value
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSectionLabel('Giờ nhắc học'),
                      SizedBox(height: 12.h),
                      _buildTimePicker(context),
                      SizedBox(height: 24.h),
                      _buildSectionLabel('Tần suất nhắc nhở'),
                      SizedBox(height: 12.h),
                      _buildFrequencyPicker(),
                    ],
                  )
                : _buildDisabledInfo()),
            const Spacer(),
            _buildFooterInfo(),
          ],
        ),
      ),
    );
  }

  Widget _buildToggleCard() {
    return Container(
      padding: EdgeInsets.all(18.w),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 12.r,
            offset: Offset(0, 6.h),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(Icons.notifications_active_rounded,
              color: const Color(0xFF1CB0F6), size: 28.sp),
          SizedBox(width: 12.w),
          Expanded(
            child: Text(
              'Nhắc học hằng ngày',
              style: TextStyle(
                color: const Color(0xFF0B1D28),
                fontSize: 16.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Obx(() => Switch.adaptive(
                value: controller.notificationsEnabled.value,
                activeColor: const Color(0xFF1CB0F6),
                onChanged: controller.toggleNotifications,
              )),
        ],
      ),
    );
  }

  Widget _buildSectionLabel(String text) {
    return Text(
      text,
      style: TextStyle(
        color: const Color(0xFF0B1D28),
        fontSize: 15.sp,
        fontWeight: FontWeight.w700,
      ),
    );
  }

  Widget _buildTimePicker(BuildContext context) {
    return Obx(() {
      final time = controller.reminderTime.value;
      final formatted = time.format(context);
      return GestureDetector(
        onTap: () async {
          final picked = await showTimePicker(
            context: context,
            initialTime: time,
          );
          if (picked != null) {
            await controller.updateTime(picked);
          }
        },
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 14.h),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18.r),
            border: Border.all(color: const Color(0xFF1CB0F6), width: 2),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                formatted,
                style: TextStyle(
                  color: const Color(0xFF0B1D28),
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Icon(Icons.chevron_right_rounded,
                  color: const Color(0xFF1CB0F6), size: 24.sp),
            ],
          ),
        ),
      );
    });
  }

  Widget _buildFrequencyPicker() {
    return Obx(() {
      final selected = controller.frequency.value;
      return Container(
        padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 6.h),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18.r),
          border: Border.all(color: const Color(0xFF1CB0F6), width: 2),
        ),
        child: Column(
          children: controller.frequencies.map((item) {
            final isSelected = item == selected;
            return ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(
                item,
                style: TextStyle(
                  color: const Color(0xFF0B1D28),
                  fontSize: 15.sp,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                ),
              ),
              trailing: isSelected
                  ? Icon(Icons.check_circle_rounded,
                      color: const Color(0xFF1CB0F6), size: 22.sp)
                  : null,
              onTap: () => controller.updateFrequency(item),
            );
          }).toList(),
        ),
      );
    });
  }

  Widget _buildDisabledInfo() {
    return Container(
      padding: EdgeInsets.all(18.w),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: const Color(0xFFB4DBF4), width: 1.5),
      ),
      child: Text(
        'Bạn đã tắt nhắc nhở học. Bật lại để được nhắc học vào thời gian bạn chọn.',
        style: TextStyle(
          color: const Color(0xFF60718C),
          fontSize: 14.sp,
        ),
      ),
    );
  }

  Widget _buildFooterInfo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            icon: const Icon(Icons.notifications_active_outlined),
            label: const Text('Gửi thử thông báo'),
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0xFF1CB0F6),
              side: const BorderSide(color: Color(0xFF1CB0F6), width: 1.6),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14.r),
              ),
              padding: EdgeInsets.symmetric(vertical: 12.h, horizontal: 12.w),
            ),
            onPressed: controller.sendTestNotification,
          ),
        ),
        SizedBox(height: 10.h),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            icon: const Icon(Icons.schedule_outlined),
            label: const Text('Gửi thử trong 1 phút'),
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0xFF1CB0F6),
              side: const BorderSide(color: Color(0xFF1CB0F6), width: 1.6),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14.r),
              ),
              padding: EdgeInsets.symmetric(vertical: 12.h, horizontal: 12.w),
            ),
            onPressed: controller.sendScheduledTestNotification,
          ),
        ),
        SizedBox(height: 10.h),
        Text(
          'Snaplingua sẽ gửi thông báo qua hệ thống của thiết bị. Hãy đảm bảo bạn đã bật quyền thông báo cho ứng dụng.',
          style: TextStyle(
            color: const Color(0xFF60718C),
            fontSize: 12.sp,
          ),
        ),
      ],
    );
  }
}
