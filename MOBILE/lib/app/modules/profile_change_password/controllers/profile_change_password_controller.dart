import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../data/services/auth_service.dart';

class ProfileChangePasswordController extends GetxController {
  ProfileChangePasswordController({AuthService? authService})
      : _authService = authService ?? AuthService.to;

  final AuthService _authService;

  final TextEditingController currentPasswordController =
      TextEditingController();
  final TextEditingController newPasswordController = TextEditingController();
  final TextEditingController confirmPasswordController =
      TextEditingController();

  final RxBool isSaving = false.obs;
  final RxString errorMessage = ''.obs;

  Future<void> submit() async {
    if (isSaving.value) return;

    final currentPassword = currentPasswordController.text.trim();
    final newPassword = newPasswordController.text.trim();
    final confirmPassword = confirmPasswordController.text.trim();

    if (currentPassword.isEmpty ||
        newPassword.isEmpty ||
        confirmPassword.isEmpty) {
      errorMessage.value = 'Vui lòng nhập đầy đủ thông tin';
      return;
    }

    errorMessage.value = '';
    isSaving.value = true;

    try {
      final result = await _authService.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
        confirmPassword: confirmPassword,
      );

      if (result['success'] == true) {
        Get.back(result: true);
        Get.snackbar(
          'Đã cập nhật',
          'Mật khẩu của bạn đã được thay đổi.',
          snackPosition: SnackPosition.BOTTOM,
        );
      } else {
        errorMessage.value = result['message'] as String? ??
            'Không thể đổi mật khẩu. Vui lòng thử lại.';
      }
    } catch (e) {
      errorMessage.value =
          'Có lỗi xảy ra khi đổi mật khẩu. Vui lòng thử lại.';
    } finally {
      isSaving.value = false;
    }
  }

  @override
  void onClose() {
    currentPasswordController.dispose();
    newPasswordController.dispose();
    confirmPasswordController.dispose();
    super.onClose();
  }
}
