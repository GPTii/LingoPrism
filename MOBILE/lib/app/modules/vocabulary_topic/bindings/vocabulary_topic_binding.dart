import 'package:get/get.dart';

import '../controllers/vocabulary_topic_controller.dart';

class VocabularyTopicBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<VocabularyTopicController>(() => VocabularyTopicController());
  }
}
