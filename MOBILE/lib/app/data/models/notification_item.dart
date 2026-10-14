enum NotificationType {
  follow,
  postReaction,
  postComment,
  streak,
  rankUp,
  achievement,
}

class NotificationItem {
  final String id;
  final NotificationType type;
  final String title;
  final String? subtitle;
  final String? imagePath;
  final DateTime date;
  final bool hasAction;
  final String? actionText;
  final bool isRead;
  final String? actorId; // user who triggered the notification
  final String? targetUserId; // profile to open (for follow)
  final String? postId; // post to open (for likes/comments)
  final String? postPhotoId; // photo id for the post
  final int? streakCount; // streak milestone
  final Map<String, dynamic>? payload; // raw payload for deeper hydration

  NotificationItem({
    required this.id,
    required this.type,
    required this.title,
    this.subtitle,
    this.imagePath,
    required this.date,
    this.hasAction = false,
    this.actionText,
    this.isRead = false,
    this.actorId,
    this.targetUserId,
    this.postId,
    this.postPhotoId,
    this.streakCount,
    this.payload,
  });

  // Format date as dd/MM/yyyy
  String get formattedDate {
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }

  NotificationItem copyWith({
    String? id,
    NotificationType? type,
    String? title,
    String? subtitle,
    String? imagePath,
    DateTime? date,
    bool? hasAction,
    String? actionText,
    bool? isRead,
    String? actorId,
    String? targetUserId,
    String? postId,
    String? postPhotoId,
    int? streakCount,
    Map<String, dynamic>? payload,
  }) {
    return NotificationItem(
      id: id ?? this.id,
      type: type ?? this.type,
      title: title ?? this.title,
      subtitle: subtitle ?? this.subtitle,
      imagePath: imagePath ?? this.imagePath,
      date: date ?? this.date,
      hasAction: hasAction ?? this.hasAction,
      actionText: actionText ?? this.actionText,
      isRead: isRead ?? this.isRead,
      actorId: actorId ?? this.actorId,
      targetUserId: targetUserId ?? this.targetUserId,
      postId: postId ?? this.postId,
      postPhotoId: postPhotoId ?? this.postPhotoId,
      streakCount: streakCount ?? this.streakCount,
      payload: payload ?? this.payload,
    );
  }
}
