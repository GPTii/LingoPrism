import 'package:get/get.dart';
import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/service_binding.dart';
import '../../home/controllers/home_stats_controller.dart';
import '../../home/controllers/learning_tab_controller.dart';
import '../../../routes/app_pages.dart';
import '../../profile/controllers/profile_controller.dart';
import '../../../routes/app_pages.dart' as routes;
import 'package:lingoprism/app/core/theme/app_colors.dart';

class ProfileSettingsController extends GetxController {
  ProfileSettingsController({AuthService? authService})
      : _authService = authService ?? AuthService.to;

  final AuthService _authService;
  final RxBool isProcessing = false.obs;

  /// Language being learned, Chinese script (mainland simplified / Taiwan traditional), Zhuyin.
  Future<void> openLanguage() async {
    final user = _authService.currentUser;
    if (user == null) return;
    var value = user.activeLanguage == 'zh' ? 'zh:${user.zhScript}' : user.activeLanguage;
    var zhuyin = user.showZhuyin;
    const options = [
      ('en', 'Tiếng Anh', 'English · IPA giọng Mỹ'),
      ('zh:hans', 'Tiếng Trung giản thể', '简体中文 · chuẩn Trung Quốc đại lục'),
      ('zh:hant', 'Tiếng Trung phồn thể', '繁體中文 · chuẩn Đài Loan'),
      ('vi', 'Tiếng Việt', 'Dành cho bé học từ vựng tiếng Việt'),
    ];
    final ok = await Get.bottomSheet<bool>(
      StatefulBuilder(builder: (context, setState) {
        return Container(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          decoration: BoxDecoration(color: AppColors.surface, borderRadius: const BorderRadius.vertical(top: Radius.circular(24))),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Ngôn ngữ học', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            for (final o in options)
              RadioListTile<String>(
                value: o.$1,
                groupValue: value,
                onChanged: (v) => setState(() => value = v!),
                title: Text(o.$2),
                subtitle: Text(o.$3),
              ),
            if (value == 'zh:hant')
              SwitchListTile(
                value: zhuyin,
                onChanged: (v) => setState(() => zhuyin = v),
                title: const Text('Hiện Zhuyin (注音)'),
              ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(onPressed: () => Get.back(result: true), child: const Text('Lưu')),
            ),
          ]),
        );
      }),
      isScrollControlled: true,
    );
    if (ok != true) return;
    final parts = value.split(':');
    try {
      await _authService.updateProfile({
        'active_language': parts.first,
        if (parts.length > 1) 'zh_script': parts[1],
        'show_zhuyin': zhuyin,
        'learning_languages': {...user.learningLanguages, parts.first}.toList(),
      });
      await GameService.to.refreshAll();
      Get.snackbar('Đã cập nhật', 'Đang học: ${_authService.currentUser?.languageLabel}', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void openGoals() {
    Get.toNamed(Routes.profileGoal);
  }

  Future<void> openEditProfile() async {
    final result = await Get.toNamed(Routes.profileEdit);
    if (result == true && Get.isRegistered<ProfileController>()) {
      await Get.find<ProfileController>().loadProfile();
    }
  }

  Future<void> openChangePassword() async {
    final result = await Get.toNamed(Routes.profileChangePassword);
    if (result == true) {
      Get.snackbar(
        'Thành công',
        'Bạn đã đổi mật khẩu.',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }

  Future<void> openNotifications() async {
    await Get.toNamed(Routes.profileNotification);
  }

  void openGuide() {
    Get.toNamed(routes.Routes.profileGuide);
  }

  Future<void> logout() async {
    if (isProcessing.value) return;
    final confirmed = await Get.dialog<bool>(
      AlertDialog(
        title: const Text('Đăng xuất'),
        content: const Text('Bạn có chắc muốn đăng xuất khỏi LingoPrism?'),
        actions: [
          TextButton(
            onPressed: () => Get.back(result: false),
            child: const Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () => Get.back(result: true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
            ),
            child: const Text('Đăng xuất'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    isProcessing.value = true;
    try {
      await AppInitializer.onSessionEnded();
      await _authService.logout();
      if (Get.isRegistered<HomeStatsController>()) await Get.delete<HomeStatsController>(force: true);
      if (Get.isRegistered<LearningTabController>()) await Get.delete<LearningTabController>(force: true);
      Get.offAllNamed(Routes.login);
      Get.snackbar(
        'Đăng xuất thành công',
        'Hẹn gặp lại bạn trong buổi học tiếp theo!',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      Get.snackbar(
        'Có lỗi xảy ra',
        'Không thể đăng xuất. Vui lòng thử lại.',
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isProcessing.value = false;
    }
  }
}
