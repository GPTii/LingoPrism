import 'package:get/get.dart';
import '../controllers/vocabulary_list_controller.dart';

class VocabularyListBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<VocabularyListController>(
      () => VocabularyListController(),
    );
  }
}
