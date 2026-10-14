import 'package:get/get.dart';

import '../controllers/add_vocabulary_category_controller.dart';

class AddVocabularyCategoryBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<AddVocabularyCategoryController>(
      () => AddVocabularyCategoryController(),
    );
  }
}
