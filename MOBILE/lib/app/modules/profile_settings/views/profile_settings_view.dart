import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_settings_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';

class ProfileSettingsView extends GetView<ProfileSettingsController> {
  const ProfileSettingsView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      appBar: AppBar(
        backgroundColor: AppColors.primarySoft,
        elevation: 0,
        leading: IconButton(
          onPressed: Get.back,
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: AppColors.textPrimary,
        ),
        title: Text(
          'Cài đặt',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 24.h),
        child: Column(
          children: [
            _SettingsTile(
              label: 'Ngôn ngữ học',
              onTap: controller.openLanguage,
            ),
            SizedBox(height: 14.h),
            _SettingsTile(
              label: 'Mục tiêu',
              onTap: controller.openGoals,
            ),
            SizedBox(height: 14.h),
            _SettingsTile(
              label: 'Cập nhật hồ sơ',
              onTap: controller.openEditProfile,
            ),
            SizedBox(height: 14.h),
            _SettingsTile(
              label: 'Đổi mật khẩu',
              onTap: controller.openChangePassword,
            ),
            SizedBox(height: 14.h),
            _SettingsTile(
              label: 'Thông báo',
              onTap: controller.openNotifications,
            ),
            SizedBox(height: 14.h),
            _SettingsTile(
              label: 'Hướng dẫn sử dụng',
              onTap: controller.openGuide,
            ),
            SizedBox(height: 32.h),
            Obx(() {
              final isProcessing = controller.isProcessing.value;
              return SizedBox(
                width: double.infinity,
                height: 48.h,
                child: ElevatedButton(
                  onPressed: isProcessing ? null : controller.logout,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.error,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(18.r),
                    ),
                    elevation: 0,
                  ),
                  child: isProcessing
                      ? SizedBox(
                          width: 20.w,
                          height: 20.w,
                          child: const CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : Text(
                          'ĐĂNG XUẤT',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.label,
    required this.onTap,
  });

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18.r),
      child: Ink(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18.r),
          border: Border.all(color: const Color(0xFFB4DBF4), width: 2),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 12.r,
              offset: Offset(0, 6.h),
            ),
          ],
        ),
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            Icon(
              Icons.chevron_right_rounded,
              color: AppColors.primary,
              size: 24.sp,
            ),
          ],
        ),
      ),
    );
  }
}
