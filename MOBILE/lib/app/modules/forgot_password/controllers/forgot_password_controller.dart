import 'dart:async';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../routes/app_pages.dart';
import '../../../data/services/auth_service.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';

class ForgotPasswordController extends GetxController {
  static ForgotPasswordController get to => Get.find();

  // Controllers
  final emailController = TextEditingController();
  final newPasswordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  // Reactive email text to trigger button updates
  final _emailText = ''.obs;

  // Code input controllers
  final List<TextEditingController> codeControllers = List.generate(
    6, (index) => TextEditingController(),
  );

  // Focus nodes for OTP fields
  final List<FocusNode> codeFocusNodes = List.generate(
    6, (index) => FocusNode(),
  );

  // Observable states
  final _isLoading = false.obs;
  final _emailError = ''.obs;
  final _codeError = ''.obs;
  final _newPasswordError = ''.obs;
  final _confirmPasswordError = ''.obs;

  // Password visibility
  final _isNewPasswordVisible = false.obs;
  final _isConfirmPasswordVisible = false.obs;

  // Resend timer
  final _resendCountdown = 0.obs;
  Timer? _resendTimer;

  // Getters
  bool get isLoading => _isLoading.value;
  String get emailError => _emailError.value;
  String get codeError => _codeError.value;
  String get newPasswordError => _newPasswordError.value;
  String get confirmPasswordError => _confirmPasswordError.value;
  bool get isNewPasswordVisible => _isNewPasswordVisible.value;
  bool get isConfirmPasswordVisible => _isConfirmPasswordVisible.value;
  int get resendCountdown => _resendCountdown.value;

  bool get canResend => _resendCountdown.value == 0;

  bool get canSendCode {
    // Access reactive field to make this getter reactive
    _emailText.value;
    return emailController.text.trim().isNotEmpty;
  }

  bool get canVerifyCode {
    return codeControllers.every((controller) => controller.text.isNotEmpty);
  }

  bool get canResetPassword {
    return newPasswordController.text.isNotEmpty &&
           confirmPasswordController.text.isNotEmpty &&
           _isValidPassword(newPasswordController.text) &&
           newPasswordController.text == confirmPasswordController.text;
  }

  @override
  void onInit() {
    super.onInit();
    // Listen to text changes for reactive validation
    emailController.addListener(() {
      _validateEmail();
      _emailText.value = emailController.text; // Update reactive field
    });
    newPasswordController.addListener(() {
      _validateNewPassword();
    });
    confirmPasswordController.addListener(() {
      _validateConfirmPassword();
    });

    // Start resend timer when verify code page is opened
    _startResendTimer();
  }

  @override
  void onClose() {
    emailController.dispose();
    newPasswordController.dispose();
    confirmPasswordController.dispose();
    for (var controller in codeControllers) {
      controller.dispose();
    }
    for (var focusNode in codeFocusNodes) {
      focusNode.dispose();
    }
    _resendTimer?.cancel();
    super.onClose();
  }

  // Email validation
  bool _isValidEmail(String email) {
    return RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(email);
  }

  void _validateEmail() {
    final email = emailController.text.trim();
    if (email.isEmpty) {
      _emailError.value = '';
    } else {
      // Tạm thời accept mọi email để test
      _emailError.value = '';
    }
  }

  // Password validation
  bool _isValidPassword(String password) {
    // At least 6 characters
    return password.length >= 6;
  }

  void _validateNewPassword() {
    final password = newPasswordController.text;
    if (password.isEmpty) {
      _newPasswordError.value = '';
    } else if (!_isValidPassword(password)) {
      _newPasswordError.value = 'Mật khẩu phải có ít nhất 6 ký tự';
    } else {
      _newPasswordError.value = '';
    }
    // Also validate confirm password when new password changes
    _validateConfirmPassword();
  }

  void _validateConfirmPassword() {
    final password = newPasswordController.text;
    final confirmPassword = confirmPasswordController.text;

    if (confirmPassword.isEmpty) {
      _confirmPasswordError.value = '';
    } else if (password != confirmPassword) {
      _confirmPasswordError.value = 'Mật khẩu không khớp';
    } else {
      _confirmPasswordError.value = '';
    }
  }

  // Password visibility toggles
  void toggleNewPasswordVisibility() {
    _isNewPasswordVisible.value = !_isNewPasswordVisible.value;
  }

  void toggleConfirmPasswordVisibility() {
    _isConfirmPasswordVisible.value = !_isConfirmPasswordVisible.value;
  }

  // Shared across the 3 screens (each route builds its own controller).
  static String _flowEmail = '';
  static String _resetToken = '';

  void _snack(String title, String msg, bool ok) => Get.snackbar(title, msg,
      snackPosition: SnackPosition.BOTTOM, backgroundColor: ok ? AppColors.success : Colors.red, colorText: Colors.white);

  // Send reset code
  Future<void> sendResetCode() async {
    final email = emailController.text.trim();
    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(email)) {
      _emailError.value = 'Email không đúng định dạng';
      return;
    }
    _isLoading.value = true;
    try {
      final r = await AuthService.to.sendPasswordResetCode(email);
      if (r['success'] == true) {
        _flowEmail = email;
        _startResendTimer();
        Get.toNamed(Routes.verifyResetCode);
      } else {
        _snack('Lỗi', r['message'] as String, false);
      }
    } finally {
      _isLoading.value = false;
    }
  }

  // Start resend timer (60 seconds)
  void _startResendTimer() {
    _resendCountdown.value = 60;
    _resendTimer?.cancel();
    _resendTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendCountdown.value > 0) {
        _resendCountdown.value--;
      } else {
        timer.cancel();
      }
    });
  }

  // Resend code
  Future<void> resendCode() async {
    if (!canResend) return;

    _isLoading.value = true;

    try {
      final r = await AuthService.to.sendPasswordResetCode(_flowEmail);
      if (r['success'] != true) throw Exception(r['message']);
      _snack('Thành công', 'Mã xác thực mới đã được gửi', true);
      _startResendTimer();

    } catch (e) {
      Get.snackbar(
        'Lỗi',
        'Không thể gửi mã. Vui lòng thử lại.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );
    } finally {
      _isLoading.value = false;
    }
  }

  // Auto focus first field when view opens
  void autoFocusFirstField() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (codeFocusNodes.isNotEmpty) {
        codeFocusNodes[0].requestFocus();
      }
    });
  }

  // Handle paste operation
  void handlePaste(String pastedText) {
    // Extract only digits from pasted text
    final digits = pastedText.replaceAll(RegExp(r'[^0-9]'), '');

    // Clear all fields first
    for (var controller in codeControllers) {
      controller.clear();
    }

    // Fill fields with digits (up to 6)
    for (int i = 0; i < digits.length && i < 6; i++) {
      codeControllers[i].text = digits[i];
    }

    // Focus on the next empty field or trigger auto-submit if all filled
    if (digits.length >= 6) {
      codeFocusNodes[5].requestFocus();
      _checkAutoSubmit();
    } else if (digits.length < 6) {
      codeFocusNodes[digits.length].requestFocus();
    }
  }

  // Handle code input changes
  void onCodeChanged(int index, String value, BuildContext context) {
    _codeError.value = '';

    // Handle paste detection (when value length > 1)
    if (value.length > 1) {
      handlePaste(value);
      return;
    }

    // Handle single character input
    if (value.isNotEmpty) {
      // Move to next field if not the last one
      if (index < 5) {
        codeFocusNodes[index + 1].requestFocus();
      } else {
        // Last field - remove focus and check for auto-submit
        codeFocusNodes[index].unfocus();
        _checkAutoSubmit();
      }
    }
  }

  // Handle backspace key press
  void onCodeBackspace(int index) {
    if (codeControllers[index].text.isEmpty && index > 0) {
      // Current field is empty, move to previous field and clear it
      codeControllers[index - 1].clear();
      codeFocusNodes[index - 1].requestFocus();
    }
  }

  // Check if all fields are filled and auto-submit
  void _checkAutoSubmit() {
    if (canVerifyCode) {
      // Wait a brief moment before auto-submit to allow user to see the input
      Future.delayed(const Duration(milliseconds: 500), () {
        if (canVerifyCode) {
          verifyCode();
        }
      });
    }
  }

  // Verify reset code
  Future<void> verifyCode() async {
    if (!canVerifyCode) return;

    _isLoading.value = true;
    _codeError.value = '';

    try {
      final code = codeControllers.map((c) => c.text).join();

      final r = await AuthService.to.verifyResetCode(email: _flowEmail, code: code);
      if (r['success'] != true) {
        _codeError.value = r['message'] as String;
        return;
      }
      _resetToken = r['reset_token'] as String;

      // Success - navigate to new password page
      Get.snackbar(
        'Thành công',
        'Mã xác thực chính xác',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.success,
        colorText: Colors.white,
      );

      Get.toNamed(Routes.newPassword);

    } catch (e) {
      Get.snackbar(
        'Lỗi',
        'Không thể xác thực mã. Vui lòng thử lại.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );
    } finally {
      _isLoading.value = false;
    }
  }

  // Reset password
  Future<void> resetPassword() async {
    _validateNewPassword();
    _validateConfirmPassword();

    if (_newPasswordError.value.isNotEmpty || _confirmPasswordError.value.isNotEmpty) {
      return;
    }

    _isLoading.value = true;

    try {
      final r = await AuthService.to.resetPassword(resetToken: _resetToken, newPassword: newPasswordController.text);
      if (r['success'] != true) {
        _newPasswordError.value = r['message'] as String;
        return;
      }
      _resetToken = '';

      // Success
      Get.snackbar(
        'Thành công',
        'Mật khẩu đã được thay đổi thành công',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: AppColors.success,
        colorText: Colors.white,
      );

      // Clear all controllers
      _clearAllControllers();

      // Navigate back to login
      Get.offAllNamed(Routes.login);

    } catch (e) {
      Get.snackbar(
        'Lỗi',
        'Không thể đặt lại mật khẩu. Vui lòng thử lại.',
        snackPosition: SnackPosition.BOTTOM,
        backgroundColor: Colors.red,
        colorText: Colors.white,
      );
    } finally {
      _isLoading.value = false;
    }
  }

  void _clearAllControllers() {
    emailController.clear();
    newPasswordController.clear();
    confirmPasswordController.clear();
    for (var controller in codeControllers) {
      controller.clear();
    }
    _emailError.value = '';
    _codeError.value = '';
    _newPasswordError.value = '';
    _confirmPasswordError.value = '';
  }
}