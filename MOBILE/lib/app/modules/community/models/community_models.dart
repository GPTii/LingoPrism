enum CommunityLeaderboardStatus { promotion, safe, demotion }

class CommunityLeagueInfo {
  CommunityLeagueInfo({
    required this.name,
    required this.rankIcon,
    required this.remainingLabel,
    this.xpCapDescription,
  });

  final String name;
  final String rankIcon;
  final String remainingLabel;
  final String? xpCapDescription;
}

class CommunityLeaderboardParticipant {
  CommunityLeaderboardParticipant({
    required this.userId,
    required this.name,
    required this.rank,
    required this.avatarUrl,
    required this.totalPoints,
    required this.status,
    this.rawPoints = 0,
  });

  final String userId;
  final String name;
  final int rank;
  final String avatarUrl;
  final int totalPoints;
  final int rawPoints;
  final CommunityLeaderboardStatus status;
}

class TournamentNotice {
  TournamentNotice({
    required this.headline,
    required this.leaderboardText,
    required this.groupText,
    required this.rewardText,
  });

  final String headline;
  final String leaderboardText;
  final String groupText;
  final String rewardText;
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
    this.status,
    this.createdAt,
  });

  final String groupId;
  final String name;
  final String requirement;
  final int memberCount;
  final String assetImage;
  final String leaderId;
  final String leaderName;
  final bool requireApproval;
  final String? description;
  final String? status;
  final DateTime? createdAt;
}

class CommunityGroupDetails {
  CommunityGroupDetails({
    required this.group,
    required this.currentMilestoneLabel,
    required this.remainingLabel,
    required this.currentPoints,
    required this.milestones,
    required this.memberScores,
  });

  final CommunityStudyGroup group;
  final String currentMilestoneLabel;
  final String remainingLabel;
  final int currentPoints;
  final List<String> milestones;
  final List<String> memberScores;
}
