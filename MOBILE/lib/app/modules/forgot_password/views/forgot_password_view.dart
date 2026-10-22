import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../controllers/forgot_password_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class ForgotPasswordView extends GetView<ForgotPasswordController> {
  const ForgotPasswordView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: AppColors.primaryGradient),
        child: SafeArea(
          child: Column(
            children: [
              // Header
              Padding(
                padding: EdgeInsets.only(top: 20.h, left: 24.w, right: 24.w),
                child: Row(
                  children: [
                    IconButton(
                      onPressed: () => goBack(),
                      icon: Icon(
                        Icons.arrow_back_ios,
                        color: Colors.white,
                        size: 24.sp,
                      ),
                    ),
                    SizedBox(width: 8.w),
                    Text(
                      'Quên mật khẩu',
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
                    color: AppColors.backgroundLight,
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
                          decoration: BoxDecoration(
                            color: AppColors.buttonActive,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.lock_reset,
                            color: Colors.white,
                            size: 40.sp,
                          ),
                        ),

                        SizedBox(height: 24.h),

                        // Title and subtitle
                        Text(
                          'Khôi phục mật khẩu',
                          style: TextStyle(
                            fontSize: 24.sp,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),

                        SizedBox(height: 8.h),

                        Text(
                          'Nhập email của bạn để nhận mã xác thực',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 16.sp,
                            color: AppColors.textSecondary,
                          ),
                        ),

                        SizedBox(height: 32.h),

                        // Email field
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              decoration: BoxDecoration(
                                color: AppColors.surface.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(12.r),
                              ),
                              child: TextField(
                                controller: controller.emailController,
                                keyboardType: TextInputType.emailAddress,
                                decoration: InputDecoration(
                                  hintText: 'Nhập email của bạn',
                                  hintStyle: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 16.sp,
                                  ),
                                  prefixIcon: Icon(
                                    Icons.email_outlined,
                                    color: AppColors.textSecondary,
                                    size: 20.sp,
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
                            ),
                            Obx(() => controller.emailError.isNotEmpty
                                ? Padding(
                                    padding: EdgeInsets.only(top: 4.h, left: 8.w),
                                    child: Text(
                                      controller.emailError,
                                      style: TextStyle(
                                        color: Colors.red,
                                        fontSize: 12.sp,
                                      ),
                                    ),
                                  )
                                : const SizedBox.shrink()),
                          ],
                        ),

                        SizedBox(height: 32.h),

                        // Send code button
                        SizedBox(
                          width: double.infinity,
                          child: Obx(() => ElevatedButton(
                                onPressed: controller.isLoading || !controller.canSendCode
                                    ? null
                                    : controller.sendResetCode,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: controller.canSendCode && !controller.isLoading
                                      ? AppColors.buttonActive
                                      : AppColors.buttonDisabled,
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
                                        'Gửi mã xác thực',
                                        style: TextStyle(
                                          fontSize: 16.sp,
                                          color: Colors.white,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                              )),
                        ),

                        SizedBox(height: 24.h),

                        // Back to login
                        TextButton(
                          onPressed: () => goBack(),
                          child: Text(
                            'Quay lại đăng nhập',
                            style: TextStyle(
                              color: AppColors.buttonActive,
                              fontSize: 16.sp,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
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
}