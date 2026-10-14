import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../controllers/forgot_password_controller.dart';

class VerifyCodeView extends GetView<ForgotPasswordController> {
  const VerifyCodeView({super.key});

  @override
  Widget build(BuildContext context) {
    // Auto focus first field when view opens
    controller.autoFocusFirstField();

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: AppColors.primaryGradient,
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
                        color: AppColors.textWhite,
                        size: 24.sp,
                      ),
                    ),
                    SizedBox(width: 8.w),
                    Text(
                      'Xác thực mã',
                      style: AppTextStyles.appTitle,
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
                            color: AppColors.primaryBlue,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.shield_outlined,
                            color: AppColors.textWhite,
                            size: 40.sp,
                          ),
                        ),

                        SizedBox(height: 24.h),

                        // Title and subtitle
                        Text(
                          'Nhập mã xác thực',
                          style: AppTextStyles.loginTitle,
                        ),

                        SizedBox(height: 8.h),

                        RichText(
                          textAlign: TextAlign.center,
                          text: TextSpan(
                            text: 'Chúng tôi đã gửi mã xác thực tới\n',
                            style: AppTextStyles.loginSubtitle,
                            children: [
                              TextSpan(
                                text: 'email@example.com',
                                style: AppTextStyles.linkText,
                              ),
                            ],
                          ),
                        ),

                        SizedBox(height: 32.h),

                        // Code input fields
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: List.generate(6, (index) {
                            return SizedBox(
                              width: 45.w,
                              height: 55.h,
                              child: KeyboardListener(
                                focusNode: FocusNode(),
                                onKeyEvent: (KeyEvent event) {
                                  if (event is KeyDownEvent) {
                                    if (event.logicalKey == LogicalKeyboardKey.backspace) {
                                      controller.onCodeBackspace(index);
                                    }
                                  }
                                },
                                child: TextField(
                                  controller: controller.codeControllers[index],
                                  focusNode: controller.codeFocusNodes[index],
                                  textAlign: TextAlign.center,
                                  keyboardType: TextInputType.number,
                                  maxLength: 1,
                                  inputFormatters: [
                                    FilteringTextInputFormatter.digitsOnly,
                                  ],
                                  style: AppTextStyles.wordText,
                                  onTap: () {
                                    // Move cursor to end when tapped
                                    controller.codeControllers[index].selection = TextSelection.fromPosition(
                                      TextPosition(offset: controller.codeControllers[index].text.length),
                                    );
                                  },
                                  decoration: InputDecoration(
                                    contentPadding: EdgeInsets.zero,
                                    counterText: '',
                                    filled: true,
                                    fillColor: AppColors.cardBackground,
                                    border: OutlineInputBorder(
                                      borderRadius: BorderRadius.circular(12.r),
                                      borderSide: const BorderSide(
                                        color: AppColors.surfaceLight,
                                      ),
                                    ),
                                    focusedBorder: OutlineInputBorder(
                                      borderRadius: BorderRadius.circular(12.r),
                                      borderSide: const BorderSide(
                                        color: AppColors.primaryBlue,
                                        width: 2,
                                      ),
                                    ),
                                    enabledBorder: OutlineInputBorder(
                                      borderRadius: BorderRadius.circular(12.r),
                                      borderSide: const BorderSide(
                                        color: AppColors.surfaceLight,
                                      ),
                                    ),
                                  ),
                                  onChanged: (value) {
                                    controller.onCodeChanged(index, value, context);
                                  },
                                ),
                              ),
                            );
                          }),
                        ),

                        Obx(() => controller.codeError.isNotEmpty
                            ? Padding(
                                padding: EdgeInsets.only(top: 8.h),
                                child: Text(
                                  controller.codeError,
                                  style: AppTextStyles.errorText,
                                ),
                              )
                            : const SizedBox.shrink()),

                        SizedBox(height: 24.h),

                        // Resend code
                        Obx(() => Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  'Không nhận được mã? ',
                                  style: AppTextStyles.captionMedium,
                                ),
                                if (controller.canResend)
                                  GestureDetector(
                                    onTap: controller.resendCode,
                                    child: Text(
                                      'Gửi lại',
                                      style: AppTextStyles.linkText,
                                    ),
                                  )
                                else
                                  Text(
                                    'Gửi lại trong ${controller.resendCountdown}s',
                                    style: AppTextStyles.captionMedium,
                                  ),
                              ],
                            )),

                        SizedBox(height: 32.h),

                        // Verify button
                        SizedBox(
                          width: double.infinity,
                          child: Obx(() => ElevatedButton(
                                onPressed: controller.isLoading || !controller.canVerifyCode
                                    ? null
                                    : controller.verifyCode,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: controller.canVerifyCode && !controller.isLoading
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
                                          color: AppColors.textWhite,
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : Text(
                                        'Xác thực',
                                        style: AppTextStyles.buttonMedium,
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
}