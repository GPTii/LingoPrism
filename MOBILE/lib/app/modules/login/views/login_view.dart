import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../controllers/login_controller.dart';

class LoginView extends GetView<LoginController> {
  const LoginView({super.key});

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

              // Login form with penguin on top
              Expanded(
                flex: 4,
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    // Login form
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
                                    'Đăng nhập',
                                    style: TextStyle(
                                      fontSize: 24.sp,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.black87,
                                    ),
                                  ),
                                  SizedBox(height: 6.h),
                                  Text(
                                    'để tiếp tục vươn tới mục tiêu!',
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

                            // Forgot password
                            Align(
                              alignment: Alignment.centerRight,
                              child: TextButton(
                                onPressed: controller.forgotPassword,
                                child: Text(
                                  'Quên mật khẩu?',
                                  style: TextStyle(
                                    color: Colors.black54,
                                    fontSize: 14.sp,
                                  ),
                                ),
                              ),
                            ),

                            SizedBox(height: 12.h),

                            // Login button
                            SizedBox(
                              width: double.infinity,
                              child: Obx(() {
                                final ctrl = Get.find<LoginController>();
                                return ElevatedButton(
                                  onPressed: ctrl.isLoading || !ctrl.canLogin
                                      ? null
                                      : ctrl.login,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: ctrl.canLogin && !ctrl.isLoading
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
                                          'Đăng nhập',
                                          style: TextStyle(
                                            fontSize: 16.sp,
                                            color: Colors.white,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                );
                              }),
                            ),

                            SizedBox(height: 12.h),

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

                            SizedBox(height: 12.h),

                            // Social buttons
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                // Google
                                GestureDetector(
                                  onTap: controller.loginWithGoogle,
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
                                  onTap: controller.loginWithFacebook,
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

                            // Register link
                            Center(
                              child: GestureDetector(
                                onTap: controller.goToRegister,
                                child: RichText(
                                  text: TextSpan(
                                    text: 'Chưa có tài khoản? ',
                                    style: TextStyle(
                                      fontSize: 14.sp,
                                      color: Colors.black54,
                                    ),
                                    children: [
                                      TextSpan(
                                        text: 'Đăng ký ngay!',
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
                              Icons.person,
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