import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class ProfileGoalController extends GetxController {
  late final TextEditingController learnController;
  late final TextEditingController reviewController;

  final RxBool isSaving = false.obs;
  final RxString errorMessage = ''.obs;

  @override
  void onInit() {
    super.onInit();
    final goal = AuthService.to.currentUser?.goal;
    learnController = TextEditingController(text: '${goal?.dailyNewTarget ?? 10}');
    reviewController = TextEditingController(text: '${goal?.dailyReviewTarget ?? 20}');
  }

  Future<void> saveGoals() async {
    if (isSaving.value) return;
    final learn = int.tryParse(learnController.text.trim());
    final review = int.tryParse(reviewController.text.trim());
    if (learn == null || learn <= 0) {
      errorMessage.value = 'Số từ vựng học mỗi ngày phải lớn hơn 0';
      return;
    }
    if (review == null || review <= 0) {
      errorMessage.value = 'Số từ vựng ôn tập mỗi ngày phải lớn hơn 0';
      return;
    }
    errorMessage.value = '';
    isSaving.value = true;
    try {
      await AuthService.to.updateGoal(dailyNew: learn, dailyReview: review);
      GameService.to.refreshAll();
      goBack(result: true);
      Get.snackbar('Đã cập nhật', 'Mục tiêu học tập đã được lưu.', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      errorMessage.value = ApiClient.toApiException(e).message;
    } finally {
      isSaving.value = false;
    }
  }

  @override
  void onClose() {
    learnController.dispose();
    reviewController.dispose();
    super.onClose();
  }
}
