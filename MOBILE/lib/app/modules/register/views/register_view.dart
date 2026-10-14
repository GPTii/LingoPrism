import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../controllers/register_controller.dart';

class RegisterView extends GetView<RegisterController> {
  const RegisterView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.primaryGradient),
        child: SafeArea(
          child: Column(
            children: [
              // Header with app name
              Padding(
                padding: EdgeInsets.only(top: 40.h, left: 24.w, right: 24.w, bottom: 1.h),
                child: Row(
                  children: [
                    Text(
                      'Snaplingua',
                      style: TextStyle(
                        fontSize: 28.sp,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),

              // Register form with penguin on top
              Expanded(
                flex: 4,
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    // Register form
                    Container(
                      width: double.infinity,
                      margin: EdgeInsets.only(
                        left: 16.w,
                        right: 16.w,
                        top: 60.h, // Space for penguin
                        bottom: 0,
                      ),
                      padding: EdgeInsets.only(
                        left: 24.w,
                        right: 24.w,
                        top: 80.h, // Extra space for penguin inside
                        bottom: 24.h,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.backgroundLight,
                        borderRadius: BorderRadius.circular(24.r),
                      ),
                      child: SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Title
                            Center(
                              child: Column(
                                children: [
                                  Text(
                                    'Tạo tài khoản',
                                    style: TextStyle(
                                      fontSize: 24.sp,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.black87,
                                    ),
                                  ),
                                  SizedBox(height: 6.h),
                                  Text(
                                    'và bắt đầu học tập ngay hôm nay!',
                                    style: TextStyle(
                                      fontSize: 16.sp,
                                      color: Colors.black54,
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            SizedBox(height: 24.h),

                            // Email field
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.7),
                                    borderRadius: BorderRadius.circular(12.r),
                                  ),
                                  child: TextField(
                                    controller: controller.emailController,
                                    keyboardType: TextInputType.emailAddress,
                                    decoration: InputDecoration(
                                      hintText: 'Email',
                                      hintStyle: TextStyle(
                                        color: Colors.black54,
                                        fontSize: 16.sp,
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

                            SizedBox(height: 16.h),

                            // Password field
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Obx(() => Container(
                                      decoration: BoxDecoration(
                                        color: Colors.white.withOpacity(0.7),
                                        borderRadius: BorderRadius.circular(12.r),
                                      ),
                                      child: TextField(
                                        controller: controller.passwordController,
                                        obscureText: !controller.isPasswordVisible,
                                        decoration: InputDecoration(
                                          hintText: 'Mật khẩu',
                                          hintStyle: TextStyle(
                                            color: Colors.black54,
                                            fontSize: 16.sp,
                                          ),
                                          suffixIcon: IconButton(
                                            onPressed: controller.togglePasswordVisibility,
                                            icon: Icon(
                                              controller.isPasswordVisible
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
                                Obx(() => controller.passwordError.isNotEmpty
                                    ? Padding(
                                        padding: EdgeInsets.only(top: 4.h, left: 8.w),
                                        child: Text(
                                          controller.passwordError,
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
                                          hintText: 'Nhập lại mật khẩu',
                                          hintStyle: TextStyle(
                                            color: Colors.black54,
                                            fontSize: 16.sp,
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

                            // Register button
                            SizedBox(
                              width: double.infinity,
                              child: Obx(() {
                                final ctrl = Get.find<RegisterController>();
                                return ElevatedButton(
                                  onPressed: ctrl.isLoading || !ctrl.canRegister
                                      ? null
                                      : ctrl.register,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: ctrl.canRegister && !ctrl.isLoading
                                        ? AppColors.buttonActive
                                        : AppColors.buttonDisabled,
                                    padding: EdgeInsets.symmetric(vertical: 16.h),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12.r),
                                    ),
                                  ),
                                  child: ctrl.isLoading
                                      ? SizedBox(
                                          height: 20.h,
                                          width: 20.w,
                                          child: const CircularProgressIndicator(
                                            color: Colors.white,
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : Text(
                                          'Đăng ký',
                                          style: TextStyle(
                                            fontSize: 16.sp,
                                            color: Colors.white,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                );
                              }),
                            ),

                            SizedBox(height: 16.h),

                            // Social login
                            Center(
                              child: Text(
                                'hoặc tiếp tục với',
                                style: TextStyle(
                                  fontSize: 14.sp,
                                  color: Colors.black54,
                                ),
                              ),
                            ),

                            SizedBox(height: 16.h),

                            // Social buttons
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                // Google
                                GestureDetector(
                                  onTap: controller.registerWithGoogle,
                                  child: Image.asset(
                                    'assets/icons/google.png',
                                    width: 48.w,
                                    height: 48.h,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Icon(
                                        Icons.email,
                                        size: 48.sp,
                                        color: Colors.red,
                                      );
                                    },
                                  ),
                                ),

                                SizedBox(width: 16.w),

                                // Facebook
                                GestureDetector(
                                  onTap: controller.registerWithFacebook,
                                  child: Image.asset(
                                    'assets/icons/facebook.png',
                                    width: 48.w,
                                    height: 48.h,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Icon(
                                        Icons.people,
                                        size: 48.sp,
                                        color: AppColors.facebook,
                                      );
                                    },
                                  ),
                                ),
                              ],
                            ),

                            SizedBox(height: 32.h),

                            // Login link
                            Center(
                              child: GestureDetector(
                                onTap: controller.goToLogin,
                                child: RichText(
                                  text: TextSpan(
                                    text: 'Đã có tài khoản? ',
                                    style: TextStyle(
                                      fontSize: 14.sp,
                                      color: Colors.black54,
                                    ),
                                    children: [
                                      TextSpan(
                                        text: 'Đăng nhập ngay!',
                                        style: TextStyle(
                                          fontSize: 14.sp,
                                          color: AppColors.buttonActive,
                                          fontWeight: FontWeight.w600,
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

                    // Penguin image positioned on top of form
                    Positioned(
                      top: -60.h,
                      right: 50.w,
                      child: Image.asset(
                        'assets/images/chimcanhcut/chim_xinchao.png',
                        height: 180.h,
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) {
                          return Container(
                            height: 120.h,
                            width: 120.w,
                            decoration: const BoxDecoration(
                              color: Colors.white24,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              Icons.person_add,
                              size: 60.sp,
                              color: Colors.white,
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}