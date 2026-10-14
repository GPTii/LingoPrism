import 'package:get/get.dart';

import '../controllers/vocabulary_flashcard_controller.dart';

class VocabularyFlashcardBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<VocabularyFlashcardController>(
      () => VocabularyFlashcardController(),
    );
  }
}
