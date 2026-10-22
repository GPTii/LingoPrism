import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/models/api/social.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../routes/app_pages.dart';
import '../../profile/controllers/profile_controller.dart';
import '../../community/views/report_user_sheet.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

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
  final RxBool blocked = false.obs;
  final RxBool isFollowLoading = false.obs;
  final RxBool showFollowButton = true.obs;
  final RxBool isLoading = false.obs;
  final RxString publicId = ''.obs;
  final Rx<FriendStatus> friendStatus = FriendStatus.none.obs;
  final RxnInt friendRequestId = RxnInt();
  final RxString friendMessage = ''.obs;
  final RxInt friends = 0.obs;

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
      publicId.value = p.author.publicId;
      friendStatus.value = p.friendStatus;
      friendRequestId.value = p.friendRequestId;
      friendMessage.value = p.friendMessage;
      friends.value = p.friends;
      blocked.value = p.blocked;
      showFollowButton.value = userId != AuthService.to.userId && !p.blocked;
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> toggleBlock() async {
    if (userId == 0) return;
    final next = !blocked.value;
    if (next) {
      final ok = await Get.dialog<bool>(AlertDialog(
        title: Text('Chặn ${summary.value.displayName}?'),
        content: const Text('Hai bạn sẽ bỏ theo dõi nhau, không nhắn tin cho nhau được và không thấy bài đăng của nhau. '
            'Người kia không nhận được thông báo.'),
        actions: [
          TextButton(onPressed: () => goBack(result: false), child: const Text('Huỷ')),
          TextButton(onPressed: () => goBack(result: true), child: const Text('Chặn', style: TextStyle(color: Colors.red))),
        ],
      ));
      if (ok != true) return;
    }
    try {
      await CommunityRepository.block(userId, next);
      Get.snackbar(next ? 'Đã chặn' : 'Đã bỏ chặn', summary.value.displayName, snackPosition: SnackPosition.BOTTOM);
      await load();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> report() async {
    if (userId == 0) return;
    if (await showReportUserSheet(userId: userId, name: summary.value.displayName, blocked: blocked.value)) await load();
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
