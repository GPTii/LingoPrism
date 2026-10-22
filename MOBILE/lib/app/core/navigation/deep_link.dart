import 'package:get/get.dart';

import '../../data/repositories/repositories.dart';
import '../../modules/community/controllers/community_controller.dart';
import '../../modules/community_detail/controllers/community_detail_controller.dart';
import '../../modules/community_member_profile/controllers/community_member_profile_controller.dart';
import '../../modules/vocabulary_topic/controllers/vocabulary_topic_controller.dart';
import '../../routes/app_pages.dart';

/// Opens the in-app screen for a route sent by the server in notifications (`data.route`).
class DeepLink {
  DeepLink._();

  static Future<void> open(String route) async {
    int? id(String pattern) => int.tryParse(RegExp(pattern).firstMatch(route)?.group(1) ?? '');
    try {
      if (route.startsWith('/vocab/topics/')) {
        final topic = await VocabRepository.topic(id(r'/vocab/topics/(\d+)')!);
        Get.toNamed(Routes.vocabularyTopic, arguments: VocabularyTopicArguments(topic: topic));
      } else if (route.startsWith('/community/posts/')) {
        final post = await CommunityRepository.post(id(r'/community/posts/(\d+)')!);
        final community = Get.isRegistered<CommunityController>() ? CommunityController.to : Get.put(CommunityController());
        Get.toNamed(Routes.communityDetail, arguments: CommunityDetailArguments(post: community.toPost(post)));
      } else if (route.startsWith('/friends')) {
        Get.toNamed(Routes.friends, arguments: route.contains('tab=incoming') ? 1 : 0);
      } else if (route.startsWith('/community/users/')) {
        CommunityMemberProfileArguments.open(id(r'/community/users/(\d+)')!);
      } else if (route.startsWith('/community')) {
        Get.toNamed(Routes.community);
      } else if (route.startsWith('/exams/results/')) {
        Get.toNamed(Routes.examResult, arguments: id(r'/exams/results/(\d+)'));
      } else if (route.startsWith('/messages')) {
        final thread = id(r'/messages/(\d+)');
        thread == null ? Get.toNamed(Routes.messages) : Get.toNamed(Routes.directChat, arguments: thread);
      } else if (route.startsWith('/support')) {
        Get.toNamed(Routes.supportChat);
      } else if (route.startsWith('/profile')) {
        Get.toNamed(Routes.profile);
      }
    } catch (_) {
      Get.snackbar('Không mở được', 'Nội dung này không còn tồn tại.', snackPosition: SnackPosition.BOTTOM);
    }
  }
}
