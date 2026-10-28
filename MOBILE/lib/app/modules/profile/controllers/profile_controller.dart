import 'package:get/get.dart';

import '../../../data/models/api/game.dart';
import '../../../data/models/api/user.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import '../../../routes/app_pages.dart';

/// The 10 league tiers, lowest first – tier i uses assets/brand/rank/rank_{i+1}.png (LingoPrism artwork).
const leagueTierNames = [
  'Tia Sáng', 'Ánh Đồng', 'Ánh Bạc', 'Ánh Vàng', 'Bạch Kim',
  'Ngọc Lục', 'Lam Ngọc', 'Tử Ngọc', 'Cầu Vồng', 'Lăng Kính Huyền Thoại',
];

/// Tier name → rank image.
ProfileRank rankForTier(String? tier) {
  final i = leagueTierNames.indexOf(tier ?? '');
  final index = i < 0 ? 0 : i;
  return ProfileRank(title: leagueTierNames[index], iconPath: 'assets/brand/rank/rank_${index + 1}.png');
}

class ProfileController extends GetxController {
  final Rx<ProfileSummary> summary = ProfileSummary.initial().obs;
  final RxList<String> recentPosts = <String>[].obs;
  final RxList<int> recentPostIds = <int>[].obs;
  final RxList<BadgeInfo> badges = <BadgeInfo>[].obs;
  final RxBool isLoading = false.obs;
  final RxString errorMessage = ''.obs;

  static ProfileController get to => Get.find<ProfileController>();

  /// the account the summary was last loaded for. This controller lives for the whole app (created at the splash,
  /// often before anyone is signed in), so it reloads when the account changes: sign-in, or another account
  /// after sign-out.
  int? _loadedFor;

  @override
  void onInit() {
    super.onInit();
    ever<AppUser?>(AuthService.to.user, (u) {
      if (u == null) {
        _loadedFor = null;
        summary.value = ProfileSummary.initial();
        recentPosts.clear();
        recentPostIds.clear();
        badges.clear();
      } else if (u.id != _loadedFor) {
        loadProfile();
      }
    });
    loadProfile();
  }

  Future<void> loadProfile() async {
    final user = AuthService.to.currentUser;
    if (user == null || isLoading.value) return;
    isLoading.value = true;
    errorMessage.value = '';
    try {
      await Future.wait([AuthService.to.refreshUser(), GameService.to.refreshSummary()]);
      final me = AuthService.to.currentUser ?? user;
      final game = GameService.to.summary.value;
      final rank = rankForTier(game.leagueTier);
      var followers = 0, following = 0, posts = 0;
      var groupName = '';
      final images = <String>[];
      final ids = <int>[];
      if (!me.isKid) {
        try {
          final p = await CommunityRepository.profile(me.id);
          followers = p.followers;
          following = p.following;
          posts = p.posts;
          groupName = p.groups.isNotEmpty ? (p.groups.first['name'] ?? '').toString() : '';
          for (final r in p.recentPosts) {
            images.add((r['image'] ?? '').toString());
            ids.add(int.tryParse('${r['id']}') ?? 0);
          }
        } catch (_) {}
      }
      try {
        badges.assignAll(await GameRepository.badges());
      } catch (_) {}
      summary.value = ProfileSummary(
        displayName: me.displayName.isEmpty ? me.email.split('@').first : me.displayName,
        avatarUrl: me.avatarOrDefault,
        rankTitle: rank.title,
        rankIcon: rank.iconPath,
        groupName: groupName,
        experience: game.lifetimeXp,
        streak: game.streak,
        todayHasActivity: game.studiedToday,
        posts: posts,
        followers: followers,
        following: following,
      );
      recentPosts.assignAll(images);
      recentPostIds.assignAll(ids);
      _loadedFor = me.id;
    } catch (e) {
      errorMessage.value = 'Không thể tải dữ liệu hồ sơ. Vui lòng thử lại.';
    } finally {
      isLoading.value = false;
    }
  }

  void addLocalPostPreview(String imageUrl) {
    if (imageUrl.isEmpty) return;
    recentPosts.remove(imageUrl);
    recentPosts.insert(0, imageUrl);
    summary.value = summary.value.copyWith(posts: summary.value.posts + 1);
  }

  void adjustFollowCounts({int followersDelta = 0, int followingDelta = 0}) {
    final c = summary.value;
    summary.value = c.copyWith(
      followers: (c.followers + followersDelta).clamp(0, 1 << 30),
      following: (c.following + followingDelta).clamp(0, 1 << 30),
    );
  }

  void openSettings() => Get.toNamed(Routes.profileSettings);
}

class ProfileSummary {
  const ProfileSummary({
    required this.displayName,
    required this.rankTitle,
    required this.groupName,
    required this.experience,
    required this.streak,
    required this.posts,
    required this.followers,
    required this.following,
    required this.rankIcon,
    required this.todayHasActivity,
    this.avatarUrl,
    this.groupIcon = '',
  });

  final String displayName;
  final String? avatarUrl;
  final String rankTitle;
  final String rankIcon;
  final String groupName;
  final String groupIcon;
  final int experience;
  final int streak;
  final bool todayHasActivity;
  final int posts;
  final int followers;
  final int following;

  factory ProfileSummary.initial() => const ProfileSummary(
        displayName: 'Người học LingoPrism',
        avatarUrl: null,
        rankTitle: '',
        rankIcon: '',
        groupName: '',
        groupIcon: '',
        experience: 0,
        streak: 0,
        todayHasActivity: true,
        posts: 0,
        followers: 0,
        following: 0,
      );

  ProfileSummary copyWith({
    String? displayName,
    String? avatarUrl,
    String? rankTitle,
    String? rankIcon,
    String? groupName,
    String? groupIcon,
    int? experience,
    int? streak,
    bool? todayHasActivity,
    int? posts,
    int? followers,
    int? following,
  }) {
    return ProfileSummary(
      displayName: displayName ?? this.displayName,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      rankTitle: rankTitle ?? this.rankTitle,
      rankIcon: rankIcon ?? this.rankIcon,
      groupName: groupName ?? this.groupName,
      groupIcon: groupIcon ?? this.groupIcon,
      experience: experience ?? this.experience,
      streak: streak ?? this.streak,
      todayHasActivity: todayHasActivity ?? this.todayHasActivity,
      posts: posts ?? this.posts,
      followers: followers ?? this.followers,
      following: following ?? this.following,
    );
  }
}

class ProfileRank {
  const ProfileRank({required this.title, required this.iconPath});

  final String title;
  final String iconPath;
}
