import '../../../core/utils/brand_assets.dart';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/network/api_client.dart';
import '../../../data/services/auth_service.dart';
import '../../profile/controllers/profile_controller.dart';
import '../../../routes/app_pages.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class ProfileEditController extends GetxController {
  final TextEditingController nameController = TextEditingController();
  final TextEditingController bioController = TextEditingController();

  final RxString selectedAvatar = ''.obs;
  final Rxn<DateTime> birthDate = Rxn<DateTime>();
  final RxString gender = ''.obs;

  /// opened right after signing in (AuthService.enterAfterSignIn): "Để sau" and saving both go on to the home screen
  late final bool welcome = Get.arguments is Map && (Get.arguments as Map)['welcome'] == true;

  /// children have no Cộng đồng page, so no bio
  bool get isKid => AuthService.to.currentUser?.learnerType == 'kid';

  static const genders = [('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')];
  final RxBool isSaving = false.obs;
  final RxString errorMessage = ''.obs;

  static const List<String> avatarOptions = BrandAssets.avatars;

  @override
  void onInit() {
    super.onInit();
    final user = AuthService.to.currentUser;
    nameController.text = user?.displayName ?? '';
    bioController.text = user?.bio ?? '';
    birthDate.value = user?.birthDate;
    gender.value = user?.gender ?? '';
    selectedAvatar.value = user?.avatarOrDefault ?? avatarOptions.first;
  }

  Future<void> pickBirthDate(BuildContext context) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: birthDate.value ?? DateTime(now.year - 18),
      firstDate: DateTime(1900),
      lastDate: now,
      helpText: 'Ngày sinh',
    );
    if (picked != null) birthDate.value = picked;
  }

  void skip() => Get.offAllNamed(Routes.home);

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
      final about = <String, dynamic>{
        'display_name': name,
        if (!isKid) 'bio': bioController.text.trim(),
        if (birthDate.value != null) 'birth_date': birthDate.value!.toIso8601String().substring(0, 10),
        if (gender.value.isNotEmpty) 'gender': gender.value,
      };
      if (avatar.startsWith('assets/')) {
        await AuthService.to.updateProfile({...about, 'avatar_preset': avatar, 'avatar': null});
      } else if (avatar.isNotEmpty && !avatar.startsWith('http') && await File(avatar).exists()) {
        await AuthService.to.uploadAvatar(avatar);
        await AuthService.to.updateProfile(about);
      } else {
        await AuthService.to.updateProfile(about);
      }
      if (welcome) {
        Get.offAllNamed(Routes.home);
        return;
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
    bioController.dispose();
    super.onClose();
  }
}
