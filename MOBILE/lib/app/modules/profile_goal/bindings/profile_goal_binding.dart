import 'package:get/get.dart';

import '../controllers/profile_goal_controller.dart';

class ProfileGoalBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<ProfileGoalController>(() => ProfileGoalController());
  }
}
