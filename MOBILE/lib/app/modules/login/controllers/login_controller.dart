import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_widgets.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/google_sign_in_service.dart';
import '../../../data/services/service_binding.dart';
import '../../../routes/app_pages.dart';

class LoginController extends GetxController {
  static LoginController get to => Get.find();

  final AuthService _authService = AuthService.to;

  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  final _isPasswordVisible = false.obs;
  final _isLoading = false.obs;
  final _emailError = ''.obs;
  final _passwordError = ''.obs;

  bool get isPasswordVisible => _isPasswordVisible.value;
  bool get isLoading => _isLoading.value;
  String get emailError => _emailError.value;
  String get passwordError => _passwordError.value;

  @override
  void onInit() {
    super.onInit();
    emailController.addListener(_emailError.refresh);
    passwordController.addListener(_passwordError.refresh);
  }

  @override
  void onClose() {
    emailController.dispose();
    passwordController.dispose();
    super.onClose();
  }

  bool get canLogin {
    _emailError.value;
    _passwordError.value;
    return emailController.text.trim().isNotEmpty && passwordController.text.isNotEmpty;
  }

  void togglePasswordVisibility() => _isPasswordVisible.value = !_isPasswordVisible.value;

  void forgotPassword() => Get.toNamed(Routes.forgotPassword);

  void goToRegister() => Get.toNamed(Routes.register);

  bool _validate() {
    final email = emailController.text.trim();
    _emailError.value =
        RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(email) ? '' : 'Email không đúng định dạng';
    _passwordError.value = passwordController.text.isEmpty ? 'Mật khẩu không được để trống' : '';
    return _emailError.value.isEmpty && _passwordError.value.isEmpty;
  }

  Future<void> login() async {
    if (!_validate()) return;
    _isLoading.value = true;
    try {
      final result = await _authService.login(email: emailController.text.trim(), password: passwordController.text);
      if (result['success'] == true) {
        await _enterApp();
      } else {
        AppWidgets.showErrorDialog(title: 'Thông báo', message: result['message'] as String? ?? 'Đăng nhập thất bại');
      }
    } finally {
      _isLoading.value = false;
    }
  }

  Future<void> loginWithGoogle() async {
    if (!GoogleSignInService.configured) {
      AppWidgets.showInfoDialog(
        title: 'Đăng nhập Google',
        message: 'Bản build này chưa cấu hình Google Client ID (GOOGLE_SERVER_CLIENT_ID). Vui lòng đăng nhập bằng email.',
      );
      return;
    }
    _isLoading.value = true;
    try {
      final result = await _authService.loginWithGoogle();
      if (result['success'] == true) {
        await _enterApp();
      } else if (result['cancelled'] != true) {
        AppWidgets.showErrorDialog(title: 'Thông báo', message: result['message'] as String);
      }
    } finally {
      _isLoading.value = false;
    }
  }

  Future<void> _enterApp() async {
    await AppInitializer.onSessionStarted();
    final onboarded = _authService.currentUser?.onboardingCompleted == true;
    await Get.offAllNamed(onboarded ? Routes.home : Routes.survey);
  }
}
