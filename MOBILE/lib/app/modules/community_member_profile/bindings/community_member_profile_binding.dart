import 'package:get/get.dart';

import '../controllers/community_member_profile_controller.dart';

class CommunityMemberProfileBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<CommunityMemberProfileController>(
      () => CommunityMemberProfileController(),
    );
  }
}
