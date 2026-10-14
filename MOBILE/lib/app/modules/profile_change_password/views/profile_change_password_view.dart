import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_change_password_controller.dart';

class ProfileChangePasswordView
    extends GetView<ProfileChangePasswordController> {
  const ProfileChangePasswordView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE6F9FF),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE6F9FF),
        elevation: 0,
        leading: IconButton(
          onPressed: Get.back,
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: const Color(0xFF0B1D28),
        ),
        title: Text(
          'Đổi mật khẩu',
          style: TextStyle(
            color: const Color(0xFF0B1D28),
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: false,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 24.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _PasswordField(
              label: 'Mật khẩu hiện tại',
              controller: controller.currentPasswordController,
            ),
            SizedBox(height: 18.h),
            _PasswordField(
              label: 'Mật khẩu mới',
              controller: controller.newPasswordController,
            ),
            SizedBox(height: 18.h),
            _PasswordField(
              label: 'Nhập lại mật khẩu mới',
              controller: controller.confirmPasswordController,
            ),
            SizedBox(height: 16.h),
            Obx(() {
              final error = controller.errorMessage.value;
              if (error.isEmpty) return const SizedBox.shrink();
              return Text(
                error,
                style: TextStyle(
                  color: const Color(0xFFE8505B),
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w600,
                ),
              );
            }),
            const Spacer(),
            Obx(() {
              final isSaving = controller.isSaving.value;
              return SizedBox(
                width: double.infinity,
                height: 52.h,
                child: ElevatedButton(
                  onPressed: isSaving ? null : controller.submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1CB0F6),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(26.r),
                    ),
                    elevation: 0,
                  ),
                  child: isSaving
                      ? SizedBox(
                          width: 22.w,
                          height: 22.w,
                          child: const CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : Text(
                          'Cập nhật',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _PasswordField extends StatefulWidget {
  const _PasswordField({
    required this.label,
    required this.controller,
  });

  final String label;
  final TextEditingController controller;

  @override
  State<_PasswordField> createState() => _PasswordFieldState();
}

class _PasswordFieldState extends State<_PasswordField> {
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.label,
          style: TextStyle(
            color: const Color(0xFF0B1D28),
            fontSize: 15.sp,
            fontWeight: FontWeight.w600,
          ),
        ),
        SizedBox(height: 8.h),
        TextField(
          controller: widget.controller,
          obscureText: _obscure,
          decoration: InputDecoration(
            filled: true,
            fillColor: Colors.white,
            contentPadding:
                EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18.r),
              borderSide: const BorderSide(color: Color(0xFF1CB0F6), width: 2),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18.r),
              borderSide: const BorderSide(color: Color(0xFF1CB0F6), width: 2),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18.r),
              borderSide: const BorderSide(color: Color(0xFF1CB0F6), width: 2),
            ),
            suffixIcon: IconButton(
              icon: Icon(
                _obscure ? Icons.visibility_off : Icons.visibility,
                color: const Color(0xFF60718C),
              ),
              onPressed: () => setState(() {
                _obscure = !_obscure;
              }),
            ),
          ),
        ),
      ],
    );
  }
}
