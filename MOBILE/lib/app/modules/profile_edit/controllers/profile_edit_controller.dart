import '../../../core/utils/brand_assets.dart';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/network/api_client.dart';
import '../../../data/services/auth_service.dart';
import '../../profile/controllers/profile_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class ProfileEditController extends GetxController {
  final TextEditingController nameController = TextEditingController();

  final RxString selectedAvatar = ''.obs;
  final RxBool isSaving = false.obs;
  final RxString errorMessage = ''.obs;

  static const List<String> avatarOptions = BrandAssets.avatars;

  @override
  void onInit() {
    super.onInit();
    final user = AuthService.to.currentUser;
    nameController.text = user?.displayName ?? '';
    selectedAvatar.value = user?.avatarOrDefault ?? avatarOptions.first;
  }

  void chooseAvatar(String path) => selectedAvatar.value = path;

  Future<void> pickAvatarFromDevice() async {
    try {
      final file = await ImagePicker().pickImage(source: ImageSource.gallery, maxWidth: 800, imageQuality: 85);
      if (file != null) selectedAvatar.value = file.path;
    } catch (e) {
      Get.snackbar('Lỗi', 'Không thể chọn ảnh: $e', snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> saveProfile() async {
    if (isSaving.value) return;
    final name = nameController.text.trim();
    if (name.length < 2) {
      errorMessage.value = name.isEmpty ? 'Tên người dùng không được để trống' : 'Tên người dùng phải có ít nhất 2 ký tự';
      return;
    }
    errorMessage.value = '';
    isSaving.value = true;
    try {
      final avatar = selectedAvatar.value;
      if (avatar.startsWith('assets/')) {
        await AuthService.to.updateProfile({'display_name': name, 'avatar_preset': avatar, 'avatar': null});
      } else if (avatar.isNotEmpty && !avatar.startsWith('http') && await File(avatar).exists()) {
        await AuthService.to.uploadAvatar(avatar);
        await AuthService.to.updateProfile({'display_name': name});
      } else {
        await AuthService.to.updateProfile({'display_name': name});
      }
      if (Get.isRegistered<ProfileController>()) await Get.find<ProfileController>().loadProfile();
      goBack(result: true);
      Get.snackbar('Đã cập nhật', 'Thông tin hồ sơ đã được cập nhật.', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      errorMessage.value = ApiClient.toApiException(e).message;
    } finally {
      isSaving.value = false;
    }
  }

  @override
  void onClose() {
    nameController.dispose();
    super.onClose();
  }
}
