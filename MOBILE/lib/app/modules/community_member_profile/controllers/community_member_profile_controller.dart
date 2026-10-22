import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../routes/app_pages.dart';
import '../../profile/controllers/profile_controller.dart';

class CommunityMemberProfileArguments {
  const CommunityMemberProfileArguments({
    required this.userId,
    this.summary,
    this.recentPosts = const [],
    this.isFollowing = false,
  });

  final String? userId;
  final ProfileSummary? summary;
  final List<String> recentPosts;
  final bool isFollowing;

  /// Open another learner's public profile.
  static void open(int userId, {String? displayName, String? avatar}) {
    if (userId == AuthService.to.userId) {
      Get.toNamed(Routes.profile);
      return;
    }
    Get.toNamed(Routes.communityMemberProfile, arguments: CommunityMemberProfileArguments(
      userId: '$userId',
      summary: displayName == null
          ? null
          : ProfileSummary.initial().copyWith(displayName: displayName, avatarUrl: avatar),
    ));
  }
}

class CommunityMemberProfileController extends GetxController {
  late final int userId;
  final Rx<ProfileSummary> summary = ProfileSummary.initial().obs;
  final RxList<String> recentPosts = <String>[].obs;
  final RxBool isFollowing = false.obs;
  final RxBool canMessage = false.obs;
  final RxBool isFollowLoading = false.obs;
  final RxBool showFollowButton = true.obs;
  final RxBool isLoading = false.obs;

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments as CommunityMemberProfileArguments?;
    userId = int.tryParse(args?.userId ?? '') ?? 0;
    if (args?.summary != null) summary.value = args!.summary!;
    recentPosts.assignAll(args?.recentPosts ?? const []);
    isFollowing.value = args?.isFollowing ?? false;
    showFollowButton.value = userId != 0 && userId != AuthService.to.userId;
    load();
  }

  Future<void> load() async {
    if (userId == 0) return;
    isLoading.value = true;
    try {
      final p = await CommunityRepository.profile(userId);
      String? tier;
      try {
        tier = (await GameRepository.userStats(userId))['tier'] as String?;
      } catch (_) {}
      final rank = rankForTier(tier);
      summary.value = ProfileSummary(
        displayName: p.author.displayName,
        avatarUrl: p.author.avatarOrDefault,
        rankTitle: rank.title,
        rankIcon: rank.iconPath,
        groupName: p.groups.isNotEmpty ? '${p.groups.first['name']}' : '',
        experience: p.lifetimeXp,
        streak: p.streak,
        todayHasActivity: true,
        posts: p.posts,
        followers: p.followers,
        following: p.following,
      );
      recentPosts.assignAll(p.recentPosts.map((r) => '${r['image']}'));
      isFollowing.value = p.isFollowing;
      canMessage.value = p.canMessage;
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> toggleFollow() async {
    if (isFollowLoading.value || userId == 0) return;
    isFollowLoading.value = true;
    final next = !isFollowing.value;
    try {
      await CommunityRepository.follow(userId, next);
      isFollowing.value = next;
      load(); // following back may open private messages
      final s = summary.value;
      summary.value = s.copyWith(followers: (s.followers + (next ? 1 : -1)).clamp(0, 1 << 30));
      if (Get.isRegistered<ProfileController>()) {
        Get.find<ProfileController>().adjustFollowCounts(followingDelta: next ? 1 : -1);
      }
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      isFollowLoading.value = false;
    }
  }
}
