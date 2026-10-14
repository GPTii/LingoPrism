import 'package:get/get.dart';
import '../controllers/login_controller.dart';
import '../../../data/services/auth_service.dart';

class LoginBinding extends Bindings {
  @override
  void dependencies() {
    if (!Get.isRegistered<AuthService>()) {
      Get.put<AuthService>(AuthService(), permanent: true);
    }
    Get.lazyPut<LoginController>(
      () => LoginController(),
    );
  }
}
