import 'package:get/get.dart';

import '../controllers/community_chat_controller.dart';

class CommunityChatBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<CommunityChatController>(() => CommunityChatController());
  }
}
