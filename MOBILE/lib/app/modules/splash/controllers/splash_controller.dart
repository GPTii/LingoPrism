import 'package:get/get.dart';

import '../../../data/services/auth_service.dart';
import '../../../data/services/local_storage_service.dart';
import '../../../data/services/service_binding.dart';
import '../../../routes/app_pages.dart';

class SplashController extends GetxController {
  final RxBool _isLoading = true.obs;
  final RxString _errorMessage = ''.obs;
  bool _isNavigating = false;

  bool get isLoading => _isLoading.value;
  String get errorMessage => _errorMessage.value;

  @override
  void onReady() {
    super.onReady();
    _init();
  }

  Future<void> _init() async {
    if (_isNavigating) return;
    try {
      _isLoading.value = true;
      _errorMessage.value = '';
      await Future.delayed(const Duration(milliseconds: 2300)); // Prismo wakes up (LivingPrismoFace intro)

      if (await LocalStorageService.isFirstLaunch()) {
        _go(Routes.onboarding);
        return;
      }
      if (AuthService.to.isLoggedIn) {
        await AppInitializer.onSessionStarted();
        if (!AuthService.to.isLoggedIn) {
          _go(Routes.login); // session expired while refreshing
          return;
        }
        _go(AuthService.to.nextRoute);
        return;
      }
      _go(Routes.login);
    } catch (e) {
      _errorMessage.value = 'Không thể khởi động ứng dụng: $e';
      _go(Routes.login);
    } finally {
      _isLoading.value = false;
    }
  }

  void _go(String route) {
    if (_isNavigating) return;
    _isNavigating = true;
    Get.offAllNamed(route);
  }

  void retry() {
    _isNavigating = false;
    _init();
  }
}
