import 'package:get/get.dart';

import '../controllers/profile_guide_controller.dart';

class ProfileGuideBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<ProfileGuideController>(() => ProfileGuideController());
  }
}
