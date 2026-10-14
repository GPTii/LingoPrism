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
      bottomNavigationBar: Obx(() => BottomAppBar(
        shape: const CircularNotchedRectangle(),
        notchMargin: 8.w,
        color: Colors.white,
        elevation: 8,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildNavItem(
              icon: Icons.home,
              label: 'Trang chủ',
              index: 0,
              isActive: controller.currentIndex == 0,
            ),
            _buildNavItem(
              icon: Icons.book,
              label: 'Ôn tập',
              index: 1,
              isActive: controller.currentIndex == 1,
            ),
            SizedBox(width: 40.w), // Khoảng cách cho FloatingActionButton
            _buildNavItem(
              icon: Icons.people,
              label: 'Cộng đồng',
              index: 2,
              isActive: controller.currentIndex == 2,
            ),
            _buildNavItem(
              icon: Icons.person,
              label: 'Hồ sơ',
              index: 3,
              isActive: controller.currentIndex == 3,
            ),
          ],
        ),
      )),
      floatingActionButton: FloatingActionButton(
        heroTag: 'homeCameraFab',
        onPressed: () {
          // Ensure CameraDetectionController is initialized
          if (!Get.isRegistered<CameraDetectionController>()) {
            Get.lazyPut(() => CameraDetectionController());
          }
          // Call takePhoto to open camera and detect vocabulary
          CameraDetectionController.to.takePhoto();
        },
        backgroundColor: const Color(0xFF1CB0F6),
        elevation: 4,
        child: Icon(Icons.camera_alt, size: 30.sp, color: Colors.white),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required int index,
    required bool isActive,
  }) {
    return GestureDetector(
      onTap: () => controller.changeTab(index),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 24.sp,
            color: isActive ? const Color(0xFF1CB0F6) : Colors.grey,
          ),
          SizedBox(height: 4.h),
          Text(
            label,
            style: TextStyle(
              color: isActive ? const Color(0xFF1CB0F6) : Colors.grey,
              fontSize: 12.sp,
            ),
          ),
        ],
      ),
    );
  }
}
