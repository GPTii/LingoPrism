import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/theme_service.dart';
import '../controllers/profile_settings_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';

class ProfileSettingsView extends GetView<ProfileSettingsController> {
  const ProfileSettingsView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
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
            const _ThemeChoice(),
            SizedBox(height: 14.h),
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
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(18.r),
          border: Border.all(color: AppColors.primaryTint, width: 2),),
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


/// Giao diện: Sáng / Tối side by side; the choice is kept on the device.
class _ThemeChoice extends StatefulWidget {
  const _ThemeChoice();

  @override
  State<_ThemeChoice> createState() => _ThemeChoiceState();
}

class _ThemeChoiceState extends State<_ThemeChoice> {
  @override
  Widget build(BuildContext context) {
    final dark = ThemeService.isDark;
    Widget option(String label, IconData icon, bool selected, ThemeMode mode) => Expanded(
          child: Semantics(
            selected: selected,
            button: true,
            child: InkWell(
              borderRadius: BorderRadius.circular(10.r),
              onTap: selected ? null : () async {
                await ThemeService.set(mode);
                if (mounted) setState(() {});
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                height: 44.h,
                decoration: BoxDecoration(
                  color: selected ? AppColors.surface : Colors.transparent,
                  borderRadius: BorderRadius.circular(10.r),
                  border: selected ? Border.all(color: AppColors.lineStrong) : null,
                ),
                child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(icon, size: 18.sp, color: selected ? AppColors.textPrimary : AppColors.textSecondary),
                  SizedBox(width: 8.w),
                  Text(label,
                      style: TextStyle(
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w600,
                        color: selected ? AppColors.textPrimary : AppColors.textSecondary,
                      )),
                ]),
              ),
            ),
          ),
        );
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Giao diện', style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
      SizedBox(height: 8.h),
      Container(
        padding: EdgeInsets.all(4.w),
        decoration: BoxDecoration(color: AppColors.surfaceMuted, borderRadius: BorderRadius.circular(14.r)),
        child: Row(children: [
          option('Sáng', Icons.light_mode_outlined, !dark, ThemeMode.light),
          SizedBox(width: 4.w),
          option('Tối', Icons.dark_mode_outlined, dark, ThemeMode.dark),
        ]),
      ),
    ]);
  }
}
