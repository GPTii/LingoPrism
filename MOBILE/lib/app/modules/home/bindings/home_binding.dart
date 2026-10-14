import 'package:get/get.dart';

import '../../review/controllers/review_controller.dart';
import '../controllers/home_controller.dart';
import '../controllers/home_stats_controller.dart';
import '../controllers/learning_tab_controller.dart';

class HomeBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<HomeController>(() => HomeController());
    Get.lazyPut<ReviewController>(() => ReviewController(), fenix: true);
    if (!Get.isRegistered<HomeStatsController>()) Get.put<HomeStatsController>(HomeStatsController(), permanent: true);
    if (!Get.isRegistered<LearningTabController>()) Get.put<LearningTabController>(LearningTabController(), permanent: true);
  }
}
