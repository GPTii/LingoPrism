import 'package:get/get.dart';

import '../../community/controllers/community_controller.dart';
import '../../profile/controllers/profile_controller.dart';
import '../controllers/splash_controller.dart';

class SplashBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<SplashController>(
      () => SplashController(),
    );

    // Pre-initialize heavy controllers so community/profile tabs are ready
    // once the user reaches home.
    Get.put<CommunityController>(CommunityController(), permanent: true);
    Get.put<ProfileController>(ProfileController(), permanent: true);
  }
}
