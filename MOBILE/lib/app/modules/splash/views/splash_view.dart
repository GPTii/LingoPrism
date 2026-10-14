import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../controllers/splash_controller.dart';

class SplashView extends GetView<SplashController> {
  const SplashView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: Center(
        child: Obx(() => controller.isLoading
            ? _buildLoading()
            : controller.errorMessage.isNotEmpty
                ? _buildError()
                : _buildLoading()),
      ),
    );
  }

  Widget _buildLoading() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // App logo/mascot
        Container(
          width: 200.w,
          height: 200.h,
          decoration: const BoxDecoration(
            image: DecorationImage(
              image: AssetImage('assets/images/chimcanhcut/chim_vui1.png'),
              fit: BoxFit.contain,
            ),
          ),
        ),
        SizedBox(height: 24.h),
        // App name
        Text(
          'SnapLingua',
          style: TextStyle(
            fontSize: 32.sp,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
            letterSpacing: 1.2,
          ),
        ),
        SizedBox(height: 8.h),
        Text(
          'Học từ vựng qua hình ảnh',
          style: TextStyle(
            fontSize: 16.sp,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildError() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.error_outline,
          size: 64.sp,
          color: AppColors.textError,
        ),
        SizedBox(height: 16.h),
        Text(
          controller.errorMessage,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 16.sp,
          ),
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 24.h),
        ElevatedButton(
          onPressed: controller.retry,
          child: const Text('Thử lại'),
        ),
      ],
    );
  }
}
