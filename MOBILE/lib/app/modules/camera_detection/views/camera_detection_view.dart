import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/camera_detection_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import '../../../routes/app_pages.dart';


class CameraDetectionView extends GetView<CameraDetectionController> {
  const CameraDetectionView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.textPrimary,
      body: SafeArea(
        child: Obx(() {
          if (controller.isLoading) {
            return _buildLoadingState();
          }

          return SingleChildScrollView(
            child: Column(
              children: [
                _buildHeader(),
                SizedBox(height: 40.h),
                _buildCaptureSection(),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            color: AppColors.primary,
          ),
          SizedBox(height: 20.h),
          Text(
            'Đang nhận diện...',
            style: TextStyle(
              fontSize: 18.sp,
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.textPrimary,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Get.back(),
            icon: Icon(
              Icons.arrow_back,
              size: 24.sp,
              color: Colors.white,
            ),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Text(
              'Nhận diện từ ảnh',
              style: TextStyle(
                fontSize: 24.sp,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          IconButton(
            tooltip: 'Lịch sử ảnh',
            onPressed: () => Get.toNamed(Routes.photoHistory),
            icon: Icon(Icons.photo_library_outlined, size: 24.sp, color: Colors.white),
          ),
        ],
      ),
    );
  }

  Widget _buildCaptureSection() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.primarySoft,
        borderRadius: BorderRadius.circular(24.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      padding: EdgeInsets.all(32.w),
      margin: EdgeInsets.all(16.w),
      child: Column(
        children: [
          Icon(
            Icons.camera_alt_outlined,
            size: 80.sp,
            color: AppColors.primary,
          ),
          SizedBox(height: 20.h),
          Text(
            'Gửi ảnh, học ngay từ mới!',
            style: TextStyle(
              fontSize: 22.sp,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 12.h),
          Text(
            'Chụp hoặc chọn ảnh để nhận diện đối tượng\nvà học từ vựng tiếng Anh',
            style: TextStyle(
              fontSize: 14.sp,
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 40.h),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildActionButton(
                icon: Icons.camera_alt,
                label: 'Chụp ảnh',
                onTap: controller.takePhoto,
              ),
              _buildActionButton(
                icon: Icons.photo_library,
                label: 'Chọn ảnh',
                onTap: controller.pickFromGallery,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(16.r),
              border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
            padding: EdgeInsets.all(20.w),
            child: Icon(
              icon,
              size: 50.sp,
              color: AppColors.primary,
            ),
          ),
          SizedBox(height: 12.h),
          Text(
            label,
            style: TextStyle(
              fontSize: 16.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}
