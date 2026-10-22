import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/home_controller.dart';
import 'learning_tab_view.dart';
import '../../review/views/review_view.dart';
import '../../camera_detection/controllers/camera_detection_controller.dart';
import '../../community/controllers/community_controller.dart';
import '../../community/views/community_view.dart';
import '../../profile/controllers/profile_controller.dart';
import '../../profile/views/profile_view.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import 'package:lingoprism/app/core/widgets/app_icon.dart';

class HomeView extends GetView<HomeController> {
  const HomeView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: false, // giữ FAB cố định khi mở bàn phím
      body: Obx(() {
        switch (controller.currentIndex) {
          case 0:
            return const LearningTabView();
          case 1:
            return const ReviewView();
          case 2:
            if (!Get.isRegistered<CommunityController>()) {
              Get.lazyPut(() => CommunityController());
            }
            return const CommunityView();
          case 3:
            if (!Get.isRegistered<ProfileController>()) {
              Get.lazyPut(() => ProfileController());
            }
            return const ProfileView();
          default:
            return const LearningTabView();
        }
      }),
      bottomNavigationBar: Obx(() => DecoratedBox(
            decoration: BoxDecoration(border: Border(top: BorderSide(color: AppColors.line))),
            child: BottomAppBar(
              shape: const CircularNotchedRectangle(),
              notchMargin: 6.w,
              color: AppColors.surface,
              surfaceTintColor: Colors.transparent,
              elevation: 0,
              height: 68.h,
              padding: EdgeInsets.zero,
              child: Row(
                children: [
                  _buildNavItem(icon: 'home', label: 'Trang chủ', index: 0),
                  _buildNavItem(icon: 'review', label: 'Ôn tập', index: 1),
                  SizedBox(width: 64.w), // room for the camera button
                  _buildNavItem(icon: 'community', label: 'Cộng đồng', index: 2),
                  _buildNavItem(icon: 'profile', label: 'Hồ sơ', index: 3),
                ],
              ),
            ),
          )),
      // the camera – the heart of the app – raised in the middle
      floatingActionButton: FloatingActionButton(
        heroTag: 'homeCameraFab',
        tooltip: 'Chụp ảnh học từ',
        onPressed: () {
          if (!Get.isRegistered<CameraDetectionController>()) {
            Get.lazyPut(() => CameraDetectionController());
          }
          CameraDetectionController.to.takePhoto();
        },
        backgroundColor: AppColors.primary,
        elevation: 0,
        child: Icon(Icons.photo_camera_rounded, size: 28.sp, color: Colors.white),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }

  Widget _buildNavItem({
    required String icon,
    required String label,
    required int index,
  }) {
    final isActive = controller.currentIndex == index;
    final color = isActive ? AppColors.primary : AppColors.textSecondary;
    return Expanded(
      child: Semantics(
        selected: isActive,
        button: true,
        child: InkResponse(
          onTap: () => controller.changeTab(index),
          radius: 36,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                curve: Curves.easeOutCubic,
                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 2.h),
                decoration: BoxDecoration(
                  color: isActive ? AppColors.primarySoft : Colors.transparent,
                  border: Border.all(color: isActive ? AppColors.primaryTint : Colors.transparent, width: 2),
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: AnimatedScale(
                  scale: isActive ? 1.08 : 1,
                  duration: const Duration(milliseconds: 220),
                  curve: Curves.easeOutBack,
                  child: AppIcon(icon, size: 28.sp),
                ),
              ),
              SizedBox(height: 3.h),
              Text(
                label,
                maxLines: 1,
                style: TextStyle(color: color, fontSize: 11.5.sp, fontWeight: isActive ? FontWeight.w700 : FontWeight.w500),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
