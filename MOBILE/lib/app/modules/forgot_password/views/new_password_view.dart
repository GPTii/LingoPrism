import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/forgot_password_controller.dart';

class NewPasswordView extends GetView<ForgotPasswordController> {
  const NewPasswordView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            stops: [0.0, 0.43, 1.0],
            colors: [
              Color(0xFF0571E6),
              Color(0xFF90F3A7),
              Color(0xFF0088FF),
            ],
          ),
        ),
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
                    color: const Color(0xFFE5FFFD),
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
                            color: Color(0xFF0088FF),
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
                            color: Colors.black87,
                          ),
                        ),

                        SizedBox(height: 8.h),

                        Text(
                          'Nhập mật khẩu mới để hoàn tất quá trình khôi phục',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 16.sp,
                            color: Colors.black54,
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
                                        color: Colors.black54,
                                        fontSize: 16.sp,
                                      ),
                                      prefixIcon: Icon(
                                        Icons.lock_outline,
                                        color: Colors.black54,
                                        size: 20.sp,
                                      ),
                                      suffixIcon: IconButton(
                                        onPressed: controller.toggleNewPasswordVisibility,
                                        icon: Icon(
                                          controller.isNewPasswordVisible
                                              ? Icons.visibility
                                              : Icons.visibility_off,
                                          color: Colors.black54,
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
                                        color: Colors.black54,
                                        fontSize: 16.sp,
                                      ),
                                      prefixIcon: Icon(
                                        Icons.lock_outline,
                                        color: Colors.black54,
                                        size: 20.sp,
                                      ),
                                      suffixIcon: IconButton(
                                        onPressed: controller.toggleConfirmPasswordVisibility,
                                        icon: Icon(
                                          controller.isConfirmPasswordVisible
                                              ? Icons.visibility
                                              : Icons.visibility_off,
                                          color: Colors.black54,
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
                                  color: Colors.black87,
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
                                      ? const Color(0xFF0088FF)
                                      : const Color(0xFFBDBDBD),
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
            color: Colors.green,
          ),
          SizedBox(width: 8.w),
          Text(
            text,
            style: TextStyle(
              fontSize: 12.sp,
              color: Colors.black54,
            ),
          ),
        ],
      ),
    );
  }
}