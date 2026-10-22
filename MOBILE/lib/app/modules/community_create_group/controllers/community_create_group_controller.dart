import '../../../core/utils/brand_assets.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../core/network/api_client.dart';
import '../../../data/repositories/repositories.dart';
import 'package:lingoprism/app/data/services/auth_service.dart';
import 'package:lingoprism/app/core/navigation/back.dart';


enum StudyGroupApprovalMode { auto, require }

class CommunityCreateGroupController extends GetxController {
  final formKey = GlobalKey<FormState>();
  final nameController = TextEditingController();
  final requirementController = TextEditingController();

  final RxInt selectedIconIndex = (-1).obs;
  final Rx<StudyGroupApprovalMode> approvalMode =
      StudyGroupApprovalMode.auto.obs;
  final RxBool canSubmit = false.obs;
  final RxBool isSubmitting = false.obs;

  static const List<String> iconAssets = BrandAssets.groupIcons;

  @override
  void onInit() {
    super.onInit();
    nameController.addListener(_recomputeSubmitState);
    requirementController.addListener(_recomputeSubmitState);
  }

  void selectIcon(int index) {
    selectedIconIndex.value = index;
    _recomputeSubmitState();
  }

  void setApprovalMode(StudyGroupApprovalMode mode) {
    approvalMode.value = mode;
  }

  void _recomputeSubmitState() {
    final hasName = nameController.text.trim().isNotEmpty;
    final hasRequirement = requirementController.text.trim().isNotEmpty;
    final hasIcon = selectedIconIndex.value >= 0 &&
        selectedIconIndex.value < iconAssets.length;
    canSubmit.value = hasName && hasRequirement && hasIcon;
  }

  String? _resolveUserId() => AuthService.to.isLoggedIn ? AuthService.to.currentUserId : null;


  Future<void> submit() async {
    if (!canSubmit.value || isSubmitting.value) {
      return;
    }

    final userId = _resolveUserId();
    if (userId == null) {
      Get.snackbar(
        'Cần đăng nhập',
        'Hãy đăng nhập để tạo nhóm học tập.',
        snackPosition: SnackPosition.BOTTOM,
      );
      return;
    }

    final iconIndex = selectedIconIndex.value;
    final iconPath = iconAssets[iconIndex];
    final requireApproval =
        approvalMode.value == StudyGroupApprovalMode.require;

    final name = nameController.text.trim();
    final description = requirementController.text.trim();
    isSubmitting.value = true;
    try {
      final group = await CommunityRepository.createGroup(name, description, requireApproval, icon: iconPath);
      goBack(result: group);
    } catch (e) {
      Get.snackbar(
        'Có lỗi xảy ra',
        ApiClient.toApiException(e).message,
        snackPosition: SnackPosition.BOTTOM,
      );
    } finally {
      isSubmitting.value = false;
    }
  }

  @override
  void onClose() {
    nameController
      ..removeListener(_recomputeSubmitState)
      ..dispose();
    requirementController
      ..removeListener(_recomputeSubmitState)
      ..dispose();
    super.onClose();
  }
}
