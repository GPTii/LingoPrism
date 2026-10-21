import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';

import 'app_colors.dart';

/// Light or dark, remembered on the device (dark first, like the web).
class ThemeService {
  ThemeService._();

  static final GetStorage _box = GetStorage();
  static const _key = 'theme_mode';

  static ThemeMode get mode => _box.read<String>(_key) == 'light' ? ThemeMode.light : ThemeMode.dark;
  static bool get isDark => mode == ThemeMode.dark;

  /// Call once before runApp, after GetStorage.init().
  static void init() => AppColors.use(isDark ? Brightness.dark : Brightness.light);

  static Future<void> set(ThemeMode m) async {
    await _box.write(_key, m == ThemeMode.light ? 'light' : 'dark');
    AppColors.use(m == ThemeMode.light ? Brightness.light : Brightness.dark);
    Get.changeThemeMode(m);
    // AppColors values are read while building: rebuild every screen with the new palette
    await Get.forceAppUpdate();
  }

  static Future<void> toggle() => set(isDark ? ThemeMode.light : ThemeMode.dark);
}
