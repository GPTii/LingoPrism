/// Community Chat Models
///
/// Data models for the SnapLingua community chat feature including
/// chat messages, study groups, and group details.
///
/// Features:
/// - Comprehensive null safety and validation
/// - Enhanced business logic for chat functionality
/// - Professional documentation and structure
/// - Optimized data handling for performance
///
/// Author: Claude Code Assistant
/// Last updated: November 2024

/// Represents a chat message in a community group
///
/// Includes sender information, message content, user status indicators,
/// and support for different message types including text and stickers.
class CommunityChatMessage {
  CommunityChatMessage({
    required this.senderName,
    required this.content,
    required this.isCurrentUser,
    required this.isLeader,
    this.isSticker = false,
    this.timestamp,
    this.messageId,
  });

  /// Name of the message sender with leader indicator
  final String senderName;

  /// Message content - can be text or sticker path
  final String content;

  /// Whether this message was sent by the current user
  final bool isCurrentUser;

  /// Whether the sender is a group leader
  final bool isLeader;

  /// Whether this is a sticker message vs text message
  final bool isSticker;

  /// Optional timestamp for message ordering
  final DateTime? timestamp;

  /// Optional unique identifier for the message
  final String? messageId;

  /// Validated content with safety checks
  String get validatedContent {
    final trimmed = content.trim();
    if (trimmed.isEmpty) {
      return isSticker ? '🖼️ Sticker' : 'Tin nhắn trống';
    }
    // Limit content length for display
    if (!isSticker && trimmed.length > 1000) {
      return '${trimmed.substring(0, 997)}...';
    }
    return trimmed;
  }

  /// Validated sender name with fallback
  String get validatedSenderName {
    final trimmed = senderName.trim();
    if (trimmed.isEmpty) {
      return isCurrentUser ? 'Bạn' : 'Thành viên SnapLingua';
    }
    // Limit name length for display
    if (trimmed.length > 50) {
      return '${trimmed.substring(0, 47)}...';
    }
    return trimmed;
  }

  /// Creates a copy with updated fields
  CommunityChatMessage copyWith({
    String? senderName,
    String? content,
    bool? isCurrentUser,
    bool? isLeader,
    bool? isSticker,
    DateTime? timestamp,
    String? messageId,
  }) {
    return CommunityChatMessage(
      senderName: senderName ?? this.senderName,
      content: content ?? this.content,
      isCurrentUser: isCurrentUser ?? this.isCurrentUser,
      isLeader: isLeader ?? this.isLeader,
      isSticker: isSticker ?? this.isSticker,
      timestamp: timestamp ?? this.timestamp,
      messageId: messageId ?? this.messageId,
    );
  }
}

/// Represents a community study group
///
/// Contains group metadata including member information, requirements,
/// and visual assets with comprehensive validation and null safety.
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
    this.status,
    this.createdAt,
  });

  /// Unique identifier for the study group
  final String groupId;

  /// Display name of the group
  final String name;

  /// Group joining requirements
  final String requirement;

  /// Current number of group members
  final int memberCount;

  /// Path to group visual asset/icon
  final String assetImage;

  /// User ID of the group leader
  final String leaderId;

  /// Display name of the group leader
  final String leaderName;

  /// Whether new members need approval to join
  final bool requireApproval;

  /// Optional group description
  final String? description;

  /// Optional group status indicator
  final String? status;

  /// Optional creation timestamp
  final DateTime? createdAt;

  /// Validated group name with fallback
  String get validatedName {
    final trimmed = name.trim();
    if (trimmed.isEmpty) {
      return 'Nhóm học tập #${groupId.split('').take(6).join('')}';
    }
    if (trimmed.length > 50) {
      return '${trimmed.substring(0, 47)}...';
    }
    return trimmed;
  }

  /// Validated member count with bounds checking
  int get validatedMemberCount {
    return memberCount.clamp(0, 999999);
  }

  /// Validated requirement text
  String get validatedRequirement {
    final trimmed = requirement.trim();
    if (trimmed.isEmpty) {
      return 'Không có yêu cầu đặc biệt';
    }
    if (trimmed.length > 100) {
      return '${trimmed.substring(0, 97)}...';
    }
    return trimmed;
  }

  /// Validated leader name with fallback
  String get validatedLeaderName {
    final trimmed = leaderName.trim();
    if (trimmed.isEmpty) {
      return 'Trưởng nhóm';
    }
    if (trimmed.length > 30) {
      return '${trimmed.substring(0, 27)}...';
    }
    return trimmed;
  }

  /// Validated asset path with fallback
  String get validatedAssetImage {
    final trimmed = assetImage.trim();
    if (trimmed.isEmpty || !trimmed.startsWith('assets/')) {
      return 'assets/images/nhom/nhom_default.png';
    }
    return trimmed;
  }
}

/// Detailed information about a community group
///
/// Extended group information including milestones, progress tracking,
/// and member scores with validation and performance optimizations.
class CommunityGroupDetails {
  CommunityGroupDetails({
    required this.group,
    required this.currentMilestoneLabel,
    required this.remainingLabel,
    required this.currentPoints,
    required this.milestones,
    required this.memberScores,
  });

  /// The core study group information
  final CommunityStudyGroup group;

  /// Current milestone description
  final String currentMilestoneLabel;

  /// Time remaining label
  final String remainingLabel;

  /// Current group points/progress
  final int currentPoints;

  /// List of milestone descriptions
  final List<String> milestones;

  /// List of member score summaries
  final List<String> memberScores;

  /// Validated milestone label
  String get validatedMilestoneLabel {
    final trimmed = currentMilestoneLabel.trim();
    if (trimmed.isEmpty) {
      return 'Mốc tiếp theo';
    }
    return trimmed;
  }

  /// Validated remaining time label
  String get validatedRemainingLabel {
    final trimmed = remainingLabel.trim();
    if (trimmed.isEmpty) {
      return 'Không xác định';
    }
    return trimmed;
  }

  /// Validated current points with bounds checking
  int get validatedCurrentPoints {
    return currentPoints.clamp(0, 999999);
  }

  /// Validated milestones list with safety checks
  List<String> get validatedMilestones {
    return milestones
        .where((milestone) => milestone.trim().isNotEmpty)
        .take(20) // Limit to prevent performance issues
        .toList();
  }

  /// Validated member scores with safety checks
  List<String> get validatedMemberScores {
    return memberScores
        .where((score) => score.trim().isNotEmpty)
        .take(50) // Limit to prevent performance issues
        .toList();
  }

  /// Creates a copy with updated fields
  CommunityGroupDetails copyWith({
    CommunityStudyGroup? group,
    String? currentMilestoneLabel,
    String? remainingLabel,
    int? currentPoints,
    List<String>? milestones,
    List<String>? memberScores,
  }) {
    return CommunityGroupDetails(
      group: group ?? this.group,
      currentMilestoneLabel: currentMilestoneLabel ?? this.currentMilestoneLabel,
      remainingLabel: remainingLabel ?? this.remainingLabel,
      currentPoints: currentPoints ?? this.currentPoints,
      milestones: milestones ?? this.milestones,
      memberScores: memberScores ?? this.memberScores,
    );
  }
}