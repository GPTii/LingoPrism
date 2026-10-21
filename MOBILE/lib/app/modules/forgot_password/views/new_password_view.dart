import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/forgot_password_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';

class NewPasswordView extends GetView<ForgotPasswordController> {
  const NewPasswordView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          color: AppColors.primary,),
        child: SafeArea(
          child: Column(
            children: [
              // Header
              Padding(
                padding: EdgeInsets.only(top: 20.h, left: 24.w, right: 24.w),
                child: Row(
                  children: [
                    IconButton(
                      onPressed: () => Get.back(),
                      icon: Icon(
                        Icons.arrow_back_ios,
                        color: Colors.white,
                        size: 24.sp,
                      ),
                    ),
                    SizedBox(width: 8.w),
                    Text(
                      'Mật khẩu mới',
                      style: TextStyle(
                        fontSize: 24.sp,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),

              SizedBox(height: 40.h),

              // Form container
              Expanded(
                child: Container(
                  width: double.infinity,
                  margin: EdgeInsets.symmetric(horizontal: 16.w),
                  padding: EdgeInsets.all(24.w),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(24.r),
                  ),
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        // Icon
                        Container(
                          width: 80.w,
                          height: 80.h,
                          decoration: const BoxDecoration(
                            color: AppColors.primary,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.lock_outline,
                            color: Colors.white,
                            size: 40.sp,
                          ),
                        ),

                        SizedBox(height: 24.h),

                        // Title and subtitle
                        Text(
                          'Tạo mật khẩu mới',
                          style: TextStyle(
                            fontSize: 24.sp,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),

                        SizedBox(height: 8.h),

                        Text(
                          'Nhập mật khẩu mới để hoàn tất quá trình khôi phục',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 16.sp,
                            color: AppColors.textSecondary,
                          ),
                        ),

                        SizedBox(height: 32.h),

                        // New Password field
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Obx(() => Container(
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.7),
                                    borderRadius: BorderRadius.circular(12.r),
                                  ),
                                  child: TextField(
                                    controller: controller.newPasswordController,
                                    obscureText: !controller.isNewPasswordVisible,
                                    decoration: InputDecoration(
                                      hintText: 'Mật khẩu mới',
                                      hintStyle: TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 16.sp,
                                      ),
                                      prefixIcon: Icon(
                                        Icons.lock_outline,
                                        color: AppColors.textSecondary,
                                        size: 20.sp,
                                      ),
                                      suffixIcon: IconButton(
                                        onPressed: controller.toggleNewPasswordVisibility,
                                        icon: Icon(
                                          controller.isNewPasswordVisible
                                              ? Icons.visibility
                                              : Icons.visibility_off,
                                          color: AppColors.textSecondary,
                                        ),
                                      ),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12.r),
                                        borderSide: BorderSide.none,
                                      ),
                                      contentPadding: EdgeInsets.symmetric(
                                        horizontal: 16.w,
                                        vertical: 16.h,
                                      ),
                                    ),
                                  ),
                                )),
                            Obx(() => controller.newPasswordError.isNotEmpty
                                ? Padding(
                                    padding: EdgeInsets.only(top: 4.h, left: 8.w),
                                    child: Text(
                                      controller.newPasswordError,
                                      style: TextStyle(
                                        color: Colors.red,
                                        fontSize: 12.sp,
                                      ),
                                    ),
                                  )
                                : const SizedBox.shrink()),
                          ],
                        ),

                        SizedBox(height: 16.h),

                        // Confirm Password field
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Obx(() => Container(
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.7),
                                    borderRadius: BorderRadius.circular(12.r),
                                  ),
                                  child: TextField(
                                    controller: controller.confirmPasswordController,
                                    obscureText: !controller.isConfirmPasswordVisible,
                                    decoration: InputDecoration(
                                      hintText: 'Xác nhận mật khẩu',
                                      hintStyle: TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 16.sp,
                                      ),
                                      prefixIcon: Icon(
                                        Icons.lock_outline,
                                        color: AppColors.textSecondary,
                                        size: 20.sp,
                                      ),
                                      suffixIcon: IconButton(
                                        onPressed: controller.toggleConfirmPasswordVisibility,
                                        icon: Icon(
                                          controller.isConfirmPasswordVisible
                                              ? Icons.visibility
                                              : Icons.visibility_off,
                                          color: AppColors.textSecondary,
                                        ),
                                      ),
                                      border: OutlineInputBorder(
                                        borderRadius: BorderRadius.circular(12.r),
                                        borderSide: BorderSide.none,
                                      ),
                                      contentPadding: EdgeInsets.symmetric(
                                        horizontal: 16.w,
                                        vertical: 16.h,
                                      ),
                                    ),
                                  ),
                                )),
                            Obx(() => controller.confirmPasswordError.isNotEmpty
                                ? Padding(
                                    padding: EdgeInsets.only(top: 4.h, left: 8.w),
                                    child: Text(
                                      controller.confirmPasswordError,
                                      style: TextStyle(
                                        color: Colors.red,
                                        fontSize: 12.sp,
                                      ),
                                    ),
                                  )
                                : const SizedBox.shrink()),
                          ],
                        ),

                        SizedBox(height: 24.h),

                        // Password requirements
                        Container(
                          padding: EdgeInsets.all(16.w),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12.r),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Mật khẩu phải có:',
                                style: TextStyle(
                                  fontSize: 14.sp,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              SizedBox(height: 8.h),
                              _buildPasswordRequirement('Ít nhất 6 ký tự'),
                            ],
                          ),
                        ),

                        SizedBox(height: 32.h),

                        // Reset password button
                        SizedBox(
                          width: double.infinity,
                          child: Obx(() => ElevatedButton(
                                onPressed: controller.isLoading || !controller.canResetPassword
                                    ? null
                                    : controller.resetPassword,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: controller.canResetPassword && !controller.isLoading
                                      ? AppColors.primary
                                      : AppColors.lineStrong,
                                  padding: EdgeInsets.symmetric(vertical: 16.h),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12.r),
                                  ),
                                ),
                                child: controller.isLoading
                                    ? SizedBox(
                                        height: 20.h,
                                        width: 20.w,
                                        child: const CircularProgressIndicator(
                                          color: Colors.white,
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : Text(
                                        'Đặt lại mật khẩu',
                                        style: TextStyle(
                                          fontSize: 16.sp,
                                          color: Colors.white,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                              )),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPasswordRequirement(String text) {
    return Padding(
      padding: EdgeInsets.only(bottom: 4.h),
      child: Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 16.sp,
            color: AppColors.success,
          ),
          SizedBox(width: 8.w),
          Text(
            text,
            style: TextStyle(
              fontSize: 12.sp,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}