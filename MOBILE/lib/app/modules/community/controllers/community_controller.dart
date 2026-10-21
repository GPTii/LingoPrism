import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/models/api/social.dart';
import '../../../data/models/api/vocab.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/tts_service.dart';
import '../../../routes/app_pages.dart';
import '../../community_chat/controllers/community_chat_controller.dart' show stickerAssets;
import '../../community_chat/models/community_chat_models.dart' as chat_models;
import '../../community_member_profile/controllers/community_member_profile_controller.dart';
import '../../profile/controllers/profile_controller.dart' show ProfileController, rankForTier;
import '../../review/controllers/review_controller.dart';

int _boundIndex(int length, int index) {
  if (length <= 0 || index < 0) return 0;
  return index >= length ? length - 1 : index;
}

class CommunityVocabularyItem {
  CommunityVocabularyItem({
    required this.label,
    required this.confidence,
    required this.headword,
    required this.phonetic,
    required this.translation,
    String? topic,
    bool isSelected = false,
    this.wordId,
    this.language = 'en',
    this.ttsLocale = 'en-US',
    this.saved = false,
  })  : topic = RxnString(topic),
        isSelected = isSelected.obs;

  final int? wordId;
  final String language;
  final String ttsLocale;
  final bool saved;
  final String label;
  final double confidence;
  final String headword;
  final String phonetic;
  final String translation;
  final RxnString topic;
  final RxBool isSelected;
}

class CommunityStudyGroup {
  CommunityStudyGroup({
    required this.groupId,
    required this.name,
    required this.requirement,
    required this.memberCount,
    required this.assetImage,
    required this.leaderId,
    required this.leaderName,
    this.requireApproval = false,
    this.description,
    this.status = 'active',
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  final String groupId;
  final String name;
  final String requirement;
  final int memberCount;
  final String assetImage;
  final String leaderId;
  final bool requireApproval;
  final String leaderName;
  final String? description;
  final String status;
  final DateTime createdAt;

  CommunityStudyGroup copyWith({
    String? groupId,
    String? name,
    String? requirement,
    int? memberCount,
    String? assetImage,
    String? leaderId,
    bool? requireApproval,
    String? leaderName,
    String? description,
    String? status,
    DateTime? createdAt,
  }) {
    return CommunityStudyGroup(
      groupId: groupId ?? this.groupId,
      name: name ?? this.name,
      requirement: requirement ?? this.requirement,
      memberCount: memberCount ?? this.memberCount,
      assetImage: assetImage ?? this.assetImage,
      leaderId: leaderId ?? this.leaderId,
      leaderName: leaderName ?? this.leaderName,
      requireApproval: requireApproval ?? this.requireApproval,
      description: description ?? this.description,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

class CommunityJoinRequest {
  CommunityJoinRequest({
    required this.groupId,
    required this.memberId,
    required this.senderUserId,
    required this.groupName,
    required this.leaderName,
    required this.message,
    required this.senderName,
  });

  // Firestore ids and sender info used by leaders to accept/reject
  final String groupId;
  final String memberId;
  final String senderUserId;

  final String groupName;
  final String leaderName;
  final String message;
  final String senderName;
}

class CommunityGroupMilestone {
  CommunityGroupMilestone({
    required this.label,
    required this.requiredPoints,
    required this.isReached,
  });

  final String label;
  final int requiredPoints;
  final bool isReached;
}

class CommunityGroupMemberScore {
  CommunityGroupMemberScore({
    required this.rank,
    required this.userId,
    required this.displayName,
    required this.totalPoints,
    required this.weeklyPoints,
    required this.avatarUrl,
    this.isHighlighted = false,
  });

  final int rank;
  final String userId;
  final String displayName;
  final int totalPoints;
  final int weeklyPoints;
  final String avatarUrl;
  final bool isHighlighted;
}

class CommunityGroupDetails {
  CommunityGroupDetails({
    required this.group,
    required this.currentMilestoneLabel,
    required this.daysRemaining,
    required this.currentPoints,
    required this.milestones,
    required this.memberScores,
  });

  final CommunityStudyGroup group;
  final String currentMilestoneLabel;
  final int daysRemaining;
  final int currentPoints;
  final List<CommunityGroupMilestone> milestones;
  final List<CommunityGroupMemberScore> memberScores;
}

class CommunityChatMessage {
  CommunityChatMessage({
    required this.senderName,
    required this.content,
    required this.isCurrentUser,
    required this.isLeader,
    this.isSticker = false,
  });

  final String senderName;
  final String content;
  final bool isCurrentUser;
  final bool isLeader;
  final bool isSticker;
}

enum CommunityLeaderboardStatus { promotion, safe, demotion }

class CommunityLeaderboardParticipant {
  CommunityLeaderboardParticipant({
    required this.rank,
    required this.userId,
    required this.name,
    required this.totalPoints,
    required this.weeklyPoints,
    required this.avatarUrl,
    required this.status,
    required this.xpBreakdown,
    required this.rawPoints,
    this.isVirtual = false,
  });

  final int rank;
  final String userId;
  final String name;
  final int totalPoints;
  final int weeklyPoints;
  final String avatarUrl;
  final CommunityLeaderboardStatus status;
  final Map<String, int> xpBreakdown;
  final int rawPoints;
  final bool isVirtual;

  CommunityLeaderboardParticipant copyWith({
    int? rank,
    String? userId,
    String? name,
    int? totalPoints,
    int? weeklyPoints,
    String? avatarUrl,
    CommunityLeaderboardStatus? status,
    Map<String, int>? xpBreakdown,
    int? rawPoints,
    bool? isVirtual,
  }) {
    return CommunityLeaderboardParticipant(
      rank: rank ?? this.rank,
      userId: userId ?? this.userId,
      name: name ?? this.name,
      totalPoints: totalPoints ?? this.totalPoints,
      weeklyPoints: weeklyPoints ?? this.weeklyPoints,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      status: status ?? this.status,
      xpBreakdown: xpBreakdown ?? this.xpBreakdown,
      rawPoints: rawPoints ?? this.rawPoints,
      isVirtual: isVirtual ?? this.isVirtual,
    );
  }
}

class CommunityLeagueInfo {
  CommunityLeagueInfo({
    required this.tierId,
    required this.name,
    required this.daysRemaining,
    required this.rankIcon,
    required this.promotionCount,
    required this.safeThreshold,
    required this.demotionCount,
    required this.participants,
    this.xpCapDescription,
    this.desiredParticipants = 20,
  });

  final String tierId;
  final String name;
  final int daysRemaining;
  final String rankIcon;
  final int promotionCount;
  final int safeThreshold;
  final int demotionCount;
  final List<CommunityLeaderboardParticipant> participants;
  final String? xpCapDescription;
  final int desiredParticipants;

  factory CommunityLeagueInfo.empty() => CommunityLeagueInfo(
        tierId: '',
        name: 'Đang tải giải đấu',
        daysRemaining: 0,
        rankIcon: 'assets/brand/rank/rank_6.png',
        promotionCount: 0,
        safeThreshold: 0,
        demotionCount: 0,
        participants: const [],
        xpCapDescription: null,
        desiredParticipants: 20,
      );
}

class CommunityPost {
  CommunityPost({
    required this.id,
    required this.authorId,
    required this.authorName,
    required this.authorAvatar,
    required this.postedAt,
    required this.imageUrl,
    this.photoId,
    required List<CommunityVocabularyItem> vocabularyItems,
    required int likes,
    required int comments,
    required int bookmarks,
    bool isLiked = false,
    int initialVocabularyIndex = 0,
    bool initiallySelected = false,
    List<CommunityPostComment>? initialComments,
    bool isSendingComment = false,
    bool canFollowAuthor = false,
    bool isFollowingAuthor = false,
    bool isFollowActionPending = false,
  })  : vocabularyItems = vocabularyItems.isEmpty
            ? [
                CommunityVocabularyItem(
                  label: 'vocabulary',
                  confidence: 0,
                  headword: 'Từ vựng',
                  phonetic: '',
                  translation: '',
                ),
              ]
            : vocabularyItems,
        currentVocabularyIndex = _boundIndex(
          vocabularyItems.isEmpty ? 1 : vocabularyItems.length,
          initialVocabularyIndex,
        ).obs,
        likes = likes.obs,
        comments = (initialComments?.length ?? comments).obs,
        bookmarks = bookmarks.obs,
        isLiked = isLiked.obs,
        commentMessages = ((initialComments != null)
                ? List<CommunityPostComment>.from(initialComments)
                : List<CommunityPostComment>.generate(
                    comments,
                    (index) => CommunityPostComment(
                      id: 'placeholder_$index',
                      userId: '',
                      userName: 'Người dùng ${index + 1}',
                      avatarUrl: '',
                      content: 'Bình luận ${index + 1}',
                      createdAt: DateTime.now(),
                    ),
                  ))
            .obs,
        isCommentsExpanded = false.obs,
        isVocabularyExpanded = true.obs,
        isSendingComment = isSendingComment.obs,
        canFollowAuthor = canFollowAuthor,
        isFollowingAuthor = isFollowingAuthor.obs,
        isFollowActionPending = isFollowActionPending.obs {
    if (initiallySelected && this.vocabularyItems.isNotEmpty) {
      this.vocabularyItems[currentVocabularyIndex.value].isSelected.value =
          true;
    }
  }

  final String id;
  final String authorId;
  final String authorName;
  final String authorAvatar;
  final String postedAt;
  final String imageUrl;
  final String? photoId;
  final List<CommunityVocabularyItem> vocabularyItems;
  final RxInt currentVocabularyIndex;
  final RxInt likes;
  final RxInt comments;
  final RxInt bookmarks;
  final RxBool isLiked;
  final RxList<CommunityPostComment> commentMessages;
  final RxBool isCommentsExpanded;
  final RxBool isVocabularyExpanded;
  final RxBool isSendingComment;

  // Follow functionality properties
  final bool canFollowAuthor;
  final RxBool isFollowingAuthor;
  final RxBool isFollowActionPending;

  CommunityVocabularyItem get currentVocabulary => vocabularyItems[
      _boundIndex(vocabularyItems.length, currentVocabularyIndex.value)];
}

class CommunityPostReport {
  CommunityPostReport({
    required this.postId,
    required this.reason,
    this.description,
    DateTime? reportedAt,
  }) : reportedAt = reportedAt ?? DateTime.now();

  final String postId;
  final String reason;
  final String? description;
  final DateTime reportedAt;
}

class CommunityPostComment {
  CommunityPostComment({
    required this.id,
    required this.userId,
    required this.userName,
    required this.avatarUrl,
    required this.content,
    required this.createdAt,
    this.isPending = false,
  });

  final String id;
  final String userId;
  final String userName;
  final String avatarUrl;
  final String content;
  final DateTime createdAt;
  final bool isPending;

  CommunityPostComment copyWith({
    String? id,
    String? userId,
    String? userName,
    String? avatarUrl,
    String? content,
    DateTime? createdAt,
    bool? isPending,
  }) {
    return CommunityPostComment(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      userName: userName ?? this.userName,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      content: content ?? this.content,
      createdAt: createdAt ?? this.createdAt,
      isPending: isPending ?? this.isPending,
    );
  }
}

/// Community tab: feed of photo + vocabulary posts, study groups (one active group per learner,
/// SnapLingua style) and the weekly league – all from the REST API.
class CommunityController extends GetxController {
  static CommunityController get to => Get.find<CommunityController>();

  final RxList<CommunityPost> posts = <CommunityPost>[].obs;
  final RxList<String> availableTopics = <String>[].obs;
  final RxBool isPostsLoading = true.obs;
  final RxnString postsError = RxnString();
  final RxString groupSearchQuery = ''.obs;
  final TextEditingController groupSearchController = TextEditingController();
  final RxList<CommunityStudyGroup> studyGroups = <CommunityStudyGroup>[].obs;
  final RxList<CommunityJoinRequest> incomingJoinRequests = <CommunityJoinRequest>[].obs;
  final Rxn<CommunityGroupDetails> joinedGroupDetails = Rxn<CommunityGroupDetails>();
  final Rx<CommunityLeagueInfo> currentLeague = CommunityLeagueInfo.empty().obs;
  final RxSet<String> reportedPostIds = <String>{}.obs;
  final Map<String, Topic> _topicsByName = {};

  bool get isKid => AuthService.to.currentUser?.isKid == true;

  @override
  void onInit() {
    super.onInit();
    if (isKid) {
      isPostsLoading.value = false;
      postsError.value = 'Tài khoản trẻ em chỉ xem được bảng xếp hạng.';
    } else {
      reloadPosts();
      loadGroups();
    }
    refreshLeaderboard();
    _loadTopics();
  }

  @override
  void onClose() {
    groupSearchController.dispose();
    super.onClose();
  }

  Future<void> _loadTopics() async {
    try {
      final topics = await VocabRepository.topics();
      _topicsByName
        ..clear()
        ..addEntries(topics.map((t) => MapEntry(t.nameVi, t)));
      availableTopics.assignAll(topics.map((t) => t.nameVi));
    } catch (_) {}
  }

  // ---------------------------------------------------------------- posts

  CommunityPost toPost(Post p) => _toPost(p);

  CommunityPost _toPost(Post p) {
    final myId = AuthService.to.userId;
    return CommunityPost(
      id: '${p.id}',
      authorId: '${p.author.id}',
      authorName: p.author.displayName,
      authorAvatar: p.author.avatarOrDefault,
      postedAt: _relativeTime(p.createdAt),
      imageUrl: p.image,
      vocabularyItems: p.words
          .where((w) => w.target != null)
          .map((w) => CommunityVocabularyItem(
                label: w.slug,
                confidence: 1,
                headword: w.text,
                phonetic: w.target!.reading,
                translation: w.meaningVi,
                topic: p.topicLabel.isEmpty ? null : p.topicLabel,
                wordId: w.id,
                language: w.target!.language,
                ttsLocale: w.target!.ttsLocale,
                saved: w.personal != null,
              ))
          .toList(),
      likes: p.likeCount,
      comments: p.commentCount,
      bookmarks: p.saveCount,
      isLiked: p.liked,
      initialComments: const [],
      canFollowAuthor: p.author.id != myId,
    )..comments.value = p.commentCount;
  }

  static String _relativeTime(DateTime t) {
    final d = DateTime.now().difference(t);
    if (d.inMinutes < 1) return 'Vừa xong';
    if (d.inMinutes < 60) return '${d.inMinutes} phút trước';
    if (d.inHours < 24) return '${d.inHours} giờ trước';
    if (d.inDays < 7) return '${d.inDays} ngày trước';
    return '${t.day.toString().padLeft(2, '0')}/${t.month.toString().padLeft(2, '0')}/${t.year}';
  }

  Future<void> reloadPosts() async {
    if (isKid) return;
    isPostsLoading.value = true;
    postsError.value = null;
    try {
      final list = await CommunityRepository.feed();
      posts.assignAll(list.map(_toPost));
    } catch (e) {
      postsError.value = ApiClient.toApiException(e).message;
    } finally {
      isPostsLoading.value = false;
    }
  }

  Future<void> refreshPostsForUser(String userId) => reloadPosts();

  void applyCurrentUserProfileLocal({required String userId, String? displayName, String? avatarUrl}) => reloadPosts();

  void markPostAsViewed(CommunityPost post) {}

  bool isPostOwner(CommunityPost post) => post.authorId == '${AuthService.to.userId}';

  bool hasReportedPost(String postId) => reportedPostIds.contains(postId);

  void openPostAuthorProfile(CommunityPost post) {
    final id = int.tryParse(post.authorId);
    if (id != null) CommunityMemberProfileArguments.open(id, displayName: post.authorName, avatar: post.authorAvatar);
  }

  Future<void> deletePost(CommunityPost post) async {
    final ok = await Get.dialog<bool>(AlertDialog(
      title: const Text('Xoá bài viết'),
      content: const Text('Bạn có chắc muốn xoá bài viết này?'),
      actions: [
        TextButton(onPressed: () => Get.back(result: false), child: const Text('Huỷ')),
        TextButton(onPressed: () => Get.back(result: true), child: const Text('Xoá')),
      ],
    ));
    if (ok != true) return;
    try {
      await CommunityRepository.deletePost(int.parse(post.id));
      posts.removeWhere((p) => p.id == post.id);
      if (Get.currentRoute == Routes.communityDetail) Get.back();
      Get.snackbar('Đã xoá', 'Bài viết đã được xoá vĩnh viễn.', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  static const List<String> reportReasons = ['Spam', 'Nội dung không phù hợp', 'Từ vựng sai', 'Quấy rối', 'Khác'];

  Future<void> followAuthor(CommunityPost post) async {
    final id = int.tryParse(post.authorId);
    if (id == null) return;
    post.isFollowActionPending.value = true;
    final next = !post.isFollowingAuthor.value;
    try {
      await CommunityRepository.follow(id, next);
      for (final p in posts.where((p) => p.authorId == post.authorId)) {
        p.isFollowingAuthor.value = next;
      }
      if (Get.isRegistered<ProfileController>()) Get.find<ProfileController>().adjustFollowCounts(followingDelta: next ? 1 : -1);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      post.isFollowActionPending.value = false;
    }
  }

  static const _reasonCodes = {
    'Spam': 'spam',
    'Nội dung không phù hợp': 'inappropriate',
    'Từ vựng sai': 'wrong_vocab',
    'Quấy rối': 'harassment',
  };

  Future<void> submitPostReport({required CommunityPost post, required String reason, String? description}) async {
    try {
      await CommunityRepository.report(int.parse(post.id), _reasonCodes[reason] ?? (_reasonCodes.containsValue(reason) ? reason : 'other'),
          description?.trim() ?? reason);
      reportedPostIds.add(post.id);
      Get.snackbar('Đã gửi báo cáo', 'Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Không thể gửi báo cáo', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> toggleLike(CommunityPost post) async {
    final next = !post.isLiked.value;
    post.isLiked.value = next;
    post.likes.value += next ? 1 : -1;
    try {
      await CommunityRepository.like(int.parse(post.id), next);
    } catch (e) {
      post.isLiked.value = !next;
      post.likes.value += next ? -1 : 1;
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void showComments(CommunityPost post) {
    post.isCommentsExpanded.toggle();
    if (post.isCommentsExpanded.value) refreshCommentsForPost(post);
  }

  void showVocabulary(CommunityPost post) => post.isVocabularyExpanded.toggle();

  Future<void> refreshCommentsForPost(CommunityPost post) async {
    try {
      final list = await CommunityRepository.comments(int.parse(post.id));
      post.commentMessages.assignAll(list.map((c) => CommunityPostComment(
            id: '${c.id}',
            userId: '${c.author.id}',
            userName: c.author.displayName,
            avatarUrl: c.author.avatarOrDefault,
            content: c.kind == 'sticker' ? (stickerAssets[c.sticker] ?? c.sticker) : c.content,
            createdAt: c.createdAt,
          )));
      post.comments.value = list.length;
    } catch (_) {}
  }

  Future<void> addComment(CommunityPost post, String comment) async {
    final text = comment.trim();
    if (text.isEmpty) {
      Get.snackbar('Bình luận trống', 'Bình luận không được để trống.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    post.isSendingComment.value = true;
    try {
      await CommunityRepository.comment(int.parse(post.id), content: text);
      await refreshCommentsForPost(post);
      GameService.to.refreshQuests();
    } catch (e) {
      Get.snackbar('Không thể bình luận', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      post.isSendingComment.value = false;
    }
  }

  void goToPreviousVocabulary(CommunityPost post) {
    if (post.currentVocabularyIndex.value > 0) post.currentVocabularyIndex.value--;
  }

  void goToNextVocabulary(CommunityPost post) {
    if (post.currentVocabularyIndex.value < post.vocabularyItems.length - 1) post.currentVocabularyIndex.value++;
  }

  void toggleSelection(CommunityPost post, CommunityVocabularyItem vocabulary) => vocabulary.isSelected.toggle();

  void updateTopic(CommunityVocabularyItem vocabulary, String topicName) => vocabulary.topic.value = topicName;

  Future<void> saveVocabulary(CommunityPost post, CommunityVocabularyItem vocabulary) async {
    if (!vocabulary.isSelected.value) {
      Get.snackbar('Chọn từ vựng', 'Vui lòng chọn từ trước khi lưu vào kho của bạn.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    final wordId = vocabulary.wordId;
    if (wordId == null) return;
    try {
      final topic = _topicsByName[vocabulary.topic.value ?? ''];
      await VocabRepository.addWord(wordId, source: 'community', topic: topic?.isSystem == false ? topic!.id : null, sourceRef: post.id);
      post.bookmarks.value++;
      GameService.to.refreshLibrary();
      if (Get.isRegistered<ReviewController>()) Get.find<ReviewController>().loadCategories();
      Get.snackbar('Đã lưu', 'Đã thêm "${vocabulary.headword}" vào thư viện của bạn', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> speakWord(String word) async {
    String locale = 'en-US';
    for (final p in posts) {
      for (final v in p.vocabularyItems) {
        if (v.headword == word) locale = v.ttsLocale;
      }
    }
    await TtsService.to.speak(word, locale);
  }

  // ---------------------------------------------------------------- groups

  static const _defaultGroupIcon = 'assets/brand/group/group_2.png';

  CommunityStudyGroup _toGroup(StudyGroup g, {String leaderId = '', String leaderName = ''}) => CommunityStudyGroup(
        groupId: '${g.id}',
        name: g.name,
        requirement: g.description,
        memberCount: g.memberCount,
        assetImage: g.icon.startsWith('assets/') ? g.icon : _defaultGroupIcon,
        leaderId: leaderId,
        leaderName: leaderName,
        requireApproval: g.requireApproval,
        description: g.description,
        createdAt: g.createdAt,
      );

  List<CommunityStudyGroup> get filteredStudyGroups {
    final q = groupSearchQuery.value.trim().toLowerCase();
    final joinedId = joinedGroupDetails.value?.group.groupId;
    return studyGroups
        .where((g) => g.groupId != joinedId)
        .where((g) => q.isEmpty || g.name.toLowerCase().contains(q) || g.requirement.toLowerCase().contains(q))
        .toList();
  }

  void onStudyGroupSearch(String query) => groupSearchQuery.value = query;

  Future<void> loadGroups() async {
    try {
      final groups = await CommunityRepository.groups();
      studyGroups.assignAll(groups.map((g) => _toGroup(g)));
      final mine = groups.firstWhereOrNull((g) => g.isMember);
      if (mine == null) {
        joinedGroupDetails.value = null;
        incomingJoinRequests.clear();
        return;
      }
      await _loadJoinedGroup(mine);
    } catch (e) {
      Get.log('loadGroups: $e');
    }
  }

  /// Weekly group goal: the members' XP this week adds up towards milestones.
  static const _milestones = [('Tia sáng', 300), ('Cầu vồng', 800), ('Ngọc lăng kính', 1500), ('Ánh sáng huyền thoại', 3000)];

  Future<void> _loadJoinedGroup(StudyGroup g) async {
    final members = await CommunityRepository.members(g.id);
    final active = members.where((m) => m.status == 'active').toList()..sort((a, b) => b.weeklyXp.compareTo(a.weeklyXp));
    final leader = active.firstWhereOrNull((m) => m.role == 'leader');
    final points = active.fold<int>(0, (s, m) => s + m.weeklyXp);
    final reached = _milestones.where((m) => points >= m.$2).toList();
    final now = DateTime.now();
    final nextMonday = DateTime(now.year, now.month, now.day).add(Duration(days: 8 - now.weekday));
    joinedGroupDetails.value = CommunityGroupDetails(
      group: _toGroup(g, leaderId: '${leader?.user.id ?? ''}', leaderName: leader?.user.displayName ?? ''),
      currentMilestoneLabel: reached.isEmpty ? 'Chưa đạt mốc' : reached.last.$1,
      daysRemaining: nextMonday.difference(now).inDays,
      currentPoints: points,
      milestones: [for (final m in _milestones) CommunityGroupMilestone(label: m.$1, requiredPoints: m.$2, isReached: points >= m.$2)],
      memberScores: [
        for (var i = 0; i < active.length; i++)
          CommunityGroupMemberScore(
            rank: i + 1,
            userId: '${active[i].user.id}',
            displayName: active[i].user.displayName,
            totalPoints: active[i].weeklyXp,
            weeklyPoints: active[i].weeklyXp,
            avatarUrl: active[i].user.avatarOrDefault,
            isHighlighted: active[i].user.id == AuthService.to.userId,
          ),
      ],
    );
    if (g.isLeader) {
      incomingJoinRequests.assignAll(members.where((m) => m.status == 'pending').map((m) => CommunityJoinRequest(
            groupId: '${g.id}',
            memberId: '${m.id}',
            senderUserId: '${m.user.id}',
            groupName: g.name,
            leaderName: leader?.user.displayName ?? '',
            message: m.requestMessage,
            senderName: m.user.displayName,
          )));
    } else {
      incomingJoinRequests.clear();
    }
  }

  Future<void> onCreateGroup() async {
    if (joinedGroupDetails.value != null) {
      Get.snackbar('Thông báo', 'Bạn cần rời nhóm hiện tại trước khi tạo nhóm mới.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    final created = await Get.toNamed(Routes.communityCreateGroup);
    if (created != null) await loadGroups();
  }

  Future<void> joinGroup(CommunityStudyGroup group) => submitJoinRequest(group: group, message: '');

  Future<void> submitJoinRequest({required CommunityStudyGroup group, required String message}) async {
    if (joinedGroupDetails.value != null) {
      Get.snackbar('Thông báo', 'Bạn chỉ tham gia được một nhóm học tập.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    if (group.requireApproval && message.trim().isEmpty) {
      Get.snackbar('Thiếu thông tin', 'Hãy giới thiệu ngắn gọn về bản thân trước khi gửi yêu cầu.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    try {
      final status = await CommunityRepository.join(int.parse(group.groupId), message: message.trim());
      if (Get.isBottomSheetOpen == true || Get.isDialogOpen == true) Get.back();
      Get.snackbar(status == 'pending' ? 'Đã gửi yêu cầu' : 'Đã tham gia',
          status == 'pending' ? 'Cần trưởng nhóm duyệt.' : 'Chào mừng bạn đến với ${group.name}!', snackPosition: SnackPosition.BOTTOM);
      await loadGroups();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> leaveGroup() async {
    final details = joinedGroupDetails.value;
    if (details == null) return;
    try {
      await CommunityRepository.leave(int.parse(details.group.groupId));
      Get.snackbar('Đã rời nhóm', 'Bạn đã rời khỏi nhóm.', snackPosition: SnackPosition.BOTTOM);
      await loadGroups();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> approveJoinRequest(String memberId) => _moderate(memberId, 'approve');

  Future<void> rejectJoinRequest(String memberId) => _moderate(memberId, 'reject');

  Future<void> _moderate(String memberId, String decision) async {
    final details = joinedGroupDetails.value;
    if (details == null) return;
    try {
      await CommunityRepository.moderate(int.parse(details.group.groupId), int.parse(memberId), decision);
      await loadGroups();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void showPendingJoinRequestsSheet(BuildContext context, String groupId) {
    Get.bottomSheet(
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Theme.of(context).canvasColor, borderRadius: const BorderRadius.vertical(top: Radius.circular(16))),
        child: Obx(() {
          final requests = incomingJoinRequests.where((r) => r.groupId == groupId).toList();
          if (requests.isEmpty) return const SizedBox(height: 160, child: Center(child: Text('Không có yêu cầu nào.')));
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final r in requests)
                ListTile(
                  title: Text(r.senderName),
                  subtitle: Text(r.message),
                  trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                    TextButton(onPressed: () => approveJoinRequest(r.memberId), child: const Text('Chấp nhận')),
                    TextButton(onPressed: () => rejectJoinRequest(r.memberId), child: const Text('Từ chối')),
                  ]),
                ),
            ],
          );
        }),
      ),
      isScrollControlled: true,
    );
  }

  void openChat() {
    final d = joinedGroupDetails.value;
    if (d == null) return;
    Get.toNamed(Routes.communityChat, arguments: chat_models.CommunityGroupDetails(
      group: chat_models.CommunityStudyGroup(
        groupId: d.group.groupId,
        name: d.group.name,
        requirement: d.group.requirement,
        memberCount: d.group.memberCount,
        assetImage: d.group.assetImage,
        leaderId: d.group.leaderId,
        leaderName: d.group.leaderName,
        requireApproval: d.group.requireApproval,
      ),
      currentMilestoneLabel: d.currentMilestoneLabel,
      remainingLabel: '${d.daysRemaining} ngày',
      currentPoints: d.currentPoints,
      milestones: d.milestones.map((m) => m.label).toList(),
      memberScores: d.memberScores.map((m) => '${m.displayName}: ${m.totalPoints}').toList(),
    ));
  }

  void openGroupMemberProfile(CommunityGroupMemberScore member) {
    final id = int.tryParse(member.userId);
    if (id != null) CommunityMemberProfileArguments.open(id, displayName: member.displayName, avatar: member.avatarUrl);
  }

  void openStudyGroupLeaderProfile(CommunityStudyGroup group) {
    final id = int.tryParse(group.leaderId);
    if (id != null) CommunityMemberProfileArguments.open(id, displayName: group.leaderName);
  }

  // ---------------------------------------------------------------- leaderboard

  List<CommunityLeaderboardParticipant> get promotionLeaders =>
      currentLeague.value.participants.where((p) => p.status == CommunityLeaderboardStatus.promotion).toList();

  List<CommunityLeaderboardParticipant> get safeLeaders =>
      currentLeague.value.participants.where((p) => p.status == CommunityLeaderboardStatus.safe).toList();

  List<CommunityLeaderboardParticipant> get demotionLeaders =>
      currentLeague.value.participants.where((p) => p.status == CommunityLeaderboardStatus.demotion).toList();

  Future<void> refreshLeaderboard() async {
    try {
      final board = await GameRepository.leaderboard();
      final rank = rankForTier(board.tierName);
      final members = board.members
          .map((m) => CommunityLeaderboardParticipant(
                rank: m.rank,
                userId: '${m.userId}',
                name: m.isMe ? '${m.displayName} (bạn)' : m.displayName,
                totalPoints: m.xp,
                weeklyPoints: m.xp,
                avatarUrl: m.avatar ?? 'assets/brand/avatar/avatar_1.png',
                status: switch (m.zone) {
                  'promotion' => CommunityLeaderboardStatus.promotion,
                  'demotion' => CommunityLeaderboardStatus.demotion,
                  _ => CommunityLeaderboardStatus.safe,
                },
                xpBreakdown: const {},
                rawPoints: m.xp,
              ))
          .toList();
      final days = board.endsAt == null ? 0 : board.endsAt!.difference(DateTime.now()).inDays;
      currentLeague.value = CommunityLeagueInfo(
        tierId: board.tierCode ?? '',
        name: board.tierName ?? 'Giải đấu tuần',
        daysRemaining: days < 0 ? 0 : days,
        rankIcon: rank.iconPath,
        promotionCount: members.where((m) => m.status == CommunityLeaderboardStatus.promotion).length,
        safeThreshold: 0,
        demotionCount: members.where((m) => m.status == CommunityLeaderboardStatus.demotion).length,
        participants: members,
        xpCapDescription: 'Tối đa 500 XP mỗi ngày',
      );
    } catch (e) {
      Get.log('refreshLeaderboard: $e');
    }
  }

  void openLeaderboardProfile(CommunityLeaderboardParticipant participant) {
    final id = int.tryParse(participant.userId);
    if (id != null) CommunityMemberProfileArguments.open(id, displayName: participant.name, avatar: participant.avatarUrl);
  }
}
