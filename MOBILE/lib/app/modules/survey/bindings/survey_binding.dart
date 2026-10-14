import 'package:get/get.dart';
import '../controllers/survey_controller.dart';

class SurveyBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<SurveyController>(
      () => SurveyController(),
    );
  }
}