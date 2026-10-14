import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../data/services/local_storage_service.dart';
import 'app_pages.dart';

class InitialRouteMiddleware extends GetMiddleware {
  @override
  int? get priority => 1;

  @override
  RouteSettings? redirect(String? route) {
    return null;
  }

  /// Xác định route ban đầu dựa trên trạng thái app
  static Future<String> getInitialRoute() async {
    // Kiểm tra lần đầu mở app
    final isFirstLaunch = await LocalStorageService.isFirstLaunch();
    if (isFirstLaunch) return Routes.onboarding;

    // Kiểm tra đăng nhập
    final isLoggedIn = await LocalStorageService.isLoggedIn();

    if (isLoggedIn) {
      // Đã đăng nhập -> vào trang chủ
      return Routes.home;
    } else {
      // Chưa đăng nhập -> vào trang login
      return Routes.login;
    }
  }
}
