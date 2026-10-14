import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../data/models/onboarding_model.dart';
import '../../../data/services/local_storage_service.dart';
import '../../../routes/app_pages.dart';

class OnboardingController extends GetxController {
  static OnboardingController get to => Get.find();

  late PageController pageController;
  final _currentIndex = 0.obs;

  int get currentIndex => _currentIndex.value;
  List<OnboardingModel> get onboardingData => _onboardingData;

  final List<OnboardingModel> _onboardingData = [
    OnboardingModel(
      image: 'assets/images/chimcanhcut/chim_thich.png',
      title: 'Chụp ảnh\nhọc từ vựng',
      description: 'Chụp hoặc chọn ảnh, SnapLingua tự phát hiện vật thể và gợi ý từ, phát âm, nghĩa, ví dụ. Chọn từ muốn lưu và gắn chủ đề.',
    ),
    OnboardingModel(
      image: 'assets/images/chimcanhcut/chim_nhachoc.png',
      title: 'Học tập\nmọi lúc, mọi nơi',
      description: 'Không tiện học phát âm ở nơi đông người? Không có thời gian để hoàn thành bài học dài? Chúng tôi luôn có lựa chọn khác cho bạn!',
    ),
    OnboardingModel(
      image: 'assets/images/chimcanhcut/chim_hocnhom3.png',
      title: 'Học cùng nhau\nđể bền bỉ mỗi ngày',
      description: 'Tham gia nhóm để cùng đạt mục tiêu, chia sẻ ảnh nhận diện và học từ vựng với bạn bè.',
    ),
  ];

  @override
  void onInit() {
    super.onInit();
    pageController = PageController();
  }

  @override
  void onClose() {
    pageController.dispose();
    super.onClose();
  }

  void onPageChanged(int index) {
    _currentIndex.value = index;
  }

  void nextPage() {
    if (currentIndex < _onboardingData.length - 1) {
      pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.ease,
      );
    }
  }

  void goToLogin() async {
    // Đánh dấu đã xem onboarding
    await LocalStorageService.setFirstLaunchComplete();
    // Navigate to login page
    Get.offNamed(Routes.login);
  }

  void goToRegister() async {
    // Đánh dấu đã xem onboarding
    await LocalStorageService.setFirstLaunchComplete();
    // Navigate to register page
    Get.offNamed(Routes.register);
  }

  void skipOnboarding() async {
    // Đánh dấu đã xem onboarding
    await LocalStorageService.setFirstLaunchComplete();
    // Skip to main app
    Get.offNamed(Routes.home);
  }
}