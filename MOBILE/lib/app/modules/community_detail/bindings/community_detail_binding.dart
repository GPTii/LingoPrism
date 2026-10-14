import 'package:get/get.dart';

import '../controllers/community_detail_controller.dart';
import '../../community/controllers/community_controller.dart';

class CommunityDetailBinding extends Bindings {
  @override
  void dependencies() {
    if (!Get.isRegistered<CommunityController>()) {
      Get.put<CommunityController>(CommunityController());
    }
    Get.create<CommunityDetailController>(() => CommunityDetailController());
  }
}
