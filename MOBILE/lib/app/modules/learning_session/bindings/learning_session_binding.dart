import 'package:get/get.dart';

import '../controllers/learning_session_controller.dart';

class LearningSessionBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<LearningSessionController>(
      () => LearningSessionController(),
    );
  }
}
