import '../../../core/utils/brand_assets.dart';
import 'common.dart';
import 'vocab.dart';

class Post {
  Post({
    required this.id,
    required this.author,
    required this.image,
    this.caption = '',
    this.topicLabel = '',
    this.likeCount = 0,
    this.commentCount = 0,
    this.liked = false,
    this.saveCount = 0,
    this.words = const [],
    required this.createdAt,
  });

  final int id;
  final Author author;
  final String image;
  final String caption;
  final String topicLabel;
  final int likeCount;
  final int commentCount;
  final bool liked;
  final int saveCount;
  final List<WordCard> words;
  final DateTime createdAt;

  Post copyWith({bool? liked, int? likeCount, int? commentCount, int? saveCount}) => Post(
        id: id,
        author: author,
        image: image,
        caption: caption,
        topicLabel: topicLabel,
        likeCount: likeCount ?? this.likeCount,
        commentCount: commentCount ?? this.commentCount,
        liked: liked ?? this.liked,
        saveCount: saveCount ?? this.saveCount,
        words: words,
        createdAt: createdAt,
      );

  factory Post.fromJson(Map<String, dynamic> j) => Post(
        id: asInt(j['id']),
        author: Author.fromJson(asMap(j['author'])),
        image: brandAsset(asString(j['image'])),
        caption: asString(j['caption']),
        topicLabel: asString(j['topic_label']),
        likeCount: asInt(j['like_count']),
        commentCount: asInt(j['comment_count']),
        liked: j['liked'] == true,
        saveCount: asInt(j['save_count']),
        words: asMapList(j['words']).map(WordCard.fromJson).toList(),
        createdAt: parseDate(j['created_at']) ?? DateTime.now(),
      );
}

class PostComment {
  PostComment({required this.id, required this.author, this.kind = 'text', this.content = '', this.sticker = '', required this.createdAt});

  final int id;
  final Author author;
  final String kind; // text | sticker
  final String content;
  final String sticker;
  final DateTime createdAt;

  factory PostComment.fromJson(Map<String, dynamic> j) => PostComment(
        id: asInt(j['id']),
        author: Author.fromJson(asMap(j['author'])),
        kind: asString(j['kind'], 'text'),
        content: asString(j['content']),
        sticker: asString(j['sticker']),
        createdAt: parseDate(j['created_at']) ?? DateTime.now(),
      );
}

class StudyGroup {
  StudyGroup({required this.id, required this.name, this.description = '', this.icon = '', this.requireApproval = false,
      this.memberCount = 0, this.myStatus, this.myRole, required this.createdAt});

  final int id;
  final String name;
  final String description;
  final String icon;
  final bool requireApproval;
  final int memberCount;
  final String? myStatus; // null | pending | active
  final String? myRole; // leader | member
  final DateTime createdAt;

  bool get isMember => myStatus == 'active';
  bool get isLeader => myRole == 'leader' && isMember;
  bool get isPending => myStatus == 'pending';

  factory StudyGroup.fromJson(Map<String, dynamic> j) => StudyGroup(
        id: asInt(j['id']),
        name: asString(j['name']),
        description: asString(j['description']),
        icon: brandAsset(asString(j['icon'])),
        requireApproval: j['require_approval'] == true,
        memberCount: asInt(j['member_count']),
        myStatus: j['my_status'] as String?,
        myRole: j['my_role'] as String?,
        createdAt: parseDate(j['created_at']) ?? DateTime.now(),
      );
}

class GroupMemberInfo {
  GroupMemberInfo({required this.id, required this.user, required this.role, required this.status, this.requestMessage = '',
      this.weeklyXp = 0, this.lifetimeXp = 0});

  final int weeklyXp;
  final int lifetimeXp;

  final int id;
  final Author user;
  final String role;
  final String status;
  final String requestMessage;

  factory GroupMemberInfo.fromJson(Map<String, dynamic> j) => GroupMemberInfo(
        id: asInt(j['id']),
        user: Author.fromJson(asMap(j['user'])),
        role: asString(j['role']),
        status: asString(j['status']),
        requestMessage: asString(j['request_message']),
        weeklyXp: asInt(j['weekly_xp']),
        lifetimeXp: asInt(j['lifetime_xp']),
      );
}

class ChatMessage {
  ChatMessage({required this.id, required this.userId, required this.displayName, this.kind = 'text', this.content = '',
      this.sticker = '', this.badgeName, this.badgeIcon, this.clientId = '', required this.createdAt, this.pending = false});

  final int id;
  final int userId;
  final String displayName;
  final String kind;
  final String content;
  final String sticker;
  final String? badgeName;
  final String? badgeIcon;
  final String clientId;
  final DateTime createdAt;
  final bool pending;

  factory ChatMessage.fromJson(Map<String, dynamic> j) {
    final user = asMap(j['user'] ?? j['sender']);
    final badge = j['badge'] is Map ? asMap(j['badge']) : null;
    return ChatMessage(
      id: asInt(j['id']),
      userId: asInt(user['id']),
      displayName: asString(user['display_name']),
      kind: asString(j['kind'], 'text'),
      content: asString(j['content']),
      sticker: asString(j['sticker']),
      badgeName: badge?['name'] as String?,
      badgeIcon: badge?['icon'] as String?,
      clientId: asString(j['client_id']),
      createdAt: parseDate(j['created_at']) ?? DateTime.now(),
    );
  }
}

class CommunityProfile {
  CommunityProfile({required this.author, this.bio = '', this.followers = 0, this.following = 0, this.posts = 0,
      this.isFollowing = false, this.canMessage = false, this.blocked = false, this.lifetimeXp = 0, this.streak = 0, this.recentPosts = const [], this.groups = const []});

  final Author author;
  final String bio;
  final int followers;
  final int following;
  final int posts;
  final bool isFollowing;
  /// both follow each other and neither is a child account
  final bool canMessage;
  /// I blocked this person
  final bool blocked;
  final int lifetimeXp;
  final int streak;
  final List<Map<String, dynamic>> recentPosts; // {id, image}
  final List<Map<String, dynamic>> groups; // {id, name}

  factory CommunityProfile.fromJson(Map<String, dynamic> j) => CommunityProfile(
        author: Author.fromJson(j),
        bio: asString(j['bio']),
        followers: asInt(j['followers']),
        following: asInt(j['following']),
        posts: asInt(j['posts']),
        isFollowing: j['is_following'] == true,
        canMessage: j['can_message'] == true,
        blocked: j['blocked'] == true,
        lifetimeXp: asInt(j['lifetime_xp']),
        streak: asInt(j['streak']),
        recentPosts: asMapList(j['recent_posts']),
        groups: asMapList(j['groups']),
      );
}

class SupportConversation {
  SupportConversation({required this.id, this.subject = '', this.status = 'open', this.staffName, this.unread = 0, this.lastMessage});

  final int id;
  final String subject;
  final String status;
  final String? staffName;
  final int unread;
  final ChatMessage? lastMessage;

  factory SupportConversation.fromJson(Map<String, dynamic> j) => SupportConversation(
        id: asInt(j['id']),
        subject: asString(j['subject']),
        status: asString(j['status'], 'open'),
        staffName: j['staff_name'] as String?,
        unread: asInt(j['unread']),
        lastMessage: j['last_message'] is Map ? ChatMessage.fromJson(asMap(j['last_message'])) : null,
      );
}
