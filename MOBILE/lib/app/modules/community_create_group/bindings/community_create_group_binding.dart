import 'package:get/get.dart';

import '../controllers/community_create_group_controller.dart';

class CommunityCreateGroupBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<CommunityCreateGroupController>(
      () => CommunityCreateGroupController(),
    );
  }
}
